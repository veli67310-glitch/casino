#!/usr/bin/env python3
"""
Enhanced Payment Menu Handlers with CryptoBot Integration
Based on GitHub CasinoBot implementation
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from safe_telegram_handler import safe_edit_message
from config import VIP_LEVELS, PAYMENT_SETTINGS
from visual_assets import (
    CASINO_STICKERS, EMOJI_COMBOS, UI_EMOJIS,
    get_random_celebration, create_animated_message
)
from languages import get_text, DEFAULT_LANGUAGE
from cryptobot_payment import CryptoBotPaymentProcessor, CasinoPaymentManager, create_payment_tables
from enhanced_crypto_pay_api import CryptoPayAPI, EnhancedPaymentManager
from payment_fix_patch import safe_create_deposit_invoice, safe_process_withdrawal

logger = logging.getLogger(__name__)

async def show_balance_info(query, user, casino_bot):
    """Show user's current balance information"""
    try:
        balance = user['fun_coins']

        # Get SOL rate for conversion
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        sol_equivalent = balance / current_rate if current_rate > 0 else 0

        text = f"""💰 **BAKİYE BİLGİSİ** 💰

🐻 **Mevcut Bakiye:** {balance:,} FC
◎ **SOL Karşılığı:** ~{sol_equivalent:.4f} SOL
💵 **USD Karşılığı:** ~${sol_equivalent * solana_system.get_sol_usd_price():.2f}

🔄 **Son Güncelleme:** Az önce
        """

        buttons = [
            [("💰 SOL Yatır", "solana_deposit"), ("💸 SOL Çek", "solana_withdraw")],
            [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Balance info error: {e}")
        await safe_edit_message(query, "❌ Bakiye bilgisi alınamadı.", reply_markup=None)

# Global payment manager instance
payment_manager = None
enhanced_payment_manager = None

def get_payment_manager():
    """Get or create payment manager instance"""
    global payment_manager
    if payment_manager is None:
        try:
            from config import CRYPTO_BOT_TOKEN, CRYPTO_TESTNET
            crypto_processor = CryptoBotPaymentProcessor(CRYPTO_BOT_TOKEN, CRYPTO_TESTNET)
            # Note: db_manager will be passed when initializing
            return None  # Will be initialized in main.py
        except ImportError:
            logger.warning("CryptoBot configuration not found")
            return None
    return payment_manager

def get_enhanced_payment_manager():
    """Get or create enhanced payment manager instance"""
    global enhanced_payment_manager
    return enhanced_payment_manager

def set_enhanced_payment_manager(manager):
    """Set enhanced payment manager instance"""
    global enhanced_payment_manager
    enhanced_payment_manager = manager

async def show_payment_menu(query, user, casino_bot):
    """Show main payment menu"""
    try:
        # Get user's language preference
        user_lang = DEFAULT_LANGUAGE
        if hasattr(casino_bot.db, 'get_user_language'):
            try:
                user_lang = casino_bot.db.get_user_language(user['user_id'])
            except:
                user_lang = DEFAULT_LANGUAGE

        # Dynamic welcome based on user balance
        balance_status = ""
        if user['fun_coins'] >= 100000:
            balance_status = f"{EMOJI_COMBOS['vip_platinum']}\n👑 **VIP WHALE** 👑\n"
        elif user['fun_coins'] >= 50000:
            balance_status = f"{EMOJI_COMBOS['vip_gold']}\n🥇 **HIGH ROLLER** 🥇\n"
        elif user['fun_coins'] >= 10000:
            balance_status = f"{EMOJI_COMBOS['vip_silver']}\n🥈 **BIG PLAYER** 🥈\n"
        else:
            balance_status = f"{EMOJI_COMBOS['daily_bonus']}\n🎯 **PLAYER** 🎯\n"

        title = get_text(user_lang, "payments.title", "💳💎 **PAYMENT SYSTEM** 💎💳")

        text = f"""{title}
{balance_status}
🚀✨ **Solana Network Integration** ✨🚀
{EMOJI_COMBOS['payment_success']} Lightning-fast transactions
🔒💎 Ultra-low fees on Solana
🌍⚡ Decentralized payment system

◎ **Solana Ecosystem** ◎
• ⚡ SOL - Native Solana Token
• 💨 Sub-second confirmations
• 💸 Minimal transaction fees
• 🔗 Direct wallet integration

🎯💫 **Features:** 💫🎯
• ⚡💨 Instant Solana deposits
• 💨🚀 Fast SOL withdrawals
• 🎁🔥 Bonus rewards
• 👑✨ VIP advantages
• 🛡️💎 Secure transactions

{get_random_celebration()} Powered by Solana's speed! {get_random_celebration()}"""

        buttons = [
            [("◎ SOL Yatır", "solana_deposit_menu"),
             ("◎ SOL Çek", "solana_withdraw_menu")],
            [(get_text(user_lang, "payments.history", "📊 Transaction History"), "payment_history"),
             (get_text(user_lang, "payments.vip_info", "👑 VIP Info"), "vip_info")],
            [("📈 SOL Kurları", "solana_rates"),
             (get_text(user_lang, "payments.limits", "ℹ️ Limits"), "limits_info")],
            [(get_text(user_lang, "payments.bonus_info", "🎁 Bonus Info"), "bonus_info"),
             (get_text(user_lang, "payments.main_menu", "🏠 Main Menu"), "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Payment menu error: {e}")
        await safe_edit_message(query, "❌ Error loading menu!")

async def show_deposit_menu(query, user, casino_bot):
    """Show deposit menu with crypto options"""
    try:
        # Calculate suggested amounts based on user level
        level = user['level'] if 'level' in user.keys() else 1
        suggestions = [
            1000 * level,    # Based on level
            5000,            # Standard
            10000,           # Medium
            25000,           # High
            50000,           # Premium
            100000           # VIP
        ]
        
        text = f"""
💵 **YATIRIM YAP** 💵

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC

🎯 **Önerilen Miktarlar:**
"""
        
        for amount in suggestions:
            usdt_amount = amount * 0.001  # 1000 FC = 1 USDT
            text += f"• {amount:,} FC ≈ ${usdt_amount:.2f}\n"
        
        text += """

📱 **Nasıl Çalışır:**
1️⃣ Kripto para seçin
2️⃣ Miktarı belirleyin  
3️⃣ QR kod ile ödeyin
4️⃣ Anında hesabınıza yüklensin!

🎁 **Bonuslar:**
• İlk yatırım: +%20 bonus
• Hafta sonu: +%10 ekstra
• VIP üyeler: Ek avantajlar

💡 Minimum yatırım: 1,000 FC
        """
        
        buttons = [
            [("₮ USDT", "select_deposit_USDT"), ("💎 TON", "select_deposit_TON")],
            [("₿ Bitcoin", "select_deposit_BTC"), ("⟠ Ethereum", "select_deposit_ETH")],
            [("🔸 TRX", "select_deposit_TRX"), ("🟡 BNB", "select_deposit_BNB")],
            [("🔙 Geri", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Deposit menu error: {e}")

async def show_withdraw_menu(query, user, casino_bot):
    """Show withdrawal menu"""
    try:
        # Get user payment stats if payment manager exists
        if hasattr(casino_bot, 'payment_manager') and casino_bot.payment_manager:
            stats = casino_bot.payment_manager.get_user_payment_stats(user['user_id'])
            remaining_withdrawal = stats['remaining_withdrawal'] if 'remaining_withdrawal' in stats else 0
        else:
            remaining_withdrawal = 5000000  # Default daily limit
        
        text = f"""
💸 **PARA ÇEK** 💸

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC
🔄 **Günlük Kalan:** {remaining_withdrawal:,} FC

⚡ **Hızlı Çekim:**
• İşlem süresi: 1-5 dakika
• Minimum çekim: 1,000 FC
• Komisyon: %2 (çok düşük!)
• 7/24 otomatik işlem

🎯 **Çekim Örnekleri:**
• 10,000 FC → $9.80 USDT
• 25,000 FC → $24.50 USDT  
• 50,000 FC → $49.00 USDT
• 100,000 FC → $98.00 USDT

👑 **VIP Avantajları:**
• Düşük komisyon oranları
• Yüksek çekim limitleri
• Öncelikli işlem

⚠️ **Not:** Çekim için CryptoBot hesabınızın olması gerekir.
        """
        
        # Show crypto options only if user has enough balance
        if user['fun_coins'] >= 1000:
            buttons = [
                [("₮ USDT", "select_withdraw_USDT"), ("💎 TON", "select_withdraw_TON")],
                [("₿ Bitcoin", "select_withdraw_BTC"), ("⟠ Ethereum", "select_withdraw_ETH")],
                [("🔸 TRX", "select_withdraw_TRX"), ("🟡 BNB", "select_withdraw_BNB")],
                [("🔙 Geri", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
            ]
        else:
            buttons = [
                [("💵 Yatırım Yap", "deposit_menu"), ("🎁 Günlük Bonus", "daily_bonus")],
                [("🔙 Geri", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Withdraw menu error: {e}")


async def handle_amount_selection(query, user, crypto, amount, casino_bot):
    """Handle amount selection and show wallet selection"""
    try:
        amount = int(amount)
        logger.info(f"Amount selected: User {user['user_id']}, Amount {amount} FC, Crypto {crypto}")

        # Get crypto info for display
        crypto_info = {
            "USDT": {"name": "USDT (TRC20)", "rate": 0.001, "min": 1000},
            "TON": {"name": "TON Coin", "rate": 0.0002, "min": 5000},
            "BTC": {"name": "Bitcoin", "rate": 0.000000015, "min": 66667},
            "ETH": {"name": "Ethereum", "rate": 0.0000003, "min": 3333},
            "TRX": {"name": "Tron", "rate": 0.01, "min": 100},
            "BNB": {"name": "Binance Coin", "rate": 0.0000015, "min": 667}
        }.get(crypto, {"name": crypto, "rate": 0.001, "min": 1000})

        crypto_amount = amount * crypto_info['rate']

        text = f"""
💳 **WALLET SEÇİMİ** 💳

✅ **Seçilen Miktar:** {amount:,} FC
💎 **Ödenecek:** {crypto_amount:.6f} {crypto}
🔗 **Para Birimi:** {crypto_info['name']}

🔗 **Wallet Seçenekleri:**
Ödemenizi yapmak için kullanmak istediğiniz wallet'ı seçin:

💡 **Önerilen Wallet'lar:**
• Güvenli ve kolay kullanım
• Hızlı işlem onayı
• Düşük ağ ücretleri

⚠️ **Önemli:**
• Sadece resmi wallet uygulamalarını kullanın
• İşlem öncesi adresleri kontrol edin
• Tam miktarı gönderin
        """

        buttons = [
            [("👻 Phantom Wallet", f"confirm_deposit_{crypto}_{amount}_phantom")],
            [("☀️ Solflare Wallet", f"confirm_deposit_{crypto}_{amount}_solflare")],
            [("🛡️ Trust Wallet", f"confirm_deposit_{crypto}_{amount}_trust")],
            [("💳 CryptoBot Wallet", f"confirm_deposit_{crypto}_{amount}_cryptobot")],
            [("🔙 Miktar Değiştir", f"select_deposit_{crypto}"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Amount selection error: {e}")
        await safe_edit_message(query,
            "❌ Miktar seçimi sırasında hata oluştu!",
            reply_markup=casino_bot.create_keyboard([
                [("🔄 Tekrar Dene", f"select_deposit_{crypto}"), ("🏠 Ana Menü", "main_menu")]
            ]),
            parse_mode='Markdown'
        )

async def handle_confirm_deposit(query, user, crypto, amount, wallet=None, casino_bot=None):
    """Handle deposit confirmation with enhanced error handling"""
    try:
        amount = int(amount)
        wallet_info = ""

        if wallet:
            wallet_names = {
                "phantom": "👻 Phantom Wallet",
                "solflare": "☀️ Solflare Wallet",
                "trust": "🛡️ Trust Wallet",
                "cryptobot": "💳 CryptoBot Wallet"
            }
            wallet_info = f"\n🔗 **Seçilen Wallet:** {wallet_names.get(wallet, wallet)}"

        logger.info(f"Processing deposit: User {user['user_id']}, Amount {amount} FC, Crypto {crypto}, Wallet {wallet}")

        # Use safe deposit invoice creation with automatic fallbacks
        result = await safe_create_deposit_invoice(casino_bot, user['user_id'], amount, crypto)
        
        if result and result.get("success"):
            crypto_amount = result.get("amount", 0)
            bonus_coins = result.get("bonus_coins", 0)
            total_coins = result.get("total_coins", amount)
            
            # Get the best available invoice URL
            invoice_url = (
                result.get("bot_invoice_url") or 
                result.get("mini_app_invoice_url") or 
                result.get("web_app_invoice_url") or 
                result.get("invoice_url", "")
            )
            
            # Enhanced bonus display
            bonus_text = ""
            if bonus_coins > 0:
                bonus_info = result.get("bonus_info", {})
                bonus_text = "\n🎁 **Aktif Bonuslar:**\n"
                if bonus_info.get('first_deposit_bonus', 0) > 0:
                    bonus_text += f"• İlk yatırım bonusu: +{bonus_info['first_deposit_bonus']:,} FC\n"
                if bonus_info.get('weekend_bonus', 0) > 0:
                    bonus_text += f"• Hafta sonu bonusu: +{bonus_info['weekend_bonus']:,} FC\n"
                if bonus_info.get('vip_bonus', 0) > 0:
                    bonus_text += f"• VIP bonusu: +{bonus_info['vip_bonus']:,} FC\n"
                if not bonus_info:
                    bonus_text += f"• Yatırım bonusu: +{bonus_coins:,} FC\n"
                bonus_text += f"• **Toplam bonus: +{bonus_coins:,} FC**\n"
            
            text = f"""
✅ **YATIRIM FATURASI OLUŞTURULDU** ✅

🐻 **Yatırım:** {amount:,} Fun Coins
💎 **Ödenecek:** {crypto_amount} {crypto}
🎁 **Bonus:** +{bonus_coins:,} FC
💫 **Toplam alacağınız:** {total_coins:,} FC
🌐 **Ağ:** {result.get("network", crypto)}
⏰ **Geçerlilik:** 1 saat{wallet_info}{bonus_text}

📱 **Ödeme Adımları:**
1️⃣ "💳 Ödeme Yap" butonuna tıklayın
2️⃣ CryptoBot uygulamasında ödemeyi tamamlayın
3️⃣ Otomatik olarak hesabınıza yüklenir!

⚡ İşlem genellikle 1-2 dakika sürer.

🔒 **Güvenlik:** Ödeme tamamen şifrelenmiştir.
            """
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            # Create enhanced inline keyboard
            buttons = []
            if invoice_url:
                buttons.append([InlineKeyboardButton("💳 Ödeme Yap", url=invoice_url)])
            
            # Add multiple URL options if available
            url_buttons = []
            if result.get("mini_app_invoice_url") and result.get("mini_app_invoice_url") != invoice_url:
                url_buttons.append(InlineKeyboardButton("📱 Mini App", url=result["mini_app_invoice_url"]))
            if result.get("web_app_invoice_url") and result.get("web_app_invoice_url") != invoice_url:
                url_buttons.append(InlineKeyboardButton("🌐 Web App", url=result["web_app_invoice_url"]))
            if url_buttons:
                buttons.append(url_buttons)
            
            buttons.extend([
                [InlineKeyboardButton("🔄 Yenile", callback_data=f"confirm_deposit_{crypto}_{amount}"), 
                 InlineKeyboardButton("❌ İptal", callback_data="deposit_menu")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
            ])
            
            keyboard = InlineKeyboardMarkup(buttons)
            await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
            
        else:
            error_msg = result.get("error", "Sistem hatası") if result else "Ödeme sistemi kullanılamıyor"
            logger.error(f"Deposit failed: {error_msg}")
            
            await safe_edit_message(query, 
                f"❌ **FATURA OLUŞTURULAMADI**\n\n"
                f"🚫 **Sebep:** {error_msg}\n\n"
                f"💡 **Çözüm Önerileri:**\n"
                f"• Minimum 1,000 FC yatırım yapın\n"
                f"• İnternet bağlantınızı kontrol edin\n"
                f"• Birkaç dakika sonra tekrar deneyin\n"
                f"• Farklı kripto para deneyin\n\n"
                f"🔧 **Teknik Detay:** {error_msg}",
                reply_markup=casino_bot.create_keyboard([
                    [("🔄 Tekrar Dene", f"select_deposit_{crypto}"), ("📊 Limitler", "limits_info")],
                    [("💬 Destek", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
                ]), 
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Deposit confirmation error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        await safe_edit_message(query, 
            f"❌ İşlem sırasında hata oluştu!\n\n"
            f"🔧 **Hata:** {str(e)}\n\n"
            f"💡 **Çözüm:**\n"
            f"• Birkaç dakika bekleyip tekrar deneyin\n"
            f"• Daha düşük miktar deneyin\n"
            f"• Ana menüden tekrar giriş yapın\n\n"
            f"🔄 Lütfen tekrar deneyin.",
            reply_markup=casino_bot.create_keyboard([
                [("🔄 Tekrar Dene", "deposit_menu"), ("📊 Bakiye", "profile")],
                [("🏠 Ana Menü", "main_menu")]
            ]),
            parse_mode='Markdown'
        )

async def handle_withdraw_crypto_selection(query, user, crypto, casino_bot):
    """Handle crypto selection for withdrawal"""
    try:
        # Get crypto info
        crypto_info = {
            "USDT": {"name": "USDT (TRC20)", "rate": 0.001, "min": 1000},
            "TON": {"name": "TON Coin", "rate": 0.0002, "min": 5000},
            "BTC": {"name": "Bitcoin", "rate": 0.000000015, "min": 66667},
            "ETH": {"name": "Ethereum", "rate": 0.0000003, "min": 3333},
            "TRX": {"name": "Tron", "rate": 0.01, "min": 100},
            "BNB": {"name": "Binance Coin", "rate": 0.0000015, "min": 667}
        }.get(crypto, {"name": crypto, "rate": 0.001, "min": 1000})
        
        min_withdrawal = crypto_info['min']
        max_withdrawal = min(user['fun_coins'], 1000000)  # Max 1M FC or user balance
        
        if user['fun_coins'] < min_withdrawal:
            await safe_edit_message(query, 
                f"❌ **YETERSİZ BAKİYE**\n\n"
                f"🐻 Mevcut Bakiye: {user['fun_coins']:,} FC\n"
                f"💎 Minimum Çekim: {min_withdrawal:,} FC\n\n"
                f"💡 Daha fazla Fun Coins kazanmak için oyun oynayın!",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyun Oyna", "solo_games"), ("💵 Yatırım Yap", "deposit_menu")],
                    [("🏠 Ana Menü", "main_menu")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        # Withdrawal suggestions
        suggestions = []
        base_amounts = [10000, 25000, 50000, 100000, 250000, 500000]
        
        for amount in base_amounts:
            if min_withdrawal <= amount <= max_withdrawal:
                suggestions.append(amount)
        
        # Add max withdrawal if not in suggestions
        if max_withdrawal not in suggestions and max_withdrawal >= min_withdrawal:
            suggestions.append(max_withdrawal)
        
        text = f"""
💸 **{crypto_info['name']} ÇEKİMİ** 💸

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC
📊 **Dönüşüm Oranı:** 1 {crypto} = {int(1/crypto_info['rate']):,} FC
💎 **Minimum Çekim:** {min_withdrawal:,} FC
💸 **Komisyon:** %2

🎯 **Çekim Seçenekleri:**
"""
        
        buttons = []
        for amount in suggestions[:6]:  # Max 6 options
            crypto_amount = amount * crypto_info['rate']
            fee = amount * 0.02  # 2% fee
            net_amount = amount - fee
            net_crypto = net_amount * crypto_info['rate']
            
            text += f"• {amount:,} FC → {net_crypto:.6f} {crypto} (net)\n"
            buttons.append([(f"💸 {amount:,} FC", f"confirm_withdraw_{crypto}_{amount}")])
        
        text += f"""

📝 **Çekim Süreci:**
1️⃣ Miktarı seçin
2️⃣ CryptoBot hesabınıza gönderilir
3️⃣ 1-5 dakika içinde alırsınız

⚠️ **Önemli:** CryptoBot hesabınız olmalı!
        """
        
        buttons.append([("🔙 Geri", "withdraw_menu"), ("🏠 Ana Menü", "main_menu")])
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Withdraw crypto selection error: {e}")

async def handle_confirm_withdraw(query, user, crypto, amount, casino_bot):
    """Handle withdrawal confirmation with enhanced error handling"""
    try:
        amount = int(amount)
        logger.info(f"Processing withdrawal: User {user['user_id']}, Amount {amount} FC, Crypto {crypto}")
        
        # Use safe withdrawal processing with automatic fallbacks
        result = await safe_process_withdrawal(casino_bot, user['user_id'], amount, crypto)
        
        if result.get("success"):
            # Get withdrawal details
            crypto_amount = result.get("crypto_amount", 0)
            fee_amount = result.get("fee_amount", 0)
            withdrawal_type = result.get("type", "transfer")
            
            if withdrawal_type == "check":
                text = f"""
✅ **ÇEKİM BAŞARILI - CHECK** ✅

🐻 **Çekilen Tutar:** {amount:,} Fun Coins
💎 **Alacağınız:** {crypto_amount:.6f} {crypto}
💸 **Komisyon:** {fee_amount:.6f} {crypto}
🎫 **Tip:** Check çeki oluşturuldu

📱 **Ne Yapmalısınız:**
• Aşağıdaki check linkine tıklayın
• CryptoBot'ta check'i aktifleştirin
• Paranız hesabınıza yüklenecek

🔗 **Check Linki:** {result.get('check_url', 'Link oluşturuluyor...')}

⚡ Check'ler 24 saat geçerlidir.
                """
            else:
                text = f"""
✅ **ÇEKİM BAŞARILI - TRANSFER** ✅

🐻 **Çekilen Tutar:** {amount:,} Fun Coins
💎 **Alacağınız:** {crypto_amount:.6f} {crypto}
💸 **Komisyon:** {fee_amount:.6f} {crypto}
⚡ **Süre:** 1-5 dakika

📱 **Ne Olacak:**
• CryptoBot hesabınıza gönderildi
• Bildirimi yakında alacaksınız
• İşlem geçmişinizde görünecek

🎉 Çekiminiz başarıyla işleme alındı!
                """
            
            # Update user balance in database
            try:
                with casino_bot.db.get_connection() as conn:
                    conn.execute(
                        'UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?',
                        (amount, user['user_id'])
                    )
                    conn.commit()
                    logger.info(f"User balance updated: -{amount} FC for user {user['user_id']}")
            except Exception as db_error:
                logger.error(f"Database update error: {db_error}")
            
            buttons = [
                [("📊 İşlem Geçmişi", "payment_history"), ("💸 Tekrar Çek", "withdraw_menu")],
                [("🏠 Ana Menü", "main_menu")]
            ]
            
        else:
            error_msg = result.get("error", "Bilinmeyen hata")
            logger.error(f"Withdrawal failed: {error_msg}")
            
            text = f"""
❌ **ÇEKİM BAŞARISIZ** ❌

🚫 **Sebep:** {error_msg}

💡 **Çözüm Önerileri:**
• Daha düşük miktar deneyin ({min(user['fun_coins'], 50000):,} FC veya altı)
• Günlük limitinizi kontrol edin
• CryptoBot hesabınızın aktif olduğundan emin olun
• Minimum çekim miktarını kontrol edin
• Birkaç dakika sonra tekrar deneyin

🐻 Bakiyeniz güvende, tekrar deneyebilirsiniz.

🔧 **Teknik Detay:** {error_msg}
            """
            
            buttons = [
                [("🔄 Tekrar Dene", f"select_withdraw_{crypto}"), ("📊 Limitler", "limits_info")],
                [("💬 Destek", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Withdraw confirmation error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        await safe_edit_message(query, 
            f"❌ İşlem sırasında hata oluştu!\n\n"
            f"🔧 **Hata:** {str(e)}\n\n"
            f"💡 **Çözüm:**\n"
            f"• Birkaç dakika bekleyip tekrar deneyin\n"
            f"• Daha düşük miktar deneyin\n"
            f"• Ana menüden tekrar giriş yapın\n\n"
            f"🔄 Lütfen tekrar deneyin.",
            reply_markup=casino_bot.create_keyboard([
                [("🔄 Tekrar Dene", "withdraw_menu"), ("📊 Bakiye", "profile")],
                [("🏠 Ana Menü", "main_menu")]
            ]),
            parse_mode='Markdown'
        )

async def show_payment_history(query, user, casino_bot):
    """Show payment history"""
    try:
        # Check if payment manager exists
        if not hasattr(casino_bot, 'payment_manager') or not casino_bot.payment_manager:
            await safe_edit_message(query, 
                "❌ İşlem geçmişi şu anda kullanılamıyor.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
            )
            return
        
        stats = casino_bot.payment_manager.get_user_payment_stats(user['user_id'])
        
        # Get payment history manually since the function might not exist
        with casino_bot.db.get_connection() as conn:
            deposits = conn.execute('''
                SELECT * FROM deposits WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 5
            ''', (user['user_id'],)).fetchall()
            
            withdrawals = conn.execute('''
                SELECT * FROM withdrawals WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 5
            ''', (user['user_id'],)).fetchall()
            
            history = {
                'deposits': [dict(d) for d in deposits],
                'withdrawals': [dict(w) for w in withdrawals]
            }
        
        text = f"""
📊 **İŞLEM GEÇMİŞİ** 📊

🐻 **Özet:**
• Toplam Yatırım: {stats['total_deposits']:,} FC
• Toplam Çekim: {stats['total_withdrawals']:,} FC
• Net Kar/Zarar: {stats['net_profit']:,} FC
• Alınan Bonuslar: {stats['total_bonuses']:,} FC

📈 **Son Yatırımlar:**
"""
        
        if history['deposits']:
            for deposit in history['deposits'][:5]:
                status_emoji = {"paid": "✅", "pending": "⏳", "expired": "❌"}.get(deposit['status'], "❓")
                date = datetime.fromisoformat(deposit['created_at']).strftime("%d.%m %H:%M")
                text += f"{status_emoji} {deposit['fun_coins']:,} FC ({deposit['currency']}) - {date}\n"
        else:
            text += "• Henüz yatırım yapılmamış\n"
        
        text += "\n📉 **Son Çekimler:**\n"
        
        if history['withdrawals']:
            for withdrawal in history['withdrawals'][:5]:
                status_emoji = {"completed": "✅", "pending": "⏳", "failed": "❌"}.get(withdrawal['status'], "❓")
                date = datetime.fromisoformat(withdrawal['created_at']).strftime("%d.%m %H:%M")
                text += f"{status_emoji} {withdrawal['fun_coins']:,} FC ({withdrawal['currency']}) - {date}\n"
        else:
            text += "• Henüz çekim yapılmamış\n"
        
        text += f"""

📅 **Bugün:**
• Yatırım: {stats['daily_deposited']:,} FC
• Çekim: {stats['daily_withdrawn']:,} FC
• Bahis: {stats['daily_bets']:,} FC

💡 Detaylar için işlem ID'sini kaydedin!
        """
        
        buttons = [
            [("🔄 Yenile", "payment_history"), ("💳 Yeni İşlem", "payment_menu")],
            [("📈 İstatistikler", "profile"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Payment history error: {e}")

async def show_vip_info(query, user, casino_bot):
    """Show VIP information"""
    try:
        # Get user VIP level
        if hasattr(casino_bot, 'get_user_vip_level'):
            vip_level = casino_bot.get_user_vip_level(user['user_id'])
            max_bet = casino_bot.get_user_max_bet(user['user_id'])
        else:
            vip_level = 0
            max_bet = 100000
        
        if hasattr(casino_bot, 'payment_manager') and casino_bot.payment_manager:
            stats = casino_bot.payment_manager.get_user_payment_stats(user['user_id'])
            total_deposited = stats['total_deposits']
        else:
            total_deposited = 0
        
        current_vip_emoji = "👑" if vip_level > 0 else "🆕"
        
        text = f"""
👑 **VIP DURUM BİLGİSİ** 👑

{current_vip_emoji} **Mevcut Seviye:** VIP {vip_level}
🐻 **Toplam Yatırım:** {total_deposited:,} FC
🚫 **Max Bahis Limitiniz:** {max_bet:,} FC

📈 **VIP SEVİYELERİ:**
"""
        
        for level, requirements in VIP_LEVELS.items():
            status = "✅" if vip_level >= level else "🔒"
            required = requirements['min_deposit']
            bet_bonus = int((requirements.get('bet_bonus', 1) - 1) * 100)
            withdrawal_discount = int(requirements.get('withdrawal_discount', 0) * 100)
            
            # Calculate max bet for this level
            if hasattr(casino_bot, 'get_user_max_bet_by_vip'):
                level_max_bet = casino_bot.get_user_max_bet_by_vip(level)
            else:
                level_max_bet = 100000 * level
            
            text += f"""
{status} **VIP {level}** - {required:,} FC gerekli
   🎲 Bahis bonusu: +%{bet_bonus}
   💸 Çekim indirimi: %{withdrawal_discount}
   🚫 Max bahis: {level_max_bet:,} FC
"""
        
        text += f"""

💎 **VIP AVANTAJLARI:**
• Yüksek bahis limitleri
• Bonus çarpanlar  
• Düşük komisyonlar
• Öncelikli destek
• Özel etkinlikler
• VIP turnuvaları

🚀 **Sonraki Seviye İçin:**
"""
        
        if vip_level < 5:
            next_level = vip_level + 1
            next_requirement = VIP_LEVELS[next_level]['min_deposit']
            remaining = max(0, next_requirement - total_deposited)
            text += f"VIP {next_level} için {remaining:,} FC daha yatırım yapın!"
        else:
            text += "Maksimum VIP seviyesindesiniz! 👑"
        
        buttons = [
            [("💵 Yatırım Yap", "deposit_menu"), ("👑 VIP Avantajları", "bonus_info")],
            [("📊 İstatistikler", "payment_history"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"VIP info error: {e}")

async def show_crypto_rates(query, casino_bot):
    """Show cryptocurrency rates"""
    try:
        text = """
📈 **KRİPTO KURLARI** 📈

💱 **Fun Coins Dönüşüm Oranları:**

₮ **USDT (TRC20)**
• 1,000 FC = 1.00 USDT
• Minimum: 1,000 FC
• Ağ: Tron (TRC20)
• İşlem ücreti: ~1 TRX

💎 **TON Coin**  
• 5,000 FC = 1.00 TON
• Minimum: 5,000 FC
• Ağ: TON Network
• Hızlı ve ucuz

₿ **Bitcoin (BTC)**
• 66,667 FC = 1.00 BTC
• Minimum: 66,667 FC  
• Ağ: Bitcoin Network
• Yüksek değer

⟠ **Ethereum (ETH)**
• 3,333 FC = 1.00 ETH
• Minimum: 3,333 FC
• Ağ: Ethereum (ERC20)
• Popüler seçenek

🔸 **Tron (TRX)**
• 100 FC = 1.00 TRX
• Minimum: 100 FC
• Ağ: Tron Network
• Düşük ücretli

🟡 **Binance Coin (BNB)**
• 667 FC = 1.00 BNB
• Minimum: 667 FC
• Ağ: BSC Network
• Hızlı transferler

🐻 **Özellikler:**
• ⚡ Anında dönüşüm
• 🔒 Güvenli işlemler
• 📱 Otomatik hesaplama
• 🌍 Global geçerlilik

⚠️ **Not:** Kurlar piyasa durumuna göre güncellenebilir.
        """
        
        buttons = [
            [("💵 Yatırım Yap", "deposit_menu"), ("💸 Para Çek", "withdraw_menu")],
            [("🔄 Kurları Yenile", "crypto_rates"), ("📊 Limitler", "limits_info")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Crypto rates error: {e}")

async def show_limits_info(query, user, casino_bot):
    """Show limits information"""
    try:
        # Get user stats
        if hasattr(casino_bot, 'payment_manager') and casino_bot.payment_manager:
            stats = casino_bot.payment_manager.get_user_payment_stats(user['user_id'])
        else:
            stats = {
                'daily_deposited': 0,
                'daily_withdrawn': 0,
                'remaining_deposit': 10000000,
                'remaining_withdrawal': 5000000
            }
        
        if hasattr(casino_bot, 'get_user_vip_level'):
            vip_level = casino_bot.get_user_vip_level(user['user_id'])
            max_bet = casino_bot.get_user_max_bet(user['user_id'])
        else:
            vip_level = 0
            max_bet = 100000
        
        text = f"""
📊 **LİMİT BİLGİLERİ** 📊

👤 **Kişisel Durumunuz:**
• VIP Seviye: {vip_level}
• Maksimum Bahis: {max_bet:,} FC
• Bugün Yatırdığınız: {stats['daily_deposited']:,} FC
• Bugün Çektiğiniz: {stats['daily_withdrawn']:,} FC

🐻 **GÜNLÜK LİMİTLER:**

📥 **Yatırım Limitleri:**
• Günlük maksimum: 10,000,000 FC
• Kalan limitiniz: {stats['remaining_deposit']:,} FC
• İşlem sayısı: Max 20/gün
• Minimum yatırım: 1,000 FC

📤 **Çekim Limitleri:**
• Günlük maksimum: 5,000,000 FC  
• Kalan limitiniz: {stats['remaining_withdrawal']:,} FC
• İşlem sayısı: Max 10/gün
• Minimum çekim: 1,000 FC

🎲 **Bahis Limitleri:**
• Tek bahis maksimum: {max_bet:,} FC
• Bakiye oranı: Max %10
• Saatlik limit: Bakiyenin %50'si
• Günlük toplam: Yatırımın 20 katı

👑 **VIP AVANTAJLARI:**
• VIP 1: 250,000 FC max bahis
• VIP 2: 500,000 FC max bahis
• VIP 3: 1,000,000 FC max bahis
• VIP 4: 2,000,000 FC max bahis
• VIP 5: 5,000,000 FC max bahis

🛡️ **GÜVENLİK ÖNLEMLERİ:**
• Anti-addiction koruması
• Fraud detection sistemi
• Otomatik limit kontrolü
• 24/7 işlem izleme

💡 **İpucu:** VIP seviyenizi yükselterek daha yüksek limitlere erişebilirsiniz!
        """
        
        buttons = [
            [("👑 VIP Ol", "vip_info"), ("💳 İşlem Yap", "payment_menu")],
            [("📊 İstatistikler", "payment_history"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Limits info error: {e}")

async def show_bonus_info(query, user, casino_bot):
    """Show bonus information"""
    try:
        # Check if user has received daily bonus today
        daily_bonus_available = True  # This should be checked from casino_bot
        
        # Get user VIP level
        if hasattr(casino_bot, 'get_user_vip_level'):
            vip_level = casino_bot.get_user_vip_level(user['user_id'])
        else:
            vip_level = 0
        
        # Calculate VIP bonus percentage
        vip_bonus_pct = vip_level * 5  # 5% per VIP level
        
        text = f"""
🎁 **BONUS SİSTEMİ** 🎁

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC
👑 **VIP Seviye:** {vip_level}

🌟 **AKTİF BONUSLAR:**

🎯 **İlk Yatırım Bonusu**
• Oran: +%20 ekstra FC
• Durum: {"✅ Kullanılabilir" if True else "❌ Kullanıldı"}
• Örnek: 10,000 FC yatırım = 12,000 FC alırsınız

📅 **Günlük Bonus**
• Oran: 100-1000 FC arası
• Durum: {"🎁 Alınabilir!" if daily_bonus_available else "⏰ Yarın tekrar"}
• Seri bonusu: Ardışık günlerde artar

🎉 **Hafta Sonu Bonusu**
• Oran: +%10 ekstra
• Geçerli: Cumartesi-Pazar
• Tüm yatırımlara uygulanır

👑 **VIP Bonusu (Seviye {vip_level})**
• Oran: +%{vip_bonus_pct} ekstra  
• Tüm yatırımlara otomatik uygulanır
• Daha yüksek VIP = Daha çok bonus

🏆 **Başarım Bonusları**
• İlk yatırım: +%20
• Büyük yatırımcı (50K+): +%5
• Balina (500K+): +%10
• Sadık oyuncu: +%15

💎 **ÖZEL ETKİNLİKLER:**

🎊 **Doğum Günü Bonusu**
• Özel gününüzde %50 bonus
• Yılda bir kez kullanılabilir

🚀 **Seviye Atlama Bonusu**  
• Her seviye atladığınızda
• Seviye × 1000 FC bonus

🎯 **Geri Dönüş Bonusu**
• 7 gün sonra geri dönerseniz
• %30 yeniden başlama bonusu

💡 **BONUS KURALLARI:**
• Bonuslar otomatik uygulanır
• Minimum yatırım gerekli
• VIP seviyesi bonus oranını etkiler
• Kötüye kullanım yasaktır

🌟 **İPUÇLARI:**
• Hafta sonları yatırım yapın (+%10)
• VIP seviyenizi yükseltin (daha çok bonus)
• Günlük bonusu kaçırmayın
• Başarımları tamamlayın

🐻 **Toplam Bonus Potansiyeli:**
İlk yatırım + VIP + Hafta sonu = %{20 + vip_bonus_pct + 10} bonus!
        """
        
        buttons = [
            [("🎁 Günlük Bonus Al", "daily_bonus"), ("💵 Yatırım Yap", "deposit_menu")],
            [("👑 VIP Avantajları", "vip_info"), ("🏆 Başarımlar", "achievements")],
            [("📊 Bonus Geçmişi", "payment_history"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Bonus info error: {e}")

async def show_deposit_menu(query, user, casino_bot):
    """Show cryptocurrency deposit menu"""
    try:
        pm = get_payment_manager()
        if not pm and not hasattr(casino_bot, 'payment_manager'):
            await safe_edit_message(query, 
                "💳 Ödeme sistemi şu anda mevcut değil.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
            )
            return
            
        # Get user's crypto balances if payment manager exists
        user_balances = {}
        if hasattr(casino_bot, 'payment_manager') and casino_bot.payment_manager:
            for asset in ['USDT', 'TON', 'BTC', 'ETH', 'TRX', 'BNB']:
                try:
                    balance = await casino_bot.payment_manager._get_user_balance(user['user_id'], asset)
                    if balance > 0:
                        user_balances[asset] = balance
                except:
                    pass  # Skip if balance check fails
        
        balance_text = ""
        if user_balances:
            balance_text = "\n🐻 **Mevcut Kripto Bakiyeleriniz:**\n"
            for asset, balance in user_balances.items():
                balance_text += f"• {asset}: {balance:.4f}\n"
        
        deposit_text = f"""
💳💎 **KRIPTO PARA YATIRMA** 💎💳

{get_random_celebration()} Kripto ile hızlı yatırım! {get_random_celebration()}
{balance_text}
🚀 **DESTEKLENaN KRİPTOLAR:**
• {UI_EMOJIS['currency_crypto']} **USDT** - Stablecoin (Önerilen)
• ⚡ **TON** - Telegram Open Network
• ₿ **BTC** - Bitcoin
• ⟠ **ETH** - Ethereum  
• ◉ **TRX** - Tron
• ⬣ **BNB** - Binance Coin

💡 **Yatırım Avantajları:**
✅ Anında işlem (1-5 dakika)
✅ Düşük ağ ücretleri
✅ Güvenli CryptoBot altyapısı
✅ 7/24 otomatik işlem
✅ Minimum: 1 USDT

🎁 **BONUSLAR:**
🎉 İlk yatırım: +%20 bonus
🏆 VIP üyeler: +%15 extra
💫 Hafta sonu: +%10 bonus

⚠️ **Önemli Notlar:**
• Sadece desteklenen ağları kullanın
• İşlem 1 saat içinde tamamlanmazsa iptal olur
• Minimum yatırım: 1 USDT
• Maksimum yatırım: 10,000 USDT

🐻 Hangi kripto ile yatırım yapmak istiyorsunuz?
        """
        
        buttons = [
            [("💎 USDT Yatır", "deposit_usdt"), ("⚡ TON Yatır", "deposit_ton")],
            [("₿ BTC Yatır", "deposit_btc"), ("⟠ ETH Yatır", "deposit_eth")],
            [("◉ TRX Yatır", "deposit_trx"), ("⬣ BNB Yatır", "deposit_bnb")],
            [("📊 İşlem Geçmişi", "payment_history"), ("💳 Ana Menü", "payment_menu")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, deposit_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Deposit menu error: {e}")
        await safe_edit_message(query, 
            "❌ Yatırım menüsü yüklenirken hata oluştu!",
            reply_markup=casino_bot.create_keyboard([[("💳 Ödeme", "payment_menu"), ("🏠 Ana Menü", "main_menu")]])
        )

async def show_withdrawal_menu(query, user, casino_bot):
    """Show cryptocurrency withdrawal menu"""
    try:
        pm = get_payment_manager()
        if not pm and not hasattr(casino_bot, 'payment_manager'):
            await safe_edit_message(query, 
                "💳 Ödeme sistemi şu anda mevcut değil.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
            )
            return
            
        # Get user's crypto balances if payment manager exists
        user_balances = {}
        total_usd_value = 0
        if hasattr(casino_bot, 'payment_manager') and casino_bot.payment_manager:
            for asset in ['USDT', 'TON', 'BTC', 'ETH', 'TRX', 'BNB']:
                try:
                    balance = await casino_bot.payment_manager._get_user_balance(user['user_id'], asset)
                    if balance > 0:
                        user_balances[asset] = balance
                        if asset == 'USDT':
                            total_usd_value += balance
                except:
                    pass  # Skip if balance check fails
                    
        if not user_balances:
            await safe_edit_message(query, 
                f"""
💸 **PARA ÇEKİM İŞLEMİ** 💸

❌ **Çekilebilir bakiyeniz bulunmuyor!**

💡 **Para çekmek için:**
1. Önce kripto para yatırımı yapın
2. Oyunlarda kazanç elde edin
3. Minimum 5 USDT bakiye gerekli

🐻 **Mevcut Oyun Bakiyesi:** {user['fun_coins']:,} FC
                """,
                reply_markup=casino_bot.create_keyboard([
                    [("💳 Para Yatır", "deposit_menu"), ("🎮 Oyun Oyna", "solo_games")],
                    [("🏠 Ana Menü", "main_menu")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        balance_text = "🐻 **Çekilebilir Bakiyeleriniz:**\n"
        for asset, balance in user_balances.items():
            balance_text += f"• {asset}: {balance:.4f}\n"
            
        withdrawal_text = f"""
💸💎 **KRIPTO PARA ÇEKİM** 💎💸

{balance_text}
💵 **Toplam Değer:** ~{total_usd_value:.2f} USD

🚀 **ÇEKİM BİLGİLERİ:**
• Minimum çekim: 5 USDT
• Maksimum çekim: 1,000 USDT  
• İşlem ücreti: %10
• İşlem süresi: 1-5 dakika

💡 **Çekim Türleri:**
🎯 **Direkt Transfer** (5+ USDT)
  → Anında Telegram hesabınıza

🎫 **Check Çeki** (<5 USDT)  
  → Check linki ile çekim

⚠️ **Önemli Notlar:**
• İşlem ücreti net miktardan düşülür
• Günlük çekim limiti: 1,000 USDT
• İşlemler geri alınamaz
• Sadece kendi Telegram hesabınıza

💸 Hangi kripto ile çekim yapmak istiyorsunuz?
        """
        
        buttons = []
        if 'USDT' in user_balances:
            buttons.append([("💎 USDT Çek", "withdraw_usdt")])
        if 'TON' in user_balances:
            buttons.append([("⚡ TON Çek", "withdraw_ton")])
        if 'BTC' in user_balances:
            buttons.append([("₿ BTC Çek", "withdraw_btc")])
        if 'ETH' in user_balances:
            buttons.append([("⟠ ETH Çek", "withdraw_eth")])
        if 'TRX' in user_balances:
            buttons.append([("◉ TRX Çek", "withdraw_trx")])
        if 'BNB' in user_balances:
            buttons.append([("⬣ BNB Çek", "withdraw_bnb")])
            
        buttons.extend([
            [("📊 İşlem Geçmişi", "payment_history"), ("💳 Ana Menü", "payment_menu")],
            [("🏠 Ana Menü", "main_menu")]
        ])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, withdrawal_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Withdrawal menu error: {e}")
        await safe_edit_message(query, 
            "❌ Çekim menüsü yüklenirken hata oluştu!",
            reply_markup=casino_bot.create_keyboard([[("💳 Ödeme", "payment_menu"), ("🏠 Ana Menü", "main_menu")]])
        )

async def process_deposit_request(query, user, asset, casino_bot):
    """Process deposit request for specific asset"""
    try:
        # Show amount selection
        deposit_amounts = {
            'USDT': [1, 5, 10, 25, 50, 100],
            'TON': [2, 10, 20, 50, 100, 200],
            'BTC': [0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01],
            'ETH': [0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
            'TRX': [50, 100, 250, 500, 1000, 2000],
            'BNB': [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
        }
        
        amounts = deposit_amounts.get(asset, [1, 5, 10, 25, 50, 100])
        
        amount_text = f"""
💳 **{asset} YATIRIM MİKTARI SEÇİN** 💳

{EMOJI_COMBOS['payment_pending']}

🐻 **Yatırım seçenekleri:**
Aşağıdaki miktarlardan birini seçin veya özel miktar girin.

🎁 **Bonus Hesaplaması:**
• İlk yatırım: +%20 bonus
• VIP üyeler: +%15 extra  
• Hafta sonu: +%10 bonus

⚡ **Örnek:** 10 {asset} yatırımda ~12-14.5 {asset} alırsınız!

💡 **Min: 1 {asset} | Max: 10,000 {asset}**
        """
        
        buttons = []
        for i in range(0, len(amounts), 2):
            row = []
            for j in range(2):
                if i + j < len(amounts):
                    amount = amounts[i + j]
                    row.append((f"{amount} {asset}", f"deposit_{asset.lower()}_{amount}"))
            if row:
                buttons.append(row)
                
        buttons.extend([
            [("💎 Özel Miktar", f"deposit_{asset.lower()}_custom")],
            [("⬅️ Geri", "deposit_menu"), ("🏠 Ana Menü", "main_menu")]
        ])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, amount_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Deposit request error: {e}")

async def process_withdrawal_request(query, user, asset, casino_bot):
    """Process withdrawal request for specific asset"""
    try:
        pm = get_payment_manager()
        if not pm and not hasattr(casino_bot, 'payment_manager'):
            return
            
        user_balance = 0
        if hasattr(casino_bot, 'payment_manager') and casino_bot.payment_manager:
            try:
                user_balance = await casino_bot.payment_manager._get_user_balance(user['user_id'], asset)
            except:
                user_balance = 0
        
        if user_balance < 5.0:  # Minimum withdrawal
            await safe_edit_message(query, 
                f"""
💸 **{asset} ÇEKİM** 💸

❌ **Yetersiz bakiye!**

🐻 **Mevcut {asset} Bakiyeniz:** {user_balance:.4f}
💡 **Minimum çekim:** 5.0 {asset}

🎯 **Öneriler:**
• Daha fazla oyun oynayın
• Başka kripto bakiyenizi kontrol edin
• Minimum tutara ulaşana kadar bekleyin
                """,
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyun Oyna", "solo_games"), ("💳 Ana Menü", "payment_menu")],
                    [("🏠 Ana Menü", "main_menu")]
                ]),
                parse_mode='Markdown'
            )
            return
            
        # Show withdrawal amounts
        max_withdrawal = min(user_balance, 1000.0)
        withdrawal_amounts = []
        
        if max_withdrawal >= 5:
            withdrawal_amounts.append(5)
        if max_withdrawal >= 10:
            withdrawal_amounts.append(10)
        if max_withdrawal >= 25:
            withdrawal_amounts.append(25)
        if max_withdrawal >= 50:
            withdrawal_amounts.append(50)
        if max_withdrawal >= 100:
            withdrawal_amounts.append(100)
        if max_withdrawal >= 500:
            withdrawal_amounts.append(500)
            
        fee_rate = 0.1  # 10%
        
        withdrawal_text = f"""
💸 **{asset} ÇEKİM MİKTARI SEÇİN** 💸

🐻 **Mevcut Bakiye:** {user_balance:.4f} {asset}
💳 **Max Çekim:** {max_withdrawal:.4f} {asset}

💡 **Ücret Hesabı (%10):**
• 10 {asset} çekim → 9 {asset} alırsınız
• 50 {asset} çekim → 45 {asset} alırsınız
• 100 {asset} çekim → 90 {asset} alırsınız

🎯 **Çekim Türü:**
• 5+ {asset}: Direkt transfer
• <5 {asset}: Check çeki

⚠️ **Dikkat:** İşlem ücreti sonuçtan düşülür!
        """
        
        buttons = []
        for i in range(0, len(withdrawal_amounts), 2):
            row = []
            for j in range(2):
                if i + j < len(withdrawal_amounts):
                    amount = withdrawal_amounts[i + j]
                    net_amount = amount * (1 - fee_rate)
                    row.append((f"{amount} → {net_amount:.1f}", f"withdraw_{asset.lower()}_{amount}"))
            if row:
                buttons.append(row)
                
        buttons.extend([
            [("💎 Tüm Bakiye", f"withdraw_{asset.lower()}_all")],
            [("💎 Özel Miktar", f"withdraw_{asset.lower()}_custom")],
            [("⬅️ Geri", "withdraw_menu"), ("🏠 Ana Menü", "main_menu")]
        ])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, withdrawal_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Withdrawal request error: {e}")

async def animate_payment_process(query, payment_type="deposit"):
    """Animate payment processing with visual feedback"""
    try:
        if payment_type == "deposit":
            animation_sequence = [
                f"💳 {EMOJI_COMBOS['payment_pending']} Ödeme işlemi başlatılıyor...",
                "💳 🔄 Kripto ağı ile bağlantı kuruluyor...",
                "💳 ⏳ İşlem onaylanıyor...",
                "💳 ✅ Blockchain'de doğrulanıyor...",
                f"💳 {EMOJI_COMBOS['payment_success']} İşlem tamamlandı!"
            ]
            sticker = CASINO_STICKERS['money_in']
        else:  # withdraw
            animation_sequence = [
                f"💸 {EMOJI_COMBOS['payment_pending']} Çekim işlemi başlatılıyor...",
                "💸 🔄 Güvenlik kontrolleri yapılıyor...",
                "💸 ⏳ Blockchain'e gönderiliyor...",
                "💸 ✅ İşlem onaylandı...",
                f"💸 {EMOJI_COMBOS['payment_success']} Para gönderildi!"
            ]
            sticker = CASINO_STICKERS['money_out']
        
        # Show animation sequence
        for i, message in enumerate(animation_sequence):
            await asyncio.sleep(0.8)
            await safe_edit_message(query, message, parse_mode='Markdown')
            
        # Show success sticker
        try:
            await query.message.reply_sticker(sticker)
        except:
            pass
            
        return True
        
    except Exception as e:
        logger.error(f"Payment animation error: {e}")
        return False

async def show_payment_success(query, amount, currency, casino_bot):
    """Show animated payment success message"""
    try:
        celebration = get_random_celebration()
        success_text = f"""
{EMOJI_COMBOS['payment_success']}

🎉 **ÖDEME BAŞARILI!** 🎉

🐻 **Miktar:** {amount} {currency}
✅ **Durum:** Tamamlandı
⚡ **Süre:** Anında işlem

{celebration} Hesabınıza başarıyla eklendi! {celebration}

🎮 Artık oyunlara başlayabilirsiniz!
        """
        
        buttons = [
            [("🎰 Oyunlara Başla", "solo_games"), ("📊 Bakiye Görüntüle", "profile")],
            [("💳 Yeni İşlem", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, success_text, reply_markup=keyboard, parse_mode='Markdown')
        
        # Send celebration sticker
        try:
            await query.message.reply_sticker(CASINO_STICKERS['celebration'])
        except:
            pass
            
    except Exception as e:
        logger.error(f"Payment success display error: {e}")

async def show_vip_upgrade_animation(query, new_level, casino_bot):
    """Show VIP level upgrade animation"""
    try:
        # VIP upgrade animation
        upgrade_sequence = [
            "👑 VIP seviyeniz kontrol ediliyor...",
            "👑 ⭐ Yeni avantajlar hesaplanıyor...",
            "👑 ✨ Özel bonuslar aktifleştiriliyor...",
            f"👑 🎉 VIP {new_level} seviyesine yükseltildiniz!"
        ]
        
        for message in upgrade_sequence:
            await asyncio.sleep(0.5)
            await safe_edit_message(query, message, parse_mode='Markdown')
        
        # Show VIP celebration
        vip_text = f"""
{EMOJI_COMBOS['vip_upgrade']}

🎊 **VIP SEVİYE YÜKSELTİLDİ!** 🎊

👑 **Yeni Seviye:** VIP {new_level}
💎 **Özel Avantajlarınız:**
• %{new_level * 5} bonus artışı
• Günlük {new_level * 1000} FC hediye
• Özel turnuvalara erişim
• Öncelikli müşteri desteği

{get_random_celebration()} Tebrikler! {get_random_celebration()}
        """
        
        buttons = [
            [("👑 VIP Avantajları", "vip_info"), ("🎁 Hediye Al", "daily_bonus")],
            [("🎮 Özel Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, vip_text, reply_markup=keyboard, parse_mode='Markdown')
        
        # Send VIP sticker
        try:
            await query.message.reply_sticker(CASINO_STICKERS['vip_upgrade'])
        except:
            pass
            
    except Exception as e:
        logger.error(f"VIP upgrade animation error: {e}")

# Enhanced API webhook handlers
async def handle_crypto_webhook(webhook_data: dict, casino_bot) -> dict:
    """Handle Crypto Pay API webhooks"""
    try:
        enhanced_pm = get_enhanced_payment_manager()
        if not enhanced_pm:
            logger.error("Enhanced payment manager not available for webhook processing")
            return {"success": False, "error": "Payment manager not available"}
            
        result = await enhanced_pm.process_webhook(webhook_data)
        
        if result["success"]:
            # Notify user if needed
            if webhook_data.get("update_type") == "invoice_paid":
                user_id = result.get("user_id")
                fun_coins = result.get("fun_coins")
                asset = result.get("asset")
                
                if user_id and fun_coins:
                    try:
                        # Send success notification to user
                        success_text = f"""
🎉 **YATIRIM BAŞARILI!** 🎉

✅ **Durum:** Ödemeniz alındı ve işlendi
🐻 **Miktar:** {fun_coins:,} Fun Coins
💎 **Para Birimi:** {asset}
⚡ **İşlem Süresi:** Anında

🎮 Artık oyunlara başlayabilirsiniz!
👑 VIP seviyenizi kontrol etmeyi unutmayın!
                        """
                        
                        buttons = [
                            [("🎰 Oyunlara Başla", "solo_games"), ("📊 Bakiye", "profile")],
                            [("👑 VIP Durumu", "vip_info"), ("🏠 Ana Menü", "main_menu")]
                        ]
                        
                        keyboard = casino_bot.create_keyboard(buttons)
                        
                        # Send notification
                        from telegram import Bot
                        bot = Bot(token=casino_bot.token)
                        await bot.send_message(
                            chat_id=user_id,
                            text=success_text,
                            reply_markup=keyboard,
                            parse_mode='Markdown'
                        )
                        
                        # Send celebration sticker
                        try:
                            await bot.send_sticker(
                                chat_id=user_id,
                                sticker=CASINO_STICKERS.get('money_in', 'CAACAgIAAxkBAAIBYWRhG9cAAWoKBgJF5cYAAVm9g4M6CwACTwADr8ZRGnMkAAHCAQAB')
                            )
                        except:
                            pass
                            
                    except Exception as notification_error:
                        logger.error(f"Error sending payment notification: {notification_error}")
                        
        return result
        
    except Exception as e:
        logger.error(f"Error handling crypto webhook: {e}")
        return {"success": False, "error": str(e)}

async def get_enhanced_crypto_rates(casino_bot) -> dict:
    """Get real-time crypto rates from API"""
    try:
        enhanced_pm = get_enhanced_payment_manager()
        if not enhanced_pm:
            return None
            
        # Get exchange rates from API
        rates = await enhanced_pm.crypto_api.get_exchange_rates()
        
        # Get supported currencies
        currencies = await enhanced_pm.crypto_api.get_currencies()
        
        return {
            "rates": rates,
            "currencies": currencies,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced crypto rates: {e}")
        return None

async def show_enhanced_crypto_rates(query, casino_bot):
    """Show enhanced cryptocurrency rates with real-time data"""
    try:
        # Try to get real-time rates
        rate_data = await get_enhanced_crypto_rates(casino_bot)
        
        if rate_data:
            rates = rate_data["rates"]
            currencies = rate_data["currencies"]
            
            text = """
📈 **GÜNCEL KRİPTO KURLARI** 📈

💱 **Anlık Döviz Kurları (API):**

"""
            # Display real-time rates
            for rate in rates[:6]:  # Show first 6 rates
                source = rate.get('source', 'N/A')
                target = rate.get('target', 'N/A')
                rate_value = rate.get('rate', 'N/A')
                text += f"• {source}/{target}: {rate_value}\n"
            
            text += "\n💎 **Desteklenen Kripto Paralar:**\n"
            for currency in currencies[:8]:  # Show first 8 currencies
                code = currency.get('code', 'N/A')
                name = currency.get('name', 'N/A')
                text += f"• {code}: {name}\n"
                
        else:
            # Fallback to static rates
            text = """
📈 **KRİPTO KURLARI** 📈

💱 **Fun Coins Dönüşüm Oranları:**

₮ **USDT (TRC20)**
• 1,000 FC = 1.00 USDT
• Minimum: 1,000 FC
• Ağ: Tron (TRC20)
• İşlem ücreti: ~1 TRX

💎 **TON Coin**  
• 5,000 FC = 1.00 TON
• Minimum: 5,000 FC
• Ağ: TON Network
• Hızlı ve ucuz

₿ **Bitcoin (BTC)**
• 66,667 FC = 1.00 BTC
• Minimum: 66,667 FC  
• Ağ: Bitcoin Network
• Yüksek değer

⟠ **Ethereum (ETH)**
• 3,333 FC = 1.00 ETH
• Minimum: 3,333 FC
• Ağ: Ethereum (ERC20)
• Popüler seçenek

🔸 **Tron (TRX)**
• 100 FC = 1.00 TRX
• Minimum: 100 FC
• Ağ: Tron Network
• Düşük ücretli

🟡 **Binance Coin (BNB)**
• 667 FC = 1.00 BNB
• Minimum: 667 FC
• Ağ: BSC Network
• Hızlı transferler
"""
            
        text += f"""

🐻 **Yeni Özellikler:**
• ⚡ Gerçek zamanlı kurlar
• 🔒 Gelişmiş güvenlik
• 📱 Çoklu ödeme seçenekleri
• 🌍 Fiat para desteği

⚠️ **Not:** Kurlar piyasa durumuna göre anlık güncellenir.

⏰ **Son Güncelleme:** {datetime.now().strftime('%H:%M:%S')}
        """
        
        buttons = [
            [("💵 Yatırım Yap", "deposit_menu"), ("💸 Para Çek", "withdraw_menu")],
            [("🔄 Kurları Yenile", "enhanced_crypto_rates"), ("📊 İstatistikler", "crypto_stats")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Enhanced crypto rates error: {e}")
        # Fallback to original function
        await show_crypto_rates(query, casino_bot)

async def show_enhanced_payment_stats(query, user, casino_bot):
    """Show enhanced payment statistics"""
    try:
        enhanced_pm = get_enhanced_payment_manager()
        
        if enhanced_pm:
            # Get enhanced stats
            stats = await enhanced_pm.get_user_stats(user['user_id'])
            
            text = f"""
📊 **GELİŞMİŞ ÖDEME İSTATİSTİKLERİ** 📊

👤 **Kullanıcı:** {user['first_name'] if 'first_name' in user.keys() else 'Kullanıcı'}
🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC

📈 **Toplam İşlemler:**
• Yatırım sayısı: {stats['deposit_count']}
• Çekim sayısı: {stats['withdrawal_count']}
• Toplam yatırım: {stats['total_deposits']:,} FC
• Toplam çekim: {stats['total_withdrawals']:,} FC
• Net kar/zarar: {stats['net_profit']:,} FC

📅 **Günlük Limitler:**
• Bugün yatırılan: ${stats['daily_deposited_usd']:.2f}
• Bugün çekilen: ${stats['daily_withdrawn_usd']:.2f}
• Kalan yatırım limiti: ${stats['remaining_daily_deposit']:.2f}
• Kalan çekim limiti: ${stats['remaining_daily_withdrawal']:.2f}

💎 **Çoklu Para Birimi Desteği:**
• USDT, TON, BTC, ETH destekleniyor
• Fiat para birimleri (USD, EUR, etc.)
• Gelişmiş dönüşüm oranları
• Düşük işlem ücretleri

🚀 **Yeni Özellikler:**
• Check sistemi (küçük transferler)
• Webhook entegrasyonu
• Gerçek zamanlı bildirimler
• Gelişmiş bonus sistemi

⏰ **Son Güncelleme:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
            """
        else:
            # Fallback to basic stats
            text = f"""
📊 **ÖDEME İSTATİSTİKLERİ** 📊

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC

🔄 **Sistem:** Güncelleniyor...
💡 **Not:** Gelişmiş istatistikler yakında!
            """
            
        buttons = [
            [("📈 Detaylı Rapor", "detailed_payment_report"), ("💳 Yeni İşlem", "payment_menu")],
            [("👑 VIP Durumu", "vip_info"), ("🏆 Başarımlar", "achievements")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Enhanced payment stats error: {e}")
        # Fallback to original function
        await show_payment_history(query, user, casino_bot)

async def show_solana_deposit_direct(query, user, casino_bot):
    """Direct SOL deposit - skip amount selection, go straight to wallet selection"""
    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        text = f"""
💰 **SOL YATIRIM** 💰

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC
💱 **Mevcut Kur:** 1 SOL = {current_rate:,.0f} FC

💳 **Admin Wallet Adresi:**
`{solana_system.get_deposit_wallet()}`

📱 **Wallet Uygulamanızı Seçin:**
Solana işlemi için hangi wallet uygulamasını kullanacaksınız?

⚡ **İşlem Adımları:**
1. Wallet uygulamanızı seçin ve açın
2. Yukarıdaki adrese istediğiniz miktarda SOL gönderin
3. Admin onayı bekleyin
4. FC'niz hesabınıza yüklenir!

🎁 **Bonuslar dahil edilecek!**

💡 **Önerilen miktarlar:** 0.1, 0.25, 0.5, 1.0 SOL
        """

        from wallet_selector import WALLET_DEEP_LINKS
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        # Wallet seçenekleri - direkt custom amount ile
        for wallet_id, wallet_info in WALLET_DEEP_LINKS.items():
            keyboard.append([
                InlineKeyboardButton(
                    wallet_info["name"],
                    callback_data=f"deposit_wallet_direct_{wallet_id}"
                )
            ])

        keyboard.extend([
            [InlineKeyboardButton("🔙 Geri", callback_data="payment_menu")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Solana direct deposit error: {e}")
        await safe_edit_message(query, "❌ Error loading menu!")

async def show_solana_deposit_menu(query, user, casino_bot):
    """Show Solana deposit menu with amount selection"""
    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        # Suggested SOL amounts
        sol_suggestions = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]

        text = f"""
💰 **SOL YATIRIMI** 💰

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC
💱 **Mevcut Kur:** 1 SOL = {current_rate:,.0f} FC

🎯 **Önerilen Miktarlar:**
"""

        for sol_amount in sol_suggestions:
            fc_amount = int(sol_amount * current_rate)
            text += f"• {sol_amount} SOL → {fc_amount:,} FC\n"

        text += f"""

📱 **Sonraki Adım:**
Miktar seçtikten sonra wallet uygulamalarını göstereceğiz!

💎 **Avantajlar:**
• Hızlı Solana ağı (1-2 saniye)
• Düşük işlem ücretleri
• Admin onayı sonrası anında yüklenir
• İlk yatırım bonusu: +%20

💡 Minimum yatırım: 0.01 SOL
        """

        buttons = []
        for i in range(0, len(sol_suggestions), 2):
            row = []
            for j in range(2):
                if i + j < len(sol_suggestions):
                    sol_amount = sol_suggestions[i + j]
                    row.append((f"{sol_amount} SOL", f"select_deposit_amount_{sol_amount}"))
            if row:
                buttons.append(row)

        buttons.extend([
            [("💎 Özel Miktar", "custom_deposit_amount")],
            [("🔙 Geri", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
        ])

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Solana deposit menu error: {e}")
        await safe_edit_message(query, "❌ Error loading menu!")

async def show_solana_withdraw_menu(query, user, casino_bot):
    """Show Solana withdrawal menu with amount selection"""
    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        # Check minimum FC requirement for withdrawal
        min_fc_for_withdrawal = 1000  # Minimum FC required
        if user['fun_coins'] < min_fc_for_withdrawal:
            await safe_edit_message(query,
                f"""
❌ **YETERSİZ BAKİYE** ❌

🐻 **Mevcut Bakiyeniz:** {user['fun_coins']:,} FC
💎 **Minimum Çekim:** {min_fc_for_withdrawal:,} FC

💡 **Daha fazla FC kazanmak için:**
• Oyunlarda kazanç elde edin
• SOL yatırımı yapın
• Günlük bonusunuzu alın
                """,
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyun Oyna", "solo_games"), ("💰 SOL Yatır", "solana_deposit_menu")],
                    [("🏠 Ana Menü", "main_menu")]
                ]),
                parse_mode='Markdown'
            )
            return

        # Calculate suggested withdrawal amounts in SOL
        max_fc = min(user['fun_coins'], 500000)  # Max 500k FC withdrawal
        sol_suggestions = []

        # Convert common FC amounts to SOL
        for fc_amount in [10000, 25000, 50000, 100000, 250000]:
            if fc_amount <= max_fc:
                sol_amount = fc_amount / current_rate
                if sol_amount >= 0.01:  # Minimum 0.01 SOL
                    sol_suggestions.append(sol_amount)

        text = f"""
💸 **SOL ÇEKİMİ** 💸

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} FC
💱 **Mevcut Kur:** 1 SOL = {current_rate:,.0f} FC
💳 **Komisyon Oranı:** %1

🎯 **Çekim Seçenekleri:**
"""

        for sol_amount in sol_suggestions:
            fc_amount = int(sol_amount * current_rate)
            fee_sol = sol_amount * 0.01  # 1% fee
            net_sol = sol_amount - fee_sol
            text += f"• {fc_amount:,} FC → {net_sol:.4f} SOL (net)\n"

        text += f"""

📱 **Sonraki Adım:**
Miktar seçtikten sonra wallet adresinizi gireceksiniz!

⚠️ **Önemli:**
• FC bakiyeniz çekim talebinde düşürülür
• Admin onayı sonrası SOL gönderilir
• Red durumunda FC otomatik iade edilir

⏱️ **İşlem Süresi:** 5-30 dakika
        """

        buttons = []
        for sol_amount in sol_suggestions[:6]:  # Max 6 options
            fc_amount = int(sol_amount * current_rate)
            buttons.append([(f"{fc_amount:,} FC", f"select_withdrawal_amount_{sol_amount}")])

        buttons.extend([
            [("💎 Özel Miktar", "custom_withdrawal_amount")],
            [("🔙 Geri", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
        ])

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Solana withdraw menu error: {e}")
        await safe_edit_message(query, "❌ Error loading menu!")

async def show_solana_rates(query, casino_bot):
    """Show Solana rates information"""
    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        text = f"""
📈 **SOLANA KURLARI** 📈

💱 **Güncel Dönüşüm Oranı:**
• 1 SOL = {current_rate:,.0f} FC
• 1,000 FC = {1000/current_rate:.4f} SOL

💰 **Örnek Dönüşümler:**
• 0.1 SOL = {int(0.1 * current_rate):,} FC
• 0.25 SOL = {int(0.25 * current_rate):,} FC
• 0.5 SOL = {int(0.5 * current_rate):,} FC
• 1.0 SOL = {int(1.0 * current_rate):,} FC
• 2.0 SOL = {int(2.0 * current_rate):,} FC
• 5.0 SOL = {int(5.0 * current_rate):,} FC

⚡ **Solana Network Özellikleri:**
• İşlem süresi: 1-2 saniye
• Ağ ücreti: ~0.00025 SOL
• Onay süresi: Anında
• Güvenlik: Proof of Stake

💎 **Avantajlarımız:**
• Minimum yatırım: 0.01 SOL
• Maksimum yatırım: Limitsiz
• İlk yatırım bonusu: +%20
• VIP bonusları mevcut

⚠️ **Not:** Kurlar piyasa koşullarına göre güncellenebilir.

⏰ **Son Güncelleme:** {datetime.now().strftime('%H:%M:%S')}
        """

        buttons = [
            [("💰 SOL Yatır", "solana_deposit_menu"), ("💸 SOL Çek", "solana_withdraw_menu")],
            [("🔄 Kurları Yenile", "solana_rates"), ("📊 Limitler", "limits_info")],
            [("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Solana rates error: {e}")

async def handle_deposit_amount_selection(query, user, sol_amount, casino_bot):
    """Handle SOL amount selection and show wallet apps"""
    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        text = f"""
💰 **SOL YATIRIM - WALLET SEÇİMİ** 💰

✅ **Seçilen Miktar:** {sol_amount} SOL
🎯 **Alacağınız FC:** {fc_amount:,} FC

📱 **Wallet Uygulamanızı Seçin:**
Solana işlemi için hangi wallet uygulamasını kullanacaksınız?

💳 **Admin Wallet Adresi:**
`{solana_system.get_deposit_wallet()}`

⚡ **İşlem Adımları:**
1. Wallet uygulamanızı seçin
2. Yukarıdaki adrese {sol_amount} SOL gönderin
3. Admin onayı bekleyin
4. FC'niz hesabınıza yüklenir!

🎁 **Bonuslar dahil edilecek!**
        """

        from wallet_selector import WALLET_DEEP_LINKS
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []

        # Wallet seçenekleri
        for wallet_id, wallet_info in WALLET_DEEP_LINKS.items():
            keyboard.append([
                InlineKeyboardButton(
                    wallet_info["name"],
                    callback_data=f"deposit_wallet_{wallet_id}_{sol_amount}"
                )
            ])

        keyboard.extend([
            [InlineKeyboardButton("🔙 Miktar Değiştir", callback_data="solana_deposit_menu")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Deposit amount selection error: {e}")
        await safe_edit_message(query, "❌ Hata oluştu!", reply_markup=None)

async def handle_deposit_wallet_selected(query, user, wallet_id, sol_amount, casino_bot):
    """Handle wallet selection and create deposit request"""
    try:
        from wallet_selector import WALLET_DEEP_LINKS
        from solana_payment import get_solana_payment

        wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
        if not wallet_info:
            await query.answer("❌ Geçersiz wallet seçimi!", show_alert=True)
            return

        solana_system = get_solana_payment()

        # Create deposit request
        result = solana_system.create_deposit_request(user['user_id'], float(sol_amount))

        if not result['success']:
            await safe_edit_message(query,
                f"❌ {result['error']}",
                reply_markup=casino_bot.create_keyboard([[("🔙 Geri", "solana_deposit_menu")]])
            )
            return

        # Deep link URL
        deep_link = wallet_info.get("ios", wallet_info.get("android", ""))

        text = f"""
✅ **ÖDEME TALEBİ OLUŞTURULDU** ✅

📋 **Talep ID:** {result['deposit_id']}
💰 **Miktar:** {result['sol_amount']} SOL
🎯 **Alacağınız:** {result['fc_amount']:,} FC
🔗 **Seçilen Wallet:** {wallet_info['name']}

💳 **ÖDEME ADRESİ:**
`{result['wallet_address']}`

📱 **ŞİMDİ YAPIN:**
1. "{wallet_info['name']}" butonuna tıklayın
2. Wallet uygulamanız açılacak
3. Yukarıdaki adrese tam {sol_amount} SOL gönderin
4. Admin onayı bekleyin

⏰ **Admin bilgilendirildi!**
        """

        keyboard = []

        # Wallet açma butonu
        if deep_link:
            keyboard.append([InlineKeyboardButton(f"🔗 {wallet_info['name']} Aç", url=deep_link)])

        # Web versiyonu varsa
        if wallet_info.get("web"):
            keyboard.append([InlineKeyboardButton("🌐 Web Versiyonu", url=wallet_info["web"])])

        keyboard.extend([
            [InlineKeyboardButton("📋 Adresi Kopyala", callback_data=f"copy_address_{result['wallet_address']}")],
            [InlineKeyboardButton("🔄 Durumu Kontrol Et", callback_data=f"check_deposit_status_{result['deposit_id']}")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, text, reply_markup=reply_markup, parse_mode='Markdown')

        # Send admin notification
        await send_admin_deposit_notification(query, user, result, wallet_info)

    except Exception as e:
        logger.error(f"Deposit wallet selection error: {e}")
        await safe_edit_message(query, "❌ Hata oluştu!")

async def send_admin_deposit_notification(query, user, deposit_result, wallet_info):
    """Send deposit notification to admins"""
    try:
        from config import ADMIN_USER_IDS
        from datetime import datetime

        admin_text = f"""
🚨 **YENİ SOL YATIRIM TALEBİ** 🚨

👤 **Kullanıcı:** {user.get('username', 'Anonymous')} (ID: {user['user_id']})
💰 **Miktar:** {deposit_result['sol_amount']} SOL
🎯 **FC Karşılığı:** {deposit_result['fc_amount']:,} FC
📋 **Talep ID:** {deposit_result['deposit_id']}
🔗 **Kullanıcı Wallet:** {wallet_info['name']}

💳 **Beklenen Adres:**
`{deposit_result['wallet_address']}`

⏰ **Talep Zamanı:** {datetime.now().strftime('%H:%M:%S')}

⚡ **İşlem:**
• Solana ağında {deposit_result['sol_amount']} SOL transfer kontrol edin
• Onayladığınızda kullanıcı bakiyesi otomatik yüklenecek
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Hemen Onayla", callback_data=f"admin_approve_deposit_{deposit_result['deposit_id']}")],
            [InlineKeyboardButton("❌ Reddet", callback_data=f"admin_reject_deposit_{deposit_result['deposit_id']}")],
            [InlineKeyboardButton("🔍 Detay Görüntüle", callback_data=f"admin_deposit_details_{deposit_result['deposit_id']}")]
        ])

        # Send to all admins
        context = query._bot if hasattr(query, '_bot') else None
        if context:
            for admin_id in ADMIN_USER_IDS:
                try:
                    await context.send_message(
                        chat_id=admin_id,
                        text=admin_text,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Deposit notification sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Admin deposit notification error: {e}")

async def handle_withdrawal_amount_selection(query, user, sol_amount, casino_bot):
    """Handle withdrawal amount selection and ask for wallet address"""
    try:
        from solana_payment import get_solana_payment
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(float(sol_amount) * current_rate)

        # Calculate fees
        fee_sol = float(sol_amount) * 0.01  # 1% fee
        net_sol = float(sol_amount) - fee_sol

        text = f"""
💸 **SOL ÇEKİM - WALLET ADRESİ** 💸

✅ **Çekim Miktarı:** {fc_amount:,} FC
💰 **SOL Karşılığı:** {sol_amount} SOL
💳 **Komisyon:** {fee_sol:.4f} SOL
🎯 **Alacağınız:** {net_sol:.4f} SOL

🔗 **Wallet Adresinizi Girin:**
SOL'lerinizi hangi Solana adresine göndermemizi istiyorsunuz?

⚠️ **ÖNEMLİ UYARILAR:**
• Sadece geçerli Solana adresi girin
• Yanlış adres = para kaybı
• İşlem geri alınamaz
• FC bakiyeniz talep anında düşürülecek

📝 **Sonraki mesajınızda wallet adresinizi yazın**
        """

        # Store withdrawal data in user context
        if not hasattr(query, 'message') or not hasattr(query.message, 'chat'):
            return

        # We'll need to handle the next message from user for wallet address
        keyboard = casino_bot.create_keyboard([
            [("❌ İptal", "solana_withdraw_menu")],
            [("🏠 Ana Menü", "main_menu")]
        ])

        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

        # Store withdrawal info for next message handling
        # This would need to be implemented in the main bot handler

    except Exception as e:
        logger.error(f"Withdrawal amount selection error: {e}")
        await safe_edit_message(query, "❌ Hata oluştu!")

async def handle_deposit_wallet_direct(query, user, wallet_id, casino_bot):
    """Handle direct wallet selection without pre-defined amount"""
    try:
        from wallet_selector import WALLET_DEEP_LINKS
        from solana_payment import get_solana_payment

        wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
        if not wallet_info:
            await query.answer("❌ Geçersiz wallet seçimi!", show_alert=True)
            return

        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        # Deep link URL
        deep_link = wallet_info.get("ios", wallet_info.get("android", ""))

        text = f"""
✅ **{wallet_info['name']} SEÇİLDİ** ✅

🔗 **Seçilen Wallet:** {wallet_info['name']}
💱 **Güncel Kur:** 1 SOL = {current_rate:,.0f} FC

💳 **ÖDEME ADRESİ:**
`{solana_system.get_deposit_wallet()}`

📱 **ŞİMDİ YAPIN:**
1. "{wallet_info['name']}" butonuna tıklayın
2. Wallet uygulamanız açılacak
3. Yukarıdaki adrese istediğiniz miktarda SOL gönderin
4. Admin onayı bekleyin

💡 **Önerilen miktarlar:**
• 0.1 SOL → {int(0.1 * current_rate):,} FC
• 0.25 SOL → {int(0.25 * current_rate):,} FC
• 0.5 SOL → {int(0.5 * current_rate):,} FC
• 1.0 SOL → {int(1.0 * current_rate):,} FC

⚡ **Admin otomatik bilgilendirilecek!**
        """

        keyboard = []

        # Wallet açma butonu
        if deep_link:
            keyboard.append([InlineKeyboardButton(f"🔗 {wallet_info['name']} Aç", url=deep_link)])

        # Web versiyonu varsa
        if wallet_info.get("web"):
            keyboard.append([InlineKeyboardButton("🌐 Web Versiyonu", url=wallet_info["web"])])

        keyboard.extend([
            [InlineKeyboardButton("✅ SOL Gönderildi - Bildirim Gönder", callback_data=f"notify_admin_deposit_{wallet_id}")],
            [InlineKeyboardButton("🔙 Başka Wallet", callback_data="solana_deposit_menu")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, text, reply_markup=reply_markup, parse_mode='Markdown')

        # Kullanıcıya bildirim
        await query.answer(f"🔗 {wallet_info['name']} seçildi!", show_alert=False)

    except Exception as e:
        logger.error(f"Direct deposit wallet selection error: {e}")
        await safe_edit_message(query, "❌ Hata oluştu!")

async def handle_notify_admin_deposit(query, user, wallet_id, casino_bot):
    """Handle admin notification for custom amount deposit"""
    try:
        from wallet_selector import WALLET_DEEP_LINKS
        from solana_payment import get_solana_payment

        wallet_info = WALLET_DEEP_LINKS.get(wallet_id)
        if not wallet_info:
            await query.answer("❌ Geçersiz wallet!", show_alert=True)
            return

        solana_system = get_solana_payment()

        # Show confirmation message to user
        text = f"""
✅ **BİLDİRİM GÖNDERİLDİ** ✅

📧 **Admin bilgilendirildi!**
🔗 **Kullandığınız Wallet:** {wallet_info['name']}

💳 **Gönderim Adresi:**
`{solana_system.get_deposit_wallet()}`

⏰ **Sonraki Adımlar:**
1. Admin gönderdiğiniz SOL'i kontrol edecek
2. Onay sonrası FC'niz hesabınıza yüklenecek
3. İşlem genellikle 5-15 dakika sürer

💡 **Unutmayın:** Tam olarak gönderdiğiniz miktarı belirtin
        """

        keyboard = [
            [InlineKeyboardButton("💰 Yeni Yatırım", callback_data="solana_deposit_menu")],
            [InlineKeyboardButton("📊 Bakiye Kontrol", callback_data="profile")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, text, reply_markup=reply_markup, parse_mode='Markdown')

        # Send admin notification
        await send_admin_custom_deposit_notification(query, user, wallet_info, solana_system)

    except Exception as e:
        logger.error(f"Admin notification error: {e}")
        await safe_edit_message(query, "❌ Hata oluştu!")

async def send_admin_custom_deposit_notification(query, user, wallet_info, solana_system):
    """Send custom amount deposit notification to admins"""
    try:
        from config import ADMIN_USER_IDS
        from datetime import datetime

        admin_text = f"""
🚨 **YENİ SOL YATIRIM BİLDİRİMİ** 🚨

👤 **Kullanıcı:** {user.get('username', 'Anonymous')} (ID: {user['user_id']})
🔗 **Kullanılan Wallet:** {wallet_info['name']}

💳 **Beklenen Adres:**
`{solana_system.get_deposit_wallet()}`

⚠️ **ÖZEL MİKTAR** - Kullanıcı özel miktar gönderdi
🔍 **Kontrol Edilmesi Gerekiyor**

⏰ **Bildirim Zamanı:** {datetime.now().strftime('%H:%M:%S')}

⚡ **İşlem:**
• Solana ağında transfer miktarını kontrol edin
• Miktarı belirleyin ve manuel onay yapın
• Onayladığınızda kullanıcı bakiyesi otomatik yüklenecek
        """

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Solana İşlemlerini Kontrol Et", url="https://explorer.solana.com")],
            [InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")],
            [InlineKeyboardButton("📋 Bekleyen Yatırımlar", callback_data="admin_pending_deposits")]
        ])

        # Send to all admins
        context = query._bot if hasattr(query, '_bot') else None
        if context:
            for admin_id in ADMIN_USER_IDS:
                try:
                    await context.send_message(
                        chat_id=admin_id,
                        text=admin_text,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Custom deposit notification sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Admin custom deposit notification error: {e}")