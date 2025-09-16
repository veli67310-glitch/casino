#!/usr/bin/env python3
"""
Solana Flow Completion Handlers
Wallet seçimi sonrası işlemleri tamamlayan fonksiyonlar
"""

import logging
from safe_telegram_handler import safe_edit_message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

async def start_automatic_deposit_detection(query, context, user, casino_bot, sol_amount):
    """Otomatik ödeme algılama sistemi başlat"""
    try:
        from database_manager import DatabaseManager

        db = DatabaseManager()
        user_id = user['user_id']

        # Kullanıcının bekleyen işlemlerini kontrol et
        pending_transactions = db.get_user_pending_transactions(user_id)

        # En son sol_amount ile eşleşen işlemi bul
        matching_transaction = None
        for tx in pending_transactions:
            if abs(float(tx[2]) - float(sol_amount)) < 0.001:  # expected_amount comparison
                matching_transaction = tx
                break

        if not matching_transaction:
            await safe_edit_message(
                query,
                "❌ Bekleyen işlem bulunamadı. Lütfen önce SOL gönderin.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Geri", callback_data="solana_deposit_menu")
                ]])
            )
            return

        text = f"""🚀 **OTOMATIK ÖDEME ALGILAMA AKTİF** 🚀

⏰ **Durum:** Blockchain taranıyor...
💰 **Beklenen Miktar:** {sol_amount} SOL
🎯 **Hedef Adres:** Admin Wallet

📊 **İŞLEM BİLGİLERİ:**
• İşlem ID: #{matching_transaction[0]}
• Oluşturulma: {matching_transaction[4][:16]}
• Durum: Bekliyor ⏳

🔍 **NASIL ÇALIŞIR:**
• Helius webhook sistemi sürekli blockchain'i tarar
• SOL geldiğinde otomatik algılanır
• Oyun paranız anında hesabınıza eklenir
• Telegram bildirimi gönderilir

⚡ **ÖNEMLİ:**
Bu işlem tamamen otomatiktir. SOL gönderdikten sonra 30-60 saniye bekleyin.

🎉 Artık manuel onay gerekmez!"""

        buttons = [
            [InlineKeyboardButton("🔄 Durumu Kontrol Et", callback_data=f"check_deposit_status_{matching_transaction[0]}")],
            [InlineKeyboardButton("📊 Bekleyen İşlemlerim", callback_data="my_pending_transactions")],
            [InlineKeyboardButton("💰 Bakiye", callback_data="check_balance")],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="main_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        await safe_edit_message(
            query=query,
            text=text,
            reply_markup=reply_markup
        )

        await query.answer("🚀 Otomatik algılama aktif! SOL'ı gönderin.", show_alert=False)

    except Exception as e:
        logger.error(f"Error starting automatic detection: {e}")
        await safe_edit_message(
            query,
            "❌ Otomatik algılama başlatılamadı.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Geri", callback_data="solana_deposit_menu")
            ]])
        )

async def handle_deposit_confirmation_with_wallet(query, context, user, casino_bot, sol_amount):
    """Wallet seçimi sonrası deposit onay işlemi"""
    try:
        # Context'ten wallet bilgilerini al
        wallet_id = context.user_data.get('solana_deposit', {}).get('wallet_id', 'unknown')
        wallet_info = context.user_data.get('solana_deposit', {}).get('wallet_info', {})
        wallet_name = wallet_info.get('name', 'Seçilen Wallet')

        # Solana deposit talebi oluştur
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        result = solana_system.create_deposit_request(user['user_id'], float(sol_amount))

        if not result['success']:
            await safe_edit_message(
                query, f"❌ {result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="solana_deposit_menu")]])
            )
            return

        # Kullanıcıya onay mesajı
        text = f"""
✅ **YATIRIM TALEBİNİZ OLUŞTURULDU** ✅

📋 **Talep ID:** {result['deposit_id']}
💰 **Miktar:** {result['sol_amount']} SOL
🎯 **Alacağınız:** {result['fc_amount']:,} FC
🔗 **Kullanılan Wallet:** {wallet_name}

💳 **ÖDEME ADRESİ:**
`{result['wallet_address']}`

⚡ **İŞLEM ADIMLARI:**
1. ✅ Wallet seçildi ({wallet_name})
2. ⏳ Admin onayı bekleniyor
3. ⏳ FC bakiyeniz yüklenecek

⏰ **Süre:** 5-15 dakika (işlem yoğunluğuna göre)

📞 **Admin bilgilendirildi!**
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Adresi Kopyala", callback_data=f"copy_wallet_address_{result['wallet_address']}")],
            [InlineKeyboardButton("🔄 Durumu Kontrol Et", callback_data=f"check_deposit_status_{result['deposit_id']}")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        await safe_edit_message(
            query, text, reply_markup=keyboard
        )

        # Admin bildirimi gönder
        from wallet_selector import send_admin_payment_notification
        await send_admin_payment_notification(context, user, result)

        # Context'i temizle
        if 'solana_deposit' in context.user_data:
            del context.user_data['solana_deposit']

    except Exception as e:
        logger.error(f"Deposit confirmation with wallet error: {e}")
        await safe_edit_message(
            query, "❌ Deposit talebi oluşturulamadı.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="solana_deposit_menu")]])
        )

async def show_wallet_address_input(query, context, sol_amount):
    """Çekim için wallet adresi girme ekranı"""
    try:
        # Context'ten wallet bilgilerini al
        wallet_id = context.user_data.get('solana_withdrawal', {}).get('wallet_id', 'unknown')
        wallet_info = context.user_data.get('solana_withdrawal', {}).get('wallet_info', {})
        wallet_name = wallet_info.get('name', 'Seçilen Wallet')

        # Solana sistemi ve hesaplamalar
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        # Komisyon hesabı
        withdrawal_fee = float(sol_amount) * solana_system.withdrawal_fee_rate
        net_sol = float(sol_amount) - withdrawal_fee

        text = f"""
💸 **{wallet_name} - CÜZDAN ADRESİ GİRİN** 💸

🔗 **Seçilen Wallet:** {wallet_name}
💰 **Çekim Miktarı:** {sol_amount} SOL
💳 **Alacağınız:** {net_sol:.4f} SOL
🏦 **Komisyon:** {withdrawal_fee:.4f} SOL

📝 **SOL Cüzdan Adresinizi Girin:**
{wallet_name} uygulamanızdan SOL adresinizi kopyalayın ve buraya mesaj olarak gönderin.

⚠️ **DİKKAT:**
• Doğru {wallet_name} SOL adresi girin
• Yanlış adres = para kaybı
• İşlem geri alınamaz
• Sadece Solana ağı desteklenir

💡 **Nasıl Bulunur:**
1. {wallet_name} uygulamasını açın
2. SOL/Solana sekmesine gidin
3. "Receive" veya "Alma" butonuna tıklayın
4. Adresi kopyalayın ve buraya yapıştırın

👇 **Cüzdan adresinizi bir sonraki mesajda gönderin.**
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Geri", callback_data=f"withdrawal_select_wallet_{wallet_id}_{sol_amount}")]
        ])

        await safe_edit_message(
            query, text, reply_markup=keyboard
        )

        # Kullanıcıyı bekleme moduna al
        context.user_data['waiting_for_withdrawal_address'] = {
            'sol_amount': sol_amount,
            'wallet_id': wallet_id,
            'wallet_name': wallet_name
        }

    except Exception as e:
        logger.error(f"Wallet address input error: {e}")
        await safe_edit_message(
            query, "❌ Adres giriş ekranı yüklenemedi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="solana_withdraw_menu")]])
        )

async def handle_withdrawal_address_input(update, context, wallet_address):
    """Kullanıcının girdiği wallet adresini işle"""
    try:
        # Context'ten withdrawal bilgilerini al
        withdrawal_info = context.user_data.get('waiting_for_withdrawal_address', {})

        if not withdrawal_info:
            await update.message.reply_text("❌ Çekim bilgileri bulunamadı. Lütfen tekrar deneyin.")
            return

        sol_amount = withdrawal_info.get('sol_amount')
        wallet_name = withdrawal_info.get('wallet_name', 'Wallet')

        # Basit Solana adres validasyonu
        if not wallet_address or len(wallet_address) < 32 or len(wallet_address) > 44:
            await update.message.reply_text(
                f"❌ **Geçersiz Solana Adresi!**\n\n"
                f"🔍 **Sorunlar:**\n"
                f"• Adres çok kısa veya uzun\n"
                f"• Solana adresleri 32-44 karakter arası olur\n\n"
                f"💡 **{wallet_name} uygulamanızdan doğru SOL adresinizi kopyalayın.**",
                parse_mode='Markdown'
            )
            return

        # Solana çekim talebini oluştur
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # FC miktarını hesapla
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        # Çekim talebi oluştur
        result = await solana_system.create_withdrawal_request(
            update.effective_user.id,
            fc_amount,
            wallet_address
        )

        if not result['success']:
            await update.message.reply_text(f"❌ {result['error']}")
            return

        # Başarı mesajı
        text = f"""
✅ **ÇEKİM TALEBİNİZ ALINDI** ✅

💸 **Çekim Detayları:**
• Çekilen FC: {result['fc_amount']:,} FC ⚠️ **BAKİYENİZDEN DÜŞTÜ**
• Alacağınız SOL: {result['sol_amount']:.4f} SOL
• Komisyon: {result['fee']:.4f} SOL
🔗 **Hedef Wallet:** {wallet_name}
💳 **Adres:** `{wallet_address[:10]}...{wallet_address[-6:]}`

📝 **Talep ID:** {result['withdrawal_id']}
⏳ **Durum:** Admin İncelemesinde

⚠️ **ÖNEMLİ:**
• Oyun paranız çoktan bakiyenizden düştü
• Admin onaylarsa SOL {wallet_name} cüzdanınıza gelecek
• Admin reddederse paranız iade edilecek

📞 **Admin bilgilendirildi!**
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Durumu Kontrol Et", callback_data=f"check_withdrawal_status_{result['withdrawal_id']}")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

        # Admin'e çekim bildirimi gönder
        from withdrawal_handlers import handle_admin_withdrawal_notification
        # User bilgisini hazırla
        user_info = {
            'user_id': update.effective_user.id,
            'username': update.effective_user.username or 'Anonymous'
        }
        await handle_admin_withdrawal_notification(context, user_info, result)

        # Context'i temizle
        del context.user_data['waiting_for_withdrawal_address']
        if 'solana_withdrawal' in context.user_data:
            del context.user_data['solana_withdrawal']

    except Exception as e:
        logger.error(f"Withdrawal address input error: {e}")
        await update.message.reply_text("❌ Çekim talebi oluşturulamadı. Lütfen tekrar deneyin.")