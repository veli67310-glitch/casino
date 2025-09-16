#!/usr/bin/env python3
"""
Solana QR Code Payment System
QR code generation, transaction confirmation and automatic balance updates
"""

import asyncio
import logging
import json
import qrcode
import io
import base64
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import os

from solana_rpc_client import get_solana_rpc_client
from solana_payment import get_solana_payment
from config import SOLANA_CONFIG

logger = logging.getLogger(__name__)

class SolanaQRPaymentSystem:
    """Enhanced Solana payment system with QR codes and confirmations"""

    def __init__(self, db_path: str = "casino_bot.db"):
        self.db_path = db_path
        self.rpc_client = get_solana_rpc_client()
        self.payment_system = get_solana_payment()
        self.config = SOLANA_CONFIG

        # QR code settings
        self.qr_size = 300
        self.qr_border = 4

        # Confirmation settings
        self.confirmation_timeout = 600  # 10 minutes
        self.check_interval = 15  # 15 seconds

        # Initialize database
        self.init_qr_payment_tables()

    def init_qr_payment_tables(self):
        """Initialize QR payment specific tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Transaction confirmations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_confirmations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    deposit_id INTEGER,
                    withdrawal_id INTEGER,
                    transaction_hash TEXT,
                    expected_amount REAL NOT NULL,
                    wallet_address TEXT NOT NULL,
                    status TEXT DEFAULT 'waiting',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    timeout_at TIMESTAMP,
                    confirmations INTEGER DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (deposit_id) REFERENCES solana_deposits (id),
                    FOREIGN KEY (withdrawal_id) REFERENCES solana_withdrawals (id)
                )
            """)

            # QR code cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qr_code_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    qr_data TEXT NOT NULL,
                    image_base64 TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)

            # Balance update log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balance_updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount_change INTEGER NOT NULL,
                    old_balance INTEGER NOT NULL,
                    new_balance INTEGER NOT NULL,
                    transaction_hash TEXT,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            conn.commit()
            logger.info("QR payment tables initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing QR payment tables: {e}")
        finally:
            conn.close()

    def generate_payment_qr(self, address: str, amount: float = None,
                          memo: str = None, label: str = None) -> Dict[str, Any]:
        """Generate QR code for Solana payment"""
        try:
            # Create Solana payment URL format
            # solana:ADDRESS?amount=AMOUNT&label=LABEL&memo=MEMO
            payment_url = f"solana:{address}"

            params = []
            if amount:
                params.append(f"amount={amount}")
            if label:
                params.append(f"label={label}")
            if memo:
                params.append(f"memo={memo}")

            if params:
                payment_url += "?" + "&".join(params)

            # Check cache first
            cache_key = f"qr_{hash(payment_url)}"
            cached_qr = self.get_cached_qr(cache_key)
            if cached_qr:
                return cached_qr

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=self.qr_border,
            )

            qr.add_data(payment_url)
            qr.make(fit=True)

            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((self.qr_size, self.qr_size), Image.Resampling.LANCZOS)

            # Add Solana branding/styling
            enhanced_img = self.enhance_qr_image(qr_img, address, amount, label)

            # Convert to base64
            img_buffer = io.BytesIO()
            enhanced_img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

            result = {
                "success": True,
                "qr_data": payment_url,
                "image_base64": img_base64,
                "address": address,
                "amount": amount,
                "memo": memo,
                "label": label
            }

            # Cache the result
            self.cache_qr(cache_key, payment_url, img_base64)

            return result

        except Exception as e:
            logger.error(f"Error generating payment QR: {e}")
            return {"success": False, "error": str(e)}

    def enhance_qr_image(self, qr_img: Image.Image, address: str,
                        amount: float = None, label: str = None) -> Image.Image:
        """Enhance QR code with branding and information"""
        try:
            # Create larger canvas
            canvas_width = self.qr_size + 100
            canvas_height = self.qr_size + 120

            # Create white background
            enhanced = Image.new('RGB', (canvas_width, canvas_height), 'white')

            # Paste QR code in center
            qr_x = (canvas_width - self.qr_size) // 2
            qr_y = 40
            enhanced.paste(qr_img, (qr_x, qr_y))

            # Add text information
            draw = ImageDraw.Draw(enhanced)

            try:
                # Try to use a nice font
                title_font = ImageFont.truetype("arial.ttf", 16)
                info_font = ImageFont.truetype("arial.ttf", 12)
                small_font = ImageFont.truetype("arial.ttf", 10)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

            # Title
            title = label or "Solana Payment"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (canvas_width - title_width) // 2
            draw.text((title_x, 10), title, fill='black', font=title_font)

            # Amount (if specified)
            if amount:
                amount_text = f"{amount} SOL"
                amount_bbox = draw.textbbox((0, 0), amount_text, font=info_font)
                amount_width = amount_bbox[2] - amount_bbox[0]
                amount_x = (canvas_width - amount_width) // 2
                draw.text((amount_x, qr_y + self.qr_size + 10), amount_text, fill='green', font=info_font)

            # Address (shortened)
            short_address = f"{address[:8]}...{address[-8:]}"
            addr_text = f"To: {short_address}"
            addr_bbox = draw.textbbox((0, 0), addr_text, font=small_font)
            addr_width = addr_bbox[2] - addr_bbox[0]
            addr_x = (canvas_width - addr_width) // 2
            addr_y = qr_y + self.qr_size + (35 if amount else 15)
            draw.text((addr_x, addr_y), addr_text, fill='gray', font=small_font)

            # Scan instruction
            instruction = "Scan with Solana wallet"
            inst_bbox = draw.textbbox((0, 0), instruction, font=small_font)
            inst_width = inst_bbox[2] - inst_bbox[0]
            inst_x = (canvas_width - inst_width) // 2
            draw.text((inst_x, addr_y + 20), instruction, fill='gray', font=small_font)

            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing QR image: {e}")
            return qr_img

    def get_cached_qr(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached QR code if valid"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT qr_data, image_base64, expires_at
                FROM qr_code_cache
                WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """, (cache_key,))

            result = cursor.fetchone()
            conn.close()

            if result:
                qr_data, image_base64, expires_at = result

                # Parse QR data to extract components
                if qr_data.startswith("solana:"):
                    address = qr_data.split("?")[0].replace("solana:", "")
                    return {
                        "success": True,
                        "qr_data": qr_data,
                        "image_base64": image_base64,
                        "address": address,
                        "cached": True
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting cached QR: {e}")
            return None

    def cache_qr(self, cache_key: str, qr_data: str, image_base64: str,
                 expires_hours: int = 24):
        """Cache QR code for reuse"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            expires_at = datetime.now() + timedelta(hours=expires_hours)

            cursor.execute("""
                INSERT OR REPLACE INTO qr_code_cache
                (cache_key, qr_data, image_base64, expires_at)
                VALUES (?, ?, ?, ?)
            """, (cache_key, qr_data, image_base64, expires_at))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error caching QR: {e}")

    async def start_transaction_confirmation(self, user_id: int,
                                           expected_amount: float,
                                           wallet_address: str,
                                           deposit_id: int = None,
                                           withdrawal_id: int = None) -> Dict[str, Any]:
        """Start monitoring for transaction confirmation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create confirmation record
            timeout_at = datetime.now() + timedelta(seconds=self.confirmation_timeout)

            cursor.execute("""
                INSERT INTO transaction_confirmations
                (user_id, deposit_id, withdrawal_id, expected_amount, wallet_address, timeout_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, deposit_id, withdrawal_id, expected_amount, wallet_address, timeout_at))

            confirmation_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Start monitoring task
            asyncio.create_task(self._monitor_transaction_confirmation(confirmation_id))

            logger.info(f"Started transaction confirmation monitoring: ID {confirmation_id}")

            return {
                "success": True,
                "confirmation_id": confirmation_id,
                "timeout_seconds": self.confirmation_timeout,
                "check_interval": self.check_interval
            }

        except Exception as e:
            logger.error(f"Error starting transaction confirmation: {e}")
            return {"success": False, "error": str(e)}

    async def _monitor_transaction_confirmation(self, confirmation_id: int):
        """Monitor specific transaction for confirmation"""
        try:
            logger.info(f"Starting transaction monitoring for confirmation ID: {confirmation_id}")

            while True:
                # Get confirmation details
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT user_id, deposit_id, withdrawal_id, expected_amount,
                           wallet_address, status, timeout_at
                    FROM transaction_confirmations
                    WHERE id = ?
                """, (confirmation_id,))

                result = cursor.fetchone()
                conn.close()

                if not result:
                    logger.warning(f"Confirmation record not found: {confirmation_id}")
                    break

                user_id, deposit_id, withdrawal_id, expected_amount, wallet_address, status, timeout_at = result

                # Check if timed out
                if datetime.now() > datetime.fromisoformat(timeout_at):
                    await self._update_confirmation_status(
                        confirmation_id, "timeout",
                        error_message="Transaction confirmation timed out"
                    )
                    logger.info(f"Transaction confirmation timed out: {confirmation_id}")
                    break

                # Check if already completed
                if status in ['confirmed', 'failed', 'timeout']:
                    break

                # Check for new transactions
                found_transaction = await self._check_for_transaction(
                    wallet_address, expected_amount, confirmation_id
                )

                if found_transaction:
                    # Transaction found and confirmed
                    await self._process_confirmed_transaction(
                        confirmation_id, found_transaction, user_id,
                        deposit_id, withdrawal_id, expected_amount
                    )
                    break

                # Wait before next check
                await asyncio.sleep(self.check_interval)

        except Exception as e:
            logger.error(f"Error in transaction confirmation monitoring: {e}")
            await self._update_confirmation_status(
                confirmation_id, "failed",
                error_message=f"Monitoring error: {str(e)}"
            )

    async def _check_for_transaction(self, wallet_address: str,
                                   expected_amount: float,
                                   confirmation_id: int) -> Optional[Dict[str, Any]]:
        """Check for matching transaction"""
        try:
            # Get recent transactions for the wallet
            signatures_result = await self.rpc_client.get_signatures_for_address(
                wallet_address, limit=10
            )

            if signatures_result.get("error"):
                logger.error(f"Error getting signatures: {signatures_result['error']}")
                return None

            # Check each recent transaction
            for sig_info in signatures_result.get("signatures", []):
                if sig_info.get("err"):
                    continue  # Skip failed transactions

                # Get transaction details
                tx_details = await self.rpc_client.get_transaction_details(sig_info["signature"])

                if tx_details.get("error") or not tx_details.get("success"):
                    continue

                # Check balance changes for matching amount
                for balance_change in tx_details.get("balance_changes", []):
                    if (balance_change["account"] == wallet_address and
                        balance_change["change_lamports"] > 0):  # Incoming transaction

                        received_sol = balance_change["change_lamports"] / 1_000_000_000

                        # Allow small tolerance for fees and rounding
                        tolerance = 0.001  # 0.001 SOL tolerance
                        if abs(received_sol - expected_amount) <= tolerance:
                            logger.info(f"Found matching transaction: {sig_info['signature']}")
                            return {
                                "signature": sig_info["signature"],
                                "amount_sol": received_sol,
                                "amount_lamports": balance_change["change_lamports"],
                                "slot": tx_details.get("slot"),
                                "block_time": tx_details.get("block_time"),
                                "confirmations": tx_details.get("confirmations", "finalized")
                            }

            return None

        except Exception as e:
            logger.error(f"Error checking for transaction: {e}")
            return None

    async def _process_confirmed_transaction(self, confirmation_id: int,
                                           transaction: Dict[str, Any],
                                           user_id: int, deposit_id: int,
                                           withdrawal_id: int, expected_amount: float):
        """Process confirmed transaction and update balances"""
        try:
            signature = transaction["signature"]
            amount_sol = transaction["amount_sol"]

            logger.info(f"Processing confirmed transaction: {signature}")

            # Update confirmation status
            await self._update_confirmation_status(
                confirmation_id, "confirmed",
                transaction_hash=signature,
                confirmations=1
            )

            # Process based on transaction type
            if deposit_id:
                # It's a deposit - update user balance
                await self._process_confirmed_deposit(
                    user_id, deposit_id, signature, amount_sol
                )
            elif withdrawal_id:
                # It's a withdrawal - mark as completed
                await self._process_confirmed_withdrawal(
                    withdrawal_id, signature
                )

            logger.info(f"Successfully processed confirmed transaction: {signature}")

        except Exception as e:
            logger.error(f"Error processing confirmed transaction: {e}")
            await self._update_confirmation_status(
                confirmation_id, "failed",
                error_message=f"Processing error: {str(e)}"
            )

    async def _process_confirmed_deposit(self, user_id: int, deposit_id: int,
                                       signature: str, amount_sol: float):
        """Process confirmed deposit transaction"""
        try:
            # Calculate FC amount
            current_rate = self.payment_system.get_sol_to_fc_rate()
            fc_amount = int(amount_sol * current_rate)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current user balance
            cursor.execute("SELECT fun_coins FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            old_balance = result[0] if result else 0

            # Update deposit status
            cursor.execute("""
                UPDATE solana_deposits
                SET status = 'confirmed', transaction_hash = ?, confirmed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (signature, deposit_id))

            # Update user balance
            new_balance = old_balance + fc_amount
            cursor.execute("""
                UPDATE users SET fun_coins = ?
                WHERE user_id = ?
            """, (new_balance, user_id))

            # Log balance update
            cursor.execute("""
                INSERT INTO balance_updates
                (user_id, transaction_type, amount_change, old_balance, new_balance,
                 transaction_hash, source)
                VALUES (?, 'deposit', ?, ?, ?, ?, 'automatic_confirmation')
            """, (user_id, fc_amount, old_balance, new_balance, signature))

            conn.commit()
            conn.close()

            logger.info(f"Processed deposit: User {user_id} received {fc_amount} FC from {amount_sol} SOL")

        except Exception as e:
            logger.error(f"Error processing confirmed deposit: {e}")
            raise

    async def _process_confirmed_withdrawal(self, withdrawal_id: int, signature: str):
        """Process confirmed withdrawal transaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update withdrawal status
            cursor.execute("""
                UPDATE solana_withdrawals
                SET status = 'completed', transaction_hash = ?, processed_at = CURRENT_TIMESTAMP,
                    admin_notes = 'Auto-confirmed via blockchain'
                WHERE id = ?
            """, (signature, withdrawal_id))

            conn.commit()
            conn.close()

            logger.info(f"Confirmed withdrawal: {withdrawal_id} with transaction {signature}")

        except Exception as e:
            logger.error(f"Error processing confirmed withdrawal: {e}")
            raise

    async def _update_confirmation_status(self, confirmation_id: int, status: str,
                                        transaction_hash: str = None,
                                        confirmations: int = None,
                                        error_message: str = None):
        """Update confirmation status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            update_fields = ["status = ?"]
            update_values = [status]

            if transaction_hash:
                update_fields.append("transaction_hash = ?")
                update_values.append(transaction_hash)

            if confirmations is not None:
                update_fields.append("confirmations = ?")
                update_values.append(confirmations)

            if error_message:
                update_fields.append("error_message = ?")
                update_values.append(error_message)

            if status in ['confirmed', 'failed', 'timeout']:
                update_fields.append("confirmed_at = CURRENT_TIMESTAMP")

            update_values.append(confirmation_id)

            cursor.execute(f"""
                UPDATE transaction_confirmations
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, update_values)

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error updating confirmation status: {e}")

    async def get_confirmation_status(self, confirmation_id: int) -> Dict[str, Any]:
        """Get current confirmation status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT status, transaction_hash, confirmations, created_at,
                       confirmed_at, timeout_at, error_message
                FROM transaction_confirmations
                WHERE id = ?
            """, (confirmation_id,))

            result = cursor.fetchone()
            conn.close()

            if not result:
                return {"success": False, "error": "Confirmation record not found"}

            status, tx_hash, confirmations, created_at, confirmed_at, timeout_at, error_msg = result

            return {
                "success": True,
                "confirmation_id": confirmation_id,
                "status": status,
                "transaction_hash": tx_hash,
                "confirmations": confirmations,
                "created_at": created_at,
                "confirmed_at": confirmed_at,
                "timeout_at": timeout_at,
                "error_message": error_msg,
                "is_complete": status in ['confirmed', 'failed', 'timeout']
            }

        except Exception as e:
            logger.error(f"Error getting confirmation status: {e}")
            return {"success": False, "error": str(e)}

    def clean_expired_cache(self):
        """Clean expired QR codes from cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM qr_code_cache
                WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
            """)

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Cleaned {deleted_count} expired QR codes from cache")

        except Exception as e:
            logger.error(f"Error cleaning expired cache: {e}")

    async def get_balance_update_history(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get balance update history for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT transaction_type, amount_change, old_balance, new_balance,
                       transaction_hash, source, created_at
                FROM balance_updates
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))

            results = cursor.fetchall()
            conn.close()

            updates = []
            for row in results:
                updates.append({
                    "transaction_type": row[0],
                    "amount_change": row[1],
                    "old_balance": row[2],
                    "new_balance": row[3],
                    "transaction_hash": row[4],
                    "source": row[5],
                    "created_at": row[6]
                })

            return updates

        except Exception as e:
            logger.error(f"Error getting balance update history: {e}")
            return []

# Global instance
_qr_payment_system = None

def get_qr_payment_system() -> SolanaQRPaymentSystem:
    """Get global QR payment system instance"""
    global _qr_payment_system
    if _qr_payment_system is None:
        _qr_payment_system = SolanaQRPaymentSystem()
    return _qr_payment_system

# Convenience functions
async def generate_payment_qr_code(address: str, amount: float = None,
                                 memo: str = None, label: str = None) -> Dict[str, Any]:
    """Generate QR code for Solana payment"""
    system = get_qr_payment_system()
    return system.generate_payment_qr(address, amount, memo, label)

async def start_payment_confirmation(user_id: int, expected_amount: float,
                                   wallet_address: str, deposit_id: int = None) -> Dict[str, Any]:
    """Start monitoring payment confirmation"""
    system = get_qr_payment_system()
    return await system.start_transaction_confirmation(
        user_id, expected_amount, wallet_address, deposit_id
    )

async def check_payment_status(confirmation_id: int) -> Dict[str, Any]:
    """Check payment confirmation status"""
    system = get_qr_payment_system()
    return await system.get_confirmation_status(confirmation_id)

if __name__ == "__main__":
    # Test the QR system
    async def test_qr_system():
        system = get_qr_payment_system()

        # Test QR generation
        test_address = "DsJd8pDi44f82dRjG3zBnxrv2t32ZyfKUjz5cqFkdrY9"
        qr_result = system.generate_payment_qr(
            test_address,
            amount=0.1,
            label="Test Payment",
            memo="Test deposit"
        )

        print(f"QR Generation: {'Success' if qr_result['success'] else 'Failed'}")
        if qr_result['success']:
            print(f"QR Data: {qr_result['qr_data']}")
            print(f"Image size: {len(qr_result['image_base64'])} bytes")

        # Test confirmation monitoring
        confirmation_result = await system.start_transaction_confirmation(
            user_id=12345,
            expected_amount=0.1,
            wallet_address=test_address
        )

        print(f"Confirmation monitoring: {'Started' if confirmation_result['success'] else 'Failed'}")

    asyncio.run(test_qr_system())