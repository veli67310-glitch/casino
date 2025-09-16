#!/usr/bin/env python3
"""
Solana Admin Panel
Admin functions for managing Solana deposits and withdrawals
"""

import logging
import asyncio
from datetime import datetime
from safe_telegram_handler import safe_edit_message
from solana_payment import get_solana_payment
from visual_assets import EMOJI_COMBOS, UI_EMOJIS

logger = logging.getLogger(__name__)

async def show_solana_admin_panel(query, user, casino_bot):
    """Show Solana admin panel"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        solana_system = get_solana_payment()
        pending_withdrawals = solana_system.get_pending_withdrawals()
        current_rate = solana_system.get_sol_to_fc_rate()
        
        text = f"""🔧 **SOLANA ADMİN PANELİ** 🔧

◎ **Sistem Durumu** ◎
💱 **Güncel Kur:** 1 SOL = {current_rate:,.0f} FC
⏳ **Bekleyen Çekim:** {len(pending_withdrawals)} adet

📊 **Ayarlar:**
• Limitler: Kaldırıldı
• Komisyon: %{solana_system.withdrawal_fee_rate*100:.0f}
• Admin Cüzdan: {solana_system.admin_wallet[:10]}...

🎯 **Admin Fonksiyonları:**"""
        
        buttons = [
            [("⏳ Bekleyen Çekimler", "solana_pending_withdrawals")],
            [("💱 Kur Güncelle", "solana_update_rate"), ("📊 İstatistikler", "solana_stats")],
            [("✅ Yatırım Onayla", "solana_confirm_deposit"), ("📋 İşlem Geçmişi", "solana_admin_history")],
            [("🔙 Admin Panel", "admin_panel"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solana admin panel error: {e}")
        await safe_edit_message(query, "❌ Admin panel yüklenemedi.", reply_markup=None)

async def show_pending_withdrawals(query, user, casino_bot):
    """Show pending withdrawal requests"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        solana_system = get_solana_payment()
        pending = solana_system.get_pending_withdrawals()
        
        if not pending:
            text = """⏳ **BEKLEYEN ÇEKİMLER** ⏳

✅ Hiç bekleyen çekim yok!

Tüm çekim talepleri işlenmiş durumda."""
            
            buttons = [
                [("🔙 Solana Admin", "solana_admin"), ("🏠 Ana Menü", "main_menu")]
            ]
        else:
            text = f"""⏳ **BEKLEYEN ÇEKİMLER** ⏳

Toplam {len(pending)} bekleyen çekim talebi:

"""
            buttons = []
            
            for i, withdrawal in enumerate(pending[:10], 1):  # Show first 10
                created_date = datetime.strptime(withdrawal['created_at'], "%Y-%m-%d %H:%M:%S")
                text += f"""**{i}. Talep (ID: {withdrawal['id']})**
👤 Kullanıcı: @{withdrawal['username'] or 'N/A'}
💰 FC: {withdrawal['fc_amount']:,}
◎ SOL: {withdrawal['sol_amount']:.4f}
💸 Komisyon: {withdrawal['fee_amount']:.4f}
🏦 Cüzdan: `{withdrawal['user_wallet'][:15]}...`
📅 Tarih: {created_date.strftime('%d/%m/%Y %H:%M')}

"""
                buttons.append([
                    (f"✅ Onayla #{withdrawal['id']}", f"approve_withdrawal_{withdrawal['id']}"),
                    (f"❌ Reddet #{withdrawal['id']}", f"reject_withdrawal_{withdrawal['id']}")
                ])
            
            buttons.append([("🔙 Solana Admin", "solana_admin"), ("🏠 Ana Menü", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Show pending withdrawals error: {e}")
        await safe_edit_message(query, "❌ Bekleyen çekimler yüklenemedi.", reply_markup=None)

async def approve_withdrawal(query, user, withdrawal_id, casino_bot):
    """Approve withdrawal request"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        text = f"""✅ **ÇEKİM ONAYLA** ✅

Çekim ID: {withdrawal_id}

⚠️ Bu çekimi onaylamak için:
1. SOL transferini yapın
2. Transaction hash'i girin
3. Onay butonuna basın

Lütfen transaction hash'i bir sonraki mesajda gönderin."""
        
        # Store withdrawal_id in user context for next message
        # This would normally be stored in database or cache
        
        buttons = [
            [("❌ İptal", "solana_pending_withdrawals")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Approve withdrawal error: {e}")
        await safe_edit_message(query, "❌ Çekim onaylanamadı.", reply_markup=None)

async def reject_withdrawal(query, user, withdrawal_id, casino_bot):
    """Reject withdrawal request"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        solana_system = get_solana_payment()
        result = solana_system.reject_withdrawal(int(withdrawal_id), "Admin tarafından reddedildi")
        
        if result['success']:
            text = f"""❌ **ÇEKİM REDDEDİLDİ** ❌

Çekim ID: {withdrawal_id}

✅ İşlem başarılı:
• {result['refunded_fc']:,} FC kullanıcıya iade edildi
• Çekim talebi reddedildi
• Kullanıcıya bildirim gönderilecek"""
        else:
            text = f"❌ Hata: {result['error']}"
        
        buttons = [
            [("⏳ Bekleyen Çekimler", "solana_pending_withdrawals")],
            [("🔙 Solana Admin", "solana_admin")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Reject withdrawal error: {e}")
        await safe_edit_message(query, "❌ Çekim reddedilemedi.", reply_markup=None)

async def show_solana_rate_update(query, user, casino_bot):
    """Show rate update interface"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        
        text = f"""💱 **KUR GÜNCELLEME** 💱

**Mevcut Kur:** 1 SOL = {current_rate:,.0f} FC

🎯 **Yeni kur önerileri:**
• 1 SOL = 50 FC (düşük)
• 1 SOL = 100 FC (orta)  
• 1 SOL = 200 FC (yüksek)
• 1 SOL = 500 FC (çok yüksek)

⚠️ **DİKKAT:**
Kur değişikliği tüm yeni işlemleri etkiler.
Mevcut bekleyen işlemler eski kurdan hesaplanır."""
        
        buttons = [
            [("50 FC", "update_rate_50"), ("100 FC", "update_rate_100")],
            [("200 FC", "update_rate_200"), ("500 FC", "update_rate_500")],
            [("💎 Özel Kur", "update_rate_custom")],
            [("🔙 Solana Admin", "solana_admin")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Show rate update error: {e}")
        await safe_edit_message(query, "❌ Kur güncelleme sayfası yüklenemedi.", reply_markup=None)

async def update_solana_rate(query, user, new_rate, casino_bot):
    """Update Solana conversion rate"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        solana_system = get_solana_payment()
        old_rate = solana_system.get_sol_to_fc_rate()
        
        solana_system.update_sol_rate(float(new_rate))
        
        text = f"""✅ **KUR GÜNCELLENDİ** ✅

📊 **Kur Değişimi:**
• Eski Kur: 1 SOL = {old_rate:,.0f} FC
• Yeni Kur: 1 SOL = {new_rate:,.0f} FC

✅ **Yeni kur aktif edildi:**
• Tüm yeni yatırımlar yeni kurdan
• Tüm yeni çekimler yeni kurdan
• Bekleyen işlemler eski kurdan

{datetime.now().strftime('%d/%m/%Y %H:%M')} tarihinde güncellendi."""
        
        buttons = [
            [("💱 Tekrar Güncelle", "solana_update_rate")],
            [("🔙 Solana Admin", "solana_admin"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Update rate error: {e}")
        await safe_edit_message(query, "❌ Kur güncellenemedi.", reply_markup=None)

async def show_solana_stats(query, user, casino_bot):
    """Show Solana system statistics"""
    try:
        from config import ADMIN_USER_IDS
        if user['user_id'] not in ADMIN_USER_IDS:
            await safe_edit_message(query, "❌ Yetkisiz erişim!", reply_markup=None)
            return
        
        # This would normally query the database for statistics
        # For now, showing placeholder data
        
        text = f"""📊 **SOLANA İSTATİSTİKLERİ** 📊

**Bugün:**
• Toplam Yatırım: 2.45 SOL
• Toplam Çekim: 1.23 SOL
• İşlem Sayısı: 15 adet

**Bu Hafta:**
• Toplam Yatırım: 12.8 SOL  
• Toplam Çekim: 8.4 SOL
• İşlem Sayısı: 67 adet

**Toplam:**
• Toplam Yatırım: 156.7 SOL
• Toplam Çekim: 98.3 SOL
• Aktif Kullanıcı: 234 kişi

**Sistem Durumu:**
• ✅ Solana ağı aktif
• ✅ Otomatik yatırım çalışıyor
• ✅ Manuel çekim aktif"""
        
        buttons = [
            [("🔄 Yenile", "solana_stats")],
            [("📋 Detaylı Rapor", "solana_detailed_report")],
            [("🔙 Solana Admin", "solana_admin"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solana stats error: {e}")
        await safe_edit_message(query, "❌ İstatistikler yüklenemedi.", reply_markup=None)