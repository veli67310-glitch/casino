#!/usr/bin/env python3
"""
Solana Transaction Monitor Service
Advanced transaction monitoring with real-time detection and processing
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from solana_rpc_client import get_solana_rpc_client
from config import SOLANA_CONFIG

logger = logging.getLogger(__name__)

class TransactionType(Enum):
    """Transaction types for monitoring"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"

class TransactionStatus(Enum):
    """Transaction processing status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"

@dataclass
class MonitoredTransaction:
    """Transaction data structure for monitoring"""
    signature: str
    slot: int
    block_time: Optional[int]
    from_address: str
    to_address: str
    amount_lamports: int
    amount_sol: float
    transaction_type: TransactionType
    status: TransactionStatus
    fee_lamports: int
    memo: Optional[str]
    detected_at: datetime
    processed_at: Optional[datetime]
    user_id: Optional[int]
    casino_transaction_id: Optional[int]
    error_message: Optional[str]

class SolanaTransactionMonitor:
    """Advanced Solana transaction monitoring service"""

    def __init__(self, db_path: str = "casino_bot.db"):
        self.db_path = db_path
        self.rpc_client = get_solana_rpc_client()
        self.config = SOLANA_CONFIG

        # Monitoring state
        self.monitored_addresses = {}  # address -> callback mapping
        self.active_monitors = {}  # address -> task mapping
        self.processing_callbacks = []  # List of processing callbacks

        # Transaction cache to avoid duplicates
        self.processed_signatures = set()
        self.signature_cache_size = 10000

        # Statistics
        self.stats = {
            "total_transactions_detected": 0,
            "deposits_detected": 0,
            "withdrawals_processed": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

        # Initialize database
        self.init_monitoring_tables()

    def init_monitoring_tables(self):
        """Initialize database tables for transaction monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Monitored transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitored_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT UNIQUE NOT NULL,
                    slot INTEGER,
                    block_time INTEGER,
                    from_address TEXT NOT NULL,
                    to_address TEXT NOT NULL,
                    amount_lamports INTEGER NOT NULL,
                    amount_sol REAL NOT NULL,
                    transaction_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    fee_lamports INTEGER DEFAULT 0,
                    memo TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    user_id INTEGER,
                    casino_transaction_id INTEGER,
                    error_message TEXT
                )
            """)

            # Monitor addresses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitor_addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    label TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    last_signature TEXT,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Transaction processing log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT NOT NULL,
                    processing_step TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Transaction monitoring tables initialized")

        except Exception as e:
            logger.error(f"Error initializing monitoring tables: {e}")
        finally:
            conn.close()

    async def add_address_to_monitor(self, address: str, label: str = None, callback: Callable = None) -> bool:
        """Add address to monitoring list"""
        try:
            # Validate address
            validation = self.rpc_client.validate_wallet_address(address)
            if not validation["is_valid"]:
                logger.error(f"Cannot monitor invalid address: {validation['error']}")
                return False

            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO monitor_addresses
                (address, label, is_active, last_check)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            """, (address, label or f"Address {address[:8]}..."))

            conn.commit()
            conn.close()

            # Add to monitoring
            self.monitored_addresses[address] = callback

            # Start monitoring task if not already running
            if address not in self.active_monitors:
                task = asyncio.create_task(self._monitor_address(address))
                self.active_monitors[address] = task
                logger.info(f"Started monitoring address: {address} ({label})")

            return True

        except Exception as e:
            logger.error(f"Error adding address to monitor: {e}")
            return False

    async def remove_address_from_monitor(self, address: str) -> bool:
        """Remove address from monitoring"""
        try:
            # Cancel monitoring task
            if address in self.active_monitors:
                self.active_monitors[address].cancel()
                del self.active_monitors[address]

            # Remove from monitoring list
            if address in self.monitored_addresses:
                del self.monitored_addresses[address]

            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE monitor_addresses SET is_active = 0 WHERE address = ?",
                (address,)
            )
            conn.commit()
            conn.close()

            logger.info(f"Stopped monitoring address: {address}")
            return True

        except Exception as e:
            logger.error(f"Error removing address from monitor: {e}")
            return False

    async def _monitor_address(self, address: str):
        """Internal method to monitor a single address"""
        logger.info(f"Starting transaction monitoring for {address}")
        last_signature = None
        poll_interval = 30  # Increased from 10 to 30 seconds for better rate limiting

        try:
            # Get initial state
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_signature FROM monitor_addresses WHERE address = ?",
                (address,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                last_signature = row[0]
            conn.close()

            while True:
                try:
                    # Get new signatures with reduced batch size
                    signatures_result = await self.rpc_client.get_signatures_for_address(
                        address,
                        limit=5,  # Reduced from 20 to 5 for better rate limiting
                        before=last_signature
                    )

                    if signatures_result.get("signatures"):
                        new_transactions = []

                        for sig_info in reversed(signatures_result["signatures"]):
                            if sig_info["signature"] != last_signature:
                                if sig_info["signature"] not in self.processed_signatures:
                                    # Get detailed transaction info
                                    tx_details = await self.rpc_client.get_transaction_details(
                                        sig_info["signature"]
                                    )

                                    if not tx_details.get("error"):
                                        transaction = await self._process_transaction(
                                            address, sig_info, tx_details
                                        )
                                        if transaction:
                                            new_transactions.append(transaction)

                                    # Add to processed cache
                                    self.processed_signatures.add(sig_info["signature"])

                                    # Limit cache size
                                    if len(self.processed_signatures) > self.signature_cache_size:
                                        self.processed_signatures.pop()

                        # Update last signature
                        if signatures_result["signatures"]:
                            last_signature = signatures_result["signatures"][0]["signature"]

                            # Update database
                            conn = sqlite3.connect(self.db_path)
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE monitor_addresses SET last_signature = ?, last_check = CURRENT_TIMESTAMP WHERE address = ?",
                                (last_signature, address)
                            )
                            conn.commit()
                            conn.close()

                        # Process new transactions
                        for transaction in new_transactions:
                            await self._handle_new_transaction(address, transaction)

                    await asyncio.sleep(poll_interval)

                except Exception as e:
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["rate limit", "429", "too many"]):
                        logger.warning(f"Rate limited while monitoring {address}, backing off")
                        await asyncio.sleep(poll_interval * 3)  # Longer backoff for rate limits
                    elif any(keyword in error_msg for keyword in ["503", "service unavailable", "network"]):
                        logger.warning(f"Service unavailable while monitoring {address}, waiting")
                        await asyncio.sleep(poll_interval * 2)
                    else:
                        logger.error(f"Error in monitoring loop for {address}: {e}")
                        await asyncio.sleep(poll_interval)

                    self.stats["errors"] += 1

        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for address: {address}")
        except Exception as e:
            logger.error(f"Fatal error monitoring address {address}: {e}")

    async def _process_transaction(self, monitored_address: str, sig_info: dict, tx_details: dict) -> Optional[MonitoredTransaction]:
        """Process and categorize a transaction"""
        try:
            signature = sig_info["signature"]

            # Determine transaction type and details
            from_address = None
            to_address = None
            amount_lamports = 0
            transaction_type = TransactionType.UNKNOWN

            # Parse balance changes to determine transaction details
            if tx_details.get("balance_changes"):
                for change in tx_details["balance_changes"]:
                    if change["account"] == monitored_address:
                        if change["change_lamports"] > 0:
                            # Incoming transaction (deposit)
                            transaction_type = TransactionType.DEPOSIT
                            amount_lamports = change["change_lamports"]
                            to_address = monitored_address

                            # Find sender
                            for other_change in tx_details["balance_changes"]:
                                if (other_change["account"] != monitored_address and
                                    other_change["change_lamports"] < 0):
                                    from_address = other_change["account"]
                                    break

                        elif change["change_lamports"] < 0:
                            # Outgoing transaction (withdrawal)
                            transaction_type = TransactionType.WITHDRAWAL
                            amount_lamports = abs(change["change_lamports"])
                            from_address = monitored_address

                            # Find recipient
                            for other_change in tx_details["balance_changes"]:
                                if (other_change["account"] != monitored_address and
                                    other_change["change_lamports"] > 0):
                                    to_address = other_change["account"]
                                    break

            # Skip if no amount or addresses found
            if amount_lamports == 0 or not from_address or not to_address:
                return None

            # Create transaction object
            transaction = MonitoredTransaction(
                signature=signature,
                slot=tx_details.get("slot", 0),
                block_time=tx_details.get("block_time"),
                from_address=from_address,
                to_address=to_address,
                amount_lamports=amount_lamports,
                amount_sol=amount_lamports / 1_000_000_000,
                transaction_type=transaction_type,
                status=TransactionStatus.CONFIRMED if tx_details.get("success") else TransactionStatus.FAILED,
                fee_lamports=tx_details.get("fee", 0),
                memo=None,  # TODO: Parse memo from transaction
                detected_at=datetime.now(),
                processed_at=None,
                user_id=None,
                casino_transaction_id=None,
                error_message=tx_details.get("error")
            )

            # Store in database
            await self._store_transaction(transaction)

            # Update statistics
            self.stats["total_transactions_detected"] += 1
            if transaction_type == TransactionType.DEPOSIT:
                self.stats["deposits_detected"] += 1
            elif transaction_type == TransactionType.WITHDRAWAL:
                self.stats["withdrawals_processed"] += 1

            return transaction

        except Exception as e:
            logger.error(f"Error processing transaction {sig_info.get('signature', 'unknown')}: {e}")
            return None

    async def _store_transaction(self, transaction: MonitoredTransaction):
        """Store transaction in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO monitored_transactions
                (signature, slot, block_time, from_address, to_address, amount_lamports,
                 amount_sol, transaction_type, status, fee_lamports, memo, detected_at,
                 error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.signature,
                transaction.slot,
                transaction.block_time,
                transaction.from_address,
                transaction.to_address,
                transaction.amount_lamports,
                transaction.amount_sol,
                transaction.transaction_type.value,
                transaction.status.value,
                transaction.fee_lamports,
                transaction.memo,
                transaction.detected_at,
                transaction.error_message
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Error storing transaction: {e}")
        finally:
            conn.close()

    async def _handle_new_transaction(self, monitored_address: str, transaction: MonitoredTransaction):
        """Handle a newly detected transaction"""
        try:
            logger.info(f"New transaction detected: {transaction.signature} "
                       f"({transaction.transaction_type.value}) "
                       f"{transaction.amount_sol} SOL")

            # Call address-specific callback
            if monitored_address in self.monitored_addresses:
                callback = self.monitored_addresses[monitored_address]
                if callback:
                    try:
                        await callback(monitored_address, transaction)
                    except Exception as e:
                        logger.error(f"Error in address callback: {e}")

            # Call global processing callbacks
            for callback in self.processing_callbacks:
                try:
                    await callback(transaction)
                except Exception as e:
                    logger.error(f"Error in processing callback: {e}")

        except Exception as e:
            logger.error(f"Error handling new transaction: {e}")

    def add_processing_callback(self, callback: Callable):
        """Add a global transaction processing callback"""
        self.processing_callbacks.append(callback)
        logger.info(f"Added processing callback: {callback.__name__}")

    def remove_processing_callback(self, callback: Callable):
        """Remove a global transaction processing callback"""
        if callback in self.processing_callbacks:
            self.processing_callbacks.remove(callback)
            logger.info(f"Removed processing callback: {callback.__name__}")

    async def get_transaction_history(self, address: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history from monitoring database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if address:
                cursor.execute("""
                    SELECT * FROM monitored_transactions
                    WHERE from_address = ? OR to_address = ?
                    ORDER BY detected_at DESC
                    LIMIT ?
                """, (address, address, limit))
            else:
                cursor.execute("""
                    SELECT * FROM monitored_transactions
                    ORDER BY detected_at DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            transactions = []
            for row in rows:
                tx_dict = dict(zip(columns, row))
                transactions.append(tx_dict)

            return transactions

        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
        finally:
            conn.close()

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get database stats
            cursor.execute("SELECT COUNT(*) FROM monitored_transactions")
            total_tx_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM monitor_addresses WHERE is_active = 1")
            active_addresses = cursor.fetchone()[0]

            cursor.execute("""
                SELECT transaction_type, COUNT(*)
                FROM monitored_transactions
                GROUP BY transaction_type
            """)
            type_counts = dict(cursor.fetchall())

            conn.close()

            uptime = datetime.now() - self.stats["start_time"]

            return {
                "uptime_seconds": uptime.total_seconds(),
                "active_monitors": len(self.active_monitors),
                "monitored_addresses": active_addresses,
                "total_transactions_in_db": total_tx_count,
                "transaction_type_counts": type_counts,
                "cache_size": len(self.processed_signatures),
                **self.stats
            }

        except Exception as e:
            logger.error(f"Error getting monitoring stats: {e}")
            return {}

    async def start_all_monitors(self):
        """Start monitoring all active addresses from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT address, label FROM monitor_addresses WHERE is_active = 1")
            addresses = cursor.fetchall()
            conn.close()

            for address, label in addresses:
                await self.add_address_to_monitor(address, label)

            logger.info(f"Started monitoring {len(addresses)} addresses")

        except Exception as e:
            logger.error(f"Error starting all monitors: {e}")

    async def stop_all_monitors(self):
        """Stop all monitoring tasks"""
        try:
            tasks_to_cancel = list(self.active_monitors.values())

            for task in tasks_to_cancel:
                task.cancel()

            # Wait for tasks to complete
            if tasks_to_cancel:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

            self.active_monitors.clear()
            self.monitored_addresses.clear()

            logger.info("Stopped all transaction monitors")

        except Exception as e:
            logger.error(f"Error stopping monitors: {e}")

# Global instance
_transaction_monitor = None

def get_transaction_monitor() -> SolanaTransactionMonitor:
    """Get global transaction monitor instance"""
    global _transaction_monitor
    if _transaction_monitor is None:
        _transaction_monitor = SolanaTransactionMonitor()
    return _transaction_monitor

# Convenience functions for casino integration
async def monitor_deposit_address(address: str, user_id: int, callback=None):
    """Monitor an address for deposit transactions"""
    monitor = get_transaction_monitor()

    async def deposit_callback(monitored_address, transaction):
        if transaction.transaction_type == TransactionType.DEPOSIT:
            # Update transaction with user info
            conn = sqlite3.connect(monitor.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE monitored_transactions SET user_id = ? WHERE signature = ?",
                (user_id, transaction.signature)
            )
            conn.commit()
            conn.close()

            if callback:
                await callback(transaction)

    await monitor.add_address_to_monitor(address, f"User {user_id} Deposit", deposit_callback)

if __name__ == "__main__":
    # Test the monitor
    async def test_monitor():
        monitor = get_transaction_monitor()

        # Test monitoring
        test_address = "DsJd8pDi44f82dRjG3zBnxrv2t32ZyfKUjz5cqFkdrY9"

        async def test_callback(address, transaction):
            print(f"New transaction: {transaction.signature} - {transaction.amount_sol} SOL")

        await monitor.add_address_to_monitor(test_address, "Test Address", test_callback)

        # Monitor for 30 seconds
        await asyncio.sleep(30)

        # Get stats
        stats = await monitor.get_monitoring_stats()
        print(f"Monitor stats: {stats}")

        await monitor.stop_all_monitors()

    asyncio.run(test_monitor())