#!/usr/bin/env python3
"""
Solana Wallet Flow Handlers
Miktar seçimi sonrası wallet seçim menülerini gösterir
"""

import logging
from safe_telegram_handler import safe_edit_message
from wallet_selector import show_wallet_selection_menu

logger = logging.getLogger(__name__)

async def show_deposit_wallet_selection(query, context, sol_amount):
    """Yatırım miktarı seçildikten sonra wallet seçim menüsü"""
    try:
        # Sol amount'u context'e kaydet
        if 'solana_deposit' not in context.user_data:
            context.user_data['solana_deposit'] = {}
        context.user_data['solana_deposit']['amount'] = sol_amount

        # Solana sistemi
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        # Format SOL amount for display
        sol_display = f"{float(sol_amount):.3f}".rstrip('0').rstrip('.')

        text = f"""
💰 **SOL YATIRMA - WALLET SEÇİMİ** 💰

✅ **Seçilen Miktar:** {sol_display} SOL
🎯 **Alacağınız FC:** {fc_amount:,} FC
💱 **Kur:** 1 SOL = {current_rate:,.0f} FC

🔗 **Wallet'ınızı seçin:**
Solana ağında işlem yapmak için hangi wallet'ı kullanmak istiyorsunuz?

⚡ **Sonraki Adımlar:**
1. Wallet seçin ve açın
2. Admin wallet adresine SOL gönderin
3. 🚀 Otomatik algılama ve FC yükleme
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from wallet_selector import WALLET_DEEP_LINKS

        keyboard = []

        # Wallet seçenekleri
        for wallet_id, wallet_info in WALLET_DEEP_LINKS.items():
            keyboard.append([
                InlineKeyboardButton(
                    wallet_info["name"],
                    callback_data=f"deposit_select_wallet_{wallet_id}_{sol_amount}"
                )
            ])

        # Geri dön butonu
        keyboard.append([
            InlineKeyboardButton("🔙 Geri", callback_data="solana_deposit_menu")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_edit_message(
            query=query,
            text=text,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Deposit wallet selection error: {e}")
        await safe_edit_message(
            query, "❌ Wallet seçim menüsü yüklenemedi.", reply_markup=None
        )

async def show_withdrawal_wallet_selection(query, context, sol_amount):
    """Çekim miktarı seçildikten sonra wallet seçim menüsü"""
    try:
        # Sol amount'u context'e kaydet
        if 'solana_withdrawal' not in context.user_data:
            context.user_data['solana_withdrawal'] = {}
        context.user_data['solana_withdrawal']['amount'] = sol_amount

        # Solana sistemi ve hesaplamalar
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        # Komisyon hesabı
        withdrawal_fee = float(sol_amount) * solana_system.withdrawal_fee_rate
        net_sol = float(sol_amount) - withdrawal_fee

        text = f"""
💸 **SOL ÇEKİM - WALLET SEÇİMİ** 💸

✅ **Çekim Miktarı:** {sol_amount} SOL
💳 **Alacağınız SOL:** {net_sol:.4f} SOL
🏦 **Komisyon:** {withdrawal_fee:.4f} SOL (%{solana_system.withdrawal_fee_rate*100:.0f})

🔗 **Wallet'ınızı seçin:**
Hangi wallet'a SOL çekmek istiyorsunuz?

⚠️ **Önemli:**
• Oyun paranız çekim talebinde düşürülecek
• Admin onayı sonrası SOL wallet'ınıza gelecek
• Admin reddederse oyun paranız iade edilecek
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from wallet_selector import WALLET_DEEP_LINKS

        keyboard = []

        # Wallet seçenekleri
        for wallet_id, wallet_info in WALLET_DEEP_LINKS.items():
            keyboard.append([
                InlineKeyboardButton(
                    wallet_info["name"],
                    callback_data=f"withdrawal_select_wallet_{wallet_id}_{sol_amount}"
                )
            ])

        # Geri dön butonu
        keyboard.append([
            InlineKeyboardButton("🔙 Geri", callback_data="solana_withdraw_menu")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_edit_message(
            query=query,
            text=text,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Withdrawal wallet selection error: {e}")
        await safe_edit_message(
            query, "❌ Wallet seçim menüsü yüklenemedi.", reply_markup=None
        )

async def handle_deposit_wallet_selection(query, context, wallet_id, sol_amount):
    """Yatırım için wallet seçimi işlemi"""
    try:
        from wallet_selector import WALLET_DEEP_LINKS
        wallet_info = WALLET_DEEP_LINKS.get(wallet_id)

        if not wallet_info:
            await query.answer("❌ Geçersiz wallet seçimi!", show_alert=True)
            return

        # Seçimi context'e kaydet
        if 'solana_deposit' not in context.user_data:
            context.user_data['solana_deposit'] = {}
        context.user_data['solana_deposit']['wallet_id'] = wallet_id
        context.user_data['solana_deposit']['wallet_info'] = wallet_info

        # Solana sistemi
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        # Deep link URL'sini belirle
        deep_link = wallet_info.get("ios", wallet_info.get("android", ""))

        # Format SOL amount for display
        sol_display = f"{float(sol_amount):.3f}".rstrip('0').rstrip('.')

        text = f"""
📱 **{wallet_info['name']} - YATIRIM** 📱

✅ **Seçilen Wallet:** {wallet_info['name']}
💰 **Yatırım Miktarı:** {sol_display} SOL

💳 **Admin Wallet Adresi:**
`{solana_system.get_deposit_wallet()}`

📋 **İşlem Adımları:**
1. Wallet'ı açmak için butona tıklayın
2. Yukarıdaki adrese tam {sol_amount} SOL gönderin
3. 🚀 Otomatik blockchain algılama
4. ⚡ Anında FC bakiye güncellemesi

⏰ **İşlem Süresi:** 30-60 saniye (otomatik)
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        # Wallet açma butonu
        if deep_link:
            keyboard.append([
                InlineKeyboardButton("🔗 Wallet'ı Aç", url=deep_link)
            ])

        # Web versiyonu varsa
        if wallet_info.get("web"):
            keyboard.append([
                InlineKeyboardButton("🌐 Web Versiyonu", url=wallet_info["web"])
            ])

        # Ödeme durumu ve seçenekler
        keyboard.extend([
            [InlineKeyboardButton("🚀 SOL Gönderildi - Otomatik Algıla", callback_data=f"start_auto_detection_{sol_amount}")],
            [InlineKeyboardButton("💰 Bakiye Kontrol", callback_data="check_balance")],
            [InlineKeyboardButton("🔄 Başka Wallet", callback_data=f"select_deposit_amount_{sol_amount}")],
            [InlineKeyboardButton("🔙 Geri", callback_data="solana_deposit_menu")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_edit_message(
            query=query,
            text=text,
            reply_markup=reply_markup
        )

        # Otomatik ödeme sistemi için pending transaction ekle
        try:
            from database_manager import DatabaseManager
            from helius_webhook import get_payment_monitor

            db = DatabaseManager()
            user_id = query.from_user.id
            admin_wallet = solana_system.get_deposit_wallet()

            # Pending transaction ekle
            transaction_id = db.add_pending_transaction(
                user_id=user_id,
                expected_amount=float(sol_amount),
                wallet_address=admin_wallet,
                notes=f"Deposit via {wallet_info['name']}"
            )

            if transaction_id:
                logger.info(f"Added pending transaction {transaction_id} for user {user_id}: {sol_amount} SOL")

                # Payment monitor'e ekle
                payment_monitor = await get_payment_monitor()
                await payment_monitor.add_pending_payment(
                    user_id=user_id,
                    expected_amount=float(sol_amount),
                    wallet_address=admin_wallet
                )
            else:
                logger.error(f"Failed to add pending transaction for user {user_id}")

        except Exception as e:
            logger.error(f"Error adding pending transaction: {e}")

        # Kullanıcıya bildirim
        await query.answer(f"🔗 {wallet_info['name']} seçildi! Otomatik algılama aktif.", show_alert=False)

    except Exception as e:
        logger.error(f"Deposit wallet selection handling error: {e}")
        await query.answer("❌ Wallet seçimi başarısız!", show_alert=True)

async def handle_withdrawal_wallet_selection(query, context, wallet_id, sol_amount):
    """Çekim için wallet seçimi işlemi"""
    try:
        from wallet_selector import WALLET_DEEP_LINKS
        wallet_info = WALLET_DEEP_LINKS.get(wallet_id)

        if not wallet_info:
            await query.answer("❌ Geçersiz wallet seçimi!", show_alert=True)
            return

        # Seçimi context'e kaydet
        if 'solana_withdrawal' not in context.user_data:
            context.user_data['solana_withdrawal'] = {}
        context.user_data['solana_withdrawal']['wallet_id'] = wallet_id
        context.user_data['solana_withdrawal']['wallet_info'] = wallet_info

        # Deep link URL'sini belirle
        deep_link = wallet_info.get("ios", wallet_info.get("android", ""))

        text = f"""
📱 **{wallet_info['name']} - ÇEKİM ADRESİ** 📱

✅ **Seçilen Wallet:** {wallet_info['name']}
💸 **Çekim Miktarı:** {sol_amount} SOL

🔗 **Wallet'ınızı açın ve adres alın:**
1. Wallet uygulamanızı açın
2. SOL adresinizi kopyalayın (Receive/Alma)
3. Aşağıdaki butona tıklayın

⚠️ **DİKKAT:**
• Doğru Solana adresini verin
• Yanlış adres = para kaybı
• İşlem geri alınamaz
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        # Wallet açma butonu
        if deep_link:
            keyboard.append([
                InlineKeyboardButton("🔗 Wallet'ı Aç", url=deep_link)
            ])

        # Web versiyonu varsa
        if wallet_info.get("web"):
            keyboard.append([
                InlineKeyboardButton("🌐 Web Versiyonu", url=wallet_info["web"])
            ])

        # Adres girme
        keyboard.extend([
            [InlineKeyboardButton("✅ Wallet Adresi Gir", callback_data=f"input_wallet_address_{sol_amount}")],
            [InlineKeyboardButton("🔄 Başka Wallet", callback_data=f"select_withdrawal_amount_{sol_amount}")],
            [InlineKeyboardButton("🔙 Geri", callback_data="solana_withdraw_menu")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await safe_edit_message(
            query=query,
            text=text,
            reply_markup=reply_markup
        )

        # Kullanıcıya bildirim
        await query.answer(f"🔗 {wallet_info['name']} seçildi!", show_alert=False)

    except Exception as e:
        logger.error(f"Withdrawal wallet selection handling error: {e}")
        await query.answer("❌ Wallet seçimi başarısız!", show_alert=True)