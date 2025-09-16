#!/usr/bin/env python3
"""
🎮 Casino Bot Diğer İşleyiciler (Arkadaşlık, Başarım, vb.) - FIXED VERSION
"""

import json
import logging
from config import ACHIEVEMENTS, GAMES
from safe_telegram_handler import safe_edit_message

logger = logging.getLogger(__name__)

async def show_daily_quests(query, user, casino_bot):
    """Günlük görevler"""
    quests = casino_bot.get_daily_quests(user['user_id'])
    
    text = "🎁 **GÜNLÜK GÖREVLER** 🎁\n\n"
    
    for quest in quests:
        status = "✅" if quest['completed'] else "⏳"
        progress = f"{quest['progress']}/{quest['target']}"
        text += f"{status} **{quest['quest_type'].replace('_', ' ').title()}:** {progress} 🐻 {quest['reward']}\n"
    
    text += "\n🌟 Yeni görev: Arkadaş davet et!"
    
    buttons = [
        [("🎮 Oyna", "solo_games"), ("📊 Profil", "profile")],
        [("🏠 Ana Menü", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_achievements(query, user, casino_bot):
    """Başarımlar sayfası"""
    text = "🏅 **BAŞARIMLAR** 🏅\n\n"
    
    with casino_bot.db.get_connection() as conn:
        unlocked = [a['achievement_id'] for a in conn.execute('SELECT achievement_id FROM user_achievements WHERE user_id = ?', (user['user_id'],)).fetchall()]
    
    for ach_id, ach in ACHIEVEMENTS.items():
        status = "✅" if ach_id in unlocked else "🔒"
        text += f"{status} {ach['emoji']} **{ach['name']}** 🐻 {ach['reward']}\n"
    
    text += f"\n📊 Tamamlanan: {len(unlocked)}/{len(ACHIEVEMENTS)} 🌟"
    
    buttons = [
        [("🎮 Oyna", "solo_games"), ("📊 Profil", "profile")],
        [("🏠 Ana Menü", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_leaderboard(query, casino_bot, period="all_time"):
    """Enhanced leaderboard with daily, weekly, monthly periods"""
    with casino_bot.db.get_connection() as conn:
        if period == "daily":
            # Top performers by today's winnings
            leaders = conn.execute('''
                SELECT u.username, u.fun_coins, u.level, 
                       COALESCE(SUM(sh.win_amount - sh.bet_amount), 0) as daily_profit
                FROM users u 
                LEFT JOIN solo_game_history sh ON u.user_id = sh.user_id 
                AND DATE(sh.played_at) = DATE('now')
                GROUP BY u.user_id 
                ORDER BY daily_profit DESC, u.fun_coins DESC 
                LIMIT 10
            ''').fetchall()
            title = "🏆 **GÜNLÜK LİDER TABLOSU** 🏆"
            desc = "📅 *Bugünkü en başarılı oyuncular*"
        elif period == "weekly":
            # Top performers by this week's winnings
            leaders = conn.execute('''
                SELECT u.username, u.fun_coins, u.level,
                       COALESCE(SUM(sh.win_amount - sh.bet_amount), 0) as weekly_profit
                FROM users u 
                LEFT JOIN solo_game_history sh ON u.user_id = sh.user_id 
                AND DATE(sh.played_at) >= DATE('now', '-7 days')
                GROUP BY u.user_id 
                ORDER BY weekly_profit DESC, u.fun_coins DESC 
                LIMIT 10
            ''').fetchall()
            title = "🏆 **HAFTALIK LİDER TABLOSU** 🏆"
            desc = "📅 *Bu haftanın en başarılı oyuncuları*"
        elif period == "monthly":
            # Top performers by this month's winnings
            leaders = conn.execute('''
                SELECT u.username, u.fun_coins, u.level,
                       COALESCE(SUM(sh.win_amount - sh.bet_amount), 0) as monthly_profit
                FROM users u 
                LEFT JOIN solo_game_history sh ON u.user_id = sh.user_id 
                AND DATE(sh.played_at) >= DATE('now', '-30 days')
                GROUP BY u.user_id 
                ORDER BY monthly_profit DESC, u.fun_coins DESC 
                LIMIT 10
            ''').fetchall()
            title = "🏆 **AYLIK LİDER TABLOSU** 🏆"
            desc = "📅 *Bu ayın en başarılı oyuncuları*"
        else:  # all_time
            leaders = conn.execute('''
                SELECT username, fun_coins, level, total_won 
                FROM users ORDER BY fun_coins DESC LIMIT 10
            ''').fetchall()
            title = "🏆 **GENEL LİDER TABLOSU** 🏆"
            desc = "🐻 *En zengin oyuncular*"
    
    text = f"{title}\n{desc}\n\n"
    
    emojis = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    for i, leader in enumerate(leaders):
        username = leader['username'] or 'Anonim'
        balance = leader['fun_coins']
        level = leader['level']
        
        if period in ["daily", "weekly", "monthly"]:
            profit_key = f"{period}_profit"
            profit = leader[profit_key] if profit_key in leader.keys() else 0
            text += f"{emojis[i]} **{username}** 🐻 {balance:,} 📈 +{profit:,} Lv.{level}\n"
        else:
            total_won = leader['total_won'] if 'total_won' in leader.keys() and leader['total_won'] else 0
            text += f"{emojis[i]} **{username}** 🐻 {balance:,} 🏆 {total_won:,} Lv.{level}\n"
    
    # Period selection buttons
    period_buttons = [
        [("📅 Günlük", "leaderboard_daily"), ("📆 Haftalık", "leaderboard_weekly")],
        [("🗓️ Aylık", "leaderboard_monthly"), ("🏆 Genel", "leaderboard_all")]
    ]
    
    # Add current period indicator
    current_indicators = {
        "daily": "📅 ▶️",
        "weekly": "📆 ▶️", 
        "monthly": "🗓️ ▶️",
        "all_time": "🏆 ▶️"
    }
    
    # Update button text to show current selection
    for row in period_buttons:
        for i, (text_btn, callback) in enumerate(row):
            if (period == "daily" and "Günlük" in text_btn) or \
               (period == "weekly" and "Haftalık" in text_btn) or \
               (period == "monthly" and "Aylık" in text_btn) or \
               (period == "all_time" and "Genel" in text_btn):
                row[i] = (f"▶️ {text_btn}", callback)
    
    buttons = period_buttons + [
        [("⚔️ Düello", "create_duel"), ("🏆 Turnuva", "tournaments")],
        [("🏠 Ana Menü", "main_menu")]
    ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_tournaments(query, user, casino_bot):
    """Tournament page - Coming Soon"""
    text = """🏆 **TOURNAMENTS** 🏆

🚧 **Coming Soon!** 🚧

🎊 **Upcoming Features:**
• Weekly Tournaments - Massive prize pools
• Live Leaderboards - Real-time rankings  
• Special Events - Seasonal competitions
• Team Battles - Group vs Group
• Championship Series - Multi-round tournaments

⏰ **Stay tuned for the biggest casino tournaments!**

🎮 **In the meantime, enjoy our solo games and duels!**
    """
    
    buttons = [
        [("🎮 Solo Games", "solo_games"), ("⚔️ Create Duel", "create_duel")],
        [("🎯 Join Duel", "join_duel"), ("📊 Leaderboard", "leaderboard")],
        [("🏠 Main Menu", "main_menu")]
    ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_friends(query, user, casino_bot):
    """Arkadaşlar sayfası"""
    try:
        with casino_bot.db.get_connection() as conn:
            friends = conn.execute('''SELECT u.username, u.level FROM friendships f 
                JOIN users u ON (CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END) = u.user_id 
                WHERE (f.user1_id = ? OR f.user2_id = ?) AND f.status = "accepted"''', 
                (user['user_id'], user['user_id'], user['user_id'])).fetchall()
        
            text = "👥 **ARKADAŞLAR** 👥\n\n"
            for friend in friends:
                text += f"👤 {friend['username']} Lv.{friend['level']}\n"
            
            if not friends:
                text += "😢 Arkadaşın yok!\n\n"
                text += f"🆔 **Arkadaş Kodun:** `{user['friend_code'] if 'friend_code' in user.keys() and user['friend_code'] else 'ERROR'}`\n"
                text += "• Kodunu paylaş ve arkadaş edinin!"
            
            buttons = [
                [("➕ Ekle", "add_friend"), ("📬 İstekler", "friend_requests")],
                [("🏠 Ana Menü", "main_menu")]
            ]
            keyboard = casino_bot.create_keyboard(buttons)
            
            await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Friends menu error: {e}")
        await safe_edit_message(query, 
            "❌ Arkadaş listesi yüklenemedi!",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )

async def show_add_friend_menu(query, user, casino_bot):
    """Arkadaş ekleme menüsü - FIXED"""
    try:
        # Ensure user has friend_code
        friend_code = user['friend_code'] if 'friend_code' in user.keys() and user['friend_code'] else None
        if not friend_code:
            # Generate friend code if missing
            with casino_bot.db.get_connection() as conn:
                import random
                import string
                friend_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                conn.execute('UPDATE users SET friend_code = ? WHERE user_id = ?', (friend_code, user['user_id']))
                conn.commit()
                user['friend_code'] = friend_code
        
        text = f"""👥 **ARKADAŞ & REFERANS SİSTEMİ** 👥

🆔 **Senin Referans Kodun:** `{friend_code}`

🎯 **SİSTEM NASIL ÇALIŞIR:**
• Kodunu paylaş, yeni üyeler kazan! 🎁
• Yeni üye referans kodunla kayıt olsun
• Sen 500 🐻 bonus, o 1000 🐻 bonus alır!
• O her oynadığında %5 komisyon kazanırsın! 🐻

📈 **KAZANÇLARİN:**
• Kayıt bonusu: 500 🐻 (her referans için)
• Sürekli komisyon: %5 (her bahisten)
• Sınırsız kazanç potansiyeli!

🔗 **PAYLAŞIM METNİ:** 
*Casino Bot'ta beraber oynayalım! Referans kodum: {friend_code} 🎮*

💡 Kod gir, arkadaş ol ve beraber kazan!"""
        
        buttons = [
            [("🔍 Kod Gir", "enter_friend_code"), ("📊 Referans İstatistik", "referral_stats")],
            [("📬 Gelen İstekler", "friend_requests")],
            [("👥 Arkadaşlarım", "friends"), ("🏠 Ana Menü", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        # Fallback safe version without markdown
        simple_text = f"👥 ARKADAŞ EKLE\n\n🆔 Kodun: {user['friend_code'] if 'friend_code' in user.keys() and user['friend_code'] else 'ERROR'}\n\n📋 Kodunu paylaş ve arkadaş ekle!"
        
        buttons = [
            [("🔍 Kod Gir", "enter_friend_code")],
            [("👥 Arkadaşlar", "friends"), ("🏠 Ana Menü", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_edit_message(query, simple_text, reply_markup=keyboard)

async def show_referral_stats(query, user, casino_bot):
    """Referans istatistikleri sayfası"""
    try:
        stats = casino_bot.get_referral_stats(user['user_id'])
        
        text = "📊 **REFERANS İSTATİSTİKLERİ & KAZANÇLARIN** 📊\n\n"
        
        # Referral summary with enhanced visual
        text += f"💎 **TOPLAM KOMİSYON KAZANCIN:** {stats['total_commission']:,} 🐻\n"
        text += f"👥 **AKTİF REFERANSLAR:** {stats['total_referrals']} kişi\n\n"
        
        # Commission rate info
        if stats['total_referrals'] > 0:
            avg_commission = stats['total_commission'] // stats['total_referrals']
            text += f"📈 **Ortalama Referans Başı Kazanç:** {avg_commission:,} 🐻\n"
        
        # Show who referred this user
        if stats['referred_by']:
            text += f"🤝 **Seni Referans Eden:** @{stats['referred_by']}\n"
        
        text += "\n" + "="*30 + "\n\n"
        
        # List referrals with enhanced info
        if stats['referrals']:
            text += "👥 **REFERANS LİSTESİ:**\n\n"
            for i, ref in enumerate(stats['referrals'][:5], 1):  # Show top 5
                commission = ref['total_commission_earned']
                join_date = ref['created_at'][:10] if ref['created_at'] else "N/A"
                text += f"{i}. 👤 **{ref['username']}**\n"
                text += f"   🐻 {commission:,} 🐻 komisyon\n"
                text += f"   📅 Katılım: {join_date}\n\n"
            
            if len(stats['referrals']) > 5:
                text += f"... ve **{len(stats['referrals']) - 5} referans** daha! 🎯\n\n"
            
            text += "🔥 **Aktif referansların seni her oyunda zenginleştiriyor!**"
        else:
            text += "🚀 **İLK REFERANSINI KAZAN!**\n\n"
            text += "💡 **Referans Nasıl Kazanılır:**\n"
            text += "• 🔗 Arkadaş kodunu sosyal medyada paylaş\n"
            text += "• 💬 Gruplarda arkadaşlarını davet et\n"
            text += "• 🎁 Her yeni üye = 500 🐻 + sürekli %5 komisyon!\n"
            text += "• 📈 Onlar oynadıkça sen de kazanırsın!\n\n"
            text += "🏆 **Hedef:** İlk 10 referansını topla!"
        
        buttons = [
            [("➕ Arkadaş Ekle", "add_friend"), ("👥 Arkadaşlar", "friends")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Referral stats error: {e}")
        await safe_edit_message(query, 
            "❌ Referans istatistikleri yüklenemedi!",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )

async def show_friend_requests_menu(query, user, casino_bot):
    """Arkadaş istekleri menüsü"""
    try:
        requests = casino_bot.get_friend_requests(user['user_id'])
        
        if not requests:
            text = """📬 **ARKADAŞLİK İSTEKLERİ** 📬

😢 Bekleyen istek yok. 😢

💡 **Arkadaş Bul:** 
• Kodunu paylaş! 
• Oyunlarda tanış!"""
            
            buttons = [
                [("👥 Arkadaş Ekle", "add_friend")],
                [("🏠 Ana Menü", "main_menu")]
            ]
        else:
            text = "📬 **BEKLEYEN İSTEKLER** 📬\n\n"
            buttons = []
            
            for req in requests[:5]:  # Max 5
                username = req['username'] or f"Oyuncu{req['user1_id']}"
                text += f"👤 **{username}** (Lv.{req['level']}) 📅 {req['created_at'][:10]}\n"
                
                buttons.append([
                    (f"✅ Kabul Et", f"accept_friend_{req['user1_id']}"),
                    (f"❌ Reddet", f"reject_friend_{req['user1_id']}")
                ])
            
            buttons.append([("🔄 Yenile", "friend_requests"), ("🏠 Ana Menü", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Friend requests error: {e}")
        await safe_edit_message(query, 
            "❌ Arkadaş istekleri yüklenemedi!",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )

# Simple versions for fallback
async def show_simple_daily_quests(query, user, casino_bot):
    """Simple daily quests fallback"""
    await show_daily_quests(query, user, casino_bot)

async def show_simple_achievements(query, user, casino_bot):
    """Simple achievements fallback"""
    await show_achievements(query, user, casino_bot)

async def show_simple_leaderboard(query, user, casino_bot):
    """Simple leaderboard fallback"""
    await show_leaderboard(query, casino_bot)

async def show_simple_friends_menu(query, user, casino_bot):
    """Simple friends menu fallback"""
    await show_friends(query, user, casino_bot)

async def show_tournament_menu(query, user, casino_bot):
    """Tournament menu"""
    await show_tournaments(query, user, casino_bot)

async def show_events_menu(query, user, casino_bot):
    """Events menu"""
    text = """🎉 **SPECIAL EVENTS** 🎉

🚧 Coming Soon! 🚧

🎊 **Upcoming Events:**
• Weekend Bonus - +50% rewards
• Lucky Hour - Double XP  
• Mega Jackpot Tournament
• Friend Referral Contest

📅 Stay tuned for announcements!"""
    
    buttons = [
        [("🏆 Tournaments", "tournaments"), ("🎁 Daily Bonus", "daily_bonus")],
        [("🏠 Main Menu", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def handle_accept_friend(query, user, friend_id, casino_bot):
    """Accept friend request"""
    try:
        with casino_bot.db.get_connection() as conn:
            conn.execute(
                'UPDATE friendships SET status = "accepted" WHERE user1_id = ? AND user2_id = ?',
                (friend_id, user['user_id'])
            )
            conn.commit()
            
        await safe_edit_message(query, 
            "✅ **FRIEND ADDED!** ✅\n\n🎉 You now have a new friend!",
            reply_markup=casino_bot.create_keyboard([
                [("👥 My Friends", "friends"), ("📬 Requests", "friend_requests")],
                [("🏠 Main Menu", "main_menu")]
            ]),
            parse_mode='Markdown'
        )
    except Exception as e:
        await safe_edit_message(query, 
            f"❌ Error adding friend: {e}",
            reply_markup=casino_bot.create_keyboard([
                [("🔄 Try Again", "friend_requests"), ("🏠 Main Menu", "main_menu")]
            ])
        )

async def handle_reject_friend(query, user, friend_id, casino_bot):
    """Reject friend request"""
    try:
        with casino_bot.db.get_connection() as conn:
            conn.execute(
                'DELETE FROM friendships WHERE user1_id = ? AND user2_id = ?',
                (friend_id, user['user_id'])
            )
            conn.commit()
            
        await safe_edit_message(query, 
            "❌ **FRIEND REQUEST DECLINED** ❌\n\n🗑 Request has been removed.",
            reply_markup=casino_bot.create_keyboard([
                [("📬 View Requests", "friend_requests"), ("👥 My Friends", "friends")],
                [("🏠 Main Menu", "main_menu")]
            ]),
            parse_mode='Markdown'
        )
    except Exception as e:
        await safe_edit_message(query, 
            f"❌ Error rejecting friend: {e}",
            reply_markup=casino_bot.create_keyboard([
                [("🔄 Try Again", "friend_requests"), ("🏠 Main Menu", "main_menu")]
            ])
        )

async def handle_create_tournament(query, user, tournament_type, casino_bot):
    """Create tournament - IMPLEMENTED"""
    try:
        # Basic tournament configuration
        tournament_configs = {
            "slots": {"name": "Slots Şampiyonası", "buy_in": 1000, "game_type": "solo_slots"},
            "blackjack": {"name": "Blackjack Turnuvası", "buy_in": 5000, "game_type": "solo_blackjack"},
            "roulette": {"name": "Roulette Showdown", "buy_in": 2500, "game_type": "solo_roulette"},
            "crash": {"name": "Crash Turnuvası", "buy_in": 10000, "game_type": "solo_crash"}
        }
        
        config = tournament_configs.get(tournament_type)
        if not config:
            await safe_edit_message(query, 
                "❌ Geçersiz turnuva türü!",
                reply_markup=casino_bot.create_keyboard([[("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]])
            )
            return
        
        # Check user balance
        if user['fun_coins'] < config['buy_in']:
            await safe_edit_message(query, 
                f"💸 Yetersiz bakiye!\n\n🏆 **{config['name']}** için {config['buy_in']:,} 🐻 gerekli.\n🐻 Mevcut bakiye: {user['fun_coins']:,} 🐻",
                reply_markup=casino_bot.create_keyboard([
                    [("💳 Yatırım Yap", "deposit_menu"), ("🎁 Günlük Bonus", "daily_bonus")],
                    [("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
        
        # Create tournament  
        tournament_id = casino_bot.create_tournament(
            user['user_id'], 
            config['game_type'], 
            config['buy_in'], 
            config['name']
        )
        
        if tournament_id:
            # Deduct buy-in
            with casino_bot.db.get_connection() as conn:
                conn.execute('UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?', 
                           (config['buy_in'], user['user_id']))
                conn.commit()
            
            text = f"""
🏆 **TURNUVA OLUŞTURULDU!** 🏆

🎮 **Turnuva:** {config['name']}
🐻 **Buy-in:** {config['buy_in']:,} 🐻
🆔 **ID:** {tournament_id[-8:]}
👤 **Oluşturan:** @{user['username'] if 'username' in user else 'Anonim'}

⏰ **Durum:** Katılımcı bekleniyor...
👥 **Katılımcılar:** 1/16

🎯 **Nasıl çalışır:**
• Minimum 4 kişi gerekli
• En yüksek skor kazanır  
• Ödül havuzu katılımcılara dağıtılır

📢 **Arkadaşlarını davet et!**
            """
            
            buttons = [
                [("📋 Turnuva Listesi", "tournaments"), ("👥 Arkadaş Davet", "friends")],
                [("🎮 Solo Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]
            ]
        else:
            text = "❌ Turnuva oluşturulamadı! Lütfen tekrar deneyin."
            buttons = [
                [("🔄 Tekrar Dene", f"create_tournament_{tournament_type}"), ("🏆 Turnuvalar", "tournaments")],
                [("🏠 Ana Menü", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Create tournament error: {e}")
        await safe_edit_message(query, 
            "❌ Turnuva oluşturulurken hata oluştu!",
            reply_markup=casino_bot.create_keyboard([[("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]])
        )

async def handle_join_tournament(query, user, tournament_id, casino_bot):
    """Join tournament - IMPLEMENTED"""
    try:
        with casino_bot.db.get_connection() as conn:
            # Get tournament info
            tournament = conn.execute(
                'SELECT * FROM tournaments WHERE tournament_id = ?', 
                (tournament_id,)
            ).fetchone()
            
            if not tournament:
                await safe_edit_message(query, 
                    "❌ Turnuva bulunamadı!",
                    reply_markup=casino_bot.create_keyboard([[("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]])
                )
                return
            
            # Check if tournament is still open
            if tournament['status'] != 'open':
                await safe_edit_message(query, 
                    f"⏰ Bu turnuva artık katılıma kapalı!\n\n📊 **Durum:** {tournament['status']}",
                    reply_markup=casino_bot.create_keyboard([[("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]])
                )
                return
            
            # Check user balance
            if user['fun_coins'] < tournament['buy_in']:
                await safe_edit_message(query, 
                    f"💸 Yetersiz bakiye!\n\n🏆 **{tournament['name']}** için {tournament['buy_in']:,} 🐻 gerekli.\n🐻 Mevcut bakiye: {user['fun_coins']:,} 🐻",
                    reply_markup=casino_bot.create_keyboard([
                        [("💳 Yatırım Yap", "deposit_menu"), ("🎁 Günlük Bonus", "daily_bonus")],
                        [("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]
                    ])
                )
                return
            
            # Join tournament
            success = casino_bot.join_tournament(tournament_id, user['user_id'])
            
            if success:
                # Deduct buy-in
                conn.execute('UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?', 
                           (tournament['buy_in'], user['user_id']))
                conn.commit()
                
                # Get updated participants
                updated_tournament = conn.execute(
                    'SELECT * FROM tournaments WHERE tournament_id = ?', 
                    (tournament_id,)
                ).fetchone()
                
                participants = json.loads(updated_tournament['participants']) if updated_tournament['participants'] else []
                
                text = f"""
✅ **TURNUVAYA KATILDIN!** ✅

🏆 **Turnuva:** {tournament['name']}
🐻 **Buy-in:** {tournament['buy_in']:,} 🐻 ödendi
👥 **Katılımcılar:** {len(participants)}/16
🏆 **Güncel Ödül Havuzu:** {updated_tournament['prize_pool']:,} FC

🎮 **Durum:** {"Başlamak üzere!" if len(participants) >= 4 else "Daha fazla katılımcı bekleniyor..."}

⏰ **Başlama Zamanı:** {tournament['start_time'] if 'start_time' in tournament.keys() and tournament['start_time'] else 'Yakında'}

🎯 **Başarı İpuçları:**
• En yüksek skoru yapmaya odaklan
• Riskleri hesapla
• Strateji geliştir
                """
                
                buttons = [
                    [("📋 Turnuva Detayları", "tournaments"), ("🎮 Pratik Yap", "solo_games")],
                    [("👥 Arkadaş Davet", "friends"), ("🏠 Ana Menü", "main_menu")]
                ]
            else:
                text = """
❌ **TURNUVAYA KATILINAMADI!** ❌

🚫 **Olası nedenler:**
• Turnuva dolu
• Zaten katılmışsın
• Turnuva başlamış

🔄 Başka turnuvalara göz at!
                """
                
                buttons = [
                    [("🏆 Diğer Turnuvalar", "tournaments"), ("🆕 Yeni Turnuva", "create_tournament")],
                    [("🏠 Ana Menü", "main_menu")]
                ]
            
            keyboard = casino_bot.create_keyboard(buttons)
            await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Join tournament error: {e}")
        await safe_edit_message(query, 
            "❌ Turnuvaya katılırken hata oluştu!",
            reply_markup=casino_bot.create_keyboard([[("🏆 Turnuvalar", "tournaments"), ("🏠 Ana Menü", "main_menu")]])
        )

async def show_invite_friends_menu(query, user, casino_bot):
    """Arkadaş davet etme menüsü"""
    try:
        # Ensure user has friend_code
        friend_code = user['friend_code'] if 'friend_code' in user.keys() and user['friend_code'] else None
        if not friend_code:
            # Generate friend code if missing
            with casino_bot.db.get_connection() as conn:
                import random
                import string
                friend_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                conn.execute('UPDATE users SET friend_code = ? WHERE user_id = ?', (friend_code, user['user_id']))
                conn.commit()
                user['friend_code'] = friend_code
        
        text = f"""📧 **ARKADAŞ DAVET MENÜSÜ** 📧

🆔 **Davet Kodun:** `{friend_code}`

🎯 **Arkadaş Davet Et:**
• Kodunu arkadaşlarınla paylaş
• Yeni üyeler kazan ve bonus al
• Sürekli komisyon kazan

🐻 **Kazançların:**
• Her referans için 500 🐻 bonus
• %5 sürekli komisyon
• Sınırsız kazanç potansiyeli

📱 **Kolay Paylaşım Metni:**
*🎮 Casino Bot'ta beraber oynayalım! Referans kodum: {friend_code}*"""
        
        buttons = [
            [("➕ Ekle", "add_friend"), ("📬 İstekler", "friend_requests")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Invite friends menu error: {e}")
        # Fallback safe version
        simple_text = f"📧 ARKADAŞ DAVET\n\n🆔 Kodun: {user['friend_code'] if 'friend_code' in user.keys() and user['friend_code'] else 'ERROR'}\n\n📋 Kodunu paylaş ve arkadaş davet et!"
        
        buttons = [
            [("➕ Ekle", "add_friend"), ("📬 İstekler", "friend_requests")],
            [("🏠 Ana Menü", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_edit_message(query, simple_text, reply_markup=keyboard)