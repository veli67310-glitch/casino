#!/usr/bin/env python3
"""
Wallet Selector Module - Kullanıcı wallet seçimi için inline keyboard menüsü
"""

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from safe_telegram_handler import safe_edit_message

logger = logging.getLogger(__name__)

# Wallet deep link URLs
WALLET_DEEP_LINKS = {
    "phantom": {
        "name": "👻 Phantom",
        "ios": "phantom://",
        "android": "phantom://",
        "web": "https://phantom.app/",
        "chrome_extension": "chrome-extension://bfnaelmomeimhlpmgjnjophhpkkoljpa/popup.html"
    },
    "solflare": {
        "name": "☀️ Solflare",
        "ios": "solflare://",
        "android": "solflare://",
        "web": "https://solflare.com/",
        "chrome_extension": "chrome-extension://bhhhlbepdkbapadjdnnojkbgioiodbic/popup.html"
    },
    "trust": {
        "name": "🛡️ Trust Wallet",
        "ios": "trust://",
        "android": "trust://",
        "web": "https://trustwallet.com/",
        "mobile_app": "https://link.trustwallet.com/open_url"
    }
}

def create_wallet_selection_keyboard():
    """Wallet seçimi için inline keyboard oluşturur"""
    keyboard = []

    # Wallet seçenekleri
    for wallet_id, wallet_info in WALLET_DEEP_LINKS.items():
        keyboard.append([
            InlineKeyboardButton(
                wallet_info["name"],
                callback_data=f"select_wallet_{wallet_id}"
            )
        ])

    # Geri dön butonu
    keyboard.append([
        InlineKeyboardButton("🔙 Geri", callback_data="solana_payment_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

def create_wallet_connect_keyboard(wallet_id: str):
    """Seçilen wallet için bağlantı seçenekleri keyboard'u"""
    wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
    if not wallet_info:
        return None

    keyboard = []

    # Mobil uygulama linki
    if wallet_info.get("ios") or wallet_info.get("android"):
        keyboard.append([
            InlineKeyboardButton(
                "📱 Mobil Uygulamayı Aç",
                callback_data=f"open_wallet_mobile_{wallet_id}"
            )
        ])

    # Web versiyonu
    if wallet_info.get("web"):
        keyboard.append([
            InlineKeyboardButton(
                "🌐 Web Versiyonu",
                url=wallet_info["web"]
            )
        ])

    # Chrome extension (varsa)
    if wallet_info.get("chrome_extension"):
        keyboard.append([
            InlineKeyboardButton(
                "🔗 Chrome Uzantısı",
                url=wallet_info["chrome_extension"]
            )
        ])

    # Başka wallet seç ve geri dön
    keyboard.extend([
        [InlineKeyboardButton("🔄 Başka Wallet Seç", callback_data="wallet_selection")],
        [InlineKeyboardButton("🔙 Geri", callback_data="solana_payment_menu")]
    ])

    return InlineKeyboardMarkup(keyboard)

async def show_wallet_selection_menu(update, context: ContextTypes.DEFAULT_TYPE):
    """Wallet seçim menüsünü gösterir"""
    text = """
🔗 **Wallet Seçimi**

Solana işlemleri için kullanmak istediğiniz wallet'ı seçin:

🔐 **Güvenlik Notu:**
• Sadece resmi wallet uygulamalarını kullanın
• Seed phrase'inizi kimseyle paylaşmayın
• İşlem öncesi adresleri kontrol edin
    """

    keyboard = create_wallet_selection_keyboard()

    await safe_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=keyboard
    )

async def handle_wallet_selection(update, context: ContextTypes.DEFAULT_TYPE):
    """Wallet seçimini işler"""
    query = update.callback_query
    wallet_id = query.data.replace("select_wallet_", "")

    wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
    if not wallet_info:
        await query.answer("❌ Geçersiz wallet seçimi!", show_alert=True)
        return

    # Kullanıcının seçimini kaydet
    if 'user_data' not in context.user_data:
        context.user_data['user_data'] = {}
    context.user_data['user_data']['selected_wallet'] = wallet_id

    text = f"""
✅ **{wallet_info['name']} Seçildi**

Wallet'ınızı açmak için aşağıdaki seçeneklerden birini kullanın:

🔗 **Bağlantı Seçenekleri:**
"""

    keyboard = create_wallet_connect_keyboard(wallet_id)

    await safe_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=keyboard
    )

async def handle_wallet_mobile_open(update, context: ContextTypes.DEFAULT_TYPE):
    """Mobil wallet uygulamasını açma ve ödeme onay sistemini başlatma"""
    query = update.callback_query
    wallet_id = query.data.replace("open_wallet_mobile_", "")

    wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
    if not wallet_info:
        await query.answer("❌ Geçersiz wallet!", show_alert=True)
        return

    # Deep link URL'sini belirle
    deep_link = wallet_info.get("ios", wallet_info.get("android", ""))

    if not deep_link:
        await query.answer("❌ Mobil link bulunamadı!", show_alert=True)
        return

    text = f"""
📱 **{wallet_info['name']} Açıldı!**

💰 **Ödeme Yapmaya Hazır**

🔗 Wallet açıldıktan sonra ödeme miktarı seçin:

💎 **Yatırım Seçenekleri:**
• Hızlı oyun başlangıcı için
• Güvenli ve hızlı Solana ağı
    """

    # Miktar seçim keyboard'u
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Wallet'ı Aç", url=deep_link)],
        [InlineKeyboardButton("0.1 SOL Yatır", callback_data="wallet_deposit_0.1"),
         InlineKeyboardButton("0.5 SOL Yatır", callback_data="wallet_deposit_0.5")],
        [InlineKeyboardButton("1.0 SOL Yatır", callback_data="wallet_deposit_1.0"),
         InlineKeyboardButton("2.0 SOL Yatır", callback_data="wallet_deposit_2.0")],
        [InlineKeyboardButton("💎 Özel Miktar", callback_data="wallet_deposit_custom")],
        [InlineKeyboardButton("🔄 Başka Wallet", callback_data="wallet_selection")]
    ])

    await safe_edit_message(
        update=update,
        context=context,
        text=text,
        reply_markup=keyboard
    )

    # Kullanıcıya bildirim
    await query.answer(f"🔗 {wallet_info['name']} açılıyor...", show_alert=False)

async def handle_wallet_deposit_amount(update, context: ContextTypes.DEFAULT_TYPE):
    """Wallet üzerinden ödeme miktarı seçimini işler"""
    query = update.callback_query
    amount_data = query.data.replace("wallet_deposit_", "")

    if amount_data == "custom":
        # Özel miktar için input işlemi
        text = """
💎 **Özel Miktar Girişi**

⌨️ Lütfen yatırmak istediğiniz SOL miktarını yazın:
• Minimum: 0.001 SOL
• Örnek: 0.25

💬 Sadece sayı yazın (örn: 0.1)
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Geri", callback_data="wallet_selection")]
        ])

        await safe_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=keyboard
        )

        # Özel miktar bekleme moduna geç
        context.user_data['waiting_for_amount'] = True
        return

    try:
        sol_amount = float(amount_data)
        await create_wallet_payment_confirmation(update, context, sol_amount)
    except ValueError:
        await query.answer("❌ Geçersiz miktar!", show_alert=True)

async def create_wallet_payment_confirmation(update, context: ContextTypes.DEFAULT_TYPE, sol_amount: float):
    """Wallet seçimi sonrası ödeme onay ekranı oluştur"""
    from solana_payment import get_solana_payment

    try:
        # Kullanıcı bilgisi al
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"

        # Solana ödeme sistemi
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(sol_amount * current_rate)

        # Seçili wallet bilgisi al
        selected_wallet = get_user_selected_wallet(context)
        wallet_name = selected_wallet['info']['name'] if selected_wallet else "Seçilen Wallet"

        text = f"""
✅ **ÖDEME ONAYI** ✅

💰 **Ödeme Detayları:**
• Miktar: {sol_amount} SOL
• Alacağınız: {fc_amount:,} FC
• Kur: 1 SOL = {current_rate:,.0f} FC

🔗 **Seçilen Wallet:** {wallet_name}

⚠️ **ÖNEMLİ:**
• Sadece {sol_amount} SOL gönderin
• Admin onayı sonrası bakiyeniz yüklenecek
• İşlem 5-10 dakika sürebilir

💳 **Admin Wallet Adresi:**
Bu adrese SOL gönderiniz:
`{solana_system.get_deposit_wallet()}`

❓ **Ödemeyi onaylıyor musunuz?**
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Ödemeyi Onayla", callback_data=f"confirm_wallet_payment_{sol_amount}")],
            [InlineKeyboardButton("🔄 Miktar Değiştir", callback_data="wallet_selection")],
            [InlineKeyboardButton("❌ İptal", callback_data="solana_payment_menu")]
        ])

        await safe_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Payment confirmation error: {e}")
        await safe_edit_message(
            update=update,
            context=context,
            text="❌ Ödeme onayı oluşturulamadı. Tekrar deneyin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="wallet_selection")]])
        )

async def handle_wallet_payment_confirmation(update, context: ContextTypes.DEFAULT_TYPE, user, casino_bot):
    """Wallet ödeme onayını işle ve admin bildirimi gönder"""
    query = update.callback_query
    sol_amount_str = query.data.replace("confirm_wallet_payment_", "")

    try:
        sol_amount = float(sol_amount_str)

        # Solana ödeme talebi oluştur
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        result = solana_system.create_deposit_request(user['user_id'], sol_amount)

        if not result['success']:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"❌ {result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="wallet_selection")]])
            )
            return

        # Kullanıcıya onay mesajı
        text = f"""
✅ **ÖDEME TALEBİ OLUŞTURULDU** ✅

📋 **Talep ID:** {result['deposit_id']}
💰 **Miktar:** {result['sol_amount']} SOL
🎯 **Alacağınız:** {result['fc_amount']:,} FC

💳 **ÖDEME ADRESİ:**
`{result['wallet_address']}`

⚡ **İŞLEM ADIMLARI:**
1. Yukarıdaki adrese tam {sol_amount} SOL gönderin
2. Admin tarafından manuel onay beklenir
3. Onay sonrası bakiyeniz otomatik yüklenecek

⏰ **Süre:** 5-15 dakika (işlem yoğunluğuna göre)

📞 **Admin bilgilendirildi!**
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Adresi Kopyala", callback_data=f"copy_wallet_address_{result['wallet_address']}")],
            [InlineKeyboardButton("🔄 Durumu Kontrol Et", callback_data=f"check_deposit_status_{result['deposit_id']}")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        await safe_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=keyboard
        )

        # Admin bildirimi gönder
        await send_admin_payment_notification(context, user, result)

    except ValueError:
        await query.answer("❌ Geçersiz miktar!", show_alert=True)
    except Exception as e:
        logger.error(f"Wallet payment confirmation error: {e}")
        await safe_edit_message(
            update=update,
            context=context,
            text="❌ Ödeme talebi oluşturulamadı. Tekrar deneyin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="wallet_selection")]])
        )

async def send_admin_payment_notification(context: ContextTypes.DEFAULT_TYPE, user, deposit_result):
    """Admin'e ödeme bildirimi gönder"""
    try:
        from config import ADMIN_USER_IDS

        admin_text = f"""
🚨 **YENİ ÖDEME TALEBİ** 🚨

👤 **Kullanıcı:** {user.get('username', 'Anonymous')} (ID: {user['user_id']})
💰 **Miktar:** {deposit_result['sol_amount']} SOL
🎯 **FC Karşılığı:** {deposit_result['fc_amount']:,} FC
📋 **Talep ID:** {deposit_result['deposit_id']}

💳 **Beklenen Adres:** {deposit_result['wallet_address']}
⏰ **Talep Zamanı:** {datetime.now().strftime('%H:%M:%S')}

⚡ **Admin İşlemleri:**
• Solana ağında işlemi kontrol edin
• Onaylamak için admin panelini kullanın
• Kullanıcı bakiyesi otomatik yüklenecek
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Hemen Onayla", callback_data=f"admin_approve_deposit_{deposit_result['deposit_id']}")],
            [InlineKeyboardButton("❌ Reddet", callback_data=f"admin_reject_deposit_{deposit_result['deposit_id']}")],
            [InlineKeyboardButton("🔍 Detay Görüntüle", callback_data=f"admin_deposit_details_{deposit_result['deposit_id']}")]
        ])

        # Tüm adminlere bildirim gönder
        for admin_id in ADMIN_USER_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                logger.info(f"Payment notification sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Admin notification error: {e}")

async def handle_admin_approve_deposit(update, context: ContextTypes.DEFAULT_TYPE, casino_bot):
    """Admin ödeme onayı işlemi"""
    query = update.callback_query
    deposit_id = query.data.replace("admin_approve_deposit_", "")

    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # Depositi onaylama
        result = solana_system.approve_deposit(int(deposit_id))

        if result['success']:
            # Kullanıcı bakiyesini güncelle
            await credit_user_balance(casino_bot, result['user_id'], result['fc_amount'])

            # Admin'e onay mesajı
            await safe_edit_message(
                update=update,
                context=context,
                text=f"""
✅ **ÖDEME ONAYLANDI** ✅

📋 **Talep ID:** {deposit_id}
👤 **Kullanıcı ID:** {result['user_id']}
💰 **Miktar:** {result['sol_amount']} SOL
🎯 **FC Yüklendi:** {result['fc_amount']:,} FC

✅ **Kullanıcı bakiyesi güncellendi!**
📞 **Kullanıcıya bildirim gönderildi.**
                """,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_panel")]])
            )

            # Kullanıcıya bildirim gönder
            await notify_user_deposit_approved(context, result)

        else:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"❌ Onaylama başarısız: {result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])
            )

    except Exception as e:
        logger.error(f"Admin approve deposit error: {e}")
        await query.answer("❌ Onaylama sırasında hata oluştu!", show_alert=True)

async def handle_admin_reject_deposit(update, context: ContextTypes.DEFAULT_TYPE, casino_bot):
    """Admin ödeme reddetme işlemi"""
    query = update.callback_query
    deposit_id = query.data.replace("admin_reject_deposit_", "")

    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # Depositi reddetme
        result = solana_system.reject_deposit(int(deposit_id))

        if result['success']:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"""
❌ **ÖDEME REDDEDİLDİ** ❌

📋 **Talep ID:** {deposit_id}
👤 **Kullanıcı ID:** {result['user_id']}
💰 **Miktar:** {result['sol_amount']} SOL

❌ **İşlem iptal edildi.**
📞 **Kullanıcıya bildirim gönderildi.**
                """,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_panel")]])
            )

            # Kullanıcıya bildirim gönder
            await notify_user_deposit_rejected(context, result)

        else:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"❌ Reddetme başarısız: {result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])
            )

    except Exception as e:
        logger.error(f"Admin reject deposit error: {e}")
        await query.answer("❌ Reddetme sırasında hata oluştu!", show_alert=True)

async def show_admin_deposit_details(update, context: ContextTypes.DEFAULT_TYPE, casino_bot):
    """Admin'e deposit detaylarını göster"""
    query = update.callback_query
    deposit_id = query.data.replace("admin_deposit_details_", "")

    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # Deposit detaylarını al
        deposit = solana_system.get_deposit_details(int(deposit_id))

        if deposit:
            text = f"""
📋 **ÖDEME DETAYLARI** 📋

🆔 **Talep ID:** {deposit['id']}
👤 **Kullanıcı ID:** {deposit['user_id']}
💰 **SOL Miktarı:** {deposit['sol_amount']} SOL
🎯 **FC Miktarı:** {deposit['fc_amount']:,} FC
📊 **Durum:** {deposit['status']}

💳 **Wallet Adresi:**
`{deposit['wallet_address']}`

⏰ **Oluşturma:** {deposit['created_at']}
✅ **Onaylanma:** {deposit['confirmed_at'] or 'Bekliyor'}

🔗 **İşlem Hash:** {deposit['transaction_hash'] or 'Henüz yok'}
            """

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Onayla", callback_data=f"admin_approve_deposit_{deposit_id}")],
                [InlineKeyboardButton("❌ Reddet", callback_data=f"admin_reject_deposit_{deposit_id}")],
                [InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]
            ])

        else:
            text = "❌ Deposit bulunamadı!"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])

        await safe_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Admin deposit details error: {e}")
        await query.answer("❌ Detaylar yüklenemedi!", show_alert=True)

async def credit_user_balance(casino_bot, user_id: int, fc_amount: int):
    """Kullanıcı bakiyesini güncelle"""
    try:
        # Casino bot üzerinden bakiye güncelleme
        casino_bot.update_user_balance(user_id, fc_amount)
        logger.info(f"Successfully credited {fc_amount} FC to user {user_id}")

        # Ek logging ve doğrulama
        updated_user = casino_bot.get_user(user_id)
        if updated_user:
            logger.info(f"User {user_id} new balance: {updated_user.get('fun_coins', 0)} FC")

    except Exception as e:
        logger.error(f"Error crediting user balance: {e}")
        raise e  # Re-raise to handle in calling function

async def notify_user_deposit_approved(context: ContextTypes.DEFAULT_TYPE, deposit_result):
    """Kullanıcıya ödeme onaylandı bildirimi gönder"""
    try:
        text = f"""
✅ **ÖDEMENİZ ONAYLANDI!** ✅

📋 **Talep ID:** {deposit_result['deposit_id']}
💰 **Yatırım:** {deposit_result['sol_amount']} SOL
🎯 **Yüklenen FC:** {deposit_result['fc_amount']:,} FC

🎉 **Bakiyeniz güncellendi!**
🎮 **Artık oyunlara başlayabilirsiniz!**

/start - Ana menüye dön
        """

        await context.bot.send_message(
            chat_id=deposit_result['user_id'],
            text=text,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"User notification error: {e}")

async def notify_user_deposit_rejected(context: ContextTypes.DEFAULT_TYPE, deposit_result):
    """Kullanıcıya ödeme reddedildi bildirimi gönder"""
    try:
        text = f"""
❌ **ÖDEMENİZ REDDEDİLDİ** ❌

📋 **Talep ID:** {deposit_result['deposit_id']}
💰 **Miktar:** {deposit_result['sol_amount']} SOL

🔍 **Olası nedenler:**
• Yanlış miktar gönderilmiş
• İşlem bulunamadı
• Adres hatası

📞 **Destek için admin'e ulaşın.**

/start - Ana menüye dön
        """

        await context.bot.send_message(
            chat_id=deposit_result['user_id'],
            text=text,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"User rejection notification error: {e}")

def get_user_selected_wallet(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Kullanıcının seçtiği wallet bilgisini döndürür"""
    if 'user_data' not in context.user_data:
        return None

    wallet_id = context.user_data.get('user_data', {}).get('selected_wallet')
    if not wallet_id:
        return None

    return {
        'id': wallet_id,
        'info': WALLET_DEEP_LINKS.get(wallet_id)
    }

def create_wallet_status_keyboard(wallet_id: str = None):
    """Wallet durumu için keyboard oluşturur"""
    keyboard = []

    if wallet_id:
        wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
        if wallet_info:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔗 {wallet_info['name']} Aç",
                    callback_data=f"open_wallet_mobile_{wallet_id}"
                )
            ])

    keyboard.extend([
        [InlineKeyboardButton("🔄 Wallet Değiştir", callback_data="wallet_selection")],
        [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
    ])

    return InlineKeyboardMarkup(keyboard)