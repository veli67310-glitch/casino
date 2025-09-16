#!/usr/bin/env python3
"""
🎉 Bonus Casino Bot Features - Interactive Elements
"""

import random
import asyncio
from datetime import datetime
from visual_assets import (
    CASINO_STICKERS, EMOJI_ANIMATIONS, EMOJI_COMBOS, 
    PROGRESSIVE_ANIMATIONS, get_win_sticker, get_random_celebration,
    create_animated_message, UI_EMOJIS
)

async def show_daily_spinner(query, user, casino_bot):
    """Daily luck spinner with enhanced animations"""
    # Check if user already spun today
    conn = casino_bot.db.get_connection()
    cursor = conn.cursor()
    try:
        last_spin = cursor.execute('SELECT last_daily_bonus FROM users WHERE user_id = ?', (user['user_id'],)).fetchone()
        if last_spin and last_spin[0]:
            last_date = datetime.fromisoformat(last_spin[0]).date()
            if last_date == datetime.now().date():
                await query.edit_message_text(
                    "🎪 **DAILY SPINNER** 🎪\n\n❌ **Already spun today!**\n\n🕐 **Come back tomorrow for another spin!**",
                    reply_markup=casino_bot.create_keyboard([
                        [("🏠 Main Menu", "main_menu")]
                    ])
                )
                return
    finally:
        conn.close()
    
    # Enhanced spinning animation with visual assets
    spin_frames = [
        f"🎰 |   {EMOJI_ANIMATIONS['slot_spinning'][0]}   | 🎰",
        f"🎰 |   {EMOJI_ANIMATIONS['slot_spinning'][1]}   | 🎰", 
        f"🎰 |   {EMOJI_ANIMATIONS['slot_spinning'][2]}   | 🎰",
        f"🎰 |   {EMOJI_ANIMATIONS['slot_result'][0]}   | 🎰",
        f"🎰 |   {EMOJI_ANIMATIONS['slot_result'][1]}   | 🎰",
        f"🎰 |   {EMOJI_ANIMATIONS['slot_result'][2]}   | 🎰"
    ]
    
    # Start spinning animation
    for i, frame in enumerate(spin_frames):
        spin_text = f"""
🎪 **DAILY LUCK SPINNER** 🎪

🐻 **Current Balance:** {user['fun_coins']:,} 🐻

{frame}

🎲 **Spinning...** {i+1}/{len(spin_frames)}
        """
        await query.edit_message_text(spin_text, parse_mode='Markdown')
        await asyncio.sleep(0.5)
    
    # Determine reward with enhanced visual feedback
    luck_value = random.random()
    if luck_value < 0.01:  # 1% - Mega jackpot
        reward = random.randint(10000, 25000)
        reward_type = "🌟 MEGA JACKPOT! 🌟"
        special_effect = f"{EMOJI_COMBOS['slot_jackpot']}\n🎆🎊🎉 INCREDIBLE LUCK! 🎉🎊🎆"
        celebration_sticker = CASINO_STICKERS['mega_win']
    elif luck_value < 0.05:  # 4% - Big reward
        reward = random.randint(5000, 10000)
        reward_type = "💎 BIG WIN! 💎"
        special_effect = f"{EMOJI_COMBOS['slot_big_win']}\n✨🔥 AMAZING SPIN! 🔥✨"
        celebration_sticker = CASINO_STICKERS['big_win']
    elif luck_value < 0.15:  # 10% - Good reward
        reward = random.randint(2000, 5000)
        reward_type = "🎁 GREAT SPIN! 🎁"
        special_effect = f"{EMOJI_COMBOS['daily_bonus']}\n🌈⭐ NICE LUCK! ⭐🌈"
        celebration_sticker = CASINO_STICKERS['daily_bonus']
    elif luck_value < 0.40:  # 25% - Medium reward
        reward = random.randint(1000, 2000)
        reward_type = "🍀 GOOD LUCK! 🍀"
        special_effect = f"{EMOJI_COMBOS['slot_win']}\n🎯💫 SOLID SPIN! 💫🎯"
        celebration_sticker = CASINO_STICKERS['slot_win']
    else:  # 60% - Standard reward
        reward = random.randint(100, 1000)
        reward_type = "🎪 DAILY BONUS! 🎪"
        special_effect = "🎈🎵 Thanks for playing! 🎵🎈"
    
    # Update user balance and last spin
    conn = casino_bot.db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET fun_coins = fun_coins + ?, last_daily_bonus = CURRENT_TIMESTAMP WHERE user_id = ?',
                   (reward, user['user_id']))
        conn.commit()
    finally:
        conn.close()
    
    # Final result with enhanced display
    final_text = f"""
🎪 **DAILY LUCK SPINNER** 🎪

{special_effect}

🎯 **RESULT:** {reward_type}
🐻 **Reward:** {reward:,} 🐻
💎 **New Balance:** {user['fun_coins'] + reward:,} 🐻

🎊 **Congratulations!** Your luck has been rewarded!

⏰ **Next spin:** Tomorrow at same time
🍀 **Keep playing to increase your luck!**
    """
    
    await query.edit_message_text(
        final_text,
        reply_markup=casino_bot.create_keyboard([
            [("🎮 Play Games", "solo_games"), ("🐻 Check Balance", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]),
        parse_mode='Markdown'
    )

async def show_fortune_wheel(query, user, casino_bot):
    """Interactive fortune wheel with various rewards"""
    # Define wheel segments
    wheel_segments = [
        {"reward": 500, "type": "coins", "emoji": "🐻", "name": "Coins"},
        {"reward": 1000, "type": "coins", "emoji": "💎", "name": "Gems"}, 
        {"reward": 2000, "type": "coins", "emoji": "🎁", "name": "Gift"},
        {"reward": 100, "type": "xp", "emoji": "⭐", "name": "XP Boost"},
        {"reward": 1500, "type": "coins", "emoji": "🍀", "name": "Lucky"},
        {"reward": 3000, "type": "coins", "emoji": "🎆", "name": "Jackpot"},
        {"reward": 0, "type": "none", "emoji": "😅", "name": "Try Again"},
        {"reward": 5000, "type": "coins", "emoji": "🏆", "name": "MEGA WIN"}
    ]
    
    # Spinning animation with wheel
    spin_animations = [
        "🎡 Spinning the Fortune Wheel... 🎡",
        "🌟 ↗️  🐻  ↖️ 🎁\n   ↘️  🎯  ↙️\n🍀 ↙️  ⭐  ↘️ 🎆",
        "🌟 ↗️  🎁  ↖️ 🐻\n   ↘️  🎯  ↙️\n🍀 ↙️  🎆  ↘️ ⭐",
        "🌟 ↗️  ⭐  ↖️ 🎁\n   ↘️  🎯  ↙️\n🍀 ↙️  🐻  ↘️ 🎆",
    ]
    
    for i, animation in enumerate(spin_animations):
        wheel_text = f"""
🎡 **FORTUNE WHEEL** 🎡

🐻 **Current Balance:** {user['fun_coins']:,} 🐻

{animation}

🎯 **Spinning...** {i+1}/{len(spin_animations)}
        """
        await query.edit_message_text(wheel_text, parse_mode='Markdown')
        await asyncio.sleep(0.8)
    
    # Select random segment
    selected = random.choice(wheel_segments)
    
    # Apply reward
    if selected["type"] == "coins":
        conn = casino_bot.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                       (selected["reward"], user['user_id']))
            conn.commit()
        finally:
            conn.close()
        reward_text = f"🐻 **+{selected['reward']:,} 🐻**"
    elif selected["type"] == "xp":
        conn = casino_bot.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET xp = xp + ? WHERE user_id = ?',
                       (selected["reward"], user['user_id']))
            conn.commit()
        finally:
            conn.close()
        reward_text = f"⭐ **+{selected['reward']} XP**"
    else:
        reward_text = "🎯 **Better luck next time!**"
    
    # Final result
    result_text = f"""
🎡 **FORTUNE WHEEL RESULT** 🎡

🎯 **Landed on:** {selected['emoji']} **{selected['name']}**

{reward_text}

💎 **New Balance:** {user['fun_coins'] + (selected['reward'] if selected['type'] == 'coins' else 0):,} 🐻

🎊 Thanks for spinning the Fortune Wheel!
    """
    
    await query.edit_message_text(
        result_text,
        reply_markup=casino_bot.create_keyboard([
            [("🔄 Spin Again", "fortune_wheel"), ("🎮 Play Games", "solo_games")],
            [("🏠 Main Menu", "main_menu")]
        ]),
        parse_mode='Markdown'
    )

async def show_mystery_box(query, user, casino_bot):
    """Mystery box opening with surprises"""
    # Check if user has enough coins to open (cost: 500 🐻)
    box_cost = 500
    if user['fun_coins'] < box_cost:
        await query.edit_message_text(
            f"📦 **MYSTERY BOX** 📦\n\n❌ **Insufficient funds!**\n\n🐻 **Cost:** {box_cost:,} 🐻\n💎 **Your balance:** {user['fun_coins']:,} 🐻",
            reply_markup=casino_bot.create_keyboard([
                [("🏠 Main Menu", "main_menu")]
            ])
        )
        return
    
    # Opening animation
    opening_frames = [
        "📦 Mystery Box is shaking...",
        "📦✨ Opening the box...",
        "📦💫 Something is glowing inside...",
        "📦🌟 Almost open...",
        "📦💥 BOX OPENED!"
    ]
    
    for i, frame in enumerate(opening_frames):
        box_text = f"""
📦 **MYSTERY BOX OPENING** 📦

🐻 **Cost:** {box_cost:,} 🐻

{frame}

🎁 **Opening...** {i+1}/{len(opening_frames)}
        """
        await query.edit_message_text(box_text, parse_mode='Markdown')
        await asyncio.sleep(0.7)
    
    # Deduct cost first
    conn = casino_bot.db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?',
                   (box_cost, user['user_id']))
        conn.commit()
    finally:
        conn.close()
    
    # Determine rewards
    mystery_rewards = []
    total_value = 0
    
    # Main reward (80% chance good, 20% chance amazing)
    if random.random() < 0.2:  # Amazing reward
        main_reward = random.randint(2000, 8000)
        mystery_rewards.append(f"💎 {main_reward:,} 🐻 (RARE!)")
        total_value += main_reward
    else:  # Good reward
        main_reward = random.randint(600, 2000)
        mystery_rewards.append(f"🐻 {main_reward:,} 🐻")
        total_value += main_reward
    
    # Bonus items (50% chance)
    if random.random() < 0.5:
        bonus_xp = random.randint(50, 200)
        mystery_rewards.append(f"⭐ {bonus_xp} XP")
        conn = casino_bot.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET xp = xp + ? WHERE user_id = ?',
                       (bonus_xp, user['user_id']))
            conn.commit()
        finally:
            conn.close()
    
    # Super rare item (5% chance)
    if random.random() < 0.05:
        super_bonus = random.randint(5000, 15000)
        mystery_rewards.append(f"🏆 {super_bonus:,} 🐻 (LEGENDARY!)")
        total_value += super_bonus
    
    # Apply coin rewards
    if total_value > 0:
        conn = casino_bot.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                       (total_value, user['user_id']))
            conn.commit()
        finally:
            conn.close()
    
    # Calculate profit/loss
    net_result = total_value - box_cost
    new_balance = user['fun_coins'] - box_cost + total_value
    
    result_text = f"""
📦 **MYSTERY BOX OPENED!** 📦

🎁 **Your Rewards:**
{chr(10).join(mystery_rewards)}

🐻 **Total Value:** {total_value:,} 🐻
💸 **Cost:** -{box_cost:,} 🐻
{'💚' if net_result > 0 else '💔'} **Net Result:** {net_result:+,} 🐻

💎 **New Balance:** {new_balance:,} 🐻

{'🎉 Congratulations on your profit!' if net_result > 0 else '🍀 Better luck next time!'}
    """
    
    await query.edit_message_text(
        result_text,
        reply_markup=casino_bot.create_keyboard([
            [("📦 Open Another", "mystery_box"), ("🎮 Play Games", "solo_games")],
            [("🏠 Main Menu", "main_menu")]
        ]),
        parse_mode='Markdown'
    )

async def show_achievement_showcase(query, user, casino_bot):
    """Show user achievements with animations"""
    conn = casino_bot.db.get_connection()
    cursor = conn.cursor()
    try:
        # Get user achievements
        achievements = cursor.execute('''
            SELECT achievement_id, unlocked_at FROM user_achievements
            WHERE user_id = ? ORDER BY unlocked_at DESC
        ''', (user['user_id'],)).fetchall()

        # Get total possible achievements
        from config import ACHIEVEMENTS
        total_achievements = len(ACHIEVEMENTS)
        unlocked_count = len(achievements)
    finally:
        conn.close()
    
    # Progress calculation
    progress_percentage = (unlocked_count / total_achievements * 100) if total_achievements > 0 else 0
    progress_bar = "▰" * (unlocked_count // 2) + "▱" * ((total_achievements - unlocked_count) // 2)
    
    # Recent achievements display
    recent_text = ""
    if achievements:
        for i, ach in enumerate(achievements[:5]):  # Show last 5
            ach_data = ACHIEVEMENTS.get(ach['achievement_id'], {})
            name = ach_data.get('name', 'Unknown')
            emoji = ach_data.get('emoji', '🏆')
            recent_text += f"{emoji} **{name}**\n"
    else:
        recent_text = "🎯 **No achievements yet - start playing to unlock them!**"
    
    showcase_text = f"""
🏆 **ACHIEVEMENT SHOWCASE** 🏆

👤 **Player:** {user['username']}

📊 **Progress:** {unlocked_count}/{total_achievements} ({progress_percentage:.1f}%)
{progress_bar}

🎖️ **Recent Achievements:**
{recent_text}

🌟 **Achievement Categories:**
🎮 **Gaming:** Win streaks, game mastery
🐻 **Wealth:** Coin milestones, big wins  
👥 **Social:** Friends, tournaments
⭐ **Special:** Rare events, perfect games

🎯 **Keep playing to unlock more achievements!**
    """
    
    await query.edit_message_text(
        showcase_text,
        reply_markup=casino_bot.create_keyboard([
            [("🎮 Play Games", "solo_games"), ("📊 Full List", "achievements")],
            [("🏠 Main Menu", "main_menu")]
        ]),
        parse_mode='Markdown'
    )

async def show_mega_win_celebration(query, win_amount, bet_amount, casino_bot):
    """Show epic celebration for mega wins"""
    try:
        multiplier = win_amount / bet_amount if bet_amount > 0 else 0
        
        # Progressive celebration animation
        if multiplier >= 100:
            celebration_sequence = PROGRESSIVE_ANIMATIONS['jackpot_buildup']
            final_sticker = CASINO_STICKERS['mega_win']
            celebration_emoji = EMOJI_COMBOS['slot_jackpot']
        elif multiplier >= 50:
            celebration_sequence = PROGRESSIVE_ANIMATIONS['big_win_buildup']
            final_sticker = CASINO_STICKERS['big_win']
            celebration_emoji = EMOJI_COMBOS['slot_big_win']
        else:
            celebration_sequence = PROGRESSIVE_ANIMATIONS['level_up_sequence']
            final_sticker = CASINO_STICKERS['celebration']
            celebration_emoji = EMOJI_COMBOS['slot_win']
        
        # Show celebration sequence
        for i, message in enumerate(celebration_sequence):
            await asyncio.sleep(0.8)
            await query.edit_message_text(f"{message}\n\n🎰 Kazanç: {win_amount:,} 🐻", parse_mode='Markdown')
        
        # Final celebration message
        final_celebration = f"""
{celebration_emoji}

🎊 **MUHTEŞEM KAZANÇ!** 🎊

🐻 **Kazandığınız:** {win_amount:,} 🐻
🎯 **Bahis:** {bet_amount:,} 🐻  
⚡ **Çarpan:** x{multiplier:.1f}

{get_random_celebration()} BRAVO! {get_random_celebration()}

🎮 Bu momentum ile devam edin!
        """
        
        buttons = [
            [("🎰 Tekrar Oyna", "solo_games"), ("💎 Profil", "profile")],
            [("🎁 Bonuslar", "bonus_features"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(final_celebration, reply_markup=keyboard, parse_mode='Markdown')
        
        # Send celebration sticker
        try:
            await query.message.reply_sticker(final_sticker)
        except:
            pass
            
    except Exception as e:
        print(f"Mega win celebration error: {e}")

async def show_streak_milestone(query, streak_count, casino_bot):
    """Show special animation for win streak milestones"""
    try:
        if streak_count >= 20:
            milestone_text = f"{EMOJI_COMBOS['streak_bonus']}\n🔥🔥🔥 LEGENDARY STREAK! 🔥🔥🔥"
            sticker = CASINO_STICKERS['mega_win']
        elif streak_count >= 10:
            milestone_text = f"{EMOJI_COMBOS['achievement_unlock']}\n🔥🔥 INCREDIBLE STREAK! 🔥🔥"
            sticker = CASINO_STICKERS['big_win']
        elif streak_count >= 5:
            milestone_text = f"{EMOJI_COMBOS['level_up']}\n🔥 HOT STREAK! 🔥"
            sticker = CASINO_STICKERS['celebration']
        else:
            return  # No milestone
        
        streak_message = f"""
{milestone_text}

🏆 **{streak_count} OYUN ÜSTÜSTE KAZANÇ!** 🏆

⚡ Bu momentum ile devam edin!
🎯 Bir sonraki hedef: {(streak_count // 5 + 1) * 5} oyun
        """
        
        # Show streak celebration
        await query.message.reply_text(streak_message, parse_mode='Markdown')
        
        # Send celebration sticker
        try:
            await query.message.reply_sticker(sticker)
        except:
            pass
            
    except Exception as e:
        print(f"Streak milestone error: {e}")

async def show_level_up_celebration(query, new_level, casino_bot):
    """Show level up celebration with visual effects"""
    try:
        # Level up animation sequence
        level_sequence = [
            "📈 XP hesaplanıyor...",
            "📈⬆️ Seviye kontrolü...",
            "📈⬆️🔥 Yeni seviye açılıyor...",
            f"📈⬆️🔥💪 SEVİYE {new_level}! 💪🔥⬆️📈"
        ]
        
        for message in level_sequence:
            await asyncio.sleep(0.6)
            await query.edit_message_text(message, parse_mode='Markdown')
        
        # Final level up message
        level_celebration = f"""
{EMOJI_COMBOS['level_up']}

🎉 **SEVİYE YÜKSELTİLDİ!** 🎉

🏆 **Yeni Seviye:** {new_level}
⭐ **Hediye XP:** {new_level * 100}
💎 **Seviye Bonusu:** {new_level * 500} 🐻

💪 **Yeni Avantajlarınız:**
• %{new_level * 2} daha fazla XP
• Günlük bonus artışı
• Özel oyunlara erişim

{get_random_celebration()} Tebrikler! {get_random_celebration()}
        """
        
        buttons = [
            [("🎁 Hediye Al", "daily_bonus"), ("🎮 Oyunlar", "solo_games")],
            [("📊 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(level_celebration, reply_markup=keyboard, parse_mode='Markdown')
        
        # Send level up sticker
        try:
            await query.message.reply_sticker(CASINO_STICKERS['celebration'])
        except:
            pass
            
    except Exception as e:
        print(f"Level up celebration error: {e}")