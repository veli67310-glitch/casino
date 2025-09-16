#!/usr/bin/env python3
"""
Enhanced Withdrawal Handlers
Admin withdrawal management with instant balance deduction and restoration
"""

import logging
from datetime import datetime
from safe_telegram_handler import safe_edit_message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

async def handle_admin_withdrawal_notification(context, user, withdrawal_result):
    """Admin'e çekim talebi bildirimi gönder"""
    try:
        from config import ADMIN_USER_IDS

        admin_text = f"""
🔴 **YENİ ÇEKİM TALEBİ** 🔴

👤 **Kullanıcı:** {user.get('username', 'Anonymous')} (ID: {user['user_id']})
💸 **FC Miktarı:** {withdrawal_result['fc_amount']:,} FC
💰 **SOL Karşılığı:** {withdrawal_result['sol_amount']:.4f} SOL
💳 **Komisyon:** {withdrawal_result['fee']:.4f} SOL

📋 **Talep ID:** {withdrawal_result['withdrawal_id']}
🔗 **Hedef Cüzdan:** `{withdrawal_result['user_wallet']}`
⏰ **Talep Zamanı:** {datetime.now().strftime('%H:%M:%S')}

⚠️ **Kullanıcı bakiyesi çoktan düşürüldü!**
✅ Onaylarsanız SOL transferini yapın
❌ Reddederseniz bakiye otomatik iade edilir
        """

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Onayla & Gönder", callback_data=f"admin_approve_withdrawal_{withdrawal_result['withdrawal_id']}")],
            [InlineKeyboardButton("❌ Reddet & İade", callback_data=f"admin_reject_withdrawal_{withdrawal_result['withdrawal_id']}")],
            [InlineKeyboardButton("🔍 Detay Görüntüle", callback_data=f"admin_withdrawal_details_{withdrawal_result['withdrawal_id']}")]
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
                logger.info(f"Withdrawal notification sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Admin withdrawal notification error: {e}")

async def handle_admin_approve_withdrawal(update, context, casino_bot):
    """Admin çekim onayı - SOL transferini başlat"""
    query = update.callback_query
    withdrawal_id = query.data.replace("admin_approve_withdrawal_", "")

    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # Çekimi onayla
        result = solana_system.approve_withdrawal(int(withdrawal_id))

        if result['success']:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"""
✅ **ÇEKİM ONAYLANDI** ✅

📋 **Talep ID:** {withdrawal_id}
👤 **Kullanıcı ID:** {result['user_id']}
💸 **FC Düşürüldü:** {result['fc_amount']:,} FC
💰 **Gönderilecek:** {result['sol_amount']:.4f} SOL

🔗 **Hedef Cüzdan:** `{result['user_wallet']}`

⚡ **ŞİMDİ YAPIN:**
1. Solana ağında {result['sol_amount']:.4f} SOL gönderin
2. Hedef: {result['user_wallet']}
3. Kullanıcıya otomatik bildirim gönderildi

✅ **Çekim durumu: ONAYLANDI**
                """,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_panel")]])
            )

            # Kullanıcıya bildirim gönder
            await notify_user_withdrawal_approved(context, result)

        else:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"❌ Onaylama başarısız: {result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])
            )

    except Exception as e:
        logger.error(f"Admin approve withdrawal error: {e}")
        await query.answer("❌ Onaylama sırasında hata oluştu!", show_alert=True)

async def handle_admin_reject_withdrawal(update, context, casino_bot):
    """Admin çekim reddetme - Bakiyeyi geri yükle"""
    query = update.callback_query
    withdrawal_id = query.data.replace("admin_reject_withdrawal_", "")

    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # Çekimi reddet ve bakiyeyi iade et
        result = solana_system.reject_withdrawal(int(withdrawal_id), "Admin tarafından reddedildi")

        if result['success']:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"""
❌ **ÇEKİM REDDEDİLDİ** ❌

📋 **Talep ID:** {withdrawal_id}
👤 **Kullanıcı ID:** {result['user_id']}
💰 **İade Edilen:** {result['fc_amount']:,} FC

✅ **Kullanıcı bakiyesi geri yüklendi!**
📞 **Kullanıcıya bildirim gönderildi.**

❌ **Red nedeni:** {result['reason']}
                """,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Admin Panel", callback_data="admin_panel")]])
            )

            # Kullanıcıya bildirim gönder
            await notify_user_withdrawal_rejected(context, result)

        else:
            await safe_edit_message(
                update=update,
                context=context,
                text=f"❌ Reddetme başarısız: {result['error']}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])
            )

    except Exception as e:
        logger.error(f"Admin reject withdrawal error: {e}")
        await query.answer("❌ Reddetme sırasında hata oluştu!", show_alert=True)

async def show_admin_withdrawal_details(update, context, casino_bot):
    """Admin'e withdrawal detaylarını göster"""
    query = update.callback_query
    withdrawal_id = query.data.replace("admin_withdrawal_details_", "")

    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()

        # Withdrawal detaylarını al
        withdrawal = solana_system.get_withdrawal_details(int(withdrawal_id))

        if withdrawal:
            text = f"""
🔴 **ÇEKİM DETAYLARI** 🔴

🆔 **Talep ID:** {withdrawal['id']}
👤 **Kullanıcı:** {withdrawal['username']} (ID: {withdrawal['user_id']})
💸 **FC Miktarı:** {withdrawal['fc_amount']:,} FC
💰 **SOL Miktarı:** {withdrawal['sol_amount']:.4f} SOL
💳 **Komisyon:** {withdrawal['fee_amount']:.4f} SOL
📊 **Durum:** {withdrawal['status']}

🔗 **Hedef Cüzdan:**
`{withdrawal['user_wallet']}`

⏰ **Talep Zamanı:** {withdrawal['created_at']}
✅ **İşlem Zamanı:** {withdrawal['processed_at'] or 'Bekliyor'}

⚠️ **NOT:** Kullanıcı bakiyesi zaten düşürülmüş!
            """

            if withdrawal['status'] == 'pending':
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Onayla", callback_data=f"admin_approve_withdrawal_{withdrawal_id}")],
                    [InlineKeyboardButton("❌ Reddet", callback_data=f"admin_reject_withdrawal_{withdrawal_id}")],
                    [InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]
                ])
            else:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])

        else:
            text = "❌ Çekim talebi bulunamadı!"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data="admin_panel")]])

        await safe_edit_message(
            update=update,
            context=context,
            text=text,
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Admin withdrawal details error: {e}")
        await query.answer("❌ Detaylar yüklenemedi!", show_alert=True)

async def notify_user_withdrawal_approved(context, withdrawal_result):
    """Kullanıcıya çekim onaylandı bildirimi gönder"""
    try:
        text = f"""
✅ **ÇEKİMİNİZ ONAYLANDI!** ✅

📋 **Talep ID:** {withdrawal_result['withdrawal_id']}
💸 **Düşürülen FC:** {withdrawal_result['fc_amount']:,} FC
💰 **Gönderilecek SOL:** {withdrawal_result['sol_amount']:.4f} SOL

🔗 **Hedef Cüzdan:** `{withdrawal_result['user_wallet']}`

⚡ **İşlem durumu:** Onaylandı
🚀 **SOL transferi yakında yapılacak**

⏰ **Tahmini süre:** 5-30 dakika

/start - Ana menüye dön
        """

        await context.bot.send_message(
            chat_id=withdrawal_result['user_id'],
            text=text,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"User withdrawal approval notification error: {e}")

async def notify_user_withdrawal_rejected(context, withdrawal_result):
    """Kullanıcıya çekim reddedildi bildirimi gönder"""
    try:
        text = f"""
❌ **ÇEKİMİNİZ REDDEDİLDİ** ❌

📋 **Talep ID:** {withdrawal_result['withdrawal_id']}
💰 **İade Edilen:** {withdrawal_result['fc_amount']:,} FC

🔄 **Bakiyeniz geri yüklendi!**
🎮 **Oyunlara devam edebilirsiniz!**

🔍 **Red nedeni:** {withdrawal_result['reason']}

📞 **Sorularınız için destek ekibiyle iletişime geçin.**

/start - Ana menüye dön
        """

        await context.bot.send_message(
            chat_id=withdrawal_result['user_id'],
            text=text,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"User withdrawal rejection notification error: {e}")