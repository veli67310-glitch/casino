#!/usr/bin/env python3
"""
🔧 Admin Panel Handlers
"""

import logging
from datetime import datetime
from safe_telegram_handler import safe_edit_message

logger = logging.getLogger(__name__)

async def show_admin_panel(query, user, casino_bot):
    """Admin panel main menu - only for authorized admins"""
    # Check admin permissions
    from config import ADMIN_USER_IDS
    if user['user_id'] not in ADMIN_USER_IDS:
        await safe_edit_message(query, 
            "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        return
    text = """
🔧 **ADMIN PANEL** 🔧

⚡ **Admin Controls**
👑 System Management

📊 **Statistics:**
• Monitor bot performance
• View user analytics
• Track financial data

👥 **User Management:**
• View user details
• Manage accounts
• Handle reports

📢 **Broadcasting:**
• Send announcements
• Notify all users
• Emergency alerts

🛠️ **System Tools:**
• Database maintenance
• Performance monitoring
• Error tracking
    """
    
    buttons = [
        [("📊 Statistics", "admin_stats"), ("👥 Users", "admin_users")],
        [("📢 Broadcast", "admin_broadcast"), ("🛠️ System", "admin_system")],
        [("◎ Solana Admin", "solana_admin")],
        [("🏠 Main Menu", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_admin_statistics(query, user, casino_bot):
    """Show admin statistics - only for authorized admins"""
    # Check admin permissions
    from config import ADMIN_USER_IDS
    if user['user_id'] not in ADMIN_USER_IDS:
        await safe_edit_message(query, 
            "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        return
    try:
        with casino_bot.db.get_connection() as conn:
            total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            active_users = conn.execute('SELECT COUNT(*) FROM users WHERE last_active > datetime("now", "-7 days")').fetchone()[0]
            total_games = conn.execute('SELECT COUNT(*) FROM solo_game_history').fetchone()[0] if hasattr(casino_bot.db, 'solo_game_history') else 0
            total_coins = conn.execute('SELECT SUM(fun_coins) FROM users').fetchone()[0] or 0
            
        text = f"""
📊 **SYSTEM STATISTICS** 📊

👥 **Users:**
• Total Registered: {total_users:,}
• Active (7 days): {active_users:,}
• Activity Rate: {(active_users/total_users*100):.1f}%

🎮 **Games:**
• Total Games Played: {total_games:,}
• Average per User: {(total_games/total_users):.1f}

🐻 **Economy:**
• Total Fun Coins: {total_coins:,} 🐻
• Average per User: {(total_coins/total_users):,.0f} 🐻

📅 **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        buttons = [
            [("🔄 Refresh", "admin_stats"), ("📈 Detailed", "admin_detailed_stats")],
            [("🔧 Admin Panel", "admin_panel"), ("🏠 Main Menu", "main_menu")]
        ]
        
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        text = f"❌ **ERROR LOADING STATS** ❌\n\nError: {str(e)}"
        buttons = [
            [("🔄 Retry", "admin_stats"), ("🔧 Admin Panel", "admin_panel")],
            [("🏠 Main Menu", "main_menu")]
        ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_admin_user_management(query, user, casino_bot):
    """Show user management panel - only for authorized admins"""
    # Check admin permissions
    from config import ADMIN_USER_IDS
    if user['user_id'] not in ADMIN_USER_IDS:
        await safe_edit_message(query, 
            "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        return
    try:
        with casino_bot.db.get_connection() as conn:
            recent_users = conn.execute('''
                SELECT user_id, username, fun_coins, level, last_active 
                FROM users 
                ORDER BY last_active DESC 
                LIMIT 10
            ''').fetchall()
            
        text = """
👥 **USER MANAGEMENT** 👥

📋 **Recent Active Users:**

"""
        buttons = []
        
        for u in recent_users:
            username = u['username'] or f"User{u['user_id']}"
            last_active = u['last_active'][:16] if u['last_active'] else "Never"
            text += f"👤 **{username}** (ID: {u['user_id']})\n"
            text += f"   🐻 {u['fun_coins']:,} 🐻 | Lv.{u['level']} | 📅 {last_active}\n\n"
            
            buttons.append([(f"🔍 {username}", f"admin_user_view_{u['user_id']}")])
        
        buttons.extend([
            [("🔍 Search User", "admin_search_user"), ("📊 User Stats", "admin_user_stats")],
            [("🔧 Admin Panel", "admin_panel"), ("🏠 Main Menu", "main_menu")]
        ])
        
    except Exception as e:
        logger.error(f"User management error: {e}")
        text = f"❌ **ERROR LOADING USERS** ❌\n\nError: {str(e)}"
        buttons = [
            [("🔄 Retry", "admin_users"), ("🔧 Admin Panel", "admin_panel")],
            [("🏠 Main Menu", "main_menu")]
        ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_admin_broadcast_menu(query, user, casino_bot):
    """Show broadcast menu - only for authorized admins"""
    # Check admin permissions
    from config import ADMIN_USER_IDS
    if user['user_id'] not in ADMIN_USER_IDS:
        await safe_edit_message(query, 
            "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        return
    text = """
📢 **BROADCAST SYSTEM** 📢

🚧 **Feature in Development** 🚧

📡 **Planned Features:**
• Send messages to all users
• Targeted announcements
• Emergency notifications
• Scheduled broadcasts

⚠️ **Important:**
Broadcasting will be implemented with proper rate limiting and user consent mechanisms.

📅 **Coming Soon!**
    """
    
    buttons = [
        [("📣 Genel Duyuru", "admin_broadcast_general"), ("🔧 Bakım Bildirimi", "admin_broadcast_maintenance")],
        [("📝 Özel Mesaj", "admin_broadcast_custom"), ("📋 Şablonlar", "admin_broadcast_templates")],
        [("🔧 Admin Panel", "admin_panel"), ("🏠 Ana Menü", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')

async def show_admin_settings(query, user, casino_bot):
    """Show admin settings menu - only for authorized admins"""
    # Check admin permissions
    from config import ADMIN_USER_IDS
    if user['user_id'] not in ADMIN_USER_IDS:
        await safe_edit_message(query, 
            "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        return
    try:
        # Get system statistics
        with casino_bot.db.get_connection() as conn:
            total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            
            # Deposits - try both table variations
            try:
                total_deposits = conn.execute('SELECT COUNT(*) FROM deposits WHERE status = "completed"').fetchone()[0]
            except:
                try:
                    total_deposits = conn.execute('SELECT COUNT(*) FROM deposits').fetchone()[0]
                except:
                    total_deposits = 0
            
            # Withdrawals - try both table variations  
            try:
                total_withdrawals = conn.execute('SELECT COUNT(*) FROM withdrawals WHERE status = "completed"').fetchone()[0]
            except:
                try:
                    total_withdrawals = conn.execute('SELECT COUNT(*) FROM withdrawals').fetchone()[0]
                except:
                    total_withdrawals = 0
            
            # Active users today - use user_activity table or fallback
            try:
                active_today = conn.execute('''
                    SELECT COUNT(DISTINCT user_id) FROM user_activity 
                    WHERE DATE(timestamp) = DATE('now')
                ''').fetchone()[0]
            except:
                # Fallback: count users who played games today
                try:
                    active_today = conn.execute('''
                        SELECT COUNT(DISTINCT user_id) FROM solo_game_history 
                        WHERE DATE(timestamp) = DATE('now')
                    ''').fetchone()[0]
                except:
                    active_today = 0
        
        text = f"""
⚙️ **SİSTEM AYARLARI** ⚙️

📊 **Sistem Durumu:**
• 👥 Toplam Kullanıcı: {total_users:,}
• 🐻 Toplam Yatırım: {total_deposits:,}
• 💸 Toplam Çekim: {total_withdrawals:,}
• 🔥 Bugün Aktif: {active_today:,}

🔧 **Mevcut Ayarlar:**
• 🐻 Min. Yatırım: 1,000 🐻
• 💸 Min. Çekim: 5,000 🐻
• 🎰 Max. Bahis: 1,000,000 🐻
• 👑 VIP Seviyeleri: Aktif

⚠️ **Güvenlik:**
• API Rate Limit: Aktif
• Anti-Spam: Aktif
• Admin Log: Aktif

🛠️ **Gelişmiş Ayarlar:**
• Maintenance Mode: Kapalı
• Debug Mode: Kapalı
• Test Mode: Aktif
        """
        
        buttons = [
            [("🐻 Para Ayarları", "admin_money_settings"), ("🎮 Oyun Ayarları", "admin_game_settings")],
            [("👑 VIP Ayarları", "admin_vip_settings"), ("🔐 Güvenlik", "admin_security_settings")],
            [("🛠️ Sistem", "admin_system_settings"), ("📊 Logları Görüntüle", "admin_view_logs")],
            [("🔧 Admin Panel", "admin_panel"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await safe_edit_message(query, text, keyboard, "Admin Settings")
        
    except Exception as e:
        logger.error(f"Admin settings error: {e}")
        try:
            await safe_edit_message(query, 
                f"❌ **HATA**\n\n🚫 Ayarlar yüklenirken hata oluştu.\n\n📝 **Detay:** {str(e)}",
                reply_markup=casino_bot.create_keyboard([[("🔧 Admin Panel", "admin_panel"), ("🏠 Ana Menü", "main_menu")]])
            )
        except:
            pass

async def safe_edit_message(query, text, keyboard, context_name="Unknown"):
    """Safely edit message, ignoring 'message not modified' errors"""
    try:
        await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as edit_error:
        # Ignore "message not modified" errors
        if "Message is not modified" in str(edit_error):
            logger.debug(f"{context_name}: Message content unchanged, skipping update")
        else:
            raise edit_error

def log_user_activity(casino_bot, user_id: int, activity_type: str, details: str = None):
    """Log user activity to database"""
    try:
        with casino_bot.db.get_connection() as conn:
            conn.execute('''
                INSERT INTO user_activity (user_id, activity_type, details)
                VALUES (?, ?, ?)
            ''', (user_id, activity_type, details))
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log user activity: {e}")

async def handle_admin_user_action(query, user, action, target_user_id, casino_bot):
    """Handle admin user actions - only for authorized admins"""
    # Check admin permissions
    from config import ADMIN_USER_IDS
    if user['user_id'] not in ADMIN_USER_IDS:
        await safe_edit_message(query, 
            "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        return
    try:
        if action == "view":
            with casino_bot.db.get_connection() as conn:
                target_user = conn.execute('SELECT * FROM users WHERE user_id = ?', (target_user_id,)).fetchone()
                
            if target_user:
                text = f"""
👤 **USER DETAILS** 👤

🆔 **ID:** {target_user['user_id']}
👤 **Username:** {target_user['username'] or 'None'}
🐻 **Balance:** {target_user['fun_coins']:,} 🐻
🏆 **Level:** {target_user['level']}
⭐ **XP:** {target_user['xp']}
🎮 **Games:** {target_user['games_count']}
🔥 **Streak:** {target_user['win_streak']}
📅 **Joined:** {target_user['created_at'][:10]}
⏰ **Last Active:** {target_user['last_active'][:16] if target_user['last_active'] else 'Never'}

🆔 **Friend Code:** {target_user['friend_code']}
                """
                
                buttons = [
                    [("🐻 Adjust Coins", f"admin_user_coins_{target_user_id}"), ("🏆 Set Level", f"admin_user_level_{target_user_id}")],
                    [("🔒 Suspend", f"admin_user_suspend_{target_user_id}"), ("📊 Full Report", f"admin_user_report_{target_user_id}")],
                    [("👥 Back to Users", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
                ]
            else:
                text = "❌ **USER NOT FOUND** ❌"
                buttons = [
                    [("👥 Back to Users", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
                ]
        
        elif action in ["coins", "level", "suspend", "report"]:
            text = f"""
🚧 **ADMIN ACTION: {action.upper()}** 🚧

⚠️ **Feature in Development**

🛡️ **Safety First:**
Advanced admin actions are being implemented with:
• Action logging
• Confirmation dialogs  
• Audit trails
• Rollback capabilities

📅 **Coming Soon!**
            """
            buttons = [
                [("👥 Back to Users", "admin_users"), ("🔧 Admin Panel", "admin_panel")],
                [("🏠 Main Menu", "main_menu")]
            ]
        else:
            text = "❌ **INVALID ACTION** ❌"
            buttons = [
                [("🔧 Admin Panel", "admin_panel"), ("🏠 Main Menu", "main_menu")]
            ]
            
    except Exception as e:
        logger.error(f"Admin user action error: {e}")
        text = f"❌ **ACTION ERROR** ❌\n\nError: {str(e)}"
        buttons = [
            [("👥 Back to Users", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
        ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, text, reply_markup=keyboard, parse_mode='Markdown')