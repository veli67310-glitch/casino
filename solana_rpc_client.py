#!/usr/bin/env python3
"""
Solana RPC Client - Enhanced Blockchain Integration
Comprehensive Solana RPC connection with wallet validation and transaction monitoring
"""

import asyncio
import logging
import json
import time
import base58
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
import aiohttp
import websockets
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction
from solders.signature import Signature
from solders.system_program import ID as SYSTEM_PROGRAM_ID
import requests

from config import SOLANA_CONFIG

logger = logging.getLogger(__name__)

class SolanaRPCClient:
    """Enhanced Solana RPC Client with comprehensive blockchain integration"""

    def __init__(self):
        self.config = SOLANA_CONFIG
        self.rpc_url = self.config["rpc_url"]
        self.websocket_url = self.config["websocket_url"]
        self.commitment = Commitment(self.config["commitment"])
        self.timeout = self.config["timeout"]
        self.max_retries = self.config["max_retries"]
        self.retry_delay = self.config["retry_delay"]

        # Rate limiting
        self.request_interval = 1.0  # Minimum seconds between requests
        self.last_request_time = 0
        self.rate_limit_backoff = 1.0
        self.max_backoff = 60.0

        # Initialize clients
        self.client = None
        self.websocket = None
        self.is_connected = False
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds

        # Admin wallet setup
        self.admin_wallet = self.config["admin_wallet"]
        self.admin_keypair = None
        if self.config["admin_private_key"]:
            try:
                self.admin_keypair = Keypair.from_secret_key(
                    base58.b58decode(self.config["admin_private_key"])
                )
                logger.info("Admin wallet keypair loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load admin keypair: {e}")

        # Connection stats
        self.connection_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "reconnections": 0,
            "last_error": None,
            "uptime_start": datetime.now()
        }

    async def connect(self) -> bool:
        """Initialize RPC connection with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                self.client = AsyncClient(
                    self.rpc_url,
                    commitment=self.commitment
                )

                # Test connection
                health = await self.get_health()
                if health:
                    self.is_connected = True
                    self.last_health_check = time.time()
                    logger.info(f"Solana RPC connected successfully to {self.rpc_url}")
                    return True

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        self.connection_stats["failed_requests"] += 1
        self.connection_stats["last_error"] = "Connection failed"
        logger.error("Failed to connect to Solana RPC after all retries")
        return False

    async def disconnect(self):
        """Close RPC connection"""
        try:
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
            if self.client:
                await self.client.close()
            self.is_connected = False
            logger.info("Solana RPC connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    async def ensure_connection(self) -> bool:
        """Ensure connection is active, reconnect if needed"""
        current_time = time.time()

        # Health check interval
        if current_time - self.last_health_check > self.health_check_interval:
            if not await self.get_health():
                logger.warning("Health check failed, attempting reconnection")
                self.is_connected = False

        # Reconnect if needed
        if not self.is_connected:
            self.connection_stats["reconnections"] += 1
            return await self.connect()

        return True

    async def get_health(self) -> bool:
        """Check RPC endpoint health"""
        try:
            if not self.client:
                return False

            # Use get_slot as health check instead of get_health (which doesn't exist in newer API)
            response = await self.client.get_slot()
            self.last_health_check = time.time()
            self.connection_stats["successful_requests"] += 1
            return response is not None and response.value is not None

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.connection_stats["failed_requests"] += 1
            self.connection_stats["last_error"] = str(e)
            return False

    def validate_wallet_address(self, address: str) -> Dict[str, Any]:
        """Validate Solana wallet address format and structure"""
        result = {
            "is_valid": False,
            "address": address,
            "error": None,
            "format_checks": {
                "length": False,
                "encoding": False,
                "checksum": False
            }
        }

        try:
            if not address or not isinstance(address, str):
                result["error"] = "Address must be a non-empty string"
                return result

            # Length check (Solana addresses are 32 bytes -> 44 chars in base58)
            if len(address) < 32 or len(address) > 44:
                result["error"] = f"Invalid address length: {len(address)} (expected 32-44)"
                return result

            result["format_checks"]["length"] = True

            # Base58 encoding check
            try:
                decoded = base58.b58decode(address)
                result["format_checks"]["encoding"] = True
            except Exception as e:
                result["error"] = f"Invalid base58 encoding: {str(e)}"
                return result

            # Length check for decoded bytes
            if len(decoded) != 32:
                result["error"] = f"Decoded address wrong length: {len(decoded)} (expected 32)"
                return result

            # Try to create PublicKey object (additional validation)
            try:
                pubkey = PublicKey.from_string(address)
                result["format_checks"]["checksum"] = True
                result["is_valid"] = True
                result["pubkey_object"] = pubkey

            except Exception as e:
                result["error"] = f"Invalid public key format: {str(e)}"
                return result

        except Exception as e:
            result["error"] = f"Validation error: {str(e)}"

        return result

    async def get_account_info(self, address: str) -> Dict[str, Any]:
        """Get detailed account information with rate limiting"""
        if not await self.ensure_connection():
            return {"error": "Connection failed", "balance": 0}

        validation = self.validate_wallet_address(address)
        if not validation["is_valid"]:
            return {"error": validation["error"], "balance": 0}

        # Apply rate limiting
        await self._apply_rate_limiting()

        try:
            self.connection_stats["total_requests"] += 1

            pubkey = PublicKey.from_string(address)
            account_info = await self.client.get_account_info(pubkey)

            result = {
                "address": address,
                "exists": account_info.value is not None,
                "balance": 0,
                "executable": False,
                "owner": None,
                "rent_epoch": None
            }

            if account_info.value:
                result.update({
                    "balance": account_info.value.lamports,
                    "executable": account_info.value.executable,
                    "owner": str(account_info.value.owner),
                    "rent_epoch": account_info.value.rent_epoch,
                    "data_size": len(account_info.value.data) if account_info.value.data else 0
                })

            self.connection_stats["successful_requests"] += 1
            return result

        except Exception as e:
            logger.error(f"Error getting account info for {address}: {e}")
            self.connection_stats["failed_requests"] += 1
            self.connection_stats["last_error"] = str(e)
            return {"error": str(e), "balance": 0}

    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get SOL balance for address"""
        account_info = await self.get_account_info(address)

        if "error" in account_info:
            return account_info

        balance_sol = account_info["balance"] / 1_000_000_000  # Convert lamports to SOL

        return {
            "address": address,
            "balance_lamports": account_info["balance"],
            "balance_sol": balance_sol,
            "exists": account_info["exists"]
        }

    async def _apply_rate_limiting(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_interval:
            wait_time = self.request_interval - time_since_last
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def _handle_rate_limit_error(self):
        """Handle rate limiting with exponential backoff"""
        self.connection_stats["rate_limited_requests"] += 1
        self.rate_limit_backoff = min(self.rate_limit_backoff * 2, self.max_backoff)
        logger.warning(f"Rate limited, backing off for {self.rate_limit_backoff} seconds")
        await asyncio.sleep(self.rate_limit_backoff)

    async def _reset_rate_limit_backoff(self):
        """Reset rate limit backoff on successful request"""
        self.rate_limit_backoff = 1.0

    async def get_transaction_details(self, signature: str) -> Dict[str, Any]:
        """Get detailed transaction information with improved error handling"""
        if not await self.ensure_connection():
            return {"error": "Connection failed"}

        # Apply rate limiting
        await self._apply_rate_limiting()

        try:
            self.connection_stats["total_requests"] += 1

            # Validate signature format
            try:
                sig = Signature.from_string(signature)
            except Exception as e:
                return {"error": f"Invalid signature format: {str(e)}"}

            # Get transaction details with timeout
            tx_info = await asyncio.wait_for(
                self.client.get_transaction(
                    sig,
                    encoding="json",
                    commitment=self.commitment,
                    max_supported_transaction_version=0
                ),
                timeout=self.timeout
            )

            if not tx_info.value:
                logger.warning(f"Transaction not found: {signature}")
                return {"error": "Transaction not found", "signature": signature}

            tx_data = tx_info.value

            # Parse transaction details with safe attribute access
            meta = getattr(tx_data.transaction, 'meta', None) if hasattr(tx_data, 'transaction') else None

            result = {
                "signature": signature,
                "slot": getattr(tx_data, 'slot', None),
                "block_time": getattr(tx_data, 'block_time', None),
                "confirmations": "finalized",  # Transaction is already confirmed when retrieved
                "fee": getattr(meta, 'fee', 0) if meta else 0,
                "success": not bool(getattr(meta, 'err', None)) if meta else False,
                "error": str(meta.err) if meta and getattr(meta, 'err', None) else None,
                "accounts": [],
                "instructions": [],
                "balance_changes": []
            }

            # Parse account keys and balance changes with safe access
            try:
                transaction = getattr(tx_data, 'transaction', None)
                if transaction and hasattr(transaction, 'transaction'):
                    inner_transaction = getattr(transaction, 'transaction', None)
                    message = getattr(inner_transaction, 'message', None) if inner_transaction else None

                    if message and hasattr(message, 'account_keys'):
                        result["accounts"] = [str(acc) for acc in message.account_keys]

                    # Parse balance changes
                    if meta and hasattr(meta, 'pre_balances') and hasattr(meta, 'post_balances'):
                        pre_balances = getattr(meta, 'pre_balances', [])
                        post_balances = getattr(meta, 'post_balances', [])

                        if pre_balances and post_balances:
                            for i, account in enumerate(result["accounts"]):
                                if i < len(pre_balances) and i < len(post_balances):
                                    change = post_balances[i] - pre_balances[i]
                                    if change != 0:
                                        result["balance_changes"].append({
                                            "account": account,
                                            "pre_balance": pre_balances[i],
                                            "post_balance": post_balances[i],
                                            "change_lamports": change,
                                            "change_sol": change / 1_000_000_000
                                        })
            except Exception as parse_error:
                logger.warning(f"Error parsing transaction details for {signature}: {parse_error}")

            self.connection_stats["successful_requests"] += 1
            await self._reset_rate_limit_backoff()
            return result

        except asyncio.TimeoutError:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.warning(f"Timeout getting transaction details for {signature}")
            self.connection_stats["failed_requests"] += 1
            self.connection_stats["last_error"] = error_msg
            return {"error": error_msg, "retry": True}

        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"

            # Enhanced error handling for common Solana RPC errors
            if any(keyword in error_msg.lower() for keyword in ["503", "service unavailable", "server error"]):
                logger.warning(f"Solana RPC temporarily unavailable for {signature}")
                await asyncio.sleep(5)  # Wait before retry
                return {"error": "RPC temporarily unavailable", "retry": True}

            elif any(keyword in error_msg.lower() for keyword in ["429", "rate limit", "too many requests"]):
                logger.warning(f"Rate limited for transaction {signature}")
                await self._handle_rate_limit_error()
                return {"error": "Rate limited", "retry": True}

            elif any(keyword in error_msg.lower() for keyword in ["not found", "404", "does not exist"]):
                logger.debug(f"Transaction {signature} not found yet")
                return {"error": "Transaction not found", "retry": False}

            elif any(keyword in error_msg.lower() for keyword in ["connection", "network", "timeout"]):
                logger.warning(f"Network error for transaction {signature}: {error_msg}")
                self.is_connected = False  # Force reconnection
                return {"error": "Network error", "retry": True}

            elif "json" in error_msg.lower() or "parse" in error_msg.lower():
                logger.error(f"JSON parsing error for {signature}: {error_msg}")
                return {"error": "Data parsing error", "retry": False}

            logger.error(f"Error getting transaction details for {signature}: {error_msg}")
            self.connection_stats["failed_requests"] += 1
            self.connection_stats["last_error"] = error_msg
            return {"error": error_msg, "retry": False}

    async def get_signatures_for_address(self, address: str, limit: int = 10, before: str = None) -> Dict[str, Any]:
        """Get transaction signatures for address with rate limiting"""
        if not await self.ensure_connection():
            return {"error": "Connection failed", "signatures": []}

        validation = self.validate_wallet_address(address)
        if not validation["is_valid"]:
            return {"error": validation["error"], "signatures": []}

        # Apply rate limiting
        await self._apply_rate_limiting()

        try:
            self.connection_stats["total_requests"] += 1

            pubkey = PublicKey.from_string(address)

            # Build options
            options = {"limit": min(limit, 1000)}  # Max 1000 per request
            if before:
                try:
                    options["before"] = Signature.from_string(before)
                except:
                    return {"error": "Invalid 'before' signature format", "signatures": []}

            signatures_info = await self.client.get_signatures_for_address(
                pubkey,
                commitment=self.commitment,
                **options
            )

            result = {
                "address": address,
                "signatures": [],
                "count": 0
            }

            if signatures_info.value:
                for sig_info in signatures_info.value:
                    result["signatures"].append({
                        "signature": str(sig_info.signature),
                        "slot": sig_info.slot,
                        "err": str(sig_info.err) if sig_info.err else None,
                        "memo": sig_info.memo,
                        "block_time": sig_info.block_time
                    })

                result["count"] = len(result["signatures"])

            self.connection_stats["successful_requests"] += 1
            await self._reset_rate_limit_backoff()
            return result

        except Exception as e:
            error_msg = str(e)

            # Handle rate limiting and network errors
            if any(keyword in error_msg.lower() for keyword in ["429", "rate limit", "too many requests"]):
                await self._handle_rate_limit_error()
            elif any(keyword in error_msg.lower() for keyword in ["503", "service unavailable", "network"]):
                await asyncio.sleep(5)

            logger.error(f"Error getting signatures for address {address}: {e}")
            self.connection_stats["failed_requests"] += 1
            self.connection_stats["last_error"] = str(e)
            return {"error": str(e), "signatures": []}

    async def monitor_address_transactions(self, address: str, callback=None, poll_interval: int = 10):
        """Monitor address for new transactions"""
        if not await self.ensure_connection():
            logger.error("Cannot start monitoring: connection failed")
            return

        validation = self.validate_wallet_address(address)
        if not validation["is_valid"]:
            logger.error(f"Cannot monitor invalid address: {validation['error']}")
            return

        logger.info(f"Starting transaction monitoring for address: {address}")
        last_signature = None

        try:
            # Get initial signature to start monitoring from
            initial_sigs = await self.get_signatures_for_address(address, limit=1)
            if initial_sigs.get("signatures"):
                last_signature = initial_sigs["signatures"][0]["signature"]
                logger.info(f"Starting monitoring from signature: {last_signature}")

            while True:
                try:
                    # Get new signatures
                    new_sigs = await self.get_signatures_for_address(
                        address,
                        limit=10,
                        before=last_signature if last_signature else None
                    )

                    if new_sigs.get("signatures"):
                        for sig_info in reversed(new_sigs["signatures"]):  # Process oldest first
                            if sig_info["signature"] != last_signature:
                                # Get full transaction details
                                tx_details = await self.get_transaction_details(sig_info["signature"])

                                # Call callback if provided
                                if callback:
                                    try:
                                        await callback(address, sig_info, tx_details)
                                    except Exception as e:
                                        logger.error(f"Callback error: {e}")

                                logger.info(f"New transaction detected: {sig_info['signature']}")

                        # Update last signature
                        last_signature = new_sigs["signatures"][0]["signature"]

                    await asyncio.sleep(poll_interval)

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(poll_interval * 2)  # Wait longer on errors

        except asyncio.CancelledError:
            logger.info(f"Transaction monitoring cancelled for address: {address}")
        except Exception as e:
            logger.error(f"Fatal error in transaction monitoring: {e}")

    async def send_sol_transaction(self, to_address: str, amount_sol: float, memo: str = None) -> Dict[str, Any]:
        """Send SOL transaction (requires admin keypair)"""
        if not self.admin_keypair:
            return {"error": "Admin keypair not configured"}

        if not await self.ensure_connection():
            return {"error": "Connection failed"}

        validation = self.validate_wallet_address(to_address)
        if not validation["is_valid"]:
            return {"error": f"Invalid recipient address: {validation['error']}"}

        try:
            self.connection_stats["total_requests"] += 1

            # Convert SOL to lamports
            amount_lamports = int(amount_sol * 1_000_000_000)

            if amount_lamports <= 0:
                return {"error": "Amount must be greater than 0"}

            # Check admin wallet balance
            admin_balance = await self.get_balance(str(self.admin_keypair.public_key))
            if admin_balance.get("balance_lamports", 0) < amount_lamports + 5000:  # +5000 for transaction fee
                return {"error": "Insufficient admin wallet balance"}

            # Create transaction
            recipient_pubkey = PublicKey.from_string(to_address)
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.admin_keypair.public_key,
                    to_pubkey=recipient_pubkey,
                    lamports=amount_lamports
                )
            )

            # Get recent blockhash
            recent_blockhash_resp = await self.client.get_recent_blockhash(commitment=self.commitment)
            recent_blockhash = recent_blockhash_resp.value.blockhash

            # Build and sign transaction
            transaction = Transaction()
            transaction.add(transfer_ix)
            transaction.recent_blockhash = recent_blockhash
            transaction.fee_payer = self.admin_keypair.public_key
            transaction.sign(self.admin_keypair)

            # Send transaction
            tx_response = await self.client.send_transaction(
                transaction,
                self.admin_keypair,
                opts=TxOpts(
                    skip_confirmation=False,
                    preflight_commitment=self.commitment
                )
            )

            signature = str(tx_response.value)

            # Wait for confirmation
            confirmation = await self.client.confirm_transaction(
                tx_response.value,
                commitment=self.commitment
            )

            result = {
                "signature": signature,
                "success": confirmation.value[0].confirmation_status is not None,
                "from_address": str(self.admin_keypair.public_key),
                "to_address": to_address,
                "amount_sol": amount_sol,
                "amount_lamports": amount_lamports,
                "memo": memo
            }

            if confirmation.value[0].err:
                result["error"] = str(confirmation.value[0].err)
                result["success"] = False

            self.connection_stats["successful_requests"] += 1
            return result

        except Exception as e:
            logger.error(f"Error sending SOL transaction: {e}")
            self.connection_stats["failed_requests"] += 1
            self.connection_stats["last_error"] = str(e)
            return {"error": str(e)}

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        uptime = datetime.now() - self.connection_stats["uptime_start"]

        return {
            "is_connected": self.is_connected,
            "rpc_url": self.rpc_url,
            "network": self.config["network"],
            "admin_wallet": self.admin_wallet,
            "admin_keypair_loaded": self.admin_keypair is not None,
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self.connection_stats["total_requests"],
            "successful_requests": self.connection_stats["successful_requests"],
            "failed_requests": self.connection_stats["failed_requests"],
            "success_rate": (
                self.connection_stats["successful_requests"] / self.connection_stats["total_requests"]
                if self.connection_stats["total_requests"] > 0 else 0
            ),
            "reconnections": self.connection_stats["reconnections"],
            "last_error": self.connection_stats["last_error"],
            "last_health_check": datetime.fromtimestamp(self.last_health_check) if self.last_health_check else None
        }

# Global instance
_solana_rpc_client = None

def get_solana_rpc_client() -> SolanaRPCClient:
    """Get global Solana RPC client instance"""
    global _solana_rpc_client
    if _solana_rpc_client is None:
        _solana_rpc_client = SolanaRPCClient()
    return _solana_rpc_client

# Convenience functions
async def validate_solana_address(address: str) -> Dict[str, Any]:
    """Validate Solana address"""
    client = get_solana_rpc_client()
    return client.validate_wallet_address(address)

async def get_solana_balance(address: str) -> Dict[str, Any]:
    """Get SOL balance for address"""
    client = get_solana_rpc_client()
    return await client.get_balance(address)

async def monitor_solana_address(address: str, callback=None, poll_interval: int = 10):
    """Monitor Solana address for transactions"""
    client = get_solana_rpc_client()
    await client.monitor_address_transactions(address, callback, poll_interval)

if __name__ == "__main__":
    # Test the client
    async def test_client():
        client = get_solana_rpc_client()

        # Test connection
        connected = await client.connect()
        print(f"Connected: {connected}")

        if connected:
            # Test address validation
            test_address = "DsJd8pDi44f82dRjG3zBnxrv2t32ZyfKUjz5cqFkdrY9"
            validation = client.validate_wallet_address(test_address)
            print(f"Address validation: {validation}")

            # Test balance check
            balance = await client.get_balance(test_address)
            print(f"Balance: {balance}")

            # Test connection stats
            stats = await client.get_connection_stats()
            print(f"Connection stats: {stats}")

        await client.disconnect()

    asyncio.run(test_client())