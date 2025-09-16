#!/usr/bin/env python3
"""
🎪 Bonus Features Menu Handler
"""

async def show_bonus_features_menu(query, user, casino_bot):
    """Show bonus features menu with interactive elements"""
    
    # Check daily bonus availability
    try:
        with casino_bot.db.get_connection() as conn:
            last_spin = conn.execute('SELECT last_daily_bonus FROM users WHERE user_id = ?', (user['user_id'],)).fetchone()
            if last_spin and last_spin['last_daily_bonus']:
                from datetime import datetime
                last_date = datetime.fromisoformat(last_spin['last_daily_bonus']).date()
                daily_available = last_date != datetime.now().date()
            else:
                daily_available = True
    except:
        daily_available = True
    
    daily_status = "🆕 Available!" if daily_available else "⏰ Tomorrow"
    
    text = f"""
🎪 **BONUS FEATURES HUB** 🎪

🐻 **Balance:** {user['fun_coins']:,} 🐻

🌟 **Interactive Features:**

┌─────── 🎲 **DAILY REWARDS** 🎲 ───────┐
│ 🎰 **Daily Spinner** - {daily_status}      │
│ 🎡 **Fortune Wheel** - Spin anytime!     │
│ 📦 **Mystery Box** - 500 🐻 to open      │
└───────────────────────────────────────────┘

┌─────── 🏆 **SHOWCASE** 🏆 ─────────────┐
│ 🎖️ **Achievement Gallery** - View all   │
│ 📊 **Detailed Stats** - Deep analytics  │
│ 🎯 **Progress Tracker** - See growth    │
└───────────────────────────────────────────┘

🎁 **Special Features:**
✨ Enhanced animations & sound effects
🎭 Interactive bonus games
🏆 Progressive achievement system
💫 Daily rewards & surprises

🎯 **Choose your bonus adventure!**
    """
    
    buttons = [
        [("🎰 Daily Spinner", "daily_spinner"), ("🎡 Fortune Wheel", "fortune_wheel")],
        [("📦 Mystery Box", "mystery_box"), ("🎖️ Achievement Showcase", "achievement_showcase")],
        [("🎮 Play Games", "solo_games"), ("📊 Profile", "profile")],
        [("🏠 Main Menu", "main_menu")]
    ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')