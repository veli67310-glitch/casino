#!/usr/bin/env python3
"""
Solana Admin Wallet Management
Comprehensive admin wallet configuration and management system
"""

import asyncio
import logging
import json
import base58
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.system_program import transfer
from solders.transaction import Transaction
from solders.signature import Signature

from solana_rpc_client import get_solana_rpc_client
from solana_transaction_monitor import get_transaction_monitor, TransactionType
from config import SOLANA_CONFIG, ADMIN_USER_IDS

logger = logging.getLogger(__name__)

class WalletRole(Enum):
    """Wallet roles in the system"""
    MASTER = "master"         # Main admin wallet
    DEPOSIT = "deposit"       # Collects deposits
    WITHDRAWAL = "withdrawal" # Processes withdrawals
    RESERVE = "reserve"       # Emergency reserve
    COLD = "cold"            # Cold storage

class WalletStatus(Enum):
    """Wallet status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    COMPROMISED = "compromised"

@dataclass
class AdminWallet:
    """Admin wallet data structure"""
    address: str
    role: WalletRole
    status: WalletStatus
    label: str
    balance_sol: float
    balance_lamports: int
    private_key_encrypted: Optional[str]
    created_at: datetime
    last_used: Optional[datetime]
    transaction_count: int
    total_received: float
    total_sent: float
    description: str

class SolanaAdminWalletManager:
    """Comprehensive admin wallet management system"""

    def __init__(self, db_path: str = "casino_bot.db"):
        self.db_path = db_path
        self.rpc_client = get_solana_rpc_client()
        self.transaction_monitor = get_transaction_monitor()
        self.config = SOLANA_CONFIG

        # Wallet instances
        self.wallets = {}  # address -> AdminWallet
        self.keypairs = {}  # address -> Keypair (for active wallets)

        # Settings
        self.auto_balance_enabled = True
        self.min_withdrawal_balance = 1.0  # SOL
        self.max_single_transaction = 100.0  # SOL
        self.daily_transaction_limit = 1000.0  # SOL

        # Transaction tracking
        self.daily_transactions = {}  # date -> amount
        self.pending_transactions = {}  # signature -> transaction_info

        # Initialize database and load wallets
        self.init_wallet_tables()
        asyncio.create_task(self.load_wallets())

    def init_wallet_tables(self):
        """Initialize wallet management database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Admin wallets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    label TEXT NOT NULL,
                    private_key_encrypted TEXT,
                    balance_sol REAL DEFAULT 0.0,
                    balance_lamports INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    transaction_count INTEGER DEFAULT 0,
                    total_received REAL DEFAULT 0.0,
                    total_sent REAL DEFAULT 0.0,
                    description TEXT
                )
            """)

            # Wallet transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_wallet_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_address TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount_sol REAL NOT NULL,
                    amount_lamports INTEGER NOT NULL,
                    from_address TEXT,
                    to_address TEXT,
                    status TEXT DEFAULT 'pending',
                    fee_sol REAL DEFAULT 0.0,
                    memo TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    FOREIGN KEY (wallet_address) REFERENCES admin_wallets (address)
                )
            """)

            # Wallet settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_wallet_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert default settings
            default_settings = [
                ("auto_balance_enabled", "true", "Enable automatic balance management"),
                ("min_withdrawal_balance", "1.0", "Minimum SOL balance for withdrawals"),
                ("max_single_transaction", "100.0", "Maximum SOL per single transaction"),
                ("daily_transaction_limit", "1000.0", "Daily transaction limit in SOL"),
                ("withdrawal_fee_rate", "0.01", "Withdrawal fee rate (1%)"),
                ("deposit_confirmation_blocks", "12", "Required confirmations for deposits")
            ]

            for key, value, description in default_settings:
                cursor.execute("""
                    INSERT OR IGNORE INTO admin_wallet_settings
                    (setting_key, setting_value, description)
                    VALUES (?, ?, ?)
                """, (key, value, description))

            conn.commit()
            logger.info("Admin wallet tables initialized")

        except Exception as e:
            logger.error(f"Error initializing wallet tables: {e}")
        finally:
            conn.close()

    async def load_wallets(self):
        """Load wallets from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM admin_wallets WHERE status = 'active'")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            for row in rows:
                wallet_data = dict(zip(columns, row))
                wallet = AdminWallet(
                    address=wallet_data["address"],
                    role=WalletRole(wallet_data["role"]),
                    status=WalletStatus(wallet_data["status"]),
                    label=wallet_data["label"],
                    balance_sol=wallet_data["balance_sol"],
                    balance_lamports=wallet_data["balance_lamports"],
                    private_key_encrypted=wallet_data["private_key_encrypted"],
                    created_at=datetime.fromisoformat(wallet_data["created_at"]),
                    last_used=datetime.fromisoformat(wallet_data["last_used"]) if wallet_data["last_used"] else None,
                    transaction_count=wallet_data["transaction_count"],
                    total_received=wallet_data["total_received"],
                    total_sent=wallet_data["total_sent"],
                    description=wallet_data["description"] or ""
                )

                self.wallets[wallet.address] = wallet

                # Load keypair if private key exists
                if wallet.private_key_encrypted:
                    try:
                        # In production, you should decrypt this properly
                        private_key_bytes = base58.b58decode(wallet.private_key_encrypted)
                        keypair = Keypair.from_secret_key(private_key_bytes)
                        self.keypairs[wallet.address] = keypair
                        logger.info(f"Loaded keypair for wallet: {wallet.address} ({wallet.role.value})")
                    except Exception as e:
                        logger.error(f"Failed to load keypair for {wallet.address}: {e}")

            conn.close()
            logger.info(f"Loaded {len(self.wallets)} admin wallets")

            # Start monitoring wallets
            await self.start_wallet_monitoring()

        except Exception as e:
            logger.error(f"Error loading wallets: {e}")

    async def create_wallet(self, role: WalletRole, label: str, description: str = "",
                          private_key: str = None) -> Dict[str, Any]:
        """Create a new admin wallet"""
        try:
            # Generate or use provided keypair
            if private_key:
                try:
                    private_key_bytes = base58.b58decode(private_key)
                    keypair = Keypair.from_secret_key(private_key_bytes)
                except Exception as e:
                    return {"error": f"Invalid private key: {str(e)}"}
            else:
                keypair = Keypair()

            address = str(keypair.public_key)

            # Check if wallet already exists
            if address in self.wallets:
                return {"error": "Wallet already exists"}

            # Validate address
            validation = self.rpc_client.validate_wallet_address(address)
            if not validation["is_valid"]:
                return {"error": f"Generated invalid address: {validation['error']}"}

            # Get initial balance
            balance_info = await self.rpc_client.get_balance(address)
            balance_sol = balance_info.get("balance_sol", 0.0)
            balance_lamports = balance_info.get("balance_lamports", 0)

            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Encrypt private key (in production, use proper encryption)
            private_key_encrypted = base58.b58encode(keypair.secret_key).decode('utf-8')

            cursor.execute("""
                INSERT INTO admin_wallets
                (address, role, status, label, private_key_encrypted, balance_sol,
                 balance_lamports, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                address, role.value, WalletStatus.ACTIVE.value, label,
                private_key_encrypted, balance_sol, balance_lamports, description
            ))

            conn.commit()
            conn.close()

            # Create wallet object
            wallet = AdminWallet(
                address=address,
                role=role,
                status=WalletStatus.ACTIVE,
                label=label,
                balance_sol=balance_sol,
                balance_lamports=balance_lamports,
                private_key_encrypted=private_key_encrypted,
                created_at=datetime.now(),
                last_used=None,
                transaction_count=0,
                total_received=0.0,
                total_sent=0.0,
                description=description
            )

            # Add to memory
            self.wallets[address] = wallet
            self.keypairs[address] = keypair

            # Start monitoring
            await self.transaction_monitor.add_address_to_monitor(
                address, f"Admin {role.value}: {label}",
                self._wallet_transaction_callback
            )

            logger.info(f"Created admin wallet: {address} ({role.value})")

            return {
                "address": address,
                "role": role.value,
                "label": label,
                "balance_sol": balance_sol,
                "public_key": str(keypair.public_key),
                "success": True
            }

        except Exception as e:
            logger.error(f"Error creating wallet: {e}")
            return {"error": str(e)}

    async def get_wallet_info(self, address: str) -> Dict[str, Any]:
        """Get detailed wallet information"""
        if address not in self.wallets:
            return {"error": "Wallet not found"}

        wallet = self.wallets[address]

        # Get current balance
        balance_info = await self.rpc_client.get_balance(address)

        # Update wallet balance
        if not balance_info.get("error"):
            wallet.balance_sol = balance_info["balance_sol"]
            wallet.balance_lamports = balance_info["balance_lamports"]
            await self.update_wallet_balance(address, wallet.balance_sol, wallet.balance_lamports)

        return {
            "address": wallet.address,
            "role": wallet.role.value,
            "status": wallet.status.value,
            "label": wallet.label,
            "balance_sol": wallet.balance_sol,
            "balance_lamports": wallet.balance_lamports,
            "created_at": wallet.created_at.isoformat(),
            "last_used": wallet.last_used.isoformat() if wallet.last_used else None,
            "transaction_count": wallet.transaction_count,
            "total_received": wallet.total_received,
            "total_sent": wallet.total_sent,
            "description": wallet.description,
            "has_private_key": address in self.keypairs
        }

    async def list_wallets(self, role: WalletRole = None) -> List[Dict[str, Any]]:
        """List all admin wallets"""
        wallets_info = []

        for address, wallet in self.wallets.items():
            if role is None or wallet.role == role:
                wallet_info = await self.get_wallet_info(address)
                wallets_info.append(wallet_info)

        return wallets_info

    async def send_sol(self, from_address: str, to_address: str, amount_sol: float,
                      memo: str = None) -> Dict[str, Any]:
        """Send SOL from admin wallet"""
        try:
            # Validation
            if from_address not in self.wallets:
                return {"error": "Source wallet not found"}

            if from_address not in self.keypairs:
                return {"error": "Private key not available for source wallet"}

            # Validate destination address
            validation = self.rpc_client.validate_wallet_address(to_address)
            if not validation["is_valid"]:
                return {"error": f"Invalid destination address: {validation['error']}"}

            # Check amount limits
            if amount_sol > self.max_single_transaction:
                return {"error": f"Amount exceeds single transaction limit ({self.max_single_transaction} SOL)"}

            # Check daily limit
            today = datetime.now().date()
            daily_total = self.daily_transactions.get(today, 0.0)
            if daily_total + amount_sol > self.daily_transaction_limit:
                return {"error": f"Amount would exceed daily limit ({self.daily_transaction_limit} SOL)"}

            # Check wallet balance
            wallet = self.wallets[from_address]
            balance_info = await self.rpc_client.get_balance(from_address)
            current_balance = balance_info.get("balance_sol", 0.0)

            if current_balance < amount_sol + 0.001:  # +0.001 for transaction fee
                return {"error": f"Insufficient balance: {current_balance} SOL available"}

            # Send transaction using RPC client
            result = await self.rpc_client.send_sol_transaction(to_address, amount_sol, memo)

            if result.get("success"):
                # Update tracking
                self.daily_transactions[today] = daily_total + amount_sol
                wallet.last_used = datetime.now()
                wallet.transaction_count += 1
                wallet.total_sent += amount_sol

                # Store transaction record
                await self.store_wallet_transaction(
                    from_address, result["signature"], "withdrawal",
                    amount_sol, from_address, to_address, memo
                )

                # Update database
                await self.update_wallet_stats(from_address)

                logger.info(f"Sent {amount_sol} SOL from {from_address} to {to_address}")

            return result

        except Exception as e:
            logger.error(f"Error sending SOL: {e}")
            return {"error": str(e)}

    async def bulk_withdrawal(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple withdrawals in batch"""
        results = []
        total_amount = 0.0

        try:
            # Validate all transactions first
            for tx in transactions:
                if not all(key in tx for key in ["to_address", "amount_sol"]):
                    return {"error": "Invalid transaction format"}

                total_amount += tx["amount_sol"]

            # Check total daily limit
            today = datetime.now().date()
            daily_total = self.daily_transactions.get(today, 0.0)
            if daily_total + total_amount > self.daily_transaction_limit:
                return {"error": f"Bulk transaction would exceed daily limit"}

            # Find best wallet for withdrawals
            withdrawal_wallet = None
            for address, wallet in self.wallets.items():
                if (wallet.role == WalletRole.WITHDRAWAL and
                    wallet.status == WalletStatus.ACTIVE and
                    address in self.keypairs):
                    balance_info = await self.rpc_client.get_balance(address)
                    if balance_info.get("balance_sol", 0.0) >= total_amount + 0.01:  # +0.01 for fees
                        withdrawal_wallet = address
                        break

            if not withdrawal_wallet:
                return {"error": "No suitable withdrawal wallet found"}

            # Process transactions
            successful_count = 0
            total_sent = 0.0

            for tx in transactions:
                result = await self.send_sol(
                    withdrawal_wallet,
                    tx["to_address"],
                    tx["amount_sol"],
                    tx.get("memo", f"Bulk withdrawal {len(results)+1}")
                )

                results.append({
                    "to_address": tx["to_address"],
                    "amount_sol": tx["amount_sol"],
                    "result": result
                })

                if result.get("success"):
                    successful_count += 1
                    total_sent += tx["amount_sol"]

                # Small delay between transactions
                await asyncio.sleep(0.5)

            return {
                "total_transactions": len(transactions),
                "successful_transactions": successful_count,
                "total_amount_sent": total_sent,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in bulk withdrawal: {e}")
            return {"error": str(e)}

    async def _wallet_transaction_callback(self, address: str, transaction):
        """Callback for wallet transaction monitoring"""
        try:
            if address not in self.wallets:
                return

            wallet = self.wallets[address]

            # Store transaction
            await self.store_wallet_transaction(
                address, transaction.signature, transaction.transaction_type.value,
                transaction.amount_sol, transaction.from_address, transaction.to_address
            )

            # Update wallet stats
            if transaction.transaction_type == TransactionType.DEPOSIT:
                wallet.total_received += transaction.amount_sol
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                wallet.total_sent += transaction.amount_sol

            wallet.transaction_count += 1
            await self.update_wallet_stats(address)

            logger.info(f"Processed transaction for wallet {address}: {transaction.signature}")

        except Exception as e:
            logger.error(f"Error in wallet transaction callback: {e}")

    async def store_wallet_transaction(self, wallet_address: str, signature: str,
                                     transaction_type: str, amount_sol: float,
                                     from_address: str, to_address: str, memo: str = None):
        """Store wallet transaction in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO admin_wallet_transactions
                (wallet_address, signature, transaction_type, amount_sol, amount_lamports,
                 from_address, to_address, status, memo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed', ?)
            """, (
                wallet_address, signature, transaction_type, amount_sol,
                int(amount_sol * 1_000_000_000), from_address, to_address, memo
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Error storing wallet transaction: {e}")
        finally:
            conn.close()

    async def update_wallet_balance(self, address: str, balance_sol: float, balance_lamports: int):
        """Update wallet balance in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE admin_wallets
                SET balance_sol = ?, balance_lamports = ?
                WHERE address = ?
            """, (balance_sol, balance_lamports, address))

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating wallet balance: {e}")
        finally:
            conn.close()

    async def update_wallet_stats(self, address: str):
        """Update wallet statistics in database"""
        try:
            if address not in self.wallets:
                return

            wallet = self.wallets[address]

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE admin_wallets
                SET last_used = ?, transaction_count = ?, total_received = ?, total_sent = ?
                WHERE address = ?
            """, (
                wallet.last_used,
                wallet.transaction_count,
                wallet.total_received,
                wallet.total_sent,
                address
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating wallet stats: {e}")
        finally:
            conn.close()

    async def start_wallet_monitoring(self):
        """Start monitoring all admin wallets"""
        for address, wallet in self.wallets.items():
            if wallet.status == WalletStatus.ACTIVE:
                await self.transaction_monitor.add_address_to_monitor(
                    address,
                    f"Admin {wallet.role.value}: {wallet.label}",
                    self._wallet_transaction_callback
                )

        logger.info(f"Started monitoring {len(self.wallets)} admin wallets")

    async def get_wallet_settings(self) -> Dict[str, Any]:
        """Get wallet management settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT setting_key, setting_value, description FROM admin_wallet_settings")
            rows = cursor.fetchall()

            settings = {}
            for key, value, description in rows:
                settings[key] = {
                    "value": value,
                    "description": description
                }

            return settings

        except Exception as e:
            logger.error(f"Error getting wallet settings: {e}")
            return {}
        finally:
            conn.close()

    async def update_wallet_setting(self, key: str, value: str) -> bool:
        """Update wallet management setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE admin_wallet_settings
                SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = ?
            """, (value, key))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating wallet setting: {e}")
            return False
        finally:
            conn.close()

    async def get_admin_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive admin dashboard data"""
        try:
            # Wallet summaries
            wallet_summary = {
                "total_wallets": len(self.wallets),
                "active_wallets": sum(1 for w in self.wallets.values() if w.status == WalletStatus.ACTIVE),
                "total_balance": sum(w.balance_sol for w in self.wallets.values()),
                "role_distribution": {}
            }

            for role in WalletRole:
                count = sum(1 for w in self.wallets.values() if w.role == role)
                balance = sum(w.balance_sol for w in self.wallets.values() if w.role == role)
                wallet_summary["role_distribution"][role.value] = {
                    "count": count,
                    "balance": balance
                }

            # Recent transactions
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM admin_wallet_transactions
                ORDER BY created_at DESC
                LIMIT 20
            """)
            recent_transactions = []
            for row in cursor.fetchall():
                columns = [desc[0] for desc in cursor.description]
                recent_transactions.append(dict(zip(columns, row)))

            # Daily transaction stats
            cursor.execute("""
                SELECT DATE(created_at) as date,
                       COUNT(*) as count,
                       SUM(amount_sol) as total_amount
                FROM admin_wallet_transactions
                WHERE created_at >= DATE('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    "date": row[0],
                    "transaction_count": row[1],
                    "total_amount": row[2]
                })

            conn.close()

            # System settings
            settings = await self.get_wallet_settings()

            return {
                "wallet_summary": wallet_summary,
                "recent_transactions": recent_transactions,
                "daily_stats": daily_stats,
                "settings": settings,
                "daily_limits": {
                    "used": self.daily_transactions.get(datetime.now().date(), 0.0),
                    "limit": self.daily_transaction_limit
                }
            }

        except Exception as e:
            logger.error(f"Error getting admin dashboard data: {e}")
            return {}

# Global instance
_admin_wallet_manager = None

def get_admin_wallet_manager() -> SolanaAdminWalletManager:
    """Get global admin wallet manager instance"""
    global _admin_wallet_manager
    if _admin_wallet_manager is None:
        _admin_wallet_manager = SolanaAdminWalletManager()
    return _admin_wallet_manager

# Convenience functions
async def create_admin_wallet(role: str, label: str, description: str = "") -> Dict[str, Any]:
    """Create new admin wallet"""
    manager = get_admin_wallet_manager()
    return await manager.create_wallet(WalletRole(role), label, description)

async def send_admin_sol(from_address: str, to_address: str, amount_sol: float, memo: str = None) -> Dict[str, Any]:
    """Send SOL from admin wallet"""
    manager = get_admin_wallet_manager()
    return await manager.send_sol(from_address, to_address, amount_sol, memo)

async def get_admin_wallets(role: str = None) -> List[Dict[str, Any]]:
    """Get admin wallets"""
    manager = get_admin_wallet_manager()
    wallet_role = WalletRole(role) if role else None
    return await manager.list_wallets(wallet_role)

if __name__ == "__main__":
    # Test the admin wallet manager
    async def test_admin_manager():
        manager = get_admin_wallet_manager()

        # Create a test wallet
        result = await manager.create_wallet(
            WalletRole.DEPOSIT,
            "Test Deposit Wallet",
            "Testing wallet creation"
        )
        print(f"Create wallet result: {result}")

        # List wallets
        wallets = await manager.list_wallets()
        print(f"Wallets: {wallets}")

        # Get dashboard data
        dashboard = await manager.get_admin_dashboard_data()
        print(f"Dashboard: {dashboard}")

    asyncio.run(test_admin_manager())