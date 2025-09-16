#!/usr/bin/env python3
"""
🎯 Enhanced Payment Processor
Gelişmiş ödeme işleme sistemi - SOL lamports dönüşümü ve otomatik oyun parası
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PaymentTransaction:
    """Payment transaction data class"""
    signature: str
    from_wallet: str
    to_wallet: str
    sol_amount: float
    lamports: int
    block_height: Optional[int] = None
    timestamp: Optional[datetime] = None

class EnhancedPaymentProcessor:
    """Gelişmiş ödeme işleyici"""

    def __init__(self):
        self.LAMPORTS_PER_SOL = 1_000_000_000
        self.AMOUNT_TOLERANCE = 0.001  # SOL tolerance for matching

    def convert_lamports_to_sol(self, lamports: int) -> float:
        """Lamports'ı SOL'a dönüştür"""
        try:
            sol_amount = lamports / self.LAMPORTS_PER_SOL
            return round(sol_amount, 9)  # 9 decimal places for precision
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.error(f"Error converting lamports to SOL: {e}")
            return 0.0

    def convert_sol_to_lamports(self, sol_amount: float) -> int:
        """SOL'u lamports'a dönüştür"""
        try:
            return int(sol_amount * self.LAMPORTS_PER_SOL)
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting SOL to lamports: {e}")
            return 0

    def validate_transaction_amount(self, received_amount: float, expected_amount: float) -> bool:
        """Transaction miktarını doğrula"""
        try:
            difference = abs(received_amount - expected_amount)
            is_valid = difference <= self.AMOUNT_TOLERANCE

            if not is_valid:
                logger.warning(f"Amount mismatch: expected {expected_amount}, got {received_amount}, diff {difference}")

            return is_valid
        except (TypeError, ValueError) as e:
            logger.error(f"Error validating transaction amount: {e}")
            return False

    async def find_matching_pending_transaction(self, wallet_address: str, sol_amount: float) -> Optional[Dict]:
        """Eşleşen pending transaction bul"""
        try:
            from database_manager import DatabaseManager
            db = DatabaseManager()

            # Wallet adresi ve miktar ile pending transaction ara
            pending_tx = db.get_pending_transaction_by_criteria(
                wallet_address=wallet_address,
                amount=sol_amount,
                tolerance=self.AMOUNT_TOLERANCE
            )

            if pending_tx:
                logger.info(f"Found matching pending transaction: ID {pending_tx[0]}")
                return {
                    'id': pending_tx[0],
                    'user_id': pending_tx[1],
                    'expected_amount': pending_tx[2],
                    'wallet_address': pending_tx[3],
                    'timestamp': pending_tx[4],
                    'status': pending_tx[5]
                }
            else:
                logger.warning(f"No matching pending transaction found for {wallet_address}, amount {sol_amount}")
                return None

        except Exception as e:
            logger.error(f"Error finding matching pending transaction: {e}")
            return None

    async def add_game_credits(self, user_id: int, fc_amount: int, transaction_signature: str) -> bool:
        """Kullanıcıya oyun parası ekle"""
        try:
            from database_manager import DatabaseManager
            db = DatabaseManager()

            with db.get_connection() as conn:
                # Mevcut bakiyeyi al
                cursor = conn.execute("SELECT fun_coins FROM users WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()

                if not user_row:
                    logger.error(f"User {user_id} not found in database")
                    return False

                old_balance = user_row[0]
                new_balance = old_balance + fc_amount

                # Bakiyeyi güncelle
                conn.execute("""
                    UPDATE users
                    SET fun_coins = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (new_balance, user_id))

                # İşlem geçmişi kaydet
                conn.execute("""
                    INSERT INTO deposits
                    (user_id, amount, status, transaction_id, timestamp, method)
                    VALUES (?, ?, 'completed', ?, CURRENT_TIMESTAMP, 'SOL_AUTO_ENHANCED')
                """, (user_id, fc_amount, transaction_signature))

                # Aktivite kaydet
                conn.execute("""
                    INSERT INTO user_activity
                    (user_id, activity_type, details, timestamp)
                    VALUES (?, 'enhanced_auto_deposit', ?, CURRENT_TIMESTAMP)
                """, (user_id, f"Enhanced auto deposit: {fc_amount} FC via {transaction_signature[:16]}..."))

                conn.commit()

                logger.info(f"✅ GAME CREDITS ADDED: User {user_id}")
                logger.info(f"   Amount: {fc_amount} FC")
                logger.info(f"   Balance: {old_balance} → {new_balance}")
                logger.info(f"   TX: {transaction_signature}")

                return True

        except Exception as e:
            logger.error(f"Error adding game credits: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def send_payment_confirmation(self, user_id: int, sol_amount: float, fc_amount: int,
                                      transaction_signature: str) -> bool:
        """Ödeme onay mesajı gönder"""
        try:
            import telegram
            from config import TELEGRAM_BOT_TOKEN

            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

            # Gelişmiş mesaj formatı
            message = f"""✅ **ÖDEMENİZ ONAYLANDI!** ✅

🎉 **Tebrikler!** Solana ödemeniz başarıyla işlendi.

💰 **İşlem Detayları:**
• Gönderilen SOL: {sol_amount:.6f} SOL
• Eklenen FC: **{fc_amount:,} FC**
• İşlem Durumu: ✅ Tamamlandı

🔗 **Transaction Hash:**
`{transaction_signature}`

🎮 **Sonraki Adımlar:**
• Oyun paranız hesabınıza eklendi
• Şimdi tüm oyunlarda kullanabilirsiniz
• Bakiyenizi kontrol edebilirsiniz

⚡ **Bu işlem otomatik olarak gerçekleştirildi.**
🚀 **Artık oynamaya hazırsınız!**

🏆 İyi şanslar!"""

            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

            # Bonus sticker gönder
            try:
                stickers = [
                    "CAACAgIAAxkBAAIBY2ZxYG9mZxYG9mZxY", # Success sticker
                    "CAACAgIAAxkBAAIBY2ZxYG9mZxYG9mZxZ", # Money sticker
                    "CAACAgIAAxkBAAIBY2ZxYG9mZxYG9mZxX"  # Gaming sticker
                ]
                # await bot.send_sticker(chat_id=user_id, sticker=random.choice(stickers))
            except:
                pass  # Sticker gönderme hatası önemli değil

            logger.info(f"📨 Payment confirmation sent to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending payment confirmation: {e}")
            return False

    async def process_payment(self, transaction_data: PaymentTransaction) -> Optional[Dict]:
        """Ana ödeme işleme fonksiyonu"""
        try:
            logger.info(f"🔄 Processing payment: {transaction_data.signature[:16]}...")

            # 1. Lamports'tan SOL'a dönüştür
            sol_amount = self.convert_lamports_to_sol(transaction_data.lamports)

            if sol_amount <= 0:
                logger.error("Invalid SOL amount after conversion")
                return None

            logger.info(f"💰 Converted amount: {transaction_data.lamports} lamports = {sol_amount} SOL")

            # 2. Eşleşen pending transaction bul
            pending_tx = await self.find_matching_pending_transaction(
                wallet_address=transaction_data.to_wallet,
                sol_amount=sol_amount
            )

            if not pending_tx:
                logger.warning("No matching pending transaction found")
                return None

            # 3. Gönderen wallet adresi ve miktar kontrolü
            if not self.validate_transaction_amount(sol_amount, pending_tx['expected_amount']):
                logger.error("Transaction amount validation failed")
                return None

            # 4. SOL'u FC'ye dönüştür
            from solana_payment import get_solana_payment
            solana_system = get_solana_payment()
            current_rate = solana_system.get_sol_to_fc_rate()
            fc_amount = int(sol_amount * current_rate)

            if fc_amount <= 0:
                logger.error("Invalid FC amount after conversion")
                return None

            logger.info(f"💱 Conversion: {sol_amount} SOL → {fc_amount} FC (rate: {current_rate})")

            # 5. Pending transaction'ı onayla
            from database_manager import DatabaseManager
            db = DatabaseManager()

            success = db.confirm_transaction(
                transaction_id=pending_tx['id'],
                transaction_signature=transaction_data.signature,
                fc_amount=fc_amount
            )

            if not success:
                logger.error("Failed to confirm transaction in database")
                return None

            # 6. Oyun parası ekle
            credits_added = await self.add_game_credits(
                user_id=pending_tx['user_id'],
                fc_amount=fc_amount,
                transaction_signature=transaction_data.signature
            )

            if not credits_added:
                logger.error("Failed to add game credits")
                return None

            # 7. Telegram onay mesajı gönder
            await self.send_payment_confirmation(
                user_id=pending_tx['user_id'],
                sol_amount=sol_amount,
                fc_amount=fc_amount,
                transaction_signature=transaction_data.signature
            )

            # 8. Başarılı işlem sonucu
            result = {
                'success': True,
                'user_id': pending_tx['user_id'],
                'sol_amount': sol_amount,
                'fc_amount': fc_amount,
                'transaction_signature': transaction_data.signature,
                'from_wallet': transaction_data.from_wallet,
                'to_wallet': transaction_data.to_wallet,
                'processed_at': datetime.utcnow(),
                'pending_transaction_id': pending_tx['id']
            }

            logger.info(f"✅ PAYMENT SUCCESSFULLY PROCESSED!")
            logger.info(f"   User: {pending_tx['user_id']}")
            logger.info(f"   Amount: {sol_amount} SOL → {fc_amount} FC")
            logger.info(f"   TX: {transaction_data.signature}")

            return result

        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def get_payment_statistics(self, user_id: Optional[int] = None, days: int = 30) -> Dict:
        """Ödeme istatistikleri al"""
        try:
            from database_manager import DatabaseManager
            db = DatabaseManager()

            with db.get_connection() as conn:
                # Total payments
                if user_id:
                    cursor = conn.execute("""
                        SELECT COUNT(*), SUM(fc_amount)
                        FROM pending_transactions
                        WHERE user_id = ? AND status = 'confirmed'
                        AND confirmed_at >= datetime('now', '-{} days')
                    """.format(days), (user_id,))
                else:
                    cursor = conn.execute("""
                        SELECT COUNT(*), SUM(fc_amount)
                        FROM pending_transactions
                        WHERE status = 'confirmed'
                        AND confirmed_at >= datetime('now', '-{} days')
                    """.format(days))

                result = cursor.fetchone()
                payment_count = result[0] or 0
                total_fc = result[1] or 0

                # Pending payments
                if user_id:
                    cursor = conn.execute("""
                        SELECT COUNT(*), SUM(expected_amount)
                        FROM pending_transactions
                        WHERE user_id = ? AND status = 'pending'
                    """, (user_id,))
                else:
                    cursor = conn.execute("""
                        SELECT COUNT(*), SUM(expected_amount)
                        FROM pending_transactions
                        WHERE status = 'pending'
                    """)

                result = cursor.fetchone()
                pending_count = result[0] or 0
                pending_sol = result[1] or 0.0

                return {
                    'payment_count': payment_count,
                    'total_fc_processed': total_fc,
                    'pending_count': pending_count,
                    'pending_sol_amount': pending_sol,
                    'days_period': days,
                    'user_id': user_id
                }

        except Exception as e:
            logger.error(f"Error getting payment statistics: {e}")
            return {}

# Global instance
enhanced_processor = EnhancedPaymentProcessor()

async def process_webhook_payment(signature: str, from_wallet: str, to_wallet: str,
                                lamports: int, block_height: Optional[int] = None) -> Optional[Dict]:
    """Webhook ödeme işleme wrapper fonksiyonu"""

    transaction_data = PaymentTransaction(
        signature=signature,
        from_wallet=from_wallet,
        to_wallet=to_wallet,
        sol_amount=0,  # Will be calculated from lamports
        lamports=lamports,
        block_height=block_height,
        timestamp=datetime.utcnow()
    )

    return await enhanced_processor.process_payment(transaction_data)

# Utility functions
def get_enhanced_processor() -> EnhancedPaymentProcessor:
    """Global enhanced processor instance döndür"""
    return enhanced_processor