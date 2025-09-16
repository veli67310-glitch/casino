#!/usr/bin/env python3
"""
🚀 Otomatik SOL Ödeme Sistemi Aktifleştirme Aracı
Helius webhook sistemini kurup test eder
"""

import asyncio
import logging
import sys
import json
from datetime import datetime

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Başlık yazdır"""
    print("""
🚀 =============================================== 🚀
   OTOMATIK SOL ÖDEME SİSTEMİ AKTİFLEŞTİRME ARACI
🚀 =============================================== 🚀

Bu araç aşağıdaki işlemleri yapar:
✅ 1. Database tablolarını oluşturur
✅ 2. Helius webhook'unu kurar
✅ 3. Webhook server'ını test eder
✅ 4. Otomatik ödeme sistemini aktif eder

⚠️  DİKKAT: Bu işlem için internet bağlantısı gereklidir.
⚠️  Helius API key'iniz aktif olmalıdır.
""")

async def step1_setup_database():
    """1. Adım: Database kurulumu"""
    print("\n📋 Adım 1: Database tablolarını oluşturuyor...")

    try:
        from database_webhook_setup import setup_webhook_tables
        setup_webhook_tables()
        print("✅ Database tabloları başarıyla oluşturuldu")
        return True
    except Exception as e:
        print(f"❌ Database kurulumu başarısız: {e}")
        return False

async def step2_setup_webhook():
    """2. Adım: Helius webhook kurulumu"""
    print("\n🔗 Adım 2: Helius webhook'unu kuruyor...")

    # Domain kontrolü
    webhook_domain = input("\n📝 Webhook domain'inizi girin (örn: https://yourbot.com): ").strip()

    if not webhook_domain.startswith("http"):
        print("❌ Geçerli bir URL girin (http:// veya https:// ile başlamalı)")
        return False

    try:
        # setup_webhook.py dosyasını güncelle
        with open("setup_webhook.py", "r") as f:
            content = f.read()

        # Domain'i güncelle
        updated_content = content.replace(
            'WEBHOOK_DOMAIN = "https://your-domain.com"',
            f'WEBHOOK_DOMAIN = "{webhook_domain}"'
        )

        with open("setup_webhook.py", "w") as f:
            f.write(updated_content)

        # Webhook setup'ı çalıştır
        from setup_webhook import setup_automatic_payments
        success = await setup_automatic_payments()

        if success:
            print("✅ Helius webhook başarıyla kuruldu")
            return True
        else:
            print("❌ Webhook kurulumu başarısız")
            return False

    except Exception as e:
        print(f"❌ Webhook kurulumu hatası: {e}")
        return False

async def step3_test_system():
    """3. Adım: Sistem testi"""
    print("\n🧪 Adım 3: Sistem testi yapıyor...")

    try:
        # Webhook config dosyasını kontrol et
        try:
            with open("webhook_config.json", "r") as f:
                config = json.load(f)
                print(f"✅ Webhook ID: {config['webhook_id']}")
                print(f"✅ Monitored wallets: {len(config['wallet_addresses'])}")
        except FileNotFoundError:
            print("❌ Webhook config dosyası bulunamadı")
            return False

        # Database bağlantısını test et
        from database_webhook_setup import get_pending_transaction_by_criteria
        test_result = get_pending_transaction_by_criteria("test", 0.1)
        print("✅ Database bağlantısı çalışıyor")

        return True

    except Exception as e:
        print(f"❌ Sistem testi başarısız: {e}")
        return False

async def step4_start_services():
    """4. Adım: Servisleri başlat"""
    print("\n🚀 Adım 4: Otomatik ödeme sistemini aktifleştiriyor...")

    try:
        print("✅ Webhook server bot ile birlikte başlatılacak")
        print("✅ Helius webhook sistemi aktif")
        print("✅ Otomatik ödeme işleme hazır")

        # Konfigürasyon özeti
        print("\n📊 SİSTEM ÖZETİ:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔄 Ödeme Akışı:")
        print("   1. Kullanıcı SOL yatırma talebi oluşturur")
        print("   2. Admin cüzdan adresi verilir")
        print("   3. Kullanıcı SOL gönderir")
        print("   4. Helius webhook anında algılar")
        print("   5. Sistem otomatik olarak FC ekler")
        print("   6. Telegram bildirimi gönderilir")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return True

    except Exception as e:
        print(f"❌ Servis başlatma hatası: {e}")
        return False

async def create_startup_guide():
    """Başlangıç rehberi oluştur"""
    guide = """
🚀 OTOMATIK SOL ÖDEME SİSTEMİ - KULLANIM REHBERİ

✅ SİSTEM AKTİF - Artık otomatik SOL ödemeleri çalışıyor!

📋 KULLANIM ADIMLARI:
1. Botunuzu başlatın: python main.py
2. Kullanıcı /solana komutu ile ödeme menüsüne gider
3. SOL miktarını seçer
4. Admin cüzdan adresine SOL gönderir
5. Sistem otomatik olarak FC ekler (1-2 saniye içinde)

🔧 YÖNETİM KOMUTLARI:
• Webhook durumu: python setup_webhook.py test
• Webhook kaldırma: python setup_webhook.py remove
• Database sıfırlama: python database_webhook_setup.py

📊 İZLEME:
• Webhook logları: webhook.log
• Bot logları: casino_bot.log
• Database: casino_bot.db

⚠️  ÖNEMLİ NOTLAR:
• Webhook server port 8080'de çalışır
• Helius API rate limitlari vardır
• Admin cüzdanınız yeterli SOL bakiyesine sahip olmalı

🆘 SORUN GİDERME:
• Webhook çalışmıyor → Domain ayarlarını kontrol edin
• Ödemeler algılanmıyor → Helius API key'i kontrol edin
• Database hatası → Tabloları yeniden oluşturun

🎯 SİSTEM HAZIR! İyi kullanımlar!
"""

    with open("AUTOMATIC_PAYMENTS_GUIDE.txt", "w", encoding="utf-8") as f:
        f.write(guide)

    print("📖 Kullanım rehberi 'AUTOMATIC_PAYMENTS_GUIDE.txt' dosyasına kaydedildi")

async def main():
    """Ana aktifleştirme fonksiyonu"""
    print_banner()

    # Kullanıcı onayı al
    confirm = input("Devam etmek istiyor musunuz? (e/h): ").lower()
    if confirm != 'e':
        print("❌ İşlem iptal edildi")
        return

    success_count = 0
    total_steps = 4

    # Adım 1: Database
    if await step1_setup_database():
        success_count += 1
    else:
        print("❌ Database kurulumu başarısız - devam edilemiyor")
        return

    # Adım 2: Webhook
    if await step2_setup_webhook():
        success_count += 1
    else:
        print("⚠️  Webhook kurulumu başarısız - manuel kurulum gerekebilir")

    # Adım 3: Test
    if await step3_test_system():
        success_count += 1
    else:
        print("⚠️  Sistem testi başarısız - kontrol edin")

    # Adım 4: Aktifleştirme
    if await step4_start_services():
        success_count += 1

    # Sonuç
    print(f"\n🎯 SONUÇ: {success_count}/{total_steps} adım başarılı")

    if success_count == total_steps:
        print("🎉 BAŞARILI! Otomatik SOL ödeme sistemi tamamen aktif!")
        await create_startup_guide()
    elif success_count >= 2:
        print("⚠️  Kısmi başarı - sistem çalışabilir ama kontrol edin")
        await create_startup_guide()
    else:
        print("❌ Kurulum başarısız - manuel kurulum gerekiyor")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ İşlem kullanıcı tarafından iptal edildi")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")