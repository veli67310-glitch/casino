#!/usr/bin/env python3
"""
🎮 Casino Bot Menu Handlers
"""

import json
import random
import asyncio
from config import GAMES, ACHIEVEMENTS, SOLO_GAMES
from languages import get_text, DEFAULT_LANGUAGE
from safe_telegram_handler import safe_edit_message
from visual_assets import (
    CASINO_STICKERS, EMOJI_ANIMATIONS, EMOJI_COMBOS, 
    UI_EMOJIS, get_random_celebration, create_animated_message
)

async def show_main_menu(casino_bot, update_or_query, context, is_callback: bool = False):
    """Main menu"""
    if is_callback:
        user_id = update_or_query.from_user.id
        username = update_or_query.from_user.username or "Anonymous"
    else:
        user_id = update_or_query.effective_user.id
        username = update_or_query.effective_user.username or "Anonymous"
    
    user = casino_bot.get_user(user_id, username)
    
    # Get user's language preference
    user_lang = DEFAULT_LANGUAGE
    if hasattr(casino_bot.db, 'get_user_language'):
        try:
            user_lang = casino_bot.db.get_user_language(user_id)
        except:
            user_lang = DEFAULT_LANGUAGE
    
    # Clean organized buttons
    buttons = [
        [("🎮 Solo Games", "solo_games"), ("⚔️ Duel", "create_duel")],
        [("🎯 Join Duel", "join_duel"), ("🏆 Tournaments", "tournaments")],
        [("🎪 Bonus Features", "bonus_features"), ("💳 Payments", "payment_menu")],
        [("📊 Profile", "profile"), ("👥 Friends", "friends")],
        [("🎁 Daily Quests", "daily_quests"), ("🏅 Achievements", "achievements")],
        [("📈 Leaderboard", "leaderboard"), ("👥 Join Group", "join_group")],
        [("🌍 Language", "language_selection")]
    ]
    
    # Add admin panel for admins only
    from config import ADMIN_USER_IDS
    if user_id in ADMIN_USER_IDS:
        buttons.append([("🔧 Admin Panel", "admin_panel")])
    
    keyboard = casino_bot.create_keyboard(buttons)
    
    # Level progress bar
    current_level_xp = user['xp'] % 1000
    progress_filled = current_level_xp // 50
    progress_empty = 20 - progress_filled
    progress = "▰" * progress_filled + "▱" * progress_empty
    
    # Time-based greetings - Localized
    import datetime
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        greeting = get_text(user_lang, "main_menu.greeting_morning", "🌅 Good morning")
        time_emoji = "☀️"
    elif 12 <= hour < 17:
        greeting = get_text(user_lang, "main_menu.greeting_afternoon", "🌞 Good afternoon")
        time_emoji = "🌤️"
    elif 17 <= hour < 21:
        greeting = get_text(user_lang, "main_menu.greeting_evening", "🌆 Good evening")
        time_emoji = "🌇"
    else:
        greeting = get_text(user_lang, "main_menu.greeting_night", "🌙 Good night")
        time_emoji = "🌜"
    
    # VIP status display
    vip_level = 0  # You can implement VIP level checking here
    vip_display = f"👑 VIP {vip_level}" if vip_level > 0 else "🎯 Standard"
    
    # Win rate calculation
    win_rate = (user['total_won'] / user['total_bet'] * 100) if user['total_bet'] > 0 else 0
    
    # Dynamic status based on streak - Localized
    if user['win_streak'] >= 10:
        status_emoji = "🔥🔥🔥"
        status_text = get_text(user_lang, "main_menu.status_on_fire", "ON FIRE!")
    elif user['win_streak'] >= 5:
        status_emoji = "🔥"
        status_text = get_text(user_lang, "main_menu.status_hot", "Hot Streak!")
    elif user['win_streak'] >= 3:
        status_emoji = "⚡"
        status_text = get_text(user_lang, "main_menu.status_good", "Good Run!")
    else:
        status_emoji = "🎯"
        status_text = get_text(user_lang, "main_menu.status_ready", "Ready to Play!")
    
    # Get localized title and welcome
    title = get_text(user_lang, "main_menu.title", "🐻 BetBear 🐻\n💎 CryptoBot Edition 💎")
    welcome = get_text(user_lang, "main_menu.welcome", "🌟 Welcome, {username}! 🌟", username=username)
    
    # Add celebration for big wins or streaks
    celebration_line = ""
    if user['win_streak'] >= 10:
        celebration_line = f"\n{EMOJI_COMBOS['streak_bonus']}\n🔥 *INCREDIBLE STREAK!* 🔥\n"
    elif user['win_streak'] >= 5:
        celebration_line = f"\n{EMOJI_COMBOS['achievement_unlock']}\n⚡ *Hot streak going!* ⚡\n"
    
    # Random welcome sticker reference
    welcome_sticker_emoji = random.choice(['🎰', '🎲', '🎯', '🎮', '💎'])
    
    welcome_text = f"""🐻 **BetBear** 
💎 *CryptoBot Edition*{celebration_line}

{greeting}, **{username}!** {status_emoji}

──────── 🐻 **ACCOUNT INFO** 🐻 ────────
💵 **Balance:** {user['fun_coins']:,} 🐻
🏆 **Level:** {user['level']} | **XP:** {current_level_xp}/1000
{progress}
📊 **Win Rate:** {win_rate:.1f}%

──────── 🎯 **GAME STATISTICS** 🎯 ────────
{status_emoji} **Status:** {status_text}
🔥 **Current Streak:** {user['win_streak']} games
🏆 **Best Streak:** {user['max_streak']} games
🎮 **Total Games:** {user['games_count']:,}

──────── 🚀 **FEATURES** 🚀 ────────
🎰 **Solo Games** - 7 different games
⚔️ **PvP Duels** - Real-time battles
🏆 **Tournaments** - Big prizes
💳 **Crypto Payments** - 6 cryptocurrencies
👥 **Social Hub** - Friends & leaderboard
🎁 **Daily Rewards** - Never miss out

🎯 **Ready to play?**"""
    
    try:
        if is_callback:
            await update_or_query.edit_message_text(welcome_text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await update_or_query.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        print(f"Main menu error: {e}")

async def show_solo_games_menu(query, user, casino_bot):
    """Enhanced Solo games menu with detailed stats"""
    
    # Calculate user's favorite game
    try:
        with casino_bot.db.get_connection() as conn:
            favorite = conn.execute('''
                SELECT game_type, COUNT(*) as plays FROM solo_game_history 
                WHERE user_id = ? GROUP BY game_type 
                ORDER BY plays DESC LIMIT 1
            ''', (user['user_id'],)).fetchone()
            
            recent_win = conn.execute('''
                SELECT game_type, win_amount FROM solo_game_history 
                WHERE user_id = ? AND win_amount > bet_amount 
                ORDER BY played_at DESC LIMIT 1
            ''', (user['user_id'],)).fetchone()
    except:
        favorite = None
        recent_win = None
    
    # Game recommendations based on balance
    recommendations = []
    balance = user['fun_coins']
    if balance >= 10000:
        recommendations.append("💎 High-roller ready!")
    elif balance >= 5000:
        recommendations.append("🎯 Medium stakes available")
    elif balance >= 1000:
        recommendations.append("🎮 All games accessible")
    else:
        recommendations.append("🍀 Low stakes - build up!")
    
    buttons = [
        [("🎰 Ultimate Slots", "solo_slots"), ("🎯 Premium Roulette", "solo_roulette"), ("🃏 Pro Blackjack", "solo_blackjack")],
        [("🚀 Rocket Crash", "solo_crash"), ("💣 Extreme Mines", "solo_mines"), ("🎴 Royal Baccarat", "solo_baccarat")],
        [("🔢 Mega Keno", "solo_keno"), ("🎲 Dice Game", "solo_dice"), ("✂️ RPS", "rock_paper_scissors")],
        [("🔢 Number Guess", "number_guess"), ("🎪 Lucky Wheel", "lucky_wheel")],
        [("📊 Game History", "solo_history"), ("🎯 Quick Play", "quick_play")],
        [("🏠 Main Menu", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    favorite_text = f"🌟 **Favorite:** {favorite['game_type'].replace('solo_', '').title()}" if favorite else "🎮 **Explore all games!**"
    recent_text = f"🎉 **Last Win:** {recent_win['win_amount']:,} 🐻 from {recent_win['game_type'].replace('solo_', '').title()}" if recent_win else "🍀 **Ready for your first big win!**"
    
    text = f"""🎮 **SOLO GAMES**

🐻 **Balance:** {user['fun_coins']:,} 🐻
{favorite_text}
{recent_text}

────── 🎰 **CLASSIC CASINO** 🎰 ──────
🎰 Ultimate Slots | 🎯 Premium Roulette | 🃏 Pro Blackjack

────── 🚀 **MODERN GAMES** 🚀 ──────  
🚀 Rocket Crash | 💣 Extreme Mines | 🎴 Royal Baccarat

────── 🎲 **FUN GAMES** 🎲 ──────
🔢 Mega Keno | 🎲 Dice Game | ✂️ Rock-Paper-Scissors

────── 🎪 **SPECIAL GAMES** 🎪 ──────
🔢 Number Guess | 🎪 Lucky Wheel

💡 **Recommendation:** {' | '.join(recommendations)}

🎯 **Choose your game!**"""
    
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_solo_game_options(query, user, game_type, casino_bot):
    """Solo game betting options"""
    game_config = SOLO_GAMES.get(game_type)
    if not game_config:
        await safe_edit_message(query, "❌ Invalid game type!", 
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]]))
        return
    
    min_bet = game_config['min_bet']
    bet_options = [min_bet, min_bet*2, min_bet*5, min_bet*10, min_bet*20]
    
    buttons = []
    for bet in bet_options:
        if user['fun_coins'] >= bet:
            buttons.append([(f"🐻 {bet} 🐻 Bet", f"play_{game_type}_{bet}")])
        else:
            buttons.append([(f"❌ {bet} 🐻 (Insufficient)", "insufficient_funds")])
    
    buttons.append([("🔙 Go Back", "solo_games"), ("🏠 Main Menu", "main_menu")])
    keyboard = casino_bot.create_keyboard(buttons)
    
    text = f"""
{game_config['name']}

🐻 **Available Coins:** {user['fun_coins']:,} 🐻
🎯 **Minimum Bet:** {min_bet} 🐻

Select bet amount (New options added!):
    """
    
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_create_duel_menu(query, user, casino_bot):
    """Duel creation menu"""
    buttons = [
        [("🪙 Coin Flip", "create_duel_duel_coinflip"), ("🎲 Dice Battle", "create_duel_duel_dice")],
        [("✊ Rock-Paper-Scissors", "create_duel_duel_rockpaper")],
        [("🏠 Main Menu", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    text = f"""
⚔️ **CREATE DUEL** ⚔️

🐻 **Coins:** {user['fun_coins']:,} 🐻

┌────── GAMES ──────┐
│ 🪙 Coin Flip (10C)  │
│ 🎲 Dice (15C)       │
│ ✊ RPS (20C)         │
└─────────────────────┘

🌟 New: Rock-Paper-Scissors!
    """
    
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_join_duel_menu(query, user, casino_bot):
    """Duel joining menu"""
    with casino_bot.db.get_connection() as conn:
        active_duels = conn.execute('SELECT ag.*, u.username FROM active_games ag LEFT JOIN users u ON ag.creator_id = u.user_id WHERE ag.status = "waiting" ORDER BY ag.created_at DESC LIMIT 10').fetchall()
    
    text = "🎯 **ACTIVE DUELS** 🎯\n\n" if active_duels else "😔 No active duels! 😔\n\n⚔️ Create your own duel!"
    buttons = []
    
    for duel in active_duels:
        creator = duel['username'] or "Anonymous"
        game_name = GAMES.get(duel['game_type'], {})['name']
        text += f"🎮 {game_name} by {creator} 🐻 {duel['bet_amount']}\n"
        buttons.append([(f"⚔️ Join", f"join_{duel['game_id']}")])
    
    buttons.append([("🔄 Refresh", "join_duel"), ("🏠 Main Menu", "main_menu")])
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_profile(query, user, casino_bot):
    """Enhanced profile page with detailed analytics"""
    win_rate = (user['total_won'] / user['total_bet'] * 100) if user['total_bet'] > 0 else 0
    current_level_xp = user['xp'] % 1000
    progress = "▰" * (current_level_xp // 50) + "▱" * (20 - (current_level_xp // 50))
    
    with casino_bot.db.get_connection() as conn:
        rank = conn.execute('SELECT COUNT(*) + 1 FROM users WHERE fun_coins > ?', (user['fun_coins'],)).fetchone()[0]
        
        # Get additional stats
        total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        rank_percentage = ((total_users - rank) / total_users * 100) if total_users > 0 else 0
        
        # Get recent achievements
        recent_achievements = conn.execute('''
            SELECT COUNT(*) FROM user_achievements WHERE user_id = ?
        ''', (user['user_id'],)).fetchone()[0]
        
        # Get favorite game
        favorite_game = conn.execute('''
            SELECT game_type, COUNT(*) as plays FROM solo_game_history 
            WHERE user_id = ? GROUP BY game_type ORDER BY plays DESC LIMIT 1
        ''', (user['user_id'],)).fetchone()
    
    # Status badges
    badges = []
    if win_rate >= 60:
        badges.append("🏆 Pro Player")
    if user['max_streak'] >= 10:
        badges.append("🔥 Streak Master")
    if user['games_count'] >= 100:
        badges.append("🎮 Veteran")
    if rank <= 10:
        badges.append("👑 Top 10")
    if not badges:
        badges.append("🌟 Rising Star")
    
    # Next level calculation
    next_level_xp = 1000 - current_level_xp
    
    favorite_display = favorite_game['game_type'].replace('solo_', '').title() if favorite_game else "None yet"
    
    text = f"""👤 **{user['username'].upper()} PROFILE**

──────── 🐻 **ACCOUNT & STATUS** 🐻 ────────
💎 **Balance:** {user['fun_coins']:,} FC
🏆 **Level:** {user['level']} ({next_level_xp} XP left)
⭐ **Progress:** {progress} {current_level_xp}/1000
📊 **Ranking:** #{rank}/{total_users} (Top {rank_percentage:.1f}%)

──────── 🎯 **GAME STATISTICS** 🎯 ────────
🔥 **Current Streak:** {user['win_streak']} games
🏆 **Best Streak:** {user['max_streak']} games  
🎮 **Total Games:** {user['games_count']:,}
💸 **Total Bet:** {user['total_bet']:,} FC
🐻 **Total Won:** {user['total_won']:,} FC
📈 **Win Rate:** {win_rate:.1f}%

──────── 🏅 **ACHIEVEMENTS** 🏅 ────────
🏆 **Unlocked:** {recent_achievements} achievements
🎖️ **Badge:** {' | '.join(badges[:2])}

🆔 **YOUR REFERRAL CODE:** `{user['friend_code']}`
💡 Share and earn!"""
    
    buttons = [
        [("🎁 Daily Bonus", "daily_bonus"), ("🏅 Achievements", "achievements")],
        [("👥 Add Friend", "add_friend"), ("📊 Game History", "solo_history")],
        [("📈 Leaderboard", "leaderboard"), ("🏠 Main Menu", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

# Additional missing handlers
async def show_enhanced_profile(query, user, casino_bot):
    """Enhanced profile with more details"""
    await show_profile(query, user, casino_bot)

async def show_enhanced_solo_games_menu(query, user, casino_bot):
    """Enhanced solo games menu"""
    await show_solo_games_menu(query, user, casino_bot)

async def show_enhanced_solo_game_options(query, user, game_type, casino_bot):
    """Enhanced solo game options"""
    await show_solo_game_options(query, user, game_type, casino_bot)

async def handle_simple_solo_game(query, user, game_data, casino_bot):
    """Simple solo game handler"""
    try:
        from game_handlers import handle_solo_game
        await handle_solo_game(query, user, game_data, casino_bot)
    except ImportError:
        await safe_edit_message(query, 
            "❌ Game system temporarily unavailable.\n\n🔄 Please try again later.",
            reply_markup=casino_bot.create_keyboard([
                [("🎮 Games", "solo_games"), ("🏠 Main Menu", "main_menu")]
            ])
        )