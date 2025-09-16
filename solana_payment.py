#!/usr/bin/env python3
"""
Enhanced Solana Payment System
Comprehensive Solana payment integration with RPC connection and monitoring
"""

import asyncio
import logging
import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import requests

# Import enhanced Solana components
from solana_rpc_client import get_solana_rpc_client, validate_solana_address
from solana_transaction_monitor import get_transaction_monitor, monitor_deposit_address
from solana_admin_wallet import get_admin_wallet_manager, WalletRole
from config import SOLANA_CONFIG

logger = logging.getLogger(__name__)

class SolanaPaymentSystem:
    """Enhanced Solana payment system with RPC integration"""

    def __init__(self, db_path: str = "casino_bot.db"):
        self.db_path = db_path
        self.config = SOLANA_CONFIG

        # Enhanced configuration
        self.sol_rate = 0.01  # 1 SOL = 100 FC (ayarlanabilir)
        self.min_deposit = self.config.get("min_sol_amount", 0.001)
        self.min_withdrawal = self.config.get("min_sol_amount", 0.001)
        self.withdrawal_fee_rate = 0.01  # %1 komisyon oranı
        self.admin_wallet = self.config["admin_wallet"]

        # Enhanced components
        self.rpc_client = get_solana_rpc_client()
        self.transaction_monitor = get_transaction_monitor()
        self.admin_wallet_manager = get_admin_wallet_manager()

        # Connection state
        self.is_connected = False

        # Initialize database tables and connections
        self.init_solana_tables()
        # Initialize connections will be called after event loop is available
        self._connections_initialized = False

    async def initialize_connections(self):
        """Initialize RPC connections and monitoring"""
        try:
            # Connect to Solana RPC
            connected = await self.rpc_client.connect()
            if connected:
                self.is_connected = True
                logger.info("Solana RPC connection established")

                # Start monitoring admin wallet
                await self.transaction_monitor.add_address_to_monitor(
                    self.admin_wallet,
                    "Main Admin Wallet",
                    self._admin_wallet_callback
                )

                logger.info("Solana payment system fully initialized")
            else:
                logger.error("Failed to connect to Solana RPC")

        except Exception as e:
            logger.error(f"Error initializing Solana connections: {e}")

    async def _admin_wallet_callback(self, address: str, transaction):
        """Callback for admin wallet transactions"""
        try:
            logger.info(f"Admin wallet transaction: {transaction.signature} - {transaction.amount_sol} SOL")
            # Additional admin wallet logic can be added here
        except Exception as e:
            logger.error(f"Error in admin wallet callback: {e}")

    async def ensure_initialized(self):
        """Ensure connections are initialized"""
        if not self._connections_initialized:
            await self.initialize_connections()
            self._connections_initialized = True

    def init_solana_tables(self):
        """Initialize Solana payment tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Solana deposits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS solana_deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sol_amount REAL NOT NULL,
                    fc_amount INTEGER NOT NULL,
                    transaction_hash TEXT,
                    wallet_address TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Solana withdrawals table  
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS solana_withdrawals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    fc_amount INTEGER NOT NULL,
                    sol_amount REAL NOT NULL,
                    fee_amount REAL NOT NULL,
                    user_wallet TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    admin_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    transaction_hash TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Solana rates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS solana_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sol_to_fc_rate REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default rate if not exists
            cursor.execute("SELECT COUNT(*) FROM solana_rates")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO solana_rates (sol_to_fc_rate) VALUES (?)", (1/self.sol_rate,))
            
            conn.commit()
            conn.close()
            logger.info("Solana payment tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Solana tables: {e}")
    
    def get_sol_to_fc_rate(self) -> float:
        """Get current SOL to FC conversion rate"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sol_to_fc_rate FROM solana_rates ORDER BY updated_at DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else (1/self.sol_rate)
        except:
            return (1/self.sol_rate)  # Default 100 FC per SOL

    def get_sol_usd_price(self) -> float:
        """Get approximate SOL price in USD"""
        # Fixed rate for now - can be updated to use live API later
        return 130.0  # ~130 USD per SOL

    def usd_to_sol_amount(self, usd_amount: float) -> float:
        """Convert USD amount to SOL"""
        sol_price = self.get_sol_usd_price()
        return usd_amount / sol_price
    
    def update_sol_rate(self, new_rate: float):
        """Update SOL to FC conversion rate"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO solana_rates (sol_to_fc_rate) VALUES (?)", (new_rate,))
            conn.commit()
            conn.close()
            self.sol_rate = 1/new_rate
            logger.info(f"SOL rate updated to: 1 SOL = {new_rate} FC")
        except Exception as e:
            logger.error(f"Error updating SOL rate: {e}")
    
    def create_deposit_request(self, user_id: int, sol_amount: float) -> Dict[str, Any]:
        """Create a SOL deposit request - uses single centralized wallet"""
        try:
            # Minimum kontrol kaldırıldı - tüm miktarlar kabul edilir
            if sol_amount <= 0:
                return {
                    "success": False,
                    "error": "Yatırım miktarı 0'dan büyük olmalıdır"
                }

            fc_amount = int(sol_amount * self.get_sol_to_fc_rate())

            # Use single centralized deposit wallet
            deposit_wallet = self.get_deposit_wallet()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Store deposit request with centralized wallet
            cursor.execute("""
                INSERT INTO solana_deposits (user_id, sol_amount, fc_amount, wallet_address, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (user_id, sol_amount, fc_amount, deposit_wallet))

            deposit_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Created deposit request for user {user_id}: {sol_amount} SOL -> {fc_amount} FC")

            return {
                "success": True,
                "deposit_id": deposit_id,
                "sol_amount": sol_amount,
                "fc_amount": fc_amount,
                "wallet_address": deposit_wallet,
                "rate": self.get_sol_to_fc_rate(),
                "note": "Otomatik işlenecek - Ödeme sonrası anında yüklenecek"
            }

        except Exception as e:
            logger.error(f"Error creating deposit request: {e}")
            return {"success": False, "error": "Yatırım talebi oluşturulamadı"}
    
    def get_deposit_wallet(self) -> str:
        """Get the single centralized deposit wallet address"""
        return self.admin_wallet

    async def validate_user_wallet_address(self, address: str) -> Dict[str, Any]:
        """Validate user's wallet address for withdrawals"""
        try:
            await self.ensure_initialized()
            # Use enhanced RPC client validation
            validation = await validate_solana_address(address)

            if validation.get("is_valid"):
                # Additional checks for withdrawal wallets
                account_info = await self.rpc_client.get_account_info(address)

                return {
                    "is_valid": True,
                    "address": address,
                    "exists_on_chain": account_info.get("exists", False),
                    "balance_sol": account_info.get("balance", 0) / 1_000_000_000,
                    "can_receive": True
                }
            else:
                return {
                    "is_valid": False,
                    "address": address,
                    "error": validation.get("error", "Invalid address format")
                }

        except Exception as e:
            logger.error(f"Error validating wallet address: {e}")
            return {
                "is_valid": False,
                "address": address,
                "error": str(e)
            }

    def get_pending_deposits(self) -> list:
        """Get all pending deposit requests (admin function)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT d.id, d.user_id, u.username, d.sol_amount, d.fc_amount,
                       d.wallet_address, d.created_at, d.status
                FROM solana_deposits d
                JOIN users u ON d.user_id = u.user_id
                WHERE d.status = 'pending'
                ORDER BY d.created_at ASC
            """)

            results = cursor.fetchall()
            conn.close()

            deposits = []
            for row in results:
                deposits.append({
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "sol_amount": row[3],
                    "fc_amount": row[4],
                    "wallet_address": row[5],
                    "created_at": row[6],
                    "status": row[7]
                })

            return deposits

        except Exception as e:
            logger.error(f"Error getting pending deposits: {e}")
            return []
    
    def confirm_deposit(self, deposit_id: int, transaction_hash: str) -> Dict[str, Any]:
        """Confirm a SOL deposit (admin function)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get deposit details
            cursor.execute("""
                SELECT user_id, fc_amount, status FROM solana_deposits 
                WHERE id = ?
            """, (deposit_id,))
            
            result = cursor.fetchone()
            if not result:
                return {"success": False, "error": "Yatırım bulunamadı"}
            
            user_id, fc_amount, status = result
            
            if status == 'confirmed':
                return {"success": False, "error": "Bu yatırım zaten onaylanmış"}
            
            # Update deposit status
            cursor.execute("""
                UPDATE solana_deposits 
                SET status = 'confirmed', transaction_hash = ?, confirmed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (transaction_hash, deposit_id))
            
            # Add FC to user balance
            cursor.execute("""
                UPDATE users SET fun_coins = fun_coins + ?
                WHERE user_id = ?
            """, (fc_amount, user_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "user_id": user_id,
                "fc_amount": fc_amount,
                "deposit_id": deposit_id
            }
            
        except Exception as e:
            logger.error(f"Error confirming deposit: {e}")
            return {"success": False, "error": "Yatırım onaylanamadı"}

    def approve_deposit(self, deposit_id: int) -> Dict[str, Any]:
        """Admin function to approve a deposit"""
        from solana_payment_extensions import get_solana_extensions
        extensions = get_solana_extensions()
        return extensions.approve_deposit(deposit_id)

    def reject_deposit(self, deposit_id: int) -> Dict[str, Any]:
        """Admin function to reject a deposit"""
        from solana_payment_extensions import get_solana_extensions
        extensions = get_solana_extensions()
        return extensions.reject_deposit(deposit_id)

    def get_deposit_details(self, deposit_id: int) -> Dict[str, Any]:
        """Get detailed information about a deposit"""
        from solana_payment_extensions import get_solana_extensions
        extensions = get_solana_extensions()
        return extensions.get_deposit_details(deposit_id)

    def reject_withdrawal(self, withdrawal_id: int, reason: str = "Admin tarafından reddedildi") -> Dict[str, Any]:
        """Admin function to reject a withdrawal and restore user balance"""
        from solana_payment_extensions import get_solana_extensions
        extensions = get_solana_extensions()
        return extensions.reject_withdrawal(withdrawal_id, reason)

    def approve_withdrawal(self, withdrawal_id: int) -> Dict[str, Any]:
        """Admin function to approve a withdrawal for processing"""
        from solana_payment_extensions import get_solana_extensions
        extensions = get_solana_extensions()
        return extensions.approve_withdrawal(withdrawal_id)

    def get_withdrawal_details(self, withdrawal_id: int) -> Dict[str, Any]:
        """Get detailed information about a withdrawal"""
        from solana_payment_extensions import get_solana_extensions
        extensions = get_solana_extensions()
        return extensions.get_withdrawal_details(withdrawal_id)
    
    async def create_withdrawal_request(self, user_id: int, fc_amount: int, user_wallet: str) -> Dict[str, Any]:
        """Create a SOL withdrawal request with enhanced validation"""
        try:
            await self.ensure_initialized()
            # Validate user's withdrawal address first
            validation = await self.validate_user_wallet_address(user_wallet)
            if not validation["is_valid"]:
                return {
                    "success": False,
                    "error": f"Geçersiz cüzdan adresi: {validation.get('error', 'Bilinmeyen hata')}"
                }

            # Check user balance
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT fun_coins FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if not result or result[0] < fc_amount:
                conn.close()
                return {"success": False, "error": "Yetersiz bakiye"}

            # Calculate SOL amount
            sol_amount = fc_amount / self.get_sol_to_fc_rate()

            # Check minimum withdrawal (flexible limits)
            if sol_amount < self.min_withdrawal:
                logger.warning(f"Small withdrawal amount: {sol_amount} SOL for user {user_id}")

            # Calculate %1 commission
            withdrawal_fee = sol_amount * self.withdrawal_fee_rate
            net_sol = sol_amount - withdrawal_fee

            # Create withdrawal request
            cursor.execute("""
                INSERT INTO solana_withdrawals
                (user_id, fc_amount, sol_amount, fee_amount, user_wallet, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (user_id, fc_amount, net_sol, withdrawal_fee, user_wallet))

            withdrawal_id = cursor.lastrowid

            # Deduct FC from user balance immediately
            cursor.execute("""
                UPDATE users SET fun_coins = fun_coins - ?
                WHERE user_id = ?
            """, (fc_amount, user_id))

            conn.commit()
            conn.close()

            logger.info(f"Created withdrawal request: ID {withdrawal_id}, User {user_id}, Amount {net_sol} SOL")

            return {
                "success": True,
                "withdrawal_id": withdrawal_id,
                "fc_amount": fc_amount,
                "sol_amount": net_sol,
                "fee": withdrawal_fee,
                "status": "pending",
                "user_wallet": user_wallet,
                "validation_info": validation
            }

        except Exception as e:
            logger.error(f"Error creating withdrawal request: {e}")
            return {"success": False, "error": "Çekim talebi oluşturulamadı"}

    async def process_withdrawal_automatically(self, withdrawal_id: int) -> Dict[str, Any]:
        """Process withdrawal automatically using admin wallet manager"""
        try:
            await self.ensure_initialized()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get withdrawal details
            cursor.execute("""
                SELECT user_id, sol_amount, user_wallet, status
                FROM solana_withdrawals
                WHERE id = ?
            """, (withdrawal_id,))

            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"success": False, "error": "Çekim talebi bulunamadı"}

            user_id, sol_amount, user_wallet, status = result

            if status != 'pending':
                conn.close()
                return {"success": False, "error": "Çekim zaten işlenmiş"}

            # Get withdrawal wallets
            withdrawal_wallets = await self.admin_wallet_manager.list_wallets(WalletRole.WITHDRAWAL)

            if not withdrawal_wallets:
                # Use master wallet as fallback
                master_wallets = await self.admin_wallet_manager.list_wallets(WalletRole.MASTER)
                if master_wallets:
                    withdrawal_wallets = master_wallets
                else:
                    conn.close()
                    return {"success": False, "error": "Çekim cüzdanı bulunamadı"}

            # Find wallet with sufficient balance
            suitable_wallet = None
            for wallet in withdrawal_wallets:
                wallet_info = await self.admin_wallet_manager.get_wallet_info(wallet["address"])
                if wallet_info.get("balance_sol", 0) >= sol_amount + 0.001:  # +0.001 for fees
                    suitable_wallet = wallet["address"]
                    break

            if not suitable_wallet:
                conn.close()
                return {"success": False, "error": "Yetersiz bakiye (admin cüzdan)"}

            # Send transaction using admin wallet manager
            tx_result = await self.admin_wallet_manager.send_sol(
                suitable_wallet,
                user_wallet,
                sol_amount,
                f"Withdrawal for user {user_id}"
            )

            if tx_result.get("success"):
                # Update withdrawal status
                cursor.execute("""
                    UPDATE solana_withdrawals
                    SET status = 'completed', transaction_hash = ?, processed_at = CURRENT_TIMESTAMP,
                        admin_notes = 'Auto-processed'
                    WHERE id = ?
                """, (tx_result["signature"], withdrawal_id))

                conn.commit()
                conn.close()

                logger.info(f"Auto-processed withdrawal {withdrawal_id}: {sol_amount} SOL to {user_wallet}")

                return {
                    "success": True,
                    "withdrawal_id": withdrawal_id,
                    "transaction_hash": tx_result["signature"],
                    "sol_amount": sol_amount,
                    "user_wallet": user_wallet
                }
            else:
                # Transaction failed, update status but don't refund (will be handled manually)
                cursor.execute("""
                    UPDATE solana_withdrawals
                    SET admin_notes = ?
                    WHERE id = ?
                """, (f"Auto-processing failed: {tx_result.get('error', 'Unknown error')}", withdrawal_id))

                conn.commit()
                conn.close()

                return {
                    "success": False,
                    "error": f"Transaction failed: {tx_result.get('error', 'Unknown error')}"
                }

        except Exception as e:
            logger.error(f"Error auto-processing withdrawal: {e}")
            return {"success": False, "error": str(e)}
    
    def get_pending_withdrawals(self) -> list:
        """Get all pending withdrawal requests (admin function)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT w.id, w.user_id, u.username, w.fc_amount, w.sol_amount, 
                       w.fee_amount, w.user_wallet, w.created_at
                FROM solana_withdrawals w
                JOIN users u ON w.user_id = u.user_id
                WHERE w.status = 'pending'
                ORDER BY w.created_at ASC
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            withdrawals = []
            for row in results:
                withdrawals.append({
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "fc_amount": row[3],
                    "sol_amount": row[4],
                    "fee_amount": row[5],
                    "user_wallet": row[6],
                    "created_at": row[7]
                })
            
            return withdrawals
            
        except Exception as e:
            logger.error(f"Error getting pending withdrawals: {e}")
            return []
    
    def process_withdrawal(self, withdrawal_id: int, transaction_hash: str, admin_notes: str = "") -> Dict[str, Any]:
        """Process a withdrawal request (admin function)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE solana_withdrawals 
                SET status = 'completed', transaction_hash = ?, admin_notes = ?, 
                    processed_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
            """, (transaction_hash, admin_notes, withdrawal_id))
            
            if cursor.rowcount == 0:
                return {"success": False, "error": "Çekim talebi bulunamadı veya zaten işlenmiş"}
            
            conn.commit()
            conn.close()
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error processing withdrawal: {e}")
            return {"success": False, "error": "Çekim işlenemedi"}
    
    def reject_withdrawal(self, withdrawal_id: int, reason: str) -> Dict[str, Any]:
        """Reject a withdrawal request (admin function)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get withdrawal details
            cursor.execute("""
                SELECT user_id, fc_amount FROM solana_withdrawals 
                WHERE id = ? AND status = 'pending'
            """, (withdrawal_id,))
            
            result = cursor.fetchone()
            if not result:
                return {"success": False, "error": "Çekim talebi bulunamadı"}
            
            user_id, fc_amount = result
            
            # Refund FC to user
            cursor.execute("""
                UPDATE users SET fun_coins = fun_coins + ?
                WHERE user_id = ?
            """, (fc_amount, user_id))
            
            # Update withdrawal status
            cursor.execute("""
                UPDATE solana_withdrawals 
                SET status = 'rejected', admin_notes = ?
                WHERE id = ?
            """, (reason, withdrawal_id))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "refunded_fc": fc_amount}
            
        except Exception as e:
            logger.error(f"Error rejecting withdrawal: {e}")
            return {"success": False, "error": "Çekim reddedilemedi"}

# Global Solana payment system instance
solana_payment = None

def get_solana_payment():
    """Get Solana payment system instance"""
    global solana_payment
    if solana_payment is None:
        solana_payment = SolanaPaymentSystem()
    return solana_payment