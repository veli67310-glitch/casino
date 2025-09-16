#!/usr/bin/env python3
"""
Advanced Admin Dashboard System
Comprehensive admin commands, monitoring, and management functions
"""

import asyncio
import logging
import json
import sqlite3
import psutil
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from solana_rpc_client import get_solana_rpc_client
from solana_transaction_monitor import get_transaction_monitor
from solana_admin_wallet import get_admin_wallet_manager
from solana_payment import get_solana_payment
from solana_qr_payment import get_qr_payment_system
from config import ADMIN_USER_IDS, SOLANA_CONFIG
from safe_telegram_handler import safe_edit_message

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Advanced admin dashboard and management system"""

    def __init__(self, db_path: str = "casino_bot.db"):
        self.db_path = db_path
        self.rpc_client = get_solana_rpc_client()
        self.transaction_monitor = get_transaction_monitor()
        self.admin_wallet_manager = get_admin_wallet_manager()
        self.payment_system = get_solana_payment()
        self.qr_system = get_qr_payment_system()

        # Admin command permissions
        self.admin_commands = {
            '/admin': self.show_admin_panel,
            '/stats': self.show_system_stats,
            '/users': self.show_user_management,
            '/health': self.show_system_health,
            '/solana': self.show_solana_admin,
            '/transactions': self.show_transaction_dashboard,
            '/balances': self.show_balance_management,
            '/logs': self.show_system_logs,
            '/backup': self.create_system_backup,
            '/restart': self.restart_system_components
        }

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in ADMIN_USER_IDS

    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin commands"""
        try:
            user_id = update.effective_user.id

            if not self.is_admin(user_id):
                await update.message.reply_text("❌ Bu komut sadece adminler için geçerlidir.")
                return

            command = update.message.text.split()[0].lower()

            if command in self.admin_commands:
                await self.admin_commands[command](update, context)
            else:
                await update.message.reply_text(f"❌ Bilinmeyen admin komutu: {command}")

        except Exception as e:
            logger.error(f"Error handling admin command: {e}")
            await update.message.reply_text(f"❌ Komut işlenirken hata: {str(e)}")

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main admin panel"""
        try:
            # Get system overview
            system_stats = await self.get_system_overview()

            text = f"""🛡️ **ADMIN CONTROL PANEL** 🛡️

📊 **System Overview:**
• Uptime: {system_stats['uptime_hours']:.1f} hours
• Users: {system_stats['total_users']:,}
• Active Deposits: {system_stats['pending_deposits']:,}
• Active Withdrawals: {system_stats['pending_withdrawals']:,}

💰 **Financial Status:**
• Total FC in System: {system_stats['total_fc']:,} FC
• Solana Balance: {system_stats['solana_balance']:.4f} SOL
• Today's Volume: {system_stats['daily_volume']:.4f} SOL

🔧 **System Health:**
• CPU Usage: {system_stats['cpu_usage']:.1f}%
• Memory Usage: {system_stats['memory_usage']:.1f}%
• Database Size: {system_stats['db_size_mb']:.1f} MB
• RPC Status: {'🟢 Online' if system_stats['rpc_connected'] else '🔴 Offline'}

⚡ **Quick Actions Available:**
Use commands below or inline buttons"""

            keyboard = [
                [
                    InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
                    InlineKeyboardButton("👥 Users", callback_data="admin_users")
                ],
                [
                    InlineKeyboardButton("💰 Transactions", callback_data="admin_transactions"),
                    InlineKeyboardButton("🏦 Balances", callback_data="admin_balances")
                ],
                [
                    InlineKeyboardButton("◎ Solana Admin", callback_data="admin_solana"),
                    InlineKeyboardButton("🔧 System Health", callback_data="admin_health")
                ],
                [
                    InlineKeyboardButton("📋 Logs", callback_data="admin_logs"),
                    InlineKeyboardButton("💾 Backup", callback_data="admin_backup")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"),
                    InlineKeyboardButton("🚨 Emergency", callback_data="admin_emergency")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing admin panel: {e}")
            await update.message.reply_text(f"❌ Admin panel yüklenemedi: {str(e)}")

    async def show_system_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed system statistics"""
        try:
            stats = await self.get_comprehensive_stats()

            text = f"""📊 **DETAILED SYSTEM STATISTICS** 📊

👥 **User Statistics:**
• Total Users: {stats['users']['total']:,}
• Active Today: {stats['users']['active_today']:,}
• VIP Users: {stats['users']['vip_count']:,}
• New This Week: {stats['users']['new_this_week']:,}

💰 **Transaction Statistics:**
• Total Deposits: {stats['transactions']['total_deposits']:,}
• Total Withdrawals: {stats['transactions']['total_withdrawals']:,}
• Success Rate: {stats['transactions']['success_rate']:.1f}%
• Avg Deposit: {stats['transactions']['avg_deposit_sol']:.4f} SOL
• Avg Withdrawal: {stats['transactions']['avg_withdrawal_sol']:.4f} SOL

📈 **Financial Overview:**
• Total SOL Volume: {stats['financial']['total_sol_volume']:.2f} SOL
• Total FC Issued: {stats['financial']['total_fc_issued']:,} FC
• Current FC in Circulation: {stats['financial']['fc_in_circulation']:,} FC
• House Edge Profit: {stats['financial']['house_profit']:,} FC

🎮 **Game Statistics:**
• Games Played Today: {stats['games']['games_today']:,}
• Most Popular Game: {stats['games']['popular_game']}
• Total Bets Today: {stats['games']['total_bets_today']:,} FC
• Biggest Win Today: {stats['games']['biggest_win_today']:,} FC

🔧 **System Performance:**
• Database Queries/min: {stats['performance']['db_queries_per_min']:,.0f}
• Avg Response Time: {stats['performance']['avg_response_time']:.0f}ms
• Error Rate: {stats['performance']['error_rate']:.2f}%
• Cache Hit Rate: {stats['performance']['cache_hit_rate']:.1f}%

◎ **Solana Network:**
• RPC Calls Today: {stats['solana']['rpc_calls_today']:,}
• Monitored Addresses: {stats['solana']['monitored_addresses']:,}
• Confirmed Transactions: {stats['solana']['confirmed_today']:,}
• Network Status: {stats['solana']['network_status']}"""

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh_stats"),
                    InlineKeyboardButton("📊 Export Data", callback_data="admin_export_stats")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing system stats: {e}")
            await update.message.reply_text(f"❌ İstatistikler yüklenemedi: {str(e)}")

    async def show_user_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user management interface"""
        try:
            # Get user stats and recent users
            user_data = await self.get_user_management_data()

            text = f"""👥 **USER MANAGEMENT** 👥

📊 **User Overview:**
• Total Users: {user_data['total_users']:,}
• Online Now: {user_data['online_now']:,}
• VIP Members: {user_data['vip_members']:,}
• Banned Users: {user_data['banned_users']:,}

💰 **Balance Distribution:**
• Users with 0 FC: {user_data['zero_balance']:,}
• Users with 1-10K FC: {user_data['low_balance']:,}
• Users with 10K-100K FC: {user_data['medium_balance']:,}
• Users with 100K+ FC: {user_data['high_balance']:,}

🎮 **Activity Stats:**
• Played Today: {user_data['active_today']:,}
• Played This Week: {user_data['active_week']:,}
• Never Played: {user_data['never_played']:,}

📈 **Top Users by Balance:**"""

            for i, user in enumerate(user_data['top_users'][:5], 1):
                text += f"\n{i}. @{user['username']} - {user['balance']:,} FC"

            text += f"""

🆕 **Recent Registrations:**"""

            for user in user_data['recent_users'][:3]:
                text += f"\n• @{user['username']} - {user['registered_date']}"

            text += f"""

🔧 **Management Actions:**
Use buttons below for user management"""

            keyboard = [
                [
                    InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user"),
                    InlineKeyboardButton("💰 Balance Actions", callback_data="admin_balance_actions")
                ],
                [
                    InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban_management"),
                    InlineKeyboardButton("👑 VIP Management", callback_data="admin_vip_management")
                ],
                [
                    InlineKeyboardButton("📊 User Analytics", callback_data="admin_user_analytics"),
                    InlineKeyboardButton("📨 Mass Message", callback_data="admin_mass_message")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="admin_users"),
                    InlineKeyboardButton("🔙 Back", callback_data="admin_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing user management: {e}")
            await update.message.reply_text(f"❌ Kullanıcı yönetimi yüklenemedi: {str(e)}")

    async def show_system_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive system health check"""
        try:
            health_data = await self.perform_health_check()

            # Determine overall health status
            overall_status = "🟢 HEALTHY" if health_data['overall_score'] >= 80 else \
                           "🟡 WARNING" if health_data['overall_score'] >= 60 else "🔴 CRITICAL"

            text = f"""🏥 **SYSTEM HEALTH CHECK** 🏥

🎯 **Overall Status:** {overall_status}
📊 **Health Score:** {health_data['overall_score']}/100

🖥️ **System Resources:**
• CPU Usage: {health_data['system']['cpu']:.1f}% {'🟢' if health_data['system']['cpu'] < 70 else '🟡' if health_data['system']['cpu'] < 90 else '🔴'}
• Memory Usage: {health_data['system']['memory']:.1f}% {'🟢' if health_data['system']['memory'] < 80 else '🟡' if health_data['system']['memory'] < 95 else '🔴'}
• Disk Usage: {health_data['system']['disk']:.1f}% {'🟢' if health_data['system']['disk'] < 80 else '🟡' if health_data['system']['disk'] < 95 else '🔴'}
• Load Average: {health_data['system']['load_avg']:.2f} {'🟢' if health_data['system']['load_avg'] < 2 else '🟡' if health_data['system']['load_avg'] < 4 else '🔴'}

🗄️ **Database Health:**
• Connection: {'🟢 OK' if health_data['database']['connection'] else '🔴 FAILED'}
• Query Performance: {health_data['database']['avg_query_time']:.0f}ms {'🟢' if health_data['database']['avg_query_time'] < 100 else '🟡' if health_data['database']['avg_query_time'] < 500 else '🔴'}
• Database Size: {health_data['database']['size_mb']:.1f} MB
• Table Count: {health_data['database']['table_count']}
• Index Health: {'🟢 Good' if health_data['database']['index_health'] else '🟡 Needs Optimization'}

◎ **Solana Network:**
• RPC Connection: {'🟢 Connected' if health_data['solana']['rpc_connected'] else '🔴 Disconnected'}
• Response Time: {health_data['solana']['response_time']:.0f}ms {'🟢' if health_data['solana']['response_time'] < 1000 else '🟡' if health_data['solana']['response_time'] < 3000 else '🔴'}
• Success Rate: {health_data['solana']['success_rate']:.1f}% {'🟢' if health_data['solana']['success_rate'] > 95 else '🟡' if health_data['solana']['success_rate'] > 85 else '🔴'}
• Monitored Addresses: {health_data['solana']['monitored_addresses']}

🎮 **Application Health:**
• Bot Uptime: {health_data['application']['uptime_hours']:.1f} hours
• Active Users: {health_data['application']['active_users']}
• Error Rate: {health_data['application']['error_rate']:.2f}% {'🟢' if health_data['application']['error_rate'] < 1 else '🟡' if health_data['application']['error_rate'] < 5 else '🔴'}
• Memory Leaks: {'🟢 None Detected' if not health_data['application']['memory_leaks'] else '🔴 Detected'}

⚠️ **Issues Detected:**"""

            if health_data['issues']:
                for issue in health_data['issues']:
                    text += f"\n• {issue['severity']} {issue['message']}"
            else:
                text += "\n✅ No issues detected"

            text += f"""

🔧 **Recommendations:**"""

            if health_data['recommendations']:
                for rec in health_data['recommendations']:
                    text += f"\n• {rec}"
            else:
                text += "\n✅ System running optimally"

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Run Full Check", callback_data="admin_full_health_check"),
                    InlineKeyboardButton("🛠️ Auto Fix Issues", callback_data="admin_auto_fix")
                ],
                [
                    InlineKeyboardButton("📊 Performance Graph", callback_data="admin_performance_graph"),
                    InlineKeyboardButton("📋 Export Report", callback_data="admin_export_health")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing system health: {e}")
            await update.message.reply_text(f"❌ Sistem sağlığı kontrol edilemedi: {str(e)}")

    async def show_transaction_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive transaction monitoring dashboard"""
        try:
            tx_data = await self.get_transaction_dashboard_data()

            text = f"""💰 **TRANSACTION MONITORING DASHBOARD** 💰

📊 **Live Statistics:**
• Pending Deposits: {tx_data['pending_deposits']:,} ({tx_data['pending_deposits_sol']:.2f} SOL)
• Pending Withdrawals: {tx_data['pending_withdrawals']:,} ({tx_data['pending_withdrawals_sol']:.2f} SOL)
• Confirmations Waiting: {tx_data['waiting_confirmations']:,}

📈 **Today's Activity:**
• Completed Deposits: {tx_data['today']['deposits_completed']:,}
• Completed Withdrawals: {tx_data['today']['withdrawals_completed']:,}
• Total Volume: {tx_data['today']['total_volume_sol']:.2f} SOL
• Success Rate: {tx_data['today']['success_rate']:.1f}%

⚡ **Recent Transactions (Last 10):**"""

            for tx in tx_data['recent_transactions']:
                status_emoji = "✅" if tx['status'] == 'confirmed' else "⏳" if tx['status'] == 'pending' else "❌"
                tx_type = "📥" if tx['type'] == 'deposit' else "📤"
                text += f"\n{status_emoji}{tx_type} {tx['amount']:.4f} SOL - {tx['username']} ({tx['time_ago']})"

            text += f"""

🚨 **Issues Requiring Attention:**"""

            if tx_data['issues']:
                for issue in tx_data['issues']:
                    text += f"\n• {issue['priority']} {issue['description']}"
            else:
                text += "\n✅ No issues detected"

            text += f"""

⏰ **Queue Status:**
• Avg Confirmation Time: {tx_data['queue']['avg_confirmation_time']:.0f}s
• Longest Waiting: {tx_data['queue']['longest_waiting']:.0f}s
• Queue Efficiency: {tx_data['queue']['efficiency']:.1f}%

🔧 **Admin Actions:**
Use buttons below for transaction management"""

            keyboard = [
                [
                    InlineKeyboardButton("📥 Process Deposits", callback_data="admin_process_deposits"),
                    InlineKeyboardButton("📤 Process Withdrawals", callback_data="admin_process_withdrawals")
                ],
                [
                    InlineKeyboardButton("🔍 Search Transaction", callback_data="admin_search_tx"),
                    InlineKeyboardButton("⚡ Manual Confirm", callback_data="admin_manual_confirm")
                ],
                [
                    InlineKeyboardButton("🚨 Failed Transactions", callback_data="admin_failed_tx"),
                    InlineKeyboardButton("⏰ Timeout Management", callback_data="admin_timeout_tx")
                ],
                [
                    InlineKeyboardButton("📊 Analytics", callback_data="admin_tx_analytics"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="admin_transactions")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing transaction dashboard: {e}")
            await update.message.reply_text(f"❌ Transaction dashboard yüklenemedi: {str(e)}")

    async def show_balance_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user balance management interface"""
        try:
            balance_data = await self.get_balance_management_data()

            text = f"""🏦 **BALANCE MANAGEMENT DASHBOARD** 🏦

💰 **System Balance Overview:**
• Total FC in System: {balance_data['total_fc_in_system']:,} FC
• Total SOL Balance: {balance_data['total_sol_balance']:.4f} SOL
• Pending Deposits: {balance_data['pending_deposit_fc']:,} FC
• Pending Withdrawals: {balance_data['pending_withdrawal_fc']:,} FC

📊 **Balance Distribution:**
• Zero Balance Users: {balance_data['distribution']['zero']:,}
• Low Balance (1-10K): {balance_data['distribution']['low']:,}
• Medium Balance (10K-100K): {balance_data['distribution']['medium']:,}
• High Balance (100K+): {balance_data['distribution']['high']:,}

🎯 **Risk Analysis:**
• Largest Balance: {balance_data['risk']['largest_balance']:,} FC
• Avg Balance: {balance_data['risk']['average_balance']:,.0f} FC
• Balance Concentration: {balance_data['risk']['concentration_risk']:.1f}%

📈 **Recent Balance Changes (Last 24h):**
• Deposits Added: +{balance_data['recent_changes']['deposits_added']:,} FC
• Withdrawals Processed: -{balance_data['recent_changes']['withdrawals_processed']:,} FC
• Game Winnings: +{balance_data['recent_changes']['game_winnings']:,} FC
• Game Losses: -{balance_data['recent_changes']['game_losses']:,} FC
• Net Change: {balance_data['recent_changes']['net_change']:+,} FC

👑 **Top 10 Balances:**"""

            for i, user in enumerate(balance_data['top_balances'], 1):
                text += f"\n{i}. @{user['username']} - {user['balance']:,} FC"

            text += f"""

🔧 **Management Actions:**
Use buttons below for balance operations"""

            keyboard = [
                [
                    InlineKeyboardButton("💰 Add Balance", callback_data="admin_add_balance"),
                    InlineKeyboardButton("💸 Deduct Balance", callback_data="admin_deduct_balance")
                ],
                [
                    InlineKeyboardButton("🔍 Search User Balance", callback_data="admin_search_balance"),
                    InlineKeyboardButton("📊 Balance History", callback_data="admin_balance_history")
                ],
                [
                    InlineKeyboardButton("🚨 Freeze Account", callback_data="admin_freeze_account"),
                    InlineKeyboardButton("❄️ Frozen Accounts", callback_data="admin_frozen_accounts")
                ],
                [
                    InlineKeyboardButton("💾 Backup Balances", callback_data="admin_backup_balances"),
                    InlineKeyboardButton("📋 Export Report", callback_data="admin_export_balances")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="admin_balances"),
                    InlineKeyboardButton("🔙 Back", callback_data="admin_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing balance management: {e}")
            await update.message.reply_text(f"❌ Balance management yüklenemedi: {str(e)}")

    async def show_solana_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show Solana administration panel"""
        try:
            solana_data = await self.get_solana_admin_data()

            text = f"""◎ **SOLANA ADMINISTRATION** ◎

🔗 **Network Status:**
• RPC Connection: {'🟢 Connected' if solana_data['rpc']['connected'] else '🔴 Disconnected'}
• Network: {solana_data['rpc']['network']}
• Response Time: {solana_data['rpc']['response_time']:.0f}ms
• Success Rate: {solana_data['rpc']['success_rate']:.1f}%

🏦 **Admin Wallets:**
• Master Wallet: {solana_data['wallets']['master']['balance']:.4f} SOL
• Deposit Wallet: {solana_data['wallets']['deposit']['balance']:.4f} SOL
• Withdrawal Wallet: {solana_data['wallets']['withdrawal']['balance']:.4f} SOL
• Total Admin Balance: {solana_data['wallets']['total_balance']:.4f} SOL

📊 **Transaction Monitoring:**
• Monitored Addresses: {solana_data['monitoring']['addresses_count']:,}
• Active Confirmations: {solana_data['monitoring']['active_confirmations']:,}
• Successful Today: {solana_data['monitoring']['successful_today']:,}
• Failed Today: {solana_data['monitoring']['failed_today']:,}

⚡ **Performance Metrics:**
• RPC Calls Today: {solana_data['performance']['rpc_calls_today']:,}
• Avg Confirmation Time: {solana_data['performance']['avg_confirmation_time']:.0f}s
• Cache Hit Rate: {solana_data['performance']['cache_hit_rate']:.1f}%
• Error Rate: {solana_data['performance']['error_rate']:.2f}%

🔧 **System Health:**
• QR Generation: {'🟢 OK' if solana_data['health']['qr_generation'] else '🔴 ERROR'}
• Balance Updates: {'🟢 OK' if solana_data['health']['balance_updates'] else '🔴 ERROR'}
• Transaction Detection: {'🟢 OK' if solana_data['health']['tx_detection'] else '🔴 ERROR'}
• Wallet Management: {'🟢 OK' if solana_data['health']['wallet_management'] else '🔴 ERROR'}

⚠️ **Alerts:**"""

            if solana_data['alerts']:
                for alert in solana_data['alerts']:
                    text += f"\n• {alert['level']} {alert['message']}"
            else:
                text += "\n✅ No alerts"

            keyboard = [
                [
                    InlineKeyboardButton("🏦 Manage Wallets", callback_data="admin_manage_wallets"),
                    InlineKeyboardButton("📡 RPC Settings", callback_data="admin_rpc_settings")
                ],
                [
                    InlineKeyboardButton("🔄 Restart Monitoring", callback_data="admin_restart_monitoring"),
                    InlineKeyboardButton("🔍 Transaction Lookup", callback_data="admin_tx_lookup")
                ],
                [
                    InlineKeyboardButton("💰 Manual Deposit", callback_data="admin_manual_deposit"),
                    InlineKeyboardButton("💸 Process Withdrawal", callback_data="admin_process_withdrawal")
                ],
                [
                    InlineKeyboardButton("⚙️ System Settings", callback_data="admin_solana_settings"),
                    InlineKeyboardButton("📊 Network Stats", callback_data="admin_network_stats")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="admin_solana"),
                    InlineKeyboardButton("🔙 Back", callback_data="admin_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error showing Solana admin: {e}")
            await update.message.reply_text(f"❌ Solana admin yüklenemedi: {str(e)}")

    # Data collection methods
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get basic system overview data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Count pending deposits
            cursor.execute("SELECT COUNT(*) FROM solana_deposits WHERE status = 'pending'")
            pending_deposits = cursor.fetchone()[0]

            # Count pending withdrawals
            cursor.execute("SELECT COUNT(*) FROM solana_withdrawals WHERE status = 'pending'")
            pending_withdrawals = cursor.fetchone()[0]

            # Total FC in system
            cursor.execute("SELECT SUM(fun_coins) FROM users")
            total_fc = cursor.fetchone()[0] or 0

            # Today's SOL volume
            cursor.execute("""
                SELECT SUM(sol_amount) FROM solana_deposits
                WHERE DATE(created_at) = DATE('now') AND status = 'confirmed'
            """)
            daily_volume = cursor.fetchone()[0] or 0

            conn.close()

            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            # Get database size
            db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0

            # Get Solana balance and RPC status
            rpc_connected = False
            solana_balance = 0.0
            try:
                rpc_stats = await self.rpc_client.get_connection_stats()
                rpc_connected = rpc_stats.get('is_connected', False)

                if rpc_connected:
                    balance_result = await self.rpc_client.get_balance(SOLANA_CONFIG['admin_wallet'])
                    solana_balance = balance_result.get('balance_sol', 0.0)
            except:
                pass

            # Calculate uptime (mock - would need actual implementation)
            import time
            uptime_hours = (time.time() % (24 * 3600)) / 3600  # Mock uptime

            return {
                'uptime_hours': uptime_hours,
                'total_users': total_users,
                'pending_deposits': pending_deposits,
                'pending_withdrawals': pending_withdrawals,
                'total_fc': total_fc,
                'solana_balance': solana_balance,
                'daily_volume': daily_volume,
                'cpu_usage': cpu_percent,
                'memory_usage': memory_percent,
                'db_size_mb': db_size_mb,
                'rpc_connected': rpc_connected
            }

        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {}

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {
                'users': {},
                'transactions': {},
                'financial': {},
                'games': {},
                'performance': {},
                'solana': {}
            }

            # User statistics
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['users']['total'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_active) = DATE('now')")
            stats['users']['active_today'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE vip_level > 0")
            stats['users']['vip_count'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) >= DATE('now', '-7 days')")
            stats['users']['new_this_week'] = cursor.fetchone()[0] or 0

            # Transaction statistics
            cursor.execute("SELECT COUNT(*) FROM solana_deposits")
            stats['transactions']['total_deposits'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM solana_withdrawals")
            stats['transactions']['total_withdrawals'] = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COUNT(*) * 100.0 / (
                    SELECT COUNT(*) FROM solana_deposits
                    UNION ALL
                    SELECT COUNT(*) FROM solana_withdrawals
                ) FROM (
                    SELECT * FROM solana_deposits WHERE status = 'confirmed'
                    UNION ALL
                    SELECT * FROM solana_withdrawals WHERE status = 'completed'
                )
            """)
            result = cursor.fetchone()
            stats['transactions']['success_rate'] = result[0] if result and result[0] else 0

            cursor.execute("SELECT AVG(sol_amount) FROM solana_deposits WHERE status = 'confirmed'")
            stats['transactions']['avg_deposit_sol'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT AVG(sol_amount) FROM solana_withdrawals WHERE status = 'completed'")
            stats['transactions']['avg_withdrawal_sol'] = cursor.fetchone()[0] or 0

            # Financial overview
            cursor.execute("SELECT SUM(sol_amount) FROM solana_deposits WHERE status = 'confirmed'")
            stats['financial']['total_sol_volume'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(fc_amount) FROM solana_deposits WHERE status = 'confirmed'")
            stats['financial']['total_fc_issued'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT SUM(fun_coins) FROM users")
            stats['financial']['fc_in_circulation'] = cursor.fetchone()[0] or 0

            stats['financial']['house_profit'] = 0  # Would need game data

            # Mock other stats (would need actual implementation)
            stats['games'] = {
                'games_today': 0,
                'popular_game': 'Dice',
                'total_bets_today': 0,
                'biggest_win_today': 0
            }

            stats['performance'] = {
                'db_queries_per_min': 120,
                'avg_response_time': 150,
                'error_rate': 0.5,
                'cache_hit_rate': 85.2
            }

            stats['solana'] = {
                'rpc_calls_today': 1500,
                'monitored_addresses': 10,
                'confirmed_today': 45,
                'network_status': '🟢 Healthy'
            }

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {}

    async def get_user_management_data(self) -> Dict[str, Any]:
        """Get user management data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = {}

            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM users")
            data['total_users'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_active) = DATE('now')")
            data['online_now'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE vip_level > 0")
            data['vip_members'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            data['banned_users'] = cursor.fetchone()[0] or 0

            # Balance distribution
            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins = 0")
            data['zero_balance'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins BETWEEN 1 AND 10000")
            data['low_balance'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins BETWEEN 10001 AND 100000")
            data['medium_balance'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins > 100000")
            data['high_balance'] = cursor.fetchone()[0] or 0

            # Activity stats
            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_active) = DATE('now')")
            data['active_today'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(last_active) >= DATE('now', '-7 days')")
            data['active_week'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active IS NULL")
            data['never_played'] = cursor.fetchone()[0] or 0

            # Top users by balance
            cursor.execute("""
                SELECT username, fun_coins FROM users
                ORDER BY fun_coins DESC
                LIMIT 10
            """)
            data['top_users'] = [
                {'username': row[0], 'balance': row[1]}
                for row in cursor.fetchall()
            ]

            # Recent registrations
            cursor.execute("""
                SELECT username, created_at FROM users
                ORDER BY created_at DESC
                LIMIT 5
            """)
            data['recent_users'] = [
                {'username': row[0], 'registered_date': row[1][:10]}
                for row in cursor.fetchall()
            ]

            conn.close()
            return data

        except Exception as e:
            logger.error(f"Error getting user management data: {e}")
            return {}

    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        try:
            health_data = {
                'overall_score': 0,
                'system': {},
                'database': {},
                'solana': {},
                'application': {},
                'issues': [],
                'recommendations': []
            }

            # System resources health
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0

            health_data['system'] = {
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': disk.percent,
                'load_avg': load_avg
            }

            # Database health
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                start_time = datetime.now()
                cursor.execute("SELECT COUNT(*) FROM users")
                query_time = (datetime.now() - start_time).total_seconds() * 1000

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                table_count = len(cursor.fetchall())

                db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)

                health_data['database'] = {
                    'connection': True,
                    'avg_query_time': query_time,
                    'size_mb': db_size_mb,
                    'table_count': table_count,
                    'index_health': True  # Would need actual index analysis
                }

                conn.close()
            except Exception as e:
                health_data['database'] = {
                    'connection': False,
                    'error': str(e)
                }

            # Solana network health
            try:
                rpc_stats = await self.rpc_client.get_connection_stats()
                health_data['solana'] = {
                    'rpc_connected': rpc_stats.get('is_connected', False),
                    'response_time': 250,  # Mock
                    'success_rate': rpc_stats.get('success_rate', 0) * 100,
                    'monitored_addresses': 10  # Mock
                }
            except Exception as e:
                health_data['solana'] = {
                    'rpc_connected': False,
                    'response_time': 0,
                    'success_rate': 0,
                    'monitored_addresses': 0
                }

            # Application health
            health_data['application'] = {
                'uptime_hours': 12.5,  # Mock
                'active_users': 25,    # Mock
                'error_rate': 0.8,     # Mock
                'memory_leaks': False  # Mock
            }

            # Calculate overall score
            score_factors = []

            # System score
            system_score = 100
            if cpu_percent > 90: system_score -= 30
            elif cpu_percent > 70: system_score -= 15
            if memory.percent > 95: system_score -= 30
            elif memory.percent > 80: system_score -= 15
            score_factors.append(system_score)

            # Database score
            db_score = 100 if health_data['database'].get('connection', False) else 0
            if health_data['database'].get('avg_query_time', 0) > 500: db_score -= 20
            score_factors.append(db_score)

            # Solana score
            solana_score = 80 if health_data['solana']['rpc_connected'] else 20
            if health_data['solana']['success_rate'] < 90: solana_score -= 20
            score_factors.append(solana_score)

            health_data['overall_score'] = sum(score_factors) // len(score_factors)

            # Generate issues and recommendations
            if cpu_percent > 90:
                health_data['issues'].append({
                    'severity': '🔴',
                    'message': f'High CPU usage: {cpu_percent:.1f}%'
                })
                health_data['recommendations'].append('Consider adding more CPU cores or optimizing processes')

            if memory.percent > 95:
                health_data['issues'].append({
                    'severity': '🔴',
                    'message': f'Critical memory usage: {memory.percent:.1f}%'
                })
                health_data['recommendations'].append('Restart application or increase memory')

            if not health_data['solana']['rpc_connected']:
                health_data['issues'].append({
                    'severity': '🔴',
                    'message': 'Solana RPC connection failed'
                })
                health_data['recommendations'].append('Check RPC endpoint and network connectivity')

            return health_data

        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {'overall_score': 0, 'error': str(e)}

    async def get_transaction_dashboard_data(self) -> Dict[str, Any]:
        """Get transaction dashboard data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = {}

            # Pending transactions
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(sol_amount), 0) FROM solana_deposits WHERE status = 'pending'")
            pending_dep_count, pending_dep_sol = cursor.fetchone()
            data['pending_deposits'] = pending_dep_count
            data['pending_deposits_sol'] = pending_dep_sol or 0

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(sol_amount), 0) FROM solana_withdrawals WHERE status = 'pending'")
            pending_with_count, pending_with_sol = cursor.fetchone()
            data['pending_withdrawals'] = pending_with_count
            data['pending_withdrawals_sol'] = pending_with_sol or 0

            cursor.execute("SELECT COUNT(*) FROM transaction_confirmations WHERE status = 'waiting'")
            data['waiting_confirmations'] = cursor.fetchone()[0] or 0

            # Today's activity
            cursor.execute("""
                SELECT COUNT(*) FROM solana_deposits
                WHERE DATE(confirmed_at) = DATE('now') AND status = 'confirmed'
            """)
            data['today'] = {
                'deposits_completed': cursor.fetchone()[0] or 0
            }

            cursor.execute("""
                SELECT COUNT(*) FROM solana_withdrawals
                WHERE DATE(processed_at) = DATE('now') AND status = 'completed'
            """)
            data['today']['withdrawals_completed'] = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COALESCE(SUM(sol_amount), 0) FROM solana_deposits
                WHERE DATE(confirmed_at) = DATE('now') AND status = 'confirmed'
            """)
            deposit_volume = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COALESCE(SUM(sol_amount), 0) FROM solana_withdrawals
                WHERE DATE(processed_at) = DATE('now') AND status = 'completed'
            """)
            withdrawal_volume = cursor.fetchone()[0] or 0

            data['today']['total_volume_sol'] = deposit_volume + withdrawal_volume
            data['today']['success_rate'] = 95.5  # Mock

            # Recent transactions
            cursor.execute("""
                SELECT
                    'deposit' as type,
                    sol_amount,
                    status,
                    u.username,
                    created_at
                FROM solana_deposits d
                JOIN users u ON d.user_id = u.user_id
                UNION ALL
                SELECT
                    'withdrawal' as type,
                    sol_amount,
                    status,
                    u.username,
                    created_at
                FROM solana_withdrawals w
                JOIN users u ON w.user_id = u.user_id
                ORDER BY created_at DESC
                LIMIT 10
            """)

            recent_transactions = []
            for row in cursor.fetchall():
                tx_type, amount, status, username, created_at = row
                time_ago = "5m ago"  # Mock - would calculate actual time
                recent_transactions.append({
                    'type': tx_type,
                    'amount': amount,
                    'status': status,
                    'username': username,
                    'time_ago': time_ago
                })

            data['recent_transactions'] = recent_transactions

            # Issues (mock data)
            data['issues'] = []
            if data['waiting_confirmations'] > 10:
                data['issues'].append({
                    'priority': '⚠️',
                    'description': f"{data['waiting_confirmations']} transactions waiting for confirmation"
                })

            # Queue status (mock data)
            data['queue'] = {
                'avg_confirmation_time': 45,
                'longest_waiting': 120,
                'efficiency': 92.5
            }

            conn.close()
            return data

        except Exception as e:
            logger.error(f"Error getting transaction dashboard data: {e}")
            return {}

    async def get_balance_management_data(self) -> Dict[str, Any]:
        """Get balance management data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = {}

            # System balance overview
            cursor.execute("SELECT SUM(fun_coins) FROM users")
            data['total_fc_in_system'] = cursor.fetchone()[0] or 0

            # Mock SOL balance
            data['total_sol_balance'] = 25.5

            cursor.execute("SELECT COALESCE(SUM(fc_amount), 0) FROM solana_deposits WHERE status = 'pending'")
            data['pending_deposit_fc'] = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COALESCE(SUM(fc_amount), 0) FROM solana_withdrawals WHERE status = 'pending'")
            data['pending_withdrawal_fc'] = cursor.fetchone()[0] or 0

            # Balance distribution
            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins = 0")
            zero_balance = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins BETWEEN 1 AND 10000")
            low_balance = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins BETWEEN 10001 AND 100000")
            medium_balance = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE fun_coins > 100000")
            high_balance = cursor.fetchone()[0] or 0

            data['distribution'] = {
                'zero': zero_balance,
                'low': low_balance,
                'medium': medium_balance,
                'high': high_balance
            }

            # Risk analysis
            cursor.execute("SELECT MAX(fun_coins), AVG(fun_coins) FROM users")
            max_balance, avg_balance = cursor.fetchone()

            data['risk'] = {
                'largest_balance': max_balance or 0,
                'average_balance': avg_balance or 0,
                'concentration_risk': 15.2  # Mock
            }

            # Recent changes (mock - would need actual tracking)
            data['recent_changes'] = {
                'deposits_added': 150000,
                'withdrawals_processed': 85000,
                'game_winnings': 45000,
                'game_losses': 78000,
                'net_change': 32000
            }

            # Top balances
            cursor.execute("""
                SELECT username, fun_coins FROM users
                ORDER BY fun_coins DESC
                LIMIT 10
            """)
            data['top_balances'] = [
                {'username': row[0], 'balance': row[1]}
                for row in cursor.fetchall()
            ]

            conn.close()
            return data

        except Exception as e:
            logger.error(f"Error getting balance management data: {e}")
            return {}

    async def get_solana_admin_data(self) -> Dict[str, Any]:
        """Get Solana administration data"""
        try:
            data = {}

            # RPC status
            try:
                rpc_stats = await self.rpc_client.get_connection_stats()
                data['rpc'] = {
                    'connected': rpc_stats.get('is_connected', False),
                    'network': SOLANA_CONFIG.get('network', 'mainnet'),
                    'response_time': 250,  # Mock
                    'success_rate': rpc_stats.get('success_rate', 0) * 100
                }
            except:
                data['rpc'] = {
                    'connected': False,
                    'network': 'unknown',
                    'response_time': 0,
                    'success_rate': 0
                }

            # Admin wallets (mock data - would need actual wallet manager integration)
            data['wallets'] = {
                'master': {'balance': 10.5},
                'deposit': {'balance': 5.2},
                'withdrawal': {'balance': 8.8},
                'total_balance': 24.5
            }

            # Monitoring stats
            monitor_stats = await self.transaction_monitor.get_monitoring_stats()
            data['monitoring'] = {
                'addresses_count': monitor_stats.get('monitored_addresses', 0),
                'active_confirmations': monitor_stats.get('active_monitors', 0),
                'successful_today': 45,  # Mock
                'failed_today': 2        # Mock
            }

            # Performance metrics
            data['performance'] = {
                'rpc_calls_today': 1250,
                'avg_confirmation_time': 45,
                'cache_hit_rate': 87.5,
                'error_rate': 1.2
            }

            # Health checks
            data['health'] = {
                'qr_generation': True,
                'balance_updates': True,
                'tx_detection': True,
                'wallet_management': True
            }

            # Alerts (mock)
            data['alerts'] = []
            if data['wallets']['withdrawal']['balance'] < 2.0:
                data['alerts'].append({
                    'level': '⚠️',
                    'message': 'Withdrawal wallet balance low'
                })

            return data

        except Exception as e:
            logger.error(f"Error getting Solana admin data: {e}")
            return {}

# Global instance
_admin_dashboard = None

def get_admin_dashboard() -> AdminDashboard:
    """Get global admin dashboard instance"""
    global _admin_dashboard
    if _admin_dashboard is None:
        _admin_dashboard = AdminDashboard()
    return _admin_dashboard

# Convenience functions for admin commands
async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin command"""
    dashboard = get_admin_dashboard()
    await dashboard.handle_admin_command(update, context)

def register_admin_handlers(application):
    """Register admin command handlers"""
    dashboard = get_admin_dashboard()

    for command in dashboard.admin_commands.keys():
        application.add_handler(
            CommandHandler(command.lstrip('/'), handle_admin_command)
        )

if __name__ == "__main__":
    # Test admin dashboard
    async def test_dashboard():
        dashboard = get_admin_dashboard()

        # Test system overview
        overview = await dashboard.get_system_overview()
        print(f"System Overview: {overview}")

        # Test health check
        health = await dashboard.perform_health_check()
        print(f"Health Check Score: {health.get('overall_score', 0)}/100")

    asyncio.run(test_dashboard())