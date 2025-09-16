#!/usr/bin/env python3
"""
Solana Payment System Extensions
Admin approval and rejection functions for wallet-based payments
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SolanaPaymentExtensions:
    """Extended functions for Solana payment system"""

    def __init__(self, db_path: str = "casino_bot.db"):
        self.db_path = db_path

    def approve_deposit(self, deposit_id: int) -> Dict[str, Any]:
        """Admin function to approve a deposit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get deposit details
            cursor.execute("""
                SELECT user_id, sol_amount, fc_amount, status, wallet_address
                FROM solana_deposits
                WHERE id = ?
            """, (deposit_id,))

            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"success": False, "error": "Deposit bulunamadı"}

            user_id, sol_amount, fc_amount, status, wallet_address = result

            if status == 'confirmed':
                conn.close()
                return {"success": False, "error": "Bu deposit zaten onaylanmış"}

            if status == 'rejected':
                conn.close()
                return {"success": False, "error": "Bu deposit reddedilmiş, onaylanamaz"}

            # Update deposit status to confirmed
            cursor.execute("""
                UPDATE solana_deposits
                SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (deposit_id,))

            # Add FC to user balance
            cursor.execute("""
                UPDATE users SET fun_coins = fun_coins + ?
                WHERE user_id = ?
            """, (fc_amount, user_id))

            conn.commit()
            conn.close()

            logger.info(f"Admin approved deposit {deposit_id}: {fc_amount} FC credited to user {user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "sol_amount": sol_amount,
                "fc_amount": fc_amount,
                "deposit_id": deposit_id
            }

        except Exception as e:
            logger.error(f"Error approving deposit {deposit_id}: {e}")
            return {"success": False, "error": "Onaylama sırasında hata oluştu"}

    def reject_deposit(self, deposit_id: int) -> Dict[str, Any]:
        """Admin function to reject a deposit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get deposit details
            cursor.execute("""
                SELECT user_id, sol_amount, fc_amount, status
                FROM solana_deposits
                WHERE id = ?
            """, (deposit_id,))

            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"success": False, "error": "Deposit bulunamadı"}

            user_id, sol_amount, fc_amount, status = result

            if status == 'confirmed':
                conn.close()
                return {"success": False, "error": "Onaylanmış deposit reddedilemez"}

            if status == 'rejected':
                conn.close()
                return {"success": False, "error": "Bu deposit zaten reddedilmiş"}

            # Update deposit status to rejected
            cursor.execute("""
                UPDATE solana_deposits
                SET status = 'rejected', confirmed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (deposit_id,))

            conn.commit()
            conn.close()

            logger.info(f"Admin rejected deposit {deposit_id} for user {user_id}")

            return {
                "success": True,
                "user_id": user_id,
                "sol_amount": sol_amount,
                "fc_amount": fc_amount,
                "deposit_id": deposit_id
            }

        except Exception as e:
            logger.error(f"Error rejecting deposit {deposit_id}: {e}")
            return {"success": False, "error": "Reddetme sırasında hata oluştu"}

    def reject_withdrawal(self, withdrawal_id: int, reason: str = "Admin tarafından reddedildi") -> Dict[str, Any]:
        """Admin function to reject a withdrawal and restore user balance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get withdrawal details
            cursor.execute("""
                SELECT user_id, fc_amount, sol_amount, fee_amount, status, user_wallet
                FROM solana_withdrawals
                WHERE id = ?
            """, (withdrawal_id,))

            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"success": False, "error": "Çekim talebi bulunamadı"}

            user_id, fc_amount, sol_amount, fee_amount, status, user_wallet = result

            if status == 'completed':
                conn.close()
                return {"success": False, "error": "Tamamlanmış çekim reddedilemez"}

            if status == 'rejected':
                conn.close()
                return {"success": False, "error": "Bu çekim zaten reddedilmiş"}

            # Update withdrawal status to rejected
            cursor.execute("""
                UPDATE solana_withdrawals
                SET status = 'rejected', processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (withdrawal_id,))

            # RESTORE USER BALANCE - Çekim reddedildiğinde parayı geri ver
            cursor.execute("""
                UPDATE users SET fun_coins = fun_coins + ?
                WHERE user_id = ?
            """, (fc_amount, user_id))

            conn.commit()
            conn.close()

            logger.info(f"Admin rejected withdrawal {withdrawal_id} for user {user_id} - Balance restored: {fc_amount} FC")

            return {
                "success": True,
                "user_id": user_id,
                "fc_amount": fc_amount,
                "sol_amount": sol_amount,
                "fee_amount": fee_amount,
                "withdrawal_id": withdrawal_id,
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Error rejecting withdrawal {withdrawal_id}: {e}")
            return {"success": False, "error": "Reddetme sırasında hata oluştu"}

    def approve_withdrawal(self, withdrawal_id: int) -> Dict[str, Any]:
        """Admin function to approve a withdrawal for processing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get withdrawal details
            cursor.execute("""
                SELECT user_id, fc_amount, sol_amount, fee_amount, status, user_wallet
                FROM solana_withdrawals
                WHERE id = ?
            """, (withdrawal_id,))

            result = cursor.fetchone()
            if not result:
                conn.close()
                return {"success": False, "error": "Çekim talebi bulunamadı"}

            user_id, fc_amount, sol_amount, fee_amount, status, user_wallet = result

            if status == 'completed':
                conn.close()
                return {"success": False, "error": "Bu çekim zaten tamamlanmış"}

            if status == 'rejected':
                conn.close()
                return {"success": False, "error": "Reddedilmiş çekim onaylanamaz"}

            # Update withdrawal status to completed (admin approved)
            cursor.execute("""
                UPDATE solana_withdrawals
                SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (withdrawal_id,))

            conn.commit()
            conn.close()

            logger.info(f"Admin approved withdrawal {withdrawal_id} for user {user_id}: {sol_amount} SOL")

            return {
                "success": True,
                "user_id": user_id,
                "fc_amount": fc_amount,
                "sol_amount": sol_amount,
                "fee_amount": fee_amount,
                "withdrawal_id": withdrawal_id,
                "user_wallet": user_wallet
            }

        except Exception as e:
            logger.error(f"Error approving withdrawal {withdrawal_id}: {e}")
            return {"success": False, "error": "Onaylama sırasında hata oluştu"}

    def get_withdrawal_details(self, withdrawal_id: int) -> Dict[str, Any]:
        """Get detailed information about a withdrawal"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT w.id, w.user_id, u.username, w.fc_amount, w.sol_amount, w.fee_amount,
                       w.user_wallet, w.status, w.created_at, w.processed_at
                FROM solana_withdrawals w
                LEFT JOIN users u ON w.user_id = u.user_id
                WHERE w.id = ?
            """, (withdrawal_id,))

            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            return {
                "id": result[0],
                "user_id": result[1],
                "username": result[2] or "Unknown",
                "fc_amount": result[3],
                "sol_amount": result[4],
                "fee_amount": result[5],
                "user_wallet": result[6],
                "status": result[7],
                "created_at": result[8],
                "processed_at": result[9]
            }

        except Exception as e:
            logger.error(f"Error getting withdrawal details {withdrawal_id}: {e}")
            return None

    def get_deposit_details(self, deposit_id: int) -> Dict[str, Any]:
        """Get detailed information about a deposit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT d.id, d.user_id, u.username, d.sol_amount, d.fc_amount,
                       d.wallet_address, d.transaction_hash, d.status,
                       d.created_at, d.confirmed_at
                FROM solana_deposits d
                LEFT JOIN users u ON d.user_id = u.user_id
                WHERE d.id = ?
            """, (deposit_id,))

            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            return {
                "id": result[0],
                "user_id": result[1],
                "username": result[2] or "Unknown",
                "sol_amount": result[3],
                "fc_amount": result[4],
                "wallet_address": result[5],
                "transaction_hash": result[6],
                "status": result[7],
                "created_at": result[8],
                "confirmed_at": result[9]
            }

        except Exception as e:
            logger.error(f"Error getting deposit details {deposit_id}: {e}")
            return None

    def get_all_pending_deposits(self) -> list:
        """Get all pending deposits (admin dashboard)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT d.id, d.user_id, u.username, d.sol_amount, d.fc_amount,
                       d.wallet_address, d.created_at, d.status
                FROM solana_deposits d
                LEFT JOIN users u ON d.user_id = u.user_id
                WHERE d.status = 'pending'
                ORDER BY d.created_at DESC
                LIMIT 50
            """)

            results = cursor.fetchall()
            conn.close()

            deposits = []
            for row in results:
                deposits.append({
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2] or "Unknown",
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

    def get_deposit_stats(self) -> Dict[str, Any]:
        """Get deposit statistics for admin dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_deposits,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_deposits,
                    COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_deposits,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_deposits,
                    COALESCE(SUM(CASE WHEN status = 'confirmed' THEN sol_amount ELSE 0 END), 0) as total_sol_confirmed,
                    COALESCE(SUM(CASE WHEN status = 'confirmed' THEN fc_amount ELSE 0 END), 0) as total_fc_confirmed
                FROM solana_deposits
                WHERE created_at >= datetime('now', '-30 days')
            """)

            result = cursor.fetchone()
            conn.close()

            return {
                "total_deposits": result[0],
                "pending_deposits": result[1],
                "confirmed_deposits": result[2],
                "rejected_deposits": result[3],
                "total_sol_confirmed": result[4],
                "total_fc_confirmed": result[5]
            }

        except Exception as e:
            logger.error(f"Error getting deposit stats: {e}")
            return {
                "total_deposits": 0,
                "pending_deposits": 0,
                "confirmed_deposits": 0,
                "rejected_deposits": 0,
                "total_sol_confirmed": 0,
                "total_fc_confirmed": 0
            }

# Global instance
_solana_extensions = None

def get_solana_extensions():
    """Get global Solana extensions instance"""
    global _solana_extensions
    if _solana_extensions is None:
        _solana_extensions = SolanaPaymentExtensions()
    return _solana_extensions