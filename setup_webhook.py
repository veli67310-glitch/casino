#!/usr/bin/env python3
"""
Helius Webhook Setup Script
Otomatik ödeme sistemi için webhook'ları kurar
"""

import asyncio
import logging
from helius_webhook import get_webhook_manager
from solana_payment import get_solana_payment

logger = logging.getLogger(__name__)

# WEBHOOK CONFIGURASYONU
WEBHOOK_DOMAIN = "https://your-domain.com"  # BURAYA KENDİ DOMAİNİNİZİ YAZIN
WEBHOOK_ENDPOINT = "/helius-webhook"
WEBHOOK_URL = f"{WEBHOOK_DOMAIN}{WEBHOOK_ENDPOINT}"

async def setup_automatic_payments():
    """Otomatik ödeme sistemi kurulumu"""
    try:
        logger.info("🚀 Setting up automatic payment system...")

        # 1. Webhook manager'ı al
        webhook_manager = await get_webhook_manager()

        # 2. Admin cüzdan adreslerini al
        solana_system = get_solana_payment()
        admin_wallet = solana_system.get_deposit_wallet()

        # Monitoring için cüzdan listesi
        wallet_addresses = [admin_wallet]

        logger.info(f"📝 Monitoring wallets: {wallet_addresses}")
        logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}")

        # 3. Helius webhook'u oluştur
        async with webhook_manager as manager:
            webhook_id = await manager.create_webhook(
                webhook_url=WEBHOOK_URL,
                wallet_addresses=wallet_addresses
            )

            if webhook_id:
                logger.info(f"✅ Webhook created successfully!")
                logger.info(f"   Webhook ID: {webhook_id}")
                logger.info(f"   Monitoring: {len(wallet_addresses)} wallets")

                # Webhook bilgilerini kaydet
                save_webhook_config(webhook_id, wallet_addresses)

                return True
            else:
                logger.error("❌ Failed to create webhook")
                return False

    except Exception as e:
        logger.error(f"Error setting up automatic payments: {e}")
        return False

def save_webhook_config(webhook_id: str, wallet_addresses: list):
    """Webhook konfigürasyonunu kaydet"""
    try:
        import json

        config = {
            "webhook_id": webhook_id,
            "webhook_url": WEBHOOK_URL,
            "wallet_addresses": wallet_addresses,
            "created_at": str(datetime.now()),
            "status": "active"
        }

        with open("webhook_config.json", "w") as f:
            json.dump(config, f, indent=2)

        logger.info("💾 Webhook configuration saved to webhook_config.json")

    except Exception as e:
        logger.error(f"Error saving webhook config: {e}")

async def test_webhook_system():
    """Webhook sistemini test et"""
    try:
        logger.info("🧪 Testing webhook system...")

        # Webhook config dosyasını kontrol et
        try:
            with open("webhook_config.json", "r") as f:
                config = json.load(f)
                webhook_id = config["webhook_id"]

                logger.info(f"📄 Found webhook config: {webhook_id}")

                # Webhook bilgilerini al
                webhook_manager = await get_webhook_manager()
                async with webhook_manager as manager:
                    info = await manager.get_webhook_info(webhook_id)

                    if info:
                        logger.info("✅ Webhook is active and working!")
                        logger.info(f"   Status: {info.get('status', 'unknown')}")
                        logger.info(f"   Addresses: {len(info.get('accountAddresses', []))}")
                        return True
                    else:
                        logger.error("❌ Webhook not found or inactive")
                        return False

        except FileNotFoundError:
            logger.error("❌ No webhook configuration found. Run setup first.")
            return False

    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        return False

async def remove_webhook():
    """Webhook'u kaldır (gerekirse)"""
    try:
        with open("webhook_config.json", "r") as f:
            config = json.load(f)
            webhook_id = config["webhook_id"]

        webhook_manager = await get_webhook_manager()
        async with webhook_manager as manager:
            success = await manager.delete_webhook(webhook_id)

            if success:
                logger.info("✅ Webhook removed successfully")
                # Config dosyasını sil
                import os
                os.remove("webhook_config.json")
            else:
                logger.error("❌ Failed to remove webhook")

    except Exception as e:
        logger.error(f"Error removing webhook: {e}")

async def main():
    """Ana setup fonksiyonu"""
    import sys

    if len(sys.argv) < 2:
        print("""
🚀 Helius Webhook Setup Tool

Kullanım:
  python setup_webhook.py setup    # Webhook'u kur
  python setup_webhook.py test     # Test et
  python setup_webhook.py remove   # Kaldır

⚠️  ÖNEMLİ: setup_webhook.py dosyasında WEBHOOK_DOMAIN'i güncelleyin!
        """)
        return

    command = sys.argv[1].lower()

    if command == "setup":
        print("🚀 Setting up automatic payment system...")
        success = await setup_automatic_payments()
        if success:
            print("✅ Setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Start webhook server: python webhook_server.py")
            print("2. Test the system: python setup_webhook.py test")
        else:
            print("❌ Setup failed. Check logs for details.")

    elif command == "test":
        print("🧪 Testing webhook system...")
        success = await test_webhook_system()
        if success:
            print("✅ Webhook system is working correctly!")
        else:
            print("❌ Webhook system test failed.")

    elif command == "remove":
        print("🗑️ Removing webhook...")
        await remove_webhook()
        print("✅ Webhook removed.")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    import json
    from datetime import datetime
    asyncio.run(main())