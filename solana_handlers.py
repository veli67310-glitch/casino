#!/usr/bin/env python3
"""
Solana Payment Handlers
Menu handlers for Solana deposit/withdrawal system
"""

import logging
import asyncio
from datetime import datetime
from safe_telegram_handler import safe_edit_message
from solana_payment import get_solana_payment
from solana_qr_payment import get_qr_payment_system, generate_payment_qr_code, start_payment_confirmation
from visual_assets import EMOJI_COMBOS, UI_EMOJIS, get_random_celebration
from languages import get_text, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

async def show_solana_payment_menu(query, user, casino_bot):
    """Show main Solana payment menu"""
    try:
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        
        # Balance status
        balance_status = ""
        if user['fun_coins'] >= 100000:
            balance_status = f"{EMOJI_COMBOS['vip_platinum']}\n👑 **VIP WHALE** 👑\n"
        elif user['fun_coins'] >= 50000:
            balance_status = f"{EMOJI_COMBOS['vip_gold']}\n🥇 **HIGH ROLLER** 🥇\n"
        elif user['fun_coins'] >= 10000:
            balance_status = f"{EMOJI_COMBOS['vip_silver']}\n🥈 **BIG PLAYER** 🥈\n"
        else:
            balance_status = f"{EMOJI_COMBOS['daily_bonus']}\n🎯 **PLAYER** 🎯\n"
        
        text = f"""◎ **SOLANA ÖDEMESİ** ◎
{balance_status}
🌞 **Solana Network** - Hızlı & Güvenli
💰 **Mevcut Bakiye:** {user['fun_coins']:,} FC

💱 **Dönüşüm Oranı:**
• 1 SOL = {current_rate:,.0f} FC
• 1 FC = {1/current_rate:.6f} SOL

📊 **Ayarlar:**
• Limitler: Kaldırıldı (tüm miktarlar)
• Çekim Komisyonu: %{solana_system.withdrawal_fee_rate*100:.0f}

🚀 **Özellikler:**
• ⚡ Hızlı Solana ağı
• 🔄 Manuel yatırım onayı
• 👨‍💼 Manuel çekim (güvenlik)
• 💎 Sadece SOL desteği

{get_random_celebration()} Sadece Solana! {get_random_celebration()}"""
        
        buttons = [
            [("💰 SOL Yatır", "solana_deposit"), ("💸 SOL Çek", "solana_withdraw")],
            [("🔗 Wallet Seç", "wallet_selection"), ("📊 İşlem Geçmişi", "solana_history")],
            [("💱 Kur Bilgisi", "solana_rates"), ("❓ Nasıl Kullanılır", "solana_help")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solana payment menu error: {e}")
        await safe_edit_message(query, "❌ Menü yüklenemedi. Tekrar deneyin.", reply_markup=None)

async def show_solana_deposit_menu(query, user, casino_bot):
    """Show Solana deposit amount selection menu"""
    try:
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        # Predefined SOL amounts for selection
        sol_options = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]

        text = f"""💰 **SOL YATIRIM MİKTARI SEÇİN** 💰

◎ **Solana Network** - Hızlı & Güvenli ◎

💱 **Güncel Dönüşüm Oranı:**
1 SOL = {current_rate:,.0f} 🐻 Fun Coins

🎯 **Yatırım Miktarınızı Seçin:**
Aşağıdaki SOL miktarlarından birini seçin ve ne kadar oyun parası alacağınızı görün!"""

        buttons = []

        # Create buttons in rows of 2
        for i in range(0, len(sol_options), 2):
            row = []
            for j in range(2):
                if i + j < len(sol_options):
                    sol_amount = sol_options[i + j]
                    fc_amount = int(sol_amount * current_rate)
                    row.append((f"{sol_amount} SOL → {fc_amount:,} FC", f"select_sol_amount_{sol_amount}"))
            buttons.append(row)

        # Add custom amount and navigation buttons
        buttons.extend([
            [("💎 Özel Miktar Gir", "deposit_sol_custom")],
            [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
        ])

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Solana deposit menu error: {e}")
        await safe_edit_message(query, "❌ Yatırım menüsü yüklenemedi.", reply_markup=None)

async def show_sol_amount_confirmation(query, user, sol_amount, casino_bot):
    """Show selected SOL amount confirmation and wallet selection"""
    try:
        sol_amount = float(sol_amount)
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(sol_amount * current_rate)

        text = f"""✨ **SEÇTİĞİNİZ MİKTAR** ✨

💰 **Yatırım Miktarı:** {sol_amount} SOL
🎮 **Alacağınız Oyun Parası:** {fc_amount:,} 🐻 Fun Coins

💱 **Dönüşüm Oranı:** 1 SOL = {current_rate:,.0f} FC

🔗 **Wallet Seçenekleri:**
Aşağıdan cüzdan türünüzü seçin ve ödeme talimatlarını alın:"""

        buttons = [
            [("📱 Phantom Wallet", f"wallet_phantom_{sol_amount}"), ("🦊 Solflare", f"wallet_solflare_{sol_amount}")],
            [("💼 Trust Wallet", f"wallet_trust_{sol_amount}"), ("⚡ Backpack", f"wallet_backpack_{sol_amount}")],
            [("🌐 Web3 Wallet", f"wallet_web3_{sol_amount}"), ("💻 Diğer Wallet", f"wallet_other_{sol_amount}")],
            [("🔙 Miktar Değiştir", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"SOL amount confirmation error: {e}")
        await safe_edit_message(query, "❌ Miktar onay sayfası yüklenemedi.", reply_markup=None)

async def handle_wallet_selection(query, user, wallet_type, sol_amount, casino_bot):
    """Handle wallet type selection and show deposit instructions"""
    try:
        sol_amount = float(sol_amount)
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        fc_amount = int(sol_amount * current_rate)

        # Wallet-specific instructions (created after sol_amount is parsed)
        wallet_info = {
            'phantom': {
                'name': '👻 Phantom Wallet',
                'instructions': [
                    '📱 Phantom uygulamasını açın',
                    '💸 "Send" butonuna tıklayın',
                    '📋 Aşağıdaki adresi yapıştırın',
                    f'💰 Miktar: {sol_amount} SOL',
                    '✅ İşlemi onaylayın'
                ]
            },
            'solflare': {
                'name': '🦊 Solflare Wallet',
                'instructions': [
                    '🦊 Solflare uygulamasını açın',
                    '💸 "Send" seçeneğini kullanın',
                    '📋 Wallet adresini kopyalayın',
                    f'💰 Miktar: {sol_amount} SOL',
                    '🚀 Transfer\'i tamamlayın'
                ]
            },
            'trust': {
                'name': '💼 Trust Wallet',
                'instructions': [
                    '💼 Trust Wallet uygulamasını açın',
                    '🔍 Solana (SOL) seçin',
                    '📤 "Send" butonuna tıklayın',
                    '📋 Adresi yapıştırın',
                    f'💰 {sol_amount} SOL gönderin'
                ]
            },
            'backpack': {
                'name': '⚡ Backpack Wallet',
                'instructions': [
                    '⚡ Backpack uygulamasını açın',
                    '💸 Send işlemini başlatın',
                    '📋 Hedef adresi girin',
                    f'💰 Miktar: {sol_amount} SOL',
                    '✅ İşlemi onaylayın'
                ]
            },
            'web3': {
                'name': '🌐 Web3 Wallet',
                'instructions': [
                    '🌐 Web3 wallet arayüzünüze gidin',
                    '💸 Transfer/Send sekmesini açın',
                    '📋 Aşağıdaki adresi kullanın',
                    f'💰 Gönderim miktarı: {sol_amount} SOL',
                    '🔐 İşlemi imzalayın'
                ]
            },
            'other': {
                'name': '💻 Diğer Wallet',
                'instructions': [
                    '💻 Cüzdan uygulamanızı açın',
                    '💸 SOL transfer özelliğini bulun',
                    '📋 Aşağıdaki adresi hedef olarak girin',
                    f'💰 Tam olarak {sol_amount} SOL gönderin',
                    '✅ İşlemi tamamlayın'
                ]
            }
        }

        wallet = wallet_info.get(wallet_type, wallet_info['other'])

        # Create deposit request
        result = solana_system.create_deposit_request(user['user_id'], sol_amount)

        if not result['success']:
            await safe_edit_message(query, f"❌ {result['error']}", reply_markup=None)
            return

        instructions_text = "\n".join([f"{i+1}. {instr}" for i, instr in enumerate(wallet['instructions'])])

        text = f"""🎯 **SEÇTİĞİNİZ MİKTAR VE WALLET** 🎯

💰 **Yatırım:** {sol_amount} SOL → {fc_amount:,} 🐻 Fun Coins
💱 **Kur:** 1 SOL = {current_rate:,.0f} FC

{wallet['name']} **İLE YATIRIM:**

📋 **Adım Adım Talimatlar:**
{instructions_text}

◎ **GÖNDERECEĞİNİZ ADRES:** ◎
`{result['wallet_address']}`

📝 **Yatırım ID:** {result['deposit_id']}
⏰ **Otomatik Takip:** Aktif

⚠️ **ÖNEMLİ:**
• Tam olarak {sol_amount} SOL gönderin
• Farklı miktar gönderirseniz işlem iptal olabilir
• İşlem 5-30 saniye içinde otomatik algılanır

{get_random_celebration()} Yatırımınız için teşekkürler! {get_random_celebration()}"""

        buttons = [
            [("🔳 QR Kodu Göster", f"show_qr_{result['deposit_id']}_{sol_amount}")],
            [("📋 Adresi Kopyala", f"copy_address_{result['wallet_address']}")],
            [("🔄 Durumu Kontrol Et", f"check_deposit_{result['deposit_id']}")],
            [("🔙 Miktar Değiştir", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

        # Start automatic confirmation monitoring
        from solana_qr_payment import start_payment_confirmation
        await start_payment_confirmation(
            user['user_id'],
            sol_amount,
            result['wallet_address'],
            deposit_id=result['deposit_id']
        )

    except Exception as e:
        logger.error(f"Wallet selection error: {e}")
        await safe_edit_message(query, "❌ Wallet seçimi işlenemedi.", reply_markup=None)

async def handle_solana_deposit(query, user, sol_amount, casino_bot):
    """Handle Solana deposit request with centralized wallet"""
    try:
        sol_amount = float(sol_amount)

        # Use centralized deposit system
        solana_system = get_solana_payment()
        result = solana_system.create_deposit_request(user['user_id'], sol_amount)

        if not result['success']:
            await safe_edit_message(query, f"❌ {result['error']}", reply_markup=None)
            return

        # Generate QR code for payment
        memo = f"Deposit ID: {result['deposit_id']}"
        label = f"Casino Deposit - {sol_amount} SOL"

        qr_result = await generate_payment_qr_code(
            result['wallet_address'],
            amount=sol_amount,
            memo=memo,
            label=label
        )

        # Start automatic confirmation monitoring
        confirmation_result = await start_payment_confirmation(
            user['user_id'],
            sol_amount,
            result['wallet_address'],
            deposit_id=result['deposit_id']
        )

        timeout_minutes = confirmation_result.get('timeout_seconds', 600) // 60

        text = f"""✅ **YATIRIM TALEBİNİZ OLUŞTURULDU** ✅

💰 **Yatırım Detayları:**
• Miktar: {result['sol_amount']} SOL
• Alacağınız FC: {result['fc_amount']:,} FC
• Kur: 1 SOL = {result['rate']:,.0f} FC

📝 **Yatırım ID:** {result['deposit_id']}

◎ **MERKEZİ SOL ADRESİ:** ◎
`{result['wallet_address']}`

📱 **3 ÖDEME SEÇENEĞİ:**

🔳 **1. QR CODE İLE:**
• QR Kodu Göster butonuna tıklayın
• Solana cüzdanınızla QR'ı tarayın
• Otomatik miktar ve adres dolacak

📋 **2. MANUEL KOPYALA:**
• Adresi kopyala butonunu kullanın
• {sol_amount} SOL gönderiniz

⚡ **3. OTOMATİK TAKİP:**
• İşlem otomatik algılanır
• Onay geldiğinde bakiyeniz güncellenir
• Timeout: {timeout_minutes} dakika

⚠️ **DİKKAT:**
• Tam miktarı gönderin ({sol_amount} SOL)
• İşlem memo: "Deposit ID: {result['deposit_id']}"

{get_random_celebration()} QR Code + Otomatik onay! {get_random_celebration()}"""

        buttons = [
            [("🔳 QR Kodu Göster", f"show_qr_{result['deposit_id']}_{sol_amount}")],
            [("📋 Adresi Kopyala", f"copy_address_{result['wallet_address']}")],
            [("🔄 Durumu Kontrol Et", f"check_deposit_{result['deposit_id']}")],
            [("📊 Yatırım Geçmişi", f"deposit_history_{user['user_id']}")],
            [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solana deposit error: {e}")
        await safe_edit_message(query, "❌ Yatırım talebi oluşturulamadı.", reply_markup=None)

async def show_deposit_qr_code(query, user, deposit_id, sol_amount, casino_bot):
    """Show QR code for deposit payment"""
    try:
        # Get deposit details
        solana_system = get_solana_payment()

        import sqlite3
        conn = sqlite3.connect(solana_system.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT wallet_address, fc_amount, status
            FROM solana_deposits
            WHERE id = ? AND user_id = ?
        """, (deposit_id, user['user_id']))

        result = cursor.fetchone()
        conn.close()

        if not result:
            await safe_edit_message(query, "❌ Yatırım bulunamadı.", reply_markup=None)
            return

        wallet_address, fc_amount, status = result
        sol_amount = float(sol_amount)

        if status != 'pending':
            await safe_edit_message(query,
                f"ℹ️ Bu yatırım zaten işlenmiş (Durum: {status})",
                reply_markup=None)
            return

        # Generate QR code
        memo = f"Deposit ID: {deposit_id}"
        label = f"Casino Deposit - {sol_amount} SOL"

        qr_result = await generate_payment_qr_code(
            wallet_address,
            amount=sol_amount,
            memo=memo,
            label=label
        )

        if not qr_result.get('success'):
            await safe_edit_message(query, "❌ QR kod oluşturulamadı.", reply_markup=None)
            return

        # Create QR message
        text = f"""🔳 **QR ÖDEME KODU** 🔳

💰 **Yatırım Bilgileri:**
• Miktar: {sol_amount} SOL
• Alacağınız FC: {fc_amount:,} FC
• Yatırım ID: {deposit_id}

📱 **QR Kod Nasıl Kullanılır:**
1. Solana cüzdanınızı açın (Phantom, Solflare vs.)
2. "Send" veya "Gönder" butonuna basın
3. QR kod tarama seçeneğini seçin
4. Aşağıdaki QR kodu tarayın
5. Miktar ve adres otomatik dolacak
6. İşlemi onaylayın

⚡ **Otomatik Algılama:**
• İşlem blockchain'e yazıldığında otomatik algılanır
• 1-2 dakika içinde bakiyeniz güncellenir
• Bildirim gelecektir

🔒 **Güvenlik:**
• QR kod tüm bilgileri içerir
• Manuel yazım hatası riski yok
• Güvenli ve hızlı

{get_random_celebration()} QR ile kolay ödeme! {get_random_celebration()}"""

        # Send QR code as photo
        try:
            import base64
            import io

            # Decode base64 image
            image_data = base64.b64decode(qr_result['image_base64'])

            # Send photo with caption
            await query.message.reply_photo(
                photo=io.BytesIO(image_data),
                caption=text,
                parse_mode='Markdown'
            )

            # Delete the original message
            await query.message.delete()

        except Exception as e:
            logger.error(f"Error sending QR image: {e}")
            # Fallback to text message
            text += f"\n\n📋 **Manuel Adres:**\n`{wallet_address}`"

            buttons = [
                [("📋 Adresi Kopyala", f"copy_address_{wallet_address}")],
                [("🔄 Durumu Kontrol Et", f"check_deposit_{deposit_id}")],
                [("🔙 Geri", "solana_deposit")]
            ]

            keyboard = casino_bot.create_keyboard(buttons)
            await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error showing QR code: {e}")
        await safe_edit_message(query, "❌ QR kod gösterilemedi.", reply_markup=None)

async def show_solana_withdraw_menu(query, user, casino_bot):
    """Show Solana withdrawal menu"""
    try:
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()
        
        user_balance = user['fun_coins']
        max_sol = user_balance / current_rate
        
        text = f"""💸 **SOL ÇEKİM** 💸

◎ **Solana Network Çekim** ◎

💰 **Mevcut Bakiye:** {user_balance:,} FC
💱 **Max Çekim:** {max_sol:.4f} SOL
📊 **Limitler:** Kaldırıldı
💸 **Komisyon:** %{solana_system.withdrawal_fee_rate*100:.0f}

🎯 **Çekilebilir Miktarlar:**
• {int(current_rate * 0.1):,} FC = 0.1 SOL
• {int(current_rate * 0.5):,} FC = 0.5 SOL
• {int(current_rate * 1.0):,} FC = 1.0 SOL
• {int(current_rate * 2.0):,} FC = 2.0 SOL

📝 **Manuel İşlem:**
1. Miktar ve cüzdan adresinizi girin
2. Talebiniz incelemeye alınır
3. Admin onayından sonra gönderilir
4. 24 saat içinde işlem yapılır

⚠️ Çekimler manuel olarak kontrol edilir."""
        
        # Limitler kaldırıldı - her miktar çekilebilir
        if user_balance <= 0:
            text += f"\n\n❌ Çekim yapabilmek için bakiye gerekli."
            buttons = [
                [("💰 SOL Yatır", "solana_deposit")],
                [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
            ]
        else:
            buttons = [
                [("0.1 SOL", "select_withdrawal_amount_0.1"), ("0.5 SOL", "select_withdrawal_amount_0.5")],
                [("1.0 SOL", "select_withdrawal_amount_1.0"), ("2.0 SOL", "select_withdrawal_amount_2.0")],
                [("💎 Özel Miktar", "withdraw_sol_custom")],
                [("📊 Çekim Durumu", "withdrawal_status")],
                [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solana withdraw menu error: {e}")
        await safe_edit_message(query, "❌ Çekim menüsü yüklenemedi.", reply_markup=None)

async def show_withdrawal_wallet_input(query, user, sol_amount, casino_bot):
    """Show wallet input for withdrawal"""
    try:
        sol_amount = float(sol_amount)
        solana_system = get_solana_payment()
        fc_amount = int(sol_amount * solana_system.get_sol_to_fc_rate())
        
        if user['fun_coins'] < fc_amount:
            await safe_edit_message(query, "❌ Yetersiz bakiye!", reply_markup=None)
            return
        
        text = f"""💸 **CÜZDAN ADRESİ GİRİN** 💸

🎯 **Çekim Detayları:**
• Çekilecek FC: {fc_amount:,} FC
• Alacağınız SOL: {sol_amount * (1 - solana_system.withdrawal_fee_rate):.4f} SOL
• Komisyon: {sol_amount * solana_system.withdrawal_fee_rate:.4f} SOL (%{solana_system.withdrawal_fee_rate*100:.0f})

📝 **SOL Cüzdan Adresinizi Girin:**
Mesaj olarak Solana cüzdan adresinizi gönderin.

⚠️ **DİKKAT:**
• Doğru Solana adresi girin
• Yanlış adres = para kaybı
• İşlem geri alınamaz

Cüzdan adresinizi bir sonraki mesajda gönderin."""
        
        # Store the withdrawal amount in user context
        # This would normally be stored in a temporary database or cache
        
        buttons = [
            [("❌ İptal Et", "solana_withdraw")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Withdrawal wallet input error: {e}")
        await safe_edit_message(query, "❌ Hata oluştu.", reply_markup=None)

async def process_solana_withdrawal(query, user, fc_amount, user_wallet, casino_bot, context=None):
    """Process Solana withdrawal request"""
    try:
        solana_system = get_solana_payment()
        
        # Create withdrawal request
        result = solana_system.create_withdrawal_request(
            user['user_id'], 
            int(fc_amount), 
            user_wallet
        )
        
        if not result['success']:
            await safe_edit_message(query, f"❌ {result['error']}", reply_markup=None)
            return
        
        text = f"""✅ **ÇEKİM TALEBİNİZ ALINDI** ✅

💸 **Çekim Detayları:**
• Çekilen FC: {result['fc_amount']:,} FC ⚠️ **BAKİYENİZDEN DÜŞTÜ**
• Alacağınız SOL: {result['sol_amount']:.4f} SOL
• Komisyon: {result['fee']:.4f} SOL
• Cüzdan: `{user_wallet[:10]}...{user_wallet[-6:]}`

📝 **Talep ID:** {result['withdrawal_id']}
⏳ **Durum:** Admin İncelemesinde

⚠️ **ÖNEMLİ:**
• Oyun paranız çoktan bakiyenizden düştü
• Admin onaylarsa SOL cüzdanınıza gelecek
• Admin reddederse paranız iade edilecek

📋 **Süreç:**
1. ✅ Talep oluşturuldu & Bakiye düştü
2. ⏳ Admin incelemesi (0-24 saat)
3. ⏳ SOL transferi veya para iadesi
4. ✅ İşlem tamamlandı

💌 **Bildirim:** İşlem sonucu size mesaj gelecektir.

{get_random_celebration()} Admin bilgilendirildi! {get_random_celebration()}"""

        # Admin'e çekim bildirimi gönder (eğer context varsa)
        if context:
            from withdrawal_handlers import handle_admin_withdrawal_notification
            await handle_admin_withdrawal_notification(context, user, result)
        
        buttons = [
            [("📊 Durumu Kontrol Et", f"check_withdrawal_{result['withdrawal_id']}")],
            [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Process withdrawal error: {e}")
        await safe_edit_message(query, "❌ Çekim talebi oluşturulamadı.", reply_markup=None)

async def show_solana_help(query, user, casino_bot):
    """Show Solana payment help"""
    try:
        text = f"""❓ **SOLANA KULLANIM REHBERİ** ❓

◎ **SOL YATIRMA:** ◎
1. 'SOL Yatır' menüsüne gidin
2. Yatırım miktarını seçin
3. Size verilen SOL adresine gönderin
4. 1-2 dakikada otomatik yüklenir

◎ **SOL ÇEKİM:** ◎  
1. 'SOL Çek' menüsüne gidin
2. Çekim miktarını seçin
3. SOL cüzdan adresinizi girin
4. 24 saat içinde manuel transfer

💰 **KURLAR:**
• Kurlar dinamik olarak güncellenir
• Min/max limitler vardır
• Çekim komisyonu alınır

🔒 **GÜVENLİK:**
• Sadece Solana ağı kullanın
• Cüzdan adresini dikkatli girin
• İşlemler geri alınamaz

🚨 **DİKKAT:**
• Yanlış ağ = para kaybı
• Yanlış adres = para kaybı
• Minimum miktarların altında göndermeyin

{get_random_celebration()} Güvenli oyunlar! {get_random_celebration()}"""
        
        buttons = [
            [("💰 SOL Yatır", "solana_deposit"), ("💸 SOL Çek", "solana_withdraw")],
            [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solana help error: {e}")
        await safe_edit_message(query, "❌ Yardım sayfası yüklenemedi.", reply_markup=None)

async def check_solana_deposit_status(query, user, deposit_id, casino_bot):
    """Check Solana deposit status with confirmation monitoring"""
    try:
        import sqlite3
        from solana_qr_payment import check_payment_status

        solana_system = get_solana_payment()

        conn = sqlite3.connect(solana_system.db_path)
        cursor = conn.cursor()

        # Check deposit details
        cursor.execute("""
            SELECT sol_amount, fc_amount, status, created_at, confirmed_at, wallet_address, transaction_hash
            FROM solana_deposits WHERE id = ? AND user_id = ?
        """, (deposit_id, user['user_id']))

        result = cursor.fetchone()
        if not result:
            await safe_edit_message(query, "❌ Yatırım bulunamadı.", reply_markup=None)
            return

        sol_amount, fc_amount, status, created_at, confirmed_at, wallet_address, tx_hash = result

        # Check if there's an active confirmation monitoring
        cursor.execute("""
            SELECT id, status, transaction_hash, confirmations, created_at, confirmed_at, error_message
            FROM transaction_confirmations
            WHERE deposit_id = ? AND user_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (deposit_id, user['user_id']))

        confirmation_result = cursor.fetchone()
        conn.close()

        # Build status message
        if status == 'confirmed':
            status_emoji = "✅"
            status_text = "ONAYLANDI"
            status_color = "Yeşil"
        elif status == 'pending':
            status_emoji = "⏳"
            status_text = "BEKLİYOR"
            status_color = "Sarı"
        else:
            status_emoji = "❌"
            status_text = status.upper()
            status_color = "Kırmızı"

        text = f"""📊 **YATIRIM DURUMU** 📊

{status_emoji} **Durum:** {status_text}

💰 **Yatırım Bilgileri:**
• ID: {deposit_id}
• Miktar: {sol_amount} SOL
• Alacağınız FC: {fc_amount:,} FC
• Oluşturma: {created_at[:16]}
• Onay Tarihi: {confirmed_at[:16] if confirmed_at else 'Henüz onaylanmadı'}

📍 **Blockchain Bilgileri:**
• Cüzdan: `{wallet_address}`
• TX Hash: {f'`{tx_hash}`' if tx_hash else 'Henüz işlem yok'}

⚡ **Otomatik İzleme:**"""

        # Add confirmation monitoring info
        if confirmation_result:
            conf_id, conf_status, conf_tx, conf_confirmations, conf_created, conf_confirmed, conf_error = confirmation_result

            if conf_status == 'waiting':
                text += f"""
• 🔄 Blockchain izleniyor
• ⏱️ Başlangıç: {conf_created[:16]}
• 🔍 {sol_amount} SOL bekleniyor
• 📡 Otomatik algılama aktif"""

            elif conf_status == 'confirmed':
                text += f"""
• ✅ Otomatik olarak algılandı
• 🎉 Onay tarihi: {conf_confirmed[:16]}
• 🔗 TX: `{conf_tx}`
• ⚡ Bakiye otomatik güncellendi"""

            elif conf_status == 'timeout':
                text += f"""
• ⏰ Otomatik izleme zaman aşımı
• 🔄 Manuel kontrol gerekebilir
• ⚠️ İşlemi manuel gönderdiğinizden emin olun"""

            elif conf_status == 'failed':
                text += f"""
• ❌ İzleme hatası
• 📝 Hata: {conf_error or 'Bilinmeyen hata'}
• 🔄 Manuel kontrol önerilir"""

        else:
            if status == 'pending':
                text += f"""
• ⚠️ Otomatik izleme başlatılmamış
• 📱 QR kod veya manuel gönderim yapın
• 🔄 İşlem sonrası otomatik algılanır"""

        text += f"""

📱 **Sonraki Adımlar:**"""

        if status == 'pending':
            text += f"""
1. {sol_amount} SOL gönderiniz
2. İşlem otomatik algılanır
3. Bakiyeniz güncellenir

{get_random_celebration()} Otomatik sistem aktif! {get_random_celebration()}"""
        elif status == 'confirmed':
            text += f"""
✅ İşlem tamamlandı!
🎉 {fc_amount:,} FC hesabınıza eklendi
💰 Mevcut bakiyeniz: {user['fun_coins']:,} FC

{get_random_celebration()} Başarılı yatırım! {get_random_celebration()}"""

        buttons = []

        if status == 'pending':
            buttons.extend([
                [("🔳 QR Kodu Göster", f"show_qr_{deposit_id}_{sol_amount}")],
                [("📋 Adresi Kopyala", f"copy_address_{wallet_address}")],
                [("🔄 Tekrar Kontrol Et", f"check_deposit_{deposit_id}")]
            ])
        else:
            buttons.append([("📊 Yatırım Geçmişi", f"deposit_history_{user['user_id']}")])

        buttons.extend([
            [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
        ])

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Check deposit status error: {e}")
        await safe_edit_message(query, "❌ Durum kontrol edilemedi.", reply_markup=None)

async def check_solana_withdrawal_status(query, user, withdrawal_id, casino_bot):
    """Check Solana withdrawal status"""
    try:
        import sqlite3
        from solana_payment import get_solana_payment
        
        solana_system = get_solana_payment()
        
        conn = sqlite3.connect(solana_system.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT fc_amount, sol_amount, fee_amount, user_wallet, status, 
                   created_at, processed_at, transaction_hash, admin_notes
            FROM solana_withdrawals WHERE id = ? AND user_id = ?
        """, (withdrawal_id, user['user_id']))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            text = f"""❌ **ÇEKİM BULUNAMADI** ❌

• Çekim ID: {withdrawal_id}
• Bu ID ile herhangi bir çekim bulunamadı
• Lütfen ID'yi kontrol edin"""
        else:
            fc_amount, sol_amount, fee_amount, user_wallet, status, created_at, processed_at, tx_hash, admin_notes = result
            
            status_text = {
                'pending': '⏳ Beklemede',
                'completed': '✅ Tamamlandı',
                'rejected': '❌ Reddedildi'
            }.get(status, '❓ Bilinmiyor')
            
            text = f"""📊 **ÇEKİM DURUMU** 📊

💸 **Çekim Detayları:**
• ID: {withdrawal_id}
• Çekilen FC: {fc_amount:,} FC
• SOL Miktarı: {sol_amount:.4f} SOL
• Komisyon: {fee_amount:.4f} SOL
• Durum: {status_text}

📍 **Cüzdan:**
`{user_wallet}`

📝 **Tarihler:**
• Talep: {created_at}
• İşlem: {processed_at if processed_at else 'Henüz işlenmedi'}

{f"🔗 **İşlem Hash:** `{tx_hash}`" if tx_hash else ""}
{f"📄 **Not:** {admin_notes}" if admin_notes else ""}

{get_random_celebration() if status == 'completed' else '⏳ İşlem kontrol ediliyor...'}"""
        
        buttons = [
            [("🔄 Tekrar Kontrol Et", f"check_withdrawal_{withdrawal_id}")],
            [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Check withdrawal status error: {e}")
        await safe_edit_message(query, "❌ Durum kontrol edilemedi.", reply_markup=None)

async def show_custom_sol_amount_input(query, user, casino_bot):
    """Show custom SOL amount input menu"""
    try:
        # Import context to set waiting flag
        from telegram.ext import CallbackContext

        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        text = f"""💎 **ÖZEL MİKTAR GİRİN** 💎

◎ **Solana Network** - Hızlı & Güvenli ◎

💱 **Güncel Dönüşüm Oranı:**
1 SOL = {current_rate:,.0f} 🐻 Fun Coins

💡 **Özel Miktar Nasıl Girilir:**
1. Bir sonraki mesajınızda sadece SOL miktarını yazın
2. Örnek: 0.75 veya 1.5 veya 3.25
3. Minimum: 0.01 SOL
4. Maksimum: 100 SOL

📝 **Örnekler:**
• 0.15 SOL = {int(0.15 * current_rate):,} FC
• 0.33 SOL = {int(0.33 * current_rate):,} FC
• 0.88 SOL = {int(0.88 * current_rate):,} FC
• 2.25 SOL = {int(2.25 * current_rate):,} FC

⚠️ **DİKKAT:**
• Sadece sayı yazın (örnek: 1.25)
• Nokta kullanın (virgül değil)
• SOL kelimesini yazmayın
• Geçerli aralıkta olmalı

📱 **Bir sonraki mesajınızda sadece SOL miktarını yazın.**

🤖 **Bot özel miktar girişinizi bekliyor...**"""

        buttons = [
            [("0.15 SOL", "select_sol_amount_0.15"), ("0.33 SOL", "select_sol_amount_0.33")],
            [("0.88 SOL", "select_sol_amount_0.88"), ("2.25 SOL", "select_sol_amount_2.25")],
            [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Custom SOL amount input error: {e}")
        await safe_edit_message(query, "❌ Özel miktar menüsü yüklenemedi.", reply_markup=None)

async def show_custom_withdrawal_amount_input(query, user, casino_bot):
    """Show custom SOL withdrawal amount input menu"""
    try:
        solana_system = get_solana_payment()
        current_rate = solana_system.get_sol_to_fc_rate()

        user_balance = user['fun_coins']
        max_sol = user_balance / current_rate

        text = f"""💎 **ÖZEL ÇEKİM MİKTARI GİRİN** 💎

◎ **Solana Network** - Güvenli Çekim ◎

💰 **Mevcut Bakiye:** {user_balance:,} FC
💱 **Max Çekim:** {max_sol:.4f} SOL
💸 **Komisyon:** %{solana_system.withdrawal_fee_rate*100:.0f}

💡 **Özel Miktar Nasıl Girilir:**
1. Bir sonraki mesajınızda sadece SOL miktarını yazın
2. Örnek: 0.75 veya 1.5 veya 3.25
3. Minimum: 0.01 SOL
4. Maksimum: {max_sol:.4f} SOL

📝 **Örnekler:**
• 0.1 SOL = {int(0.1 * current_rate):,} FC
• 0.5 SOL = {int(0.5 * current_rate):,} FC
• 1.0 SOL = {int(1.0 * current_rate):,} FC
• 2.0 SOL = {int(2.0 * current_rate):,} FC

⚠️ **DİKKAT:**
• Sadece sayı yazın (örnek: 1.25)
• Nokta kullanın (virgül değil)
• SOL kelimesini yazmayın
• Bakiyenizden fazla çekemezsiniz

📱 **Bir sonraki mesajınızda sadece SOL miktarını yazın.**

🤖 **Bot özel çekim miktarı girişinizi bekliyor...**"""

        if user_balance <= 0:
            text = """❌ **ÇEKİM YAPILAMAZ** ❌

💰 **Bakiye:** 0 FC

💡 Çekim yapabilmek için önce bakiye yüklemeniz gerekiyor."""
            buttons = [
                [("💰 SOL Yatır", "solana_deposit")],
                [("🔙 Geri", "solana_withdraw"), ("🏠 Ana Menü", "main_menu")]
            ]
        else:
            buttons = [
                [("0.1 SOL", "select_withdrawal_amount_0.1"), ("0.5 SOL", "select_withdrawal_amount_0.5")],
                [("1.0 SOL", "select_withdrawal_amount_1.0"), ("2.0 SOL", "select_withdrawal_amount_2.0")],
                [("🔙 Geri", "solana_withdraw"), ("🏠 Ana Menü", "main_menu")]
            ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Custom withdrawal amount input error: {e}")
        await safe_edit_message(query, "❌ Özel çekim menüsü yüklenemedi.", reply_markup=None)

async def show_user_deposit_history(query, user, casino_bot):
    """Show user's centralized deposit history"""
    try:
        solana_system = get_solana_payment()

        # Get user's deposit history from database
        import sqlite3
        conn = sqlite3.connect(solana_system.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sol_amount, fc_amount, status, created_at, confirmed_at
            FROM solana_deposits
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user['user_id'],))

        deposits = cursor.fetchall()
        conn.close()

        if not deposits:
            text = f"""📊 **YATIRIM GEÇMİŞİNİZ** 📊

❌ **Henüz yatırım kaydınız bulunmuyor**

💡 **İlk yatırımınızı yapın:**
• SOL Yatır butonuna tıklayın
• Miktar seçin veya özel miktar girin
• Merkezi adrese SOL gönderin
• Admin onayı bekleyin

📍 **Merkezi Adres:**
`{solana_system.get_deposit_wallet()}`"""
        else:
            total_sol = sum(d[0] for d in deposits if d[2] == 'confirmed')
            total_fc = sum(d[1] for d in deposits if d[2] == 'confirmed')
            pending_count = sum(1 for d in deposits if d[2] == 'pending')

            deposit_list = []
            for i, (sol, fc, status, created, confirmed) in enumerate(deposits[:5], 1):
                status_emoji = "✅" if status == 'confirmed' else "⏳"
                date = created[:10]  # YYYY-MM-DD
                deposit_list.append(f"{i}. {status_emoji} {sol} SOL → {fc:,} FC ({date})")

            text = f"""📊 **YATIRIM GEÇMİŞİNİZ** 📊

💰 **Özet Bilgiler:**
• Toplam Onaylı: {total_sol:.4f} SOL
• Toplam FC Alınan: {total_fc:,} FC
• Bekleyen İşlem: {pending_count} adet

📋 **Son İşlemler:**
{chr(10).join(deposit_list)}

📍 **Merkezi Adres:**
`{solana_system.get_deposit_wallet()}`

🎯 **Sistem Özellikleri:**
• ✅ Merkezi güvenli adres
• ✅ Manuel onay sistemi
• ✅ Güvenli işlemler
• ✅ Hızlı onay

{get_random_celebration()} Merkezi sistem! {get_random_celebration()}"""

        buttons = [
            [("💰 Yeni Yatırım", "solana_deposit")],
            [("💸 Para Çekme", "solana_withdraw")],
            [("🔙 Geri", "solana_payment"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Show wallet stats error: {e}")
        await safe_edit_message(query, "❌ Cüzdan istatistikleri yüklenemedi.", reply_markup=None)

async def show_cryptobot_payment_menu(query, user, casino_bot):
    """Show CryptoBot payment menu"""
    try:
        text = f"""🤖 **CRYPTOBOT ÖDEMESİ** 🤖

💰 **Mevcut Bakiye:** {user['fun_coins']:,} FC

🚀 **CryptoBot Özellikleri:**
• 💎 Çoklu kripto para desteği
• ⚡ Hızlı işlem onayları
• 🔒 Güvenli ödeme altyapısı
• 🌐 Telegram içi ödeme sistemi

💱 **Desteklenen Kriptolar:**
• USDT (TRC20/ERC20)
• TON Coin
• Bitcoin (BTC)
• Ethereum (ETH)
• TRON (TRX)
• BNB

⚠️ **Bakım Modu**
CryptoBot entegrasyonu şu anda geliştirme aşamasındadır.

🔧 **Geçici Çözüm:**
Solana ödeme sistemini kullanabilirsiniz."""

        buttons = [
            [("🔮 Solana Ödemesi", "solana_payment")],
            [("🔙 Geri", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Show CryptoBot payment menu error: {e}")
        await safe_edit_message(query, "❌ CryptoBot menüsü yüklenemedi.", reply_markup=None)