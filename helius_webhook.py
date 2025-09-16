#!/usr/bin/env python3
"""
🚀 Helius Webhook Integration for Solana Payments
Otomatik ödeme doğrulama sistemi
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Helius API Configuration
HELIUS_API_KEY = "d64ad5df-5449-4b81-9ea5-f00c5cacfec9"
HELIUS_RPC_URL = f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"
HELIUS_WEBHOOK_URL = f"https://api.helius.xyz/v0/webhooks"

@dataclass
class TransactionData:
    """Transaction data structure"""
    signature: str
    from_address: str
    to_address: str
    amount: float  # in SOL
    timestamp: datetime
    block_height: Optional[int] = None
    confirmed: bool = False

class HeliusWebhookManager:
    """Helius Webhook yöneticisi"""

    def __init__(self, api_key: str = HELIUS_API_KEY):
        self.api_key = api_key
        self.webhook_id = None
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def create_webhook(self, webhook_url: str, wallet_addresses: List[str]) -> Optional[str]:
        """Helius webhook oluştur"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            webhook_data = {
                "webhookURL": webhook_url,
                "transactionTypes": ["Any"],
                "accountAddresses": wallet_addresses,
                "webhookType": "enhanced"
            }

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.post(
                f"{HELIUS_WEBHOOK_URL}?api-key={self.api_key}",
                headers=headers,
                json=webhook_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.webhook_id = result.get("webhookID")
                    logger.info(f"Webhook created successfully: {self.webhook_id}")
                    return self.webhook_id
                else:
                    error_text = await response.text()
                    logger.error(f"Webhook creation failed: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return None

    async def get_webhook_info(self, webhook_id: str) -> Optional[Dict]:
        """Webhook bilgilerini al"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(
                f"{HELIUS_WEBHOOK_URL}/{webhook_id}?api-key={self.api_key}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get webhook info: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return None

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Webhook sil"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.delete(
                f"{HELIUS_WEBHOOK_URL}/{webhook_id}?api-key={self.api_key}"
            ) as response:
                if response.status == 200:
                    logger.info(f"Webhook deleted: {webhook_id}")
                    return True
                else:
                    logger.error(f"Failed to delete webhook: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    def parse_webhook_data(self, webhook_data: Dict) -> List[TransactionData]:
        """Webhook verisini parse et"""
        transactions = []

        try:
            # Helius enhanced webhook formatı
            for transaction in webhook_data:
                signature = transaction.get("signature")
                if not signature:
                    continue

                # Native transfers kontrol et
                native_transfers = transaction.get("nativeTransfers", [])

                for transfer in native_transfers:
                    from_address = transfer.get("fromUserAccount")
                    to_address = transfer.get("toUserAccount")
                    amount = transfer.get("amount", 0) / 1_000_000_000  # lamports to SOL

                    if from_address and to_address and amount > 0:
                        tx_data = TransactionData(
                            signature=signature,
                            from_address=from_address,
                            to_address=to_address,
                            amount=amount,
                            timestamp=datetime.utcnow(),
                            block_height=transaction.get("slot"),
                            confirmed=True
                        )
                        transactions.append(tx_data)

        except Exception as e:
            logger.error(f"Error parsing webhook data: {e}")

        return transactions

class HeliusPaymentMonitor:
    """Ödeme takip sistemi"""

    def __init__(self, webhook_manager: HeliusWebhookManager):
        self.webhook_manager = webhook_manager
        self.pending_payments = {}  # signature -> user_data

    async def add_pending_payment(self, user_id: int, expected_amount: float, wallet_address: str):
        """Bekleyen ödeme ekle"""
        payment_data = {
            "user_id": user_id,
            "expected_amount": expected_amount,
            "wallet_address": wallet_address,
            "timestamp": datetime.utcnow(),
            "confirmed": False
        }

        # Store in database
        from database_manager import DatabaseManager
        db = DatabaseManager()
        try:
            db.cursor.execute("""
                INSERT INTO pending_transactions
                (user_id, expected_amount, wallet_address, timestamp, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (user_id, expected_amount, wallet_address, payment_data["timestamp"]))
            db.conn.commit()
            logger.info(f"Added pending payment for user {user_id}: {expected_amount} SOL")
        except Exception as e:
            logger.error(f"Error adding pending payment: {e}")

    async def process_webhook_payment(self, transaction_data: TransactionData) -> Optional[Dict]:
        """Webhook'tan gelen ödemeyi işle - Otomatik oyun parası verme sistemi"""
        try:
            from database_manager import DatabaseManager
            db = DatabaseManager()

            # Bekleyen işlemi bul
            pending_transaction = db.get_pending_transaction_by_criteria(
                wallet_address=transaction_data.to_address,
                amount=transaction_data.amount,
                tolerance=0.001
            )

            if not pending_transaction:
                logger.warning(f"No matching pending transaction found for {transaction_data.signature}")
                return None

            transaction_id = pending_transaction[0]
            user_id = pending_transaction[1]

            # SOL -> FC dönüşüm hesabı
            from solana_payment import get_solana_payment
            solana_system = get_solana_payment()
            current_rate = solana_system.get_sol_to_fc_rate()
            fc_amount = int(transaction_data.amount * current_rate)

            # İşlemi onayla
            success = db.confirm_transaction(
                transaction_id=transaction_id,
                transaction_signature=transaction_data.signature,
                fc_amount=fc_amount
            )

            if not success:
                logger.error(f"Failed to confirm transaction {transaction_id}")
                return None

            # Kullanıcı bakiyesini güncelle - OTOMATIK OYUN PARASI VERME
            with db.get_connection() as conn:
                # Mevcut bakiyeyi kontrol et
                cursor = conn.execute("SELECT fun_coins FROM users WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()

                if user_row:
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
                        VALUES (?, ?, 'completed', ?, CURRENT_TIMESTAMP, 'SOL_AUTO')
                    """, (user_id, fc_amount, transaction_data.signature))

                    # Aktivite kaydet
                    conn.execute("""
                        INSERT INTO user_activity
                        (user_id, activity_type, details, timestamp)
                        VALUES (?, 'auto_deposit', ?, CURRENT_TIMESTAMP)
                    """, (user_id, f"Automatic SOL deposit: {transaction_data.amount} SOL -> {fc_amount} FC"))

                    conn.commit()

                    logger.info(f"✅ AUTOMATIC PAYMENT PROCESSED: User {user_id} received {fc_amount} FC")
                    logger.info(f"   SOL Amount: {transaction_data.amount}")
                    logger.info(f"   TX: {transaction_data.signature}")
                    logger.info(f"   Balance: {old_balance} -> {new_balance}")

                    return {
                        "user_id": user_id,
                        "sol_amount": transaction_data.amount,
                        "fc_amount": fc_amount,
                        "transaction_signature": transaction_data.signature,
                        "old_balance": old_balance,
                        "new_balance": new_balance
                    }
                else:
                    logger.error(f"User {user_id} not found in database")
                    return None

        except Exception as e:
            logger.error(f"Error processing webhook payment: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

# Global instances
webhook_manager = None
payment_monitor = None

async def get_webhook_manager() -> HeliusWebhookManager:
    """Global webhook manager instance"""
    global webhook_manager
    if webhook_manager is None:
        webhook_manager = HeliusWebhookManager(HELIUS_API_KEY)
    return webhook_manager

async def get_payment_monitor() -> HeliusPaymentMonitor:
    """Global payment monitor instance"""
    global payment_monitor
    if payment_monitor is None:
        wm = await get_webhook_manager()
        payment_monitor = HeliusPaymentMonitor(wm)
    return payment_monitor

async def setup_helius_webhooks(webhook_endpoint_url: str, wallet_addresses: List[str]) -> bool:
    """Helius webhook'larını kur"""
    try:
        async with HeliusWebhookManager() as manager:
            webhook_id = await manager.create_webhook(webhook_endpoint_url, wallet_addresses)
            if webhook_id:
                logger.info(f"Helius webhook configured successfully: {webhook_id}")
                return True
            else:
                logger.error("Failed to setup Helius webhooks")
                return False
    except Exception as e:
        logger.error(f"Error setting up Helius webhooks: {e}")
        return False

if __name__ == "__main__":
    # Test the webhook system
    async def test_webhook():
        async with HeliusWebhookManager() as manager:
            # Test wallet addresses
            test_addresses = ["11111111111111111111111111111112"]  # System program
            webhook_id = await manager.create_webhook("https://your-domain.com/webhook", test_addresses)
            if webhook_id:
                print(f"Test webhook created: {webhook_id}")

                # Get info
                info = await manager.get_webhook_info(webhook_id)
                print(f"Webhook info: {info}")

                # Clean up
                await manager.delete_webhook(webhook_id)
                print("Test webhook deleted")

    asyncio.run(test_webhook())