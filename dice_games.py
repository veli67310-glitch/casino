#!/usr/bin/env python3
"""
🎲 Telegram Dice Games Integration
All Telegram supported dice emojis with interactive gameplay
"""

import asyncio
import random
import logging
from datetime import datetime
from visual_assets import (
    TELEGRAM_DICE, DICE_RESULTS, get_dice_result_message,
    calculate_dice_payout, get_dice_celebration, get_dice_animation_sequence,
    EMOJI_COMBOS, get_random_celebration
)

logger = logging.getLogger(__name__)

class TelegramDiceGames:
    """Handle all Telegram dice emoji games"""
    
    def __init__(self, casino_bot):
        self.casino_bot = casino_bot
        
    async def show_dice_games_menu(self, query, user):
        """Show all available dice games"""
        try:
            dice_menu_text = f"""
🎲✨ **OFFICIAL TELEGRAM DICE GAMES** ✨🎲
📱 *Gerçek Telegram Dice API'sı kullanılıyor!*

🐻 **Bakiye:** {user['fun_coins']:,} 🐻
🎯 **6 Resmi Dice Oyunu - Core API Specs!**

🎲 **KLASİK ZAR** (1-6)
• 6 = x6 En yüksek skor! 🎉
• 4-5 = x2 İyi sonuç • 3 = x1 Ortalama
• Min. Bahis: 50 🐻

🎯 **DART ATMA** (1-6) 
• 6 = BULLSEYE x10! 🎯 *Tam merkez*
• 4-5 = x3 Hedefe yakın • 2-3 = x1 Hedefi vur
• 1 = KAYIP *Tahtayı kaçır*
• Min. Bahis: 100 🐻

🏀 **BASKETBOL** (1-5)
• 4-5 = BASKET x5! 🏀 *Top girdi*
• 3 = x1 Çembere çarptı • 1-2 = KAYIP
• Min. Bahis: 75 🐻

⚽ **FUTBOL** (1-5)
• 4-5 = GOL x5! ⚽ *Ağlara gitti*
• 3 = x1 Direğe çarptı • 1-2 = KAYIP  
• Min. Bahis: 75 🐻

🎳 **BOWLING** (1-6)
• 6 = STRIKE x6! 🎳 *Tüm pinler*
• 4-5 = x2 Çok pin • 3 = x1 Bazı pin
• 1-2 = KAYIP *Gutter ball*
• Min. Bahis: 100 🐻

🎰 **SLOT MAKİNESİ** (1-64)
• 64 = x100 MEGA JACKPOT! 💎 *Üçlü 7*
• 1,22,43 = x50 Özel jackpot! 🔥
• 50+ = x10 • 30+ = x5 • 15+ = x2
• Min. Bahis: 200 🐻

💡 **3 makaralı slot = 2^6 = 64 kombinasyon!**

{get_random_celebration()} Hangi oyunu oynamak istiyorsun? {get_random_celebration()}
            """
            
            buttons = [
                [("🎲 Klasik Zar", "dice_classic"), ("🎯 Dart Atma", "dice_darts")],
                [("🏀 Basketbol", "dice_basketball"), ("⚽ Futbol", "dice_football")],
                [("🎳 Bowling", "dice_bowling"), ("🎰 Slot Dice", "dice_slot")],
                [("📊 İstatistik", "dice_stats"), ("🏠 Ana Menü", "main_menu")]
            ]
            
            keyboard = self.casino_bot.create_keyboard(buttons)
            await query.edit_message_text(dice_menu_text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Dice menu error: {e}")
            
    def normalize_dice_type(self, dice_type):
        """Normalize dice type names from callback to config keys"""
        mapping = {
            'classic': 'classic_dice',
            'classic_dice': 'classic_dice',
            'darts': 'darts',
            'basketball': 'basketball',
            'football': 'football',
            'bowling': 'bowling',
            'slot_machine': 'slot_machine'
        }
        return mapping.get(dice_type, dice_type)

    async def show_dice_game_options(self, query, user, dice_type):
        """Show betting options for specific dice game"""
        try:
            # Normalize dice type
            dice_type = self.normalize_dice_type(dice_type)
            dice_config = TELEGRAM_DICE[dice_type]
            dice_name = dice_config['name']
            dice_emoji = dice_config['emoji']
            
            # Minimum bet based on game type
            min_bets = {
                'classic': 50,
                'classic_dice': 50,
                'darts': 100, 
                'basketball': 75,
                'football': 75,
                'bowling': 100,
                'slot_machine': 200
            }
            
            min_bet = min_bets.get(dice_type, 50)
            
            # Check if user has enough balance
            if user['fun_coins'] < min_bet:
                await query.edit_message_text(
                    f"💸 Yetersiz bakiye!\n\n{dice_emoji} **{dice_name}** için minimum {min_bet} 🐻 gerekli.\n🐻 **Bakiyeniz:** {user['fun_coins']} 🐻",
                    reply_markup=self.casino_bot.create_keyboard([
                        [("💳 Para Yatır", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return
            
            # Create detailed game description based on API behavior
            api_behavior = dice_config.get('api_behavior', 'Standard dice roll')
            description = dice_config.get('description', 'Dice game')
            
            game_text = f"""
{dice_emoji}✨ **{dice_name.upper()}** ✨{dice_emoji}
📱 *{api_behavior}*

🐻 **Bakiye:** {user['fun_coins']:,} 🐻
🎯 **Değer Aralığı:** {dice_config['min_value']}-{dice_config['max_value']}
📝 **Açıklama:** {description}

🎊 **KAZANÇ TABLOSU (Resmi API Kuralları):**"""
            
            # Add specific payout info based on game type
            if dice_type == 'slot_machine':
                game_text += f"""
💎 **64 = x100** MEGA JACKPOT (Üçlü 7)
🔥 **1,22,43 = x50** Özel jackpot kombinasyonları  
⭐ **50-63 = x10** Yüksek değer kombinasyonları
🐻 **30-49 = x5** Orta-yüksek kombinasyonlar
😊 **15-29 = x2** Orta kombinasyonlar
💔 **2-14 = KAYIP** Düşük kombinasyonlar"""
            elif dice_type == 'darts':
                game_text += f"""
🎯 **6 = x10** BULLSEYE (Tam merkez)
⭐ **4-5 = x3** Hedefe yakın atış
😊 **2-3 = x1** Hedefi vur ama uzak
💔 **1 = KAYIP** Dart tahtasını kaçır"""
            elif dice_type in ['basketball', 'football']:
                sport_name = "Basket" if dice_type == 'basketball' else "Gol"
                game_text += f"""
🏆 **4-5 = x5** {sport_name} başarılı!
😊 **3 = x1** Yakın kaçırma
💔 **1-2 = KAYIP** Tamamen kaçırma"""
            elif dice_type == 'bowling':
                game_text += f"""
🎳 **6 = x6** STRIKE (Tüm pinler)
⭐ **4-5 = x2** Çok pin devir
😊 **3 = x1** Bazı pin devir  
💔 **1-2 = KAYIP** Gutter ball"""
            else:  # classic_dice
                game_text += f"""
🎉 **6 = x6** En yüksek skor
⭐ **4-5 = x2** Ortalamanın üstü
😊 **3 = x1** Ortalama skor
💔 **1-2 = KAYIP** Ortalamanın altı"""
            
            game_text += f"""

💡 **Nasıl Oynanır:**
1. Bahis miktarını seç
2. Gerçek Telegram {dice_emoji} dice gönderilir
3. API sonucuna göre otomatik ödeme!

🎲 Bahis miktarını seç:
            """
            
            # Create betting buttons
            bet_amounts = [min_bet, min_bet*2, min_bet*5, min_bet*10]
            bet_buttons = []
            
            for i in range(0, len(bet_amounts), 2):
                row = []
                for j in range(2):
                    if i + j < len(bet_amounts):
                        amount = bet_amounts[i + j]
                        if amount <= user['fun_coins']:
                            row.append((f"{amount} 🐻", f"play_dice_{dice_type}_{amount}"))
                if row:
                    bet_buttons.append(row)
            
            # Add custom bet option
            if user['fun_coins'] >= min_bet * 20:
                bet_buttons.append([("💎 Özel Bahis", f"custom_dice_{dice_type}")])
                
            bet_buttons.append([("⬅️ Geri", "solo_games"), ("🏠 Ana Menü", "main_menu")])
            
            keyboard = self.casino_bot.create_keyboard(bet_buttons)
            await query.edit_message_text(game_text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Dice game options error: {e}")
            
    async def play_dice_game(self, query, user, dice_type, bet_amount):
        """Play a dice game with Telegram dice emoji"""
        try:
            # Normalize dice type
            dice_type = self.normalize_dice_type(dice_type)
            dice_config = TELEGRAM_DICE[dice_type]
            dice_emoji = dice_config['emoji']
            dice_name = dice_config['name']
            
            # Check balance
            if user['fun_coins'] < bet_amount:
                await query.edit_message_text(
                    "💸 Yetersiz bakiye!",
                    reply_markup=self.casino_bot.create_keyboard([
                        [("💳 Para Yatır", "payment_menu"), ("🏠 Ana Menü", "main_menu")]
                    ])
                )
                return
            
            # Deduct bet amount
            self.casino_bot.update_user_balance(user['user_id'], -bet_amount)
            
            # Show pre-game animation
            animation_sequence = get_dice_animation_sequence(dice_type)
            
            pre_game_text = f"""
{dice_emoji} **{dice_name.upper()}** {dice_emoji}

🐻 **Bahis:** {bet_amount:,} 🐻
🎯 **Oyun başlıyor...**

{animation_sequence[0]} Hazırlanıyor...
            """
            
            await query.edit_message_text(pre_game_text, parse_mode='Markdown')
            
            # Show animation sequence
            for i, emoji in enumerate(animation_sequence):
                await asyncio.sleep(0.5)
                anim_text = f"""
{dice_emoji} **{dice_name.upper()}** {dice_emoji}

🐻 **Bahis:** {bet_amount:,} 🐻
🎯 **Oyun başlıyor...**

{emoji} {"Atılıyor..." if i < len(animation_sequence)-1 else "Son saniye..."}
                """
                await query.edit_message_text(anim_text, parse_mode='Markdown')
            
            # Send actual Telegram dice
            await asyncio.sleep(0.5)
            await query.edit_message_text(f"{dice_emoji} **{dice_name}** atılıyor...", parse_mode='Markdown')
            
            try:
                # Send the actual Telegram dice emoji with timeout
                dice_message = await asyncio.wait_for(
                    query.message.reply_dice(emoji=dice_emoji), 
                    timeout=10.0
                )
                dice_value = dice_message.dice.value
                
                # Show special slot machine reel breakdown for slot games
                if dice_type == 'slot_machine':
                    # Convert dice value to 3-reel representation (unofficial visualization)
                    reel1 = ((dice_value - 1) // 16) % 4 + 1  # 1-4
                    reel2 = ((dice_value - 1) // 4) % 4 + 1   # 1-4  
                    reel3 = ((dice_value - 1) % 4) + 1        # 1-4
                    
                    reel_symbols = {1: '🍒', 2: '🍋', 3: '🔔', 4: '7️⃣'}
                    
                    await asyncio.sleep(1)
                    await query.message.reply_text(
                        f"🎰 **3 MAKARA SONUCU:**\n"
                        f"┌─────────────┐\n"
                        f"│ {reel_symbols[reel1]} │ {reel_symbols[reel2]} │ {reel_symbols[reel3]} │\n"
                        f"└─────────────┘\n"
                        f"📊 **Kombinasyon #{dice_value}**"
                    )
                
                # Wait for dice animation to complete - UZATILDI
                await asyncio.sleep(6)
                
            except asyncio.TimeoutError:
                logger.error(f"Dice sending timeout for {dice_type}")
                # Fallback to random value if dice sending times out
                dice_value = random.randint(dice_config['min_value'], dice_config['max_value'])
                await query.message.reply_text(f"🎲 Sonuç: {dice_value} (Network timeout - backup mode)")
                dice_message = None
            except Exception as e:
                logger.error(f"Dice sending error: {e}")
                # Fallback to random value if dice sending fails
                dice_value = random.randint(dice_config['min_value'], dice_config['max_value'])
                await query.message.reply_text(f"🎲 Sonuç: {dice_value} (Backup mode)")
                dice_message = None
            
            # Calculate payout
            payout = calculate_dice_payout(dice_type, dice_value, bet_amount)
            profit = payout - bet_amount
            
            # Update balance with payout
            if payout > 0:
                self.casino_bot.update_user_balance(user['user_id'], payout)
            
            # Get result message and celebration
            result_message = get_dice_result_message(dice_type, dice_value)
            celebration = get_dice_celebration(dice_type, dice_value)
            
            # Determine result type
            dice_win_values = dice_config['win_values']
            dice_good_values = dice_config['good_values'] 
            dice_bad_values = dice_config['bad_values']
            
            if dice_value in dice_win_values:
                result_type = "🏆 JACKPOT"
                result_emoji = "🎉🎊🥳"
            elif dice_value in dice_good_values:
                result_type = "⭐ KAZANÇ"
                result_emoji = "😊👍✨"
            elif dice_value in dice_bad_values:
                result_type = "💔 KAYIP"
                result_emoji = "😔👎💸"
            else:
                result_type = "😐 EŞIT"
                result_emoji = "😐🤷‍♂️"
            
            # Create result message
            result_text = f"""
{celebration}

{result_emoji} **{result_type}** {result_emoji}

{dice_emoji} **{dice_name}:** {dice_value}
{result_message}

🐻 **Bahis:** {bet_amount:,} 🐻
💎 **Kazanç:** {payout:,} 🐻
📈 **Kâr/Zarar:** {profit:+,} 🐻
🐻 **Yeni Bakiye:** {user['fun_coins'] + payout:,} 🐻

{get_random_celebration() if profit > 0 else "Bir dahaki sefere daha şanslı olacaksın! 🍀"}
            """
            
            # Create result buttons
            result_buttons = [
                [(f"🎲 Tekrar Oyna", f"dice_game_options_{dice_type}"), ("🎯 Diğer Oyunlar", "solo_games")],
                [("📊 İstatistik", "dice_stats"), ("🏠 Ana Menü", "main_menu")]
            ]
            
            keyboard = self.casino_bot.create_keyboard(result_buttons)
            await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
            
            # Delete the dice emoji message after showing result (with 1 second delay)
            if dice_message:
                try:
                    await asyncio.sleep(3.0)  # UZATILDI - 3 second delay before deletion
                    await dice_message.delete()
                except Exception as e:
                    # Message deletion is optional and can fail due to Telegram restrictions
                    # (e.g., message too old, insufficient permissions, etc.)
                    # This is not critical for game functionality, so we'll just log it as debug
                    logger.debug(f"Could not delete dice message (this is normal): {e}")
                    pass
            
            # Update user statistics
            self.casino_bot.update_user_stats(user['user_id'], 1, profit, profit > 0)
            
            # Send celebration sticker for big wins
            if profit >= bet_amount * 3:
                try:
                    await query.message.reply_sticker(
                        "CAACAgIAAxkBAAICEmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJEFAACzL8xSoOACgAB6ZyUSS0E"  # big win sticker
                    )
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Dice game play error: {e}")
            await query.edit_message_text(
                "❌ Oyun hatası oluştu!",
                reply_markup=self.casino_bot.create_keyboard([
                    [("🎮 Solo Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            
    async def show_dice_statistics(self, query, user):
        """Show dice games statistics"""
        try:
            # Get user stats from database
            with self.casino_bot.db.get_connection() as conn:
                stats = conn.execute('''
                    SELECT 
                        total_bet, total_won, games_count, 
                        win_streak, max_streak
                    FROM users WHERE user_id = ?
                ''', (user['user_id'],)).fetchone()
            
            if not stats:
                stats = {'total_bet': 0, 'total_won': 0, 'games_count': 0, 'win_streak': 0, 'max_streak': 0}
            
            win_rate = (stats['total_won'] / stats['total_bet'] * 100) if stats['total_bet'] > 0 else 0
            profit = stats['total_won'] - stats['total_bet']
            
            stats_text = f"""
📊✨ **DICE OYUNLARI İSTATİSTİKLERİ** ✨📊

👤 **Oyuncu:** {user['username'] if 'username' in user else 'Anonim'}
🐻 **Mevcut Bakiye:** {user['fun_coins']:,} 🐻

🎲 **GENEL İSTATİSTİKLER:**
🎮 **Toplam Oyun:** {stats['games_count']:,}
💵 **Toplam Bahis:** {stats['total_bet']:,} 🐻
🐻 **Toplam Kazanç:** {stats['total_won']:,} 🐻
📈 **Kâr/Zarar:** {profit:+,} 🐻
🎯 **Kazanma Oranı:** {win_rate:.1f}%

🔥 **STREAK İSTATİSTİKLERİ:**
⚡ **Mevcut Streak:** {stats['win_streak']}
🏆 **En İyi Streak:** {stats['max_streak']}

🎲 **DICE TİPLERİ ve ORANLAR:**
🎲 Klasik Zar: 6 = x6 🎯
🎯 Dart: Bullseye = x10 🏆
🏀 Basketbol: Basket = x5 ⭐
⚽ Futbol: Gol = x5 🥅
🎳 Bowling: Strike = x6 🎳
🎰 Dice Slots: Mega Jackpot = x100 💎

💡 **İPUÇLARI:**
• Küçük bahislerle başla
• Streak'ını koru 
• Şansını zorla
• Kaybettiğinde ara ver

{get_random_celebration()} İyi oyunlar! {get_random_celebration()}
            """
            
            buttons = [
                [("🎮 Solo Oyunlar", "solo_games"), ("📊 Profil", "profile")],
                [("📊 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
            ]
            
            keyboard = self.casino_bot.create_keyboard(buttons)
            await query.edit_message_text(stats_text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Dice statistics error: {e}")

# Global dice games instance
dice_games_instance = None

def get_dice_games_instance(casino_bot):
    """Get or create dice games instance"""
    global dice_games_instance
    if dice_games_instance is None:
        dice_games_instance = TelegramDiceGames(casino_bot)
    return dice_games_instance

# Handler functions for integration
async def handle_dice_games_menu(query, user, casino_bot):
    """Handler for dice games menu"""
    dice_games = get_dice_games_instance(casino_bot)
    await dice_games.show_dice_games_menu(query, user)

async def handle_dice_game_options(query, user, casino_bot, dice_type):
    """Handler for dice game options"""
    dice_games = get_dice_games_instance(casino_bot)
    await dice_games.show_dice_game_options(query, user, dice_type)
    
async def handle_play_dice_game(query, user, casino_bot, dice_type, bet_amount):
    """Handler for playing dice game"""
    dice_games = get_dice_games_instance(casino_bot)
    await dice_games.play_dice_game(query, user, dice_type, bet_amount)
    
async def handle_dice_statistics(query, user, casino_bot):
    """Handler for dice statistics"""
    dice_games = get_dice_games_instance(casino_bot)
    await dice_games.show_dice_statistics(query, user)

async def handle_custom_dice_bet(query, user, casino_bot, dice_type):
    """Handler for custom dice bet amount input"""
    try:
        dice_info = TELEGRAM_DICE.get(dice_type, {})
        min_bet = dice_info.get('min_bet', 50)
        max_balance_bet = min(user['fun_coins'], 10000)  # Max 10k bet

        custom_bet_text = f"""
💎 **ÖZEL BAHIS - {dice_info.get('name', dice_type.upper())} {dice_info.get('emoji', '🎲')}**

🐻 **Mevcut Bakiye:** {user['fun_coins']:,} 🐻
💎 **Minimum Bahis:** {min_bet} 🐻
💎 **Maximum Bahis:** {max_balance_bet:,} 🐻

💡 **Bahis miktarını seçin veya yazın:**
        """

        # Create custom amount buttons
        bet_amounts = []
        amounts = [min_bet * 5, min_bet * 10, min_bet * 20, min_bet * 50]

        row = []
        for amount in amounts:
            if amount <= user['fun_coins']:
                row.append((f"{amount} 🐻", f"play_dice_{dice_type}_{amount}"))
                if len(row) == 2:
                    bet_amounts.append(row)
                    row = []
        if row:
            bet_amounts.append(row)

        # Add maximum bet option
        if max_balance_bet > min_bet * 50:
            bet_amounts.append([(f"💎 MAX: {max_balance_bet:,} 🐻", f"play_dice_{dice_type}_{max_balance_bet}")])

        bet_amounts.append([("⬅️ Geri", f"dice_{dice_type}"), ("🏠 Ana Menü", "main_menu")])

        keyboard = casino_bot.create_keyboard(bet_amounts)
        await query.edit_message_text(custom_bet_text, reply_markup=keyboard, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Custom dice bet error: {e}")
        await query.edit_message_text(
            "❌ Özel bahis özelliği şu anda kullanılamıyor.",
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Oyunlar", "solo_games")]])
        )