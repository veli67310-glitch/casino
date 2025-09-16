#!/usr/bin/env python3
"""
Enhanced Casino Bot with CryptoBot Integration and Max Bet Limits - FIXED VERSION
"""

import asyncio
import logging
import json
import time
import sys
import os
import warnings
from datetime import datetime, timedelta
import threading
import gc

# Suppress specific warnings
warnings.filterwarnings("ignore", message="coroutine.*was never awaited")
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Enable tracemalloc with memory limit
import tracemalloc
tracemalloc.start(10)
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TimedOut, NetworkError
import httpx

# Fix import errors
try:
    from casino_bot import MultiplayerCasino
    from config import BOT_TOKEN, CRYPTO_BOT_TOKEN, CRYPTO_TESTNET, PAYMENT_SETTINGS, VIP_LEVELS, CRYPTO_RATES, REQUIRED_GROUP_USERNAME, REQUIRED_GROUP_URL, REQUIRED_GROUP_ID, GAMES
    from menu_handlers import show_main_menu
    from solo_games import SoloGameEngine
    from admin_handlers import show_admin_settings

    # Optional imports
    try:
        from cryptobot_payment import CryptoBotPaymentProcessor, CasinoPaymentManager
        CRYPTO_AVAILABLE = True
    except ImportError:
        print("WARNING: CryptoBot module not found - payment system disabled")
        CRYPTO_AVAILABLE = False

except ImportError as e:
    print(f"ERROR: Critical Import Error: {e}")
    print("ERROR: Basic configuration files missing!")
    sys.exit(1)

# Import critical callback handler functions at global scope
try:
    from bonus_menu_handler import show_bonus_features_menu
    BONUS_MENU_AVAILABLE = True
except ImportError:
    print("WARNING: bonus_menu_handler not found")
    BONUS_MENU_AVAILABLE = False

try:
    from payment_handlers import show_payment_menu
    PAYMENT_HANDLERS_AVAILABLE = True
except ImportError:
    print("WARNING: payment_handlers not found")
    PAYMENT_HANDLERS_AVAILABLE = False

try:
    from game_handlers import handle_solo_game, handle_create_duel, handle_join_game
    from enhanced_game_handlers import handle_enhanced_solo_game
    from bonus_features import show_daily_spinner, show_fortune_wheel, show_mystery_box, show_achievement_showcase
    from other_handlers import (show_daily_quests, show_achievements, show_leaderboard, show_tournaments, show_friends,
                               show_simple_daily_quests, show_simple_achievements, show_simple_leaderboard,
                               show_simple_friends_menu, show_tournament_menu, show_events_menu,
                               show_add_friend_menu, show_friend_requests_menu, handle_accept_friend, handle_reject_friend,
                               handle_create_tournament, handle_join_tournament)
    from solana_handlers import (show_solana_payment_menu, show_solana_deposit_menu,
                               handle_solana_deposit, show_solana_withdraw_menu, handle_wallet_selection,
                               show_withdrawal_wallet_input, process_solana_withdrawal,
                               show_solana_help, check_solana_deposit_status,
                               check_solana_withdrawal_status, show_user_wallet_stats,
                               show_cryptobot_payment_menu)
    from solana_admin import (show_solana_admin_panel, show_pending_withdrawals,
                            approve_withdrawal, reject_withdrawal, show_solana_rate_update,
                            update_solana_rate, show_solana_stats)
    from menu_handlers import (show_create_duel_menu, show_join_duel_menu, show_enhanced_profile,
                              show_enhanced_solo_games_menu, show_enhanced_solo_game_options, handle_simple_solo_game)
    from admin_handlers import (show_admin_panel, show_admin_statistics, show_admin_user_management,
                               show_admin_broadcast_menu, handle_admin_user_action)
    HANDLERS_AVAILABLE = True
except ImportError:
    print("WARNING: Some handler modules not found - using basic functionality")
    HANDLERS_AVAILABLE = False

# Logging setup - Fixed with UTF-8 encoding
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('casino_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Fix console encoding for Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
logger = logging.getLogger(__name__)

def is_admin_user(user_id: int) -> bool:
    """Check if user is admin - reads from config.py"""
    from config import ADMIN_USER_IDS
    return user_id in ADMIN_USER_IDS

def is_group_chat(update: Update) -> bool:
    """Check if the current chat is a group or supergroup"""
    chat_type = update.effective_chat.type
    return chat_type in ['group', 'supergroup']

class EnhancedCasinoBot:
    """Enhanced Casino Bot with CryptoBot payments and max bet limits"""
    
    def __init__(self):
        try:
            self.casino = MultiplayerCasino()
            logger.info("SUCCESS: Casino system initialized")
        except Exception as e:
            logger.error(f"ERROR: Casino initialization failed: {e}")
            raise
        
        # Start CryptoBot handler - add error control
        if CRYPTO_AVAILABLE:
            try:
                self.crypto_processor = CryptoBotPaymentProcessor(CRYPTO_BOT_TOKEN, CRYPTO_TESTNET)
                self.payment_manager = CasinoPaymentManager(self.crypto_processor, self.casino.db)
                logger.info("SUCCESS: CryptoBot integration initialized")
            except Exception as e:
                logger.error(f"WARNING: CryptoBot initialization failed: {e}")
                self.crypto_processor = None
                self.payment_manager = None
        else:
            self.crypto_processor = None
            self.payment_manager = None
            logger.info("WARNING: CryptoBot module missing - payment system disabled")
        
        # Add payment manager to casino for easy access
        if self.payment_manager:
            self.casino.payment_manager = self.payment_manager
        
        # Initialize Solana payment system (lazy initialization)
        self.solana_system = None
        self._solana_initialized = False
        
        # Enhanced bet limits with user-specific calculation
        self.max_bet_limits = {
            'default': 100000,  # Default max bet
            'vip1': 250000,     # VIP 1 max bet
            'vip2': 500000,     # VIP 2 max bet  
            'vip3': 1000000,    # VIP 3 max bet
            'vip4': 2000000,    # VIP 4 max bet
            'vip5': 5000000,    # VIP 5 max bet
        }
        
        # High-performance group system for 100+ concurrent users
        try:
            from group_performance_optimizer import (
                initialize_group_performance, group_performance_manager, 
                optimized_group_handler
            )
            from group_performance_monitor import get_performance_monitor
            
            self.perf_manager, self.optimized_handler = initialize_group_performance()
            self.performance_monitor = get_performance_monitor()
            self.performance_monitor.start_monitoring()
            
            logger.info("High-performance group system with monitoring initialized")
        except ImportError:
            logger.warning("WARNING: Group performance optimizer not found - using legacy system")
            self.perf_manager = None
            self.optimized_handler = None
            self.performance_monitor = None
        
        # Legacy group game lock system (kept for compatibility)
        self.group_game_locks = {}  # chat_id: {'user_id': user_id, 'game_type': str, 'timestamp': time.time()}
        self.group_locks_lock = threading.Lock()  # Thread-safe access to group_game_locks
        
        # Performance cache for frequently accessed data
        self.cache = {}
        self.cache_expiry = {}  # Cache expiry times
        self.last_cache_cleanup = time.time()
        
        # Auto payment processing settings
        self.auto_payment_enabled = True
        self.payment_check_interval = 30  # seconds
        self.last_payment_check = 0
        
        # Transaction cache for performance - with limits
        self.pending_transactions = {}
        self.max_pending_transactions = 500
        
        # Bot health monitoring
        self.bot_start_time = datetime.now()
        self.total_commands_processed = 0
        
    def get_user_vip_level(self, user_id: int) -> int:
        """Get user's VIP level based on total deposits - with caching"""
        cache_key = f"vip_{user_id}"
        current_time = time.time()
        
        # Check cache first
        if cache_key in self.cache and current_time < self.cache_expiry.get(cache_key, 0):
            return self.cache[cache_key]
            
        if not self.payment_manager:
            return 0
            
        try:
            stats = self.payment_manager.get_user_payment_stats(user_id)
            total_deposited = stats['total_deposits']
            
            vip_level = 0
            for level, requirements in VIP_LEVELS.items():
                if total_deposited >= requirements['min_deposit']:
                    vip_level = level
            
            # Cache result for 5 minutes
            self.cache[cache_key] = vip_level
            self.cache_expiry[cache_key] = current_time + 300
            
            return vip_level
        except Exception as e:
            logger.error(f"VIP level calculation error: {e}")
            return 0
    
    def get_user_max_bet(self, user_id: int) -> int:
        """Get user's maximum bet limit based on VIP status"""
        vip_level = self.get_user_vip_level(user_id)
        return self.get_user_max_bet_by_vip(vip_level)
    
    def get_user_max_bet_by_vip(self, vip_level: int) -> int:
        """Get max bet by VIP level directly"""
        if vip_level >= 5:
            return self.max_bet_limits['vip5']
        elif vip_level >= 4:
            return self.max_bet_limits['vip4']
        elif vip_level >= 3:
            return self.max_bet_limits['vip3']
        elif vip_level >= 2:
            return self.max_bet_limits['vip2']
        elif vip_level >= 1:
            return self.max_bet_limits['vip1']
        else:
            return self.max_bet_limits['default']
    
    def create_keyboard(self, buttons):
        """Create inline keyboard for bot messages"""
        return self.casino.create_keyboard(buttons)
    
    def validate_bet_amount(self, user_id: int, bet_amount: int, user_balance: int) -> dict:
        """Enhanced bet validation with VIP-based limits and balance checks"""
        
        # Basic validation
        if bet_amount <= 0:
            return {
                'valid': False,
                'reason': "ERROR: Bet amount must be positive!"
            }
        
        # Basic balance check
        if bet_amount > user_balance:
            return {
                'valid': False,
                'reason': f"💸 Insufficient balance! Current: {user_balance:,} 🐻"
            }
        
        # Get user's max bet limit
        max_bet = self.get_user_max_bet(user_id)
        if bet_amount > max_bet:
            vip_level = self.get_user_vip_level(user_id)
            return {
                'valid': False,
                'reason': f"🚫 Your maximum bet limit: {max_bet:,} 🐻 (VIP {vip_level})"
            }
        
        # Balance ratio check (max 10% of balance in single bet)
        max_balance_bet = int(user_balance * PAYMENT_SETTINGS.get('max_bet_ratio', 0.1))
        if bet_amount > max_balance_bet:
            return {
                'valid': False,
                'reason': f"WARNING: Maximum {int(PAYMENT_SETTINGS.get('max_bet_ratio', 0.1)*100)}% of balance can be bet: {max_balance_bet:,} 🐻"
            }
        
        # Use payment manager's additional checks if available
        if self.payment_manager:
            try:
                payment_check = self.payment_manager.check_bet_limits(user_id, bet_amount, user_balance)
                if not payment_check['allowed']:
                    return {
                        'valid': False,
                        'reason': payment_check['reason']
                    }
            except Exception as e:
                logger.error(f"Payment manager bet check error: {e}")
                # Continue without payment manager checks
        
        return {'valid': True, 'reason': None}
    
    def acquire_group_game_lock(self, chat_id, user_id, game_type):
        """Acquire a game lock for a group. Returns True if successful, False if someone else is playing."""
        with self.group_locks_lock:
            current_time = time.time()
            
            # Clean up expired locks (older than 5 minutes)
            if chat_id in self.group_game_locks:
                if current_time - self.group_game_locks[chat_id]['timestamp'] > 300:
                    del self.group_game_locks[chat_id]
            
            # Check if group is already locked by someone else
            if chat_id in self.group_game_locks:
                current_lock = self.group_game_locks[chat_id]
                if current_lock['user_id'] != user_id:
                    return False, current_lock
            
            # Acquire lock
            self.group_game_locks[chat_id] = {
                'user_id': user_id,
                'game_type': game_type,
                'timestamp': current_time
            }
            return True, None
    
    def release_group_game_lock(self, chat_id, user_id):
        """Release a game lock for a group"""
        with self.group_locks_lock:
            if chat_id in self.group_game_locks:
                if self.group_game_locks[chat_id]['user_id'] == user_id:
                    del self.group_game_locks[chat_id]
    
    def get_group_game_status(self, chat_id):
        """Get current game status for a group"""
        with self.group_locks_lock:
            if chat_id in self.group_game_locks:
                return self.group_game_locks[chat_id]
            return None
    
    def get_cached_or_fetch(self, key, fetch_func, ttl=60):
        """Get cached data or fetch and cache new data"""
        current_time = time.time()
        
        # Check if we have valid cached data
        if key in self.cache and key in self.cache_expiry:
            if current_time < self.cache_expiry[key]:
                return self.cache[key]
        
        # Fetch new data and cache it
        data = fetch_func()
        self.cache[key] = data
        self.cache_expiry[key] = current_time + ttl
        return data
    
    async def get_cached_or_fetch_async(self, key, fetch_func, ttl=60):
        """Get cached data or fetch and cache new data (async version)"""
        current_time = time.time()
        
        # Periodic cache cleanup to prevent memory bloat
        if current_time - self.last_cache_cleanup > 300:  # Every 5 minutes
            self.cleanup_expired_cache()
            self.last_cache_cleanup = current_time
        
        # Check if we have valid cached data
        if key in self.cache and key in self.cache_expiry:
            if current_time < self.cache_expiry[key]:
                return self.cache[key]
        
        # Fetch new data and cache it
        data = await fetch_func()
        self.cache[key] = data
        self.cache_expiry[key] = current_time + ttl
        return data
    
    def cleanup_expired_cache(self):
        """Clean up expired cache entries - optimized"""
        current_time = time.time()
        expired_keys = [k for k, expire_time in self.cache_expiry.items() if current_time > expire_time]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_expiry.pop(key, None)
        
        # Memory optimization: limit cache size
        if len(self.cache) > 1000:
            # Remove oldest 10% of entries
            sorted_keys = sorted(self.cache_expiry.keys(), key=lambda k: self.cache_expiry[k])[:100]
            for key in sorted_keys:
                self.cache.pop(key, None)
                self.cache_expiry.pop(key, None)
            # Force garbage collection after cleanup
            gc.collect()
        
        # Clean up telegram cache as well
        try:
            from safe_telegram_handler import cleanup_telegram_cache
            cleanup_telegram_cache()
        except ImportError:
            pass
            
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def process_pending_payments(self):
        """Auto-process pending payments with error handling"""
        if not self.auto_payment_enabled or not self.crypto_handler:
            return
            
        # Rate limiting - only check every 30 seconds
        current_time = time.time()
        if current_time - self.last_payment_check < self.payment_check_interval:
            return
        
        self.last_payment_check = current_time
        
        try:
            with self.casino.db.get_connection() as conn:
                # Check pending deposits (only recent ones)
                pending_deposits = conn.execute(
                    '''SELECT * FROM deposits 
                       WHERE status = "pending" 
                       AND datetime(created_at, '+1 hour') > datetime('now')
                       LIMIT 20'''
                ).fetchall()
                
                logger.info(f"🔍 Checking {len(pending_deposits)} pending deposits")
                
                # Limit processing to prevent memory overload
                if len(pending_deposits) > 100:
                    pending_deposits = pending_deposits[:100]
                    logger.warning("Too many pending deposits, processing first 100 only")
                
                for deposit in pending_deposits:
                    # Memory check for pending transactions
                    if len(self.pending_transactions) >= self.max_pending_transactions:
                        # Remove oldest transactions
                        old_keys = list(self.pending_transactions.keys())[:100]
                        for key in old_keys:
                            self.pending_transactions.pop(key, None)
                    
                    try:
                        # Check payment status with CryptoBot
                        invoices = self.crypto_handler.get_invoices(
                            asset=deposit['currency'],
                            status='paid'
                        )
                        
                        if invoices.get('ok') and invoices.get('result'):
                            for invoice in invoices['result']:
                                if invoice['invoice_id'] == deposit['invoice_id']:
                                    await self.credit_user_deposit(deposit)
                                    logger.info(f"SUCCESS: Payment confirmed for user {deposit['user_id']}: {deposit['fun_coins']} 🐻")
                                    break
                    except Exception as e:
                        logger.error(f"Error checking deposit {deposit['id']}: {e}")
                        continue
                
                # Mark expired deposits
                expired_count = conn.execute(
                    '''UPDATE deposits SET status = 'expired' 
                       WHERE status = 'pending' AND 
                       datetime(created_at, '+1 hour') < datetime('now')'''
                ).rowcount
                
                if expired_count > 0:
                    logger.info(f"⏰ Marked {expired_count} deposits as expired")
                    conn.commit()
                
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
    
    async def credit_user_deposit(self, deposit):
        """Credit user account after successful payment with bonuses"""
        try:
            with self.casino.db.get_connection() as conn:
                # Check if already processed
                current_status = conn.execute(
                    'SELECT status FROM deposits WHERE id = ?',
                    (deposit['id'],)
                ).fetchone()
                
                if current_status and current_status['status'] != 'pending':
                    return  # Already processed
                
                # Mark deposit as paid
                conn.execute(
                    'UPDATE deposits SET status = "paid", paid_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (deposit['id'],)
                )
                
                # Calculate bonuses
                deposit_count = conn.execute(
                    'SELECT COUNT(*) FROM deposits WHERE user_id = ? AND status = "paid"',
                    (deposit['user_id'],)
                ).fetchone()[0]
                
                is_first_deposit = deposit_count == 1
                bonus_amount = 0
                
                # First deposit bonus
                if is_first_deposit:
                    bonus_amount += int(deposit['fun_coins'] * PAYMENT_SETTINGS.get('first_deposit_bonus', 0.2))
                
                # Weekend bonus
                is_weekend = datetime.now().weekday() >= 5
                if is_weekend:
                    weekend_bonus = int(deposit['fun_coins'] * 0.1)  # 10% weekend bonus
                    bonus_amount += weekend_bonus
                
                # VIP bonus
                vip_level = self.get_user_vip_level(deposit['user_id'])
                if vip_level > 0:
                    vip_bonus = int(deposit['fun_coins'] * (vip_level * 0.05))  # 5% per VIP level
                    bonus_amount += vip_bonus
                
                total_credit = deposit['fun_coins'] + bonus_amount
                
                # Credit user account
                conn.execute(
                    'UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                    (total_credit, deposit['user_id'])
                )
                
                # Update daily limits
                today = datetime.now().date().isoformat()
                conn.execute(
                    '''INSERT OR REPLACE INTO daily_limits 
                       (user_id, date, deposited_amount) VALUES 
                       (?, ?, COALESCE((SELECT deposited_amount FROM daily_limits 
                                       WHERE user_id = ? AND date = ?), 0) + ?)''',
                    (deposit['user_id'], today, deposit['user_id'], today, deposit['fun_coins'])
                )
                
                # Award achievements
                if is_first_deposit:
                    self.casino.unlock_achievement(deposit['user_id'], "first_deposit")
                
                if deposit['fun_coins'] >= 50000:
                    self.casino.unlock_achievement(deposit['user_id'], "big_depositor")
                
                if deposit['fun_coins'] >= 500000:
                    self.casino.unlock_achievement(deposit['user_id'], "whale")
                
                conn.commit()
                
                logger.info(f"🐻 Credited {total_credit} 🐻 to user {deposit['user_id']} (base: {deposit['fun_coins']}, bonus: {bonus_amount})")
                
        except Exception as e:
            logger.error(f"Error crediting deposit: {e}")
    
    def get_bet_suggestion(self, user_balance: int, vip_level: int) -> list:
        """Get suggested bet amounts based on user balance and VIP level"""
        max_bet = self.get_user_max_bet_by_vip(vip_level)
        
        # Calculate safe bet amounts
        suggestions = []
        
        # Conservative bets (1-5% of balance)
        suggestions.extend([
            int(user_balance * 0.01),  # 1%
            int(user_balance * 0.025), # 2.5%
            int(user_balance * 0.05),  # 5%
        ])
        
        # Medium bets (based on VIP level)
        if vip_level >= 1:
            suggestions.extend([
                int(user_balance * 0.1),   # 10%
                int(user_balance * 0.15),  # 15%
            ])
        
        if vip_level >= 3:
            suggestions.append(int(user_balance * 0.2))  # 20%
        
        # Filter valid bets
        valid_suggestions = []
        for bet in suggestions:
            if 5 <= bet <= min(max_bet, user_balance):
                valid_suggestions.append(bet)
        
        # Remove duplicates and sort
        return sorted(list(set(valid_suggestions)))[:6]  # Max 6 suggestions

    async def async_init_solana(self):
        """Initialize Solana system asynchronously after event loop is running"""
        if self._solana_initialized:
            return

        try:
            from solana_payment import get_solana_payment
            self.solana_system = get_solana_payment()
            if self.solana_system:
                await self.solana_system.ensure_initialized()
            logger.info("SUCCESS: Solana payment system initialized")
            self._solana_initialized = True
        except Exception as e:
            logger.error(f"WARNING: Solana system initialization failed: {e}")
            self.solana_system = None

# Global bot instance
bot = None

async def process_referral_bonus(casino, new_user_id, referral_code):
    """Process referral bonus for new users using new referral system"""
    try:
        result = casino.create_referral(referral_code, new_user_id)
        return result
    except Exception as e:
        logger.error(f"Referral bonus error: {e}")
        return {'success': False, 'error': str(e)}

# Bot handlers
async def check_group_membership(context_or_bot, user_id, chat_id=None):
    """Check if user is a member of the required group"""
    try:
        # Use the configured group username
        if not REQUIRED_GROUP_USERNAME:
            # If no group is configured, allow access
            return True
        
        # Try using group username first
        group_identifier = f"@{REQUIRED_GROUP_USERNAME}"
        
        # If a specific group ID is configured, use that instead
        if REQUIRED_GROUP_ID:
            group_identifier = REQUIRED_GROUP_ID
        
        # Get the bot from context or directly from the bot parameter
        bot_instance = None
        
        # More robust bot instance detection
        if hasattr(context_or_bot, 'bot') and context_or_bot.bot is not None:
            # This is a context object
            bot_instance = context_or_bot.bot
        elif hasattr(context_or_bot, 'application') and hasattr(context_or_bot.application, 'bot'):
            # This is an application object
            bot_instance = context_or_bot.application.bot
        elif hasattr(context_or_bot, 'get_chat_member') and 'Bot' in str(type(context_or_bot).__name__) and not hasattr(context_or_bot, 'first_name'):
            # This is already a bot instance - check by type name and ensure it's not a User object
            bot_instance = context_or_bot
        else:
            logger.error(f"Unable to extract bot instance. Object type: {type(context_or_bot)}, has bot: {hasattr(context_or_bot, 'bot')}, has get_chat_member: {hasattr(context_or_bot, 'get_chat_member')}, has first_name: {hasattr(context_or_bot, 'first_name')}")
            return False
            
        if bot_instance is None:
            logger.error("Bot instance is None after extraction")
            return False
            
        member = await bot_instance.get_chat_member(group_identifier, user_id)
        is_member = member.status in ['member', 'administrator', 'creator']
        
        logger.info(f"Group membership check for user {user_id}: {is_member} (status: {member.status})")
        return is_member
        
    except Exception as e:
        logger.error(f"Group membership check error for user {user_id}: {e}")
        # For new groups or if bot isn't admin, we can't check membership
        # In production, you might want to return False here to be more strict
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with error handling, referral system, and group requirement"""
    try:
        # Gruplarda /start komutuna yanıt verme
        if update.effective_chat.type in ['group', 'supergroup']:
            return
            
        if bot is None:
            await update.message.reply_text(
                "❌ Bot not initialized. Please restart the bot."
            )
            return
            
        bot.total_commands_processed += 1
        
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonim"
        
        
        # Check for referral code in start parameter
        referral_code = None
        if context.args and len(context.args) > 0:
            start_param = context.args[0]
            if start_param.startswith("friend_"):
                referral_code = start_param[7:]  # Remove "friend_" prefix
        
        # Get or create user
        user = bot.casino.get_user(user_id, username)

        # Process referral if this is a new user
        if referral_code and (user['games_count'] if 'games_count' in user else 0) == 0:  # New user
            referral_result = await process_referral_bonus(bot.casino, user_id, referral_code)
            if referral_result['success']:
                await update.message.reply_text(
                    f"🎉 **Referral Bonus!** 🎉\n\n"
                    f"🐻 You received {referral_result['message']}\n"
                    f"🤝 Your referrer: {referral_result['referrer_name']}\n"
                    f"📈 Now your referrer will earn 5% commission when you play!\n\n"
                    f"🎮 Welcome to the Casino!",
                    parse_mode='Markdown'
                )

        await show_main_menu(bot.casino, update, context, is_callback=False)
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await update.message.reply_text(
            "ERROR: Bot failed to start. Please try again in a few seconds."
        )

async def handle_group_solo_game(query, user, casino, game_type, bet_amount, game_name):
    """Handle independent group games - NO LOCK SYSTEM - Everyone can play simultaneously"""
    try:
        # Import the new independent game handler
        try:
            from independent_group_game_handler import handle_independent_group_game
            
            # Redirect to the new independent handler
            await handle_independent_group_game(query, user, casino, game_type, bet_amount)
            return
        except ImportError:
            # Fall back to original implementation if the handler doesn't exist
            pass
        except Exception as e:
            # Log error and fall back to original implementation
            logger.error(f"Independent group game handler error: {e}")
            pass
        
        # Check if user has enough balance
        if user['fun_coins'] < bet_amount:
            await query.edit_message_text(
                f"💸 Yetersiz bakiye!\n\n"
                f"💰 Mevcut bakiye: {user['fun_coins']:,} 🐻\n"
                f"🎯 Gerekli miktar: {bet_amount:,} 🐻\n\n"
                f"🎁 Günlük bonus alarak bakiye artırabilirsiniz!",
                reply_markup=casino.create_keyboard([
                    [("🎁 Günlük Bonus", "daily_bonus")],
                    [("🔙 Geri", f"/game")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        # Deduct bet amount
        casino.db.execute(
            "UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?",
            (bet_amount, user['user_id'])
        )
        casino.db.commit()
        
        # Play the game using solo engine
        from solo_games import SoloGameEngine
        if not hasattr(casino, 'solo_engine'):
            casino.solo_engine = SoloGameEngine()
        
        # Play game based on type
        result = None
        if game_type == "solo_slots":
            result = casino.solo_engine.play_solo_slots(bet_amount, user['user_id'])
        elif game_type == "solo_roulette":
            result = casino.solo_engine.play_solo_roulette(bet_amount, "color", "red", user['user_id'])
        elif game_type == "solo_blackjack":
            result = casino.solo_engine.play_solo_blackjack(bet_amount, user['user_id'])
        elif game_type == "solo_baccarat":
            result = casino.solo_engine.play_solo_baccarat(bet_amount, "player", user['user_id'])
        elif game_type == "solo_crash":
            result = casino.solo_engine.play_solo_crash(bet_amount, 2.0, user['user_id'])
        elif game_type == "solo_mines":
            result = casino.solo_engine.play_solo_mines(bet_amount, 3, 3, user['user_id'])
        elif game_type == "solo_keno":
            result = casino.solo_engine.play_solo_keno(bet_amount, None, user['user_id'])
        elif game_type == "solo_dice":
            result = casino.solo_engine.play_solo_dice(bet_amount, 4, user['user_id'])
        elif game_type == "rock_paper_scissors":
            result = casino.solo_engine.play_rock_paper_scissors(bet_amount, None, user['user_id'])
        elif game_type == "number_guess":
            result = casino.solo_engine.play_number_guess(bet_amount, None, user['user_id'])
        elif game_type == "lucky_wheel":
            result = casino.solo_engine.play_lucky_wheel(bet_amount, user['user_id'])
        else:
            result = {'won': False, 'win_amount': 0, 'result_text': 'Oyun bulunamadı!'}
        
        # Add winnings if won
        if result['won'] and result.get('win_amount', 0) > 0:
            casino.db.execute(
                "UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?",
                (result['win_amount'], user['user_id'])
            )
            casino.db.commit()
        
        # Update game statistics
        casino.db.execute(
            "UPDATE users SET games_count = games_count + 1 WHERE user_id = ?",
            (user['user_id'],)
        )
        
        # Record group game history for statistics
        try:
            chat_id = query.message.chat.id
            casino.db.execute("""
                INSERT OR IGNORE INTO game_history 
                (user_id, username, game_type, bet_amount, win_amount, won, chat_id, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                user['user_id'], user['username'], game_type, bet_amount, 
                result.get('win_amount', 0), result['won'], chat_id
            ))
        except:
            # Create table if it doesn't exist
            casino.db.execute("""
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    game_type TEXT,
                    bet_amount INTEGER,
                    win_amount INTEGER,
                    won BOOLEAN,
                    chat_id INTEGER,
                    created_at DATETIME
                )
            """)
            casino.db.execute("""
                INSERT INTO game_history 
                (user_id, username, game_type, bet_amount, win_amount, won, chat_id, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                user['user_id'], user['username'], game_type, bet_amount, 
                result.get('win_amount', 0), result['won'], chat_id
            ))
        
        # Create user_bonuses table if needed
        try:
            casino.db.execute("""
                CREATE TABLE IF NOT EXISTS user_bonuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    bonus_type TEXT,
                    amount INTEGER,
                    created_at DATETIME
                )
            """)
        except:
            pass
            
        casino.db.commit()
        
        # Get updated balance
        updated_user = casino.get_user(user['user_id'], user['username'])
        
        # Check for big wins and send live notifications
        win_amount = result.get('win_amount', 0)
        net_profit = win_amount - bet_amount
        
        # Optimized notification check - only for very big wins
        if result['won'] and (net_profit >= 2000 or win_amount >= 5000):
            # Send notification in background without blocking
            asyncio.create_task(send_big_win_notification(
                query.message.chat.id, user['username'], game_name, 
                win_amount, net_profit, result.get('special_effect', '🎊 Muhteşem!')
            ))
        
        # Create result message
        if result['won']:
            result_text = f"""
🎉 **{game_name} - KAZANDIN!** 🎉

🎮 **Bahis:** {bet_amount:,} 🐻
💰 **Kazanç:** {win_amount:,} 🐻
✨ **Net Kar:** +{net_profit:,} 🐻

💰 **Yeni Bakiye:** {updated_user['fun_coins']:,} 🐻

{result.get('result_text', '🎊 Harika oyun!')}
{result.get('special_effect', '')}
            """
        else:
            result_text = f"""
😔 **{game_name} - Kaybettin** 😔

🎮 **Bahis:** {bet_amount:,} 🐻
💸 **Kayıp:** -{bet_amount:,} 🐻

💰 **Yeni Bakiye:** {updated_user['fun_coins']:,} 🐻

{result.get('result_text', '🍀 Bir dahaki sefere şansın olur!')}
            """
        
        # Create keyboard with URL button
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = [
            [InlineKeyboardButton("🔄 Tekrar Oyna", callback_data=f"group_{game_type}_100"), 
             InlineKeyboardButton("📊 İstatistikler", callback_data="group_stats")],
            [InlineKeyboardButton("🎮 Diğer Oyunlar", callback_data="game_menu_return"), 
             InlineKeyboardButton("💰 Günlük Bonus", callback_data="daily_bonus")],
            [InlineKeyboardButton("💬 Bot ile Özel Oyna", url=f"https://t.me/{query.get_bot().username}?start=fullgames")]
        ]
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        # Release group game lock
        bot.release_group_game_lock(chat_id, user_id)
        
        # Send private result message only to the player
        private_result_text = f"""
🎯 **Grup Oyunu Sonucu - Sadece Sen Görüyorsun**

{result_text}

⚠️ Diğer grup üyeleri sadece genel durumu görebilir.
💡 Özel bilgilerin gizli kalması için bu mesaj sadece sana gönderildi.
        """
        
        try:
            # Prepare messages
            public_summary = f"""
🎮 **Grup Oyunu Tamamlandı**

👤 **Oyuncu:** @{user['username']}
🎯 **Oyun:** {game_name}
{'🎉 Kazandı!' if result['won'] else '😔 Kaybetti'}

💡 Detayları özel mesajda görebilirsin.
🎮 Sen de oynamak için: /game
            """
            
            # Send both messages in parallel for speed
            private_task = asyncio.create_task(
                query.get_bot().send_message(
                    chat_id=user['user_id'], 
                    text=private_result_text, 
                    parse_mode='Markdown',
                    reply_markup=casino.create_keyboard([
                        [("🔄 Tekrar Oyna", f"group_{game_type}_{bet_amount}")],
                        [("🎮 Tüm Oyunlar", "solo_games")]
                    ])
                )
            )
            
            public_task = asyncio.create_task(
                query.edit_message_text(
                    public_summary,
                    reply_markup=casino.create_keyboard([
                        [("🎮 Oyun Oyna", "games")],
                        [("📊 Grup İstatistikleri", "group_stats")]
                    ]),
                    parse_mode='Markdown'
                )
            )
            
            # Wait for both to complete
            await asyncio.gather(private_task, public_task, return_exceptions=True)
            
        except Exception as pm_error:
            logger.error(f"Private message error: {pm_error}")
            # Fallback to group message if private message fails
            await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Group solo game error: {e}")
        # Release lock on error
        try:
            bot.release_group_game_lock(query.message.chat.id, user['user_id'])
        except:
            pass
        await query.edit_message_text(
            "❌ Oyun oynanırken hata oluştu!\n"
            "🔄 Lütfen tekrar deneyin.",
            reply_markup=casino.create_keyboard([
                [("🔙 Geri", f"/game")]
            ])
        )

async def handle_group_dice_game(query, user, casino, dice_type, bet_amount, game_name):
    """Handle group dice games with Telegram dice API and group lock system"""
    try:
        chat_id = query.message.chat.id
        user_id = user['user_id']
        
        # Check if user has enough balance first
        if user['fun_coins'] < bet_amount:
            await query.edit_message_text(
                f"💸 **Yetersiz Bakiye!**\n\n"
                f"💰 Mevcut: {user['fun_coins']:,} 🐻\n"
                f"🎯 Gerekli: {bet_amount:,} 🐻\n\n"
                f"🎁 Günlük bonus alarak bakiye artırabilirsin!",
                reply_markup=casino.create_keyboard([
                    [("🎁 Günlük Bonus", "daily_bonus")],
                    [("🔙 Oyunlara Dön", "games")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        # Deduct bet amount
        casino.db.execute(
            "UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?",
            (bet_amount, user['user_id'])
        )
        casino.db.commit()
        
        # Import and use dice games
        from dice_games import get_dice_games_instance
        dice_games = get_dice_games_instance(casino)
        
        # Show pre-game animation
        dice_config = {
            'classic': {'emoji': '🎲', 'name': 'Klasik Zar', 'min': 1, 'max': 6},
            'darts': {'emoji': '🎯', 'name': 'Dart', 'min': 1, 'max': 6},
            'basketball': {'emoji': '🏀', 'name': 'Basketbol', 'min': 1, 'max': 5},
            'football': {'emoji': '⚽', 'name': 'Futbol', 'min': 1, 'max': 5},
            'bowling': {'emoji': '🎳', 'name': 'Bowling', 'min': 1, 'max': 6},
            'slot_machine': {'emoji': '🎰', 'name': 'Slot Dice', 'min': 1, 'max': 64}
        }
        
        config = dice_config.get(dice_type, dice_config['classic'])
        dice_emoji = config['emoji']
        dice_name = config['name']
        
        # Show animation
        await query.edit_message_text(
            f"{dice_emoji} **{dice_name}** {dice_emoji}\n\n"
            f"🐻 **Bahis:** {bet_amount:,} 🐻\n"
            f"🎯 **{dice_name} atılıyor...**\n\n"
            f"⏳ Lütfen bekleyin...",
            parse_mode='Markdown'
        )
        
        # Send actual Telegram dice
        import asyncio
        import random
        
        try:
            dice_message = await asyncio.wait_for(
                query.message.reply_dice(emoji=dice_emoji),
                timeout=10.0
            )
            dice_value = dice_message.dice.value
            
            # Wait for dice animation - UZATILDI
            await asyncio.sleep(6)

            # Delete dice message after animation
            try:
                await dice_message.delete()
            except:
                pass
                
        except:
            # Fallback to random value
            dice_value = random.randint(config['min'], config['max'])
        
        # Calculate payout based on dice type and value
        payout = 0
        result_text = ""
        
        if dice_type == 'classic':
            if dice_value == 6:
                payout = bet_amount * 6
                result_text = "🎉 **6 GELDİ!** JACKPOT! 🎉"
            elif dice_value >= 4:
                payout = bet_amount * 2
                result_text = f"⭐ **{dice_value}** - İyi skor! ⭐"
            elif dice_value == 3:
                payout = bet_amount
                result_text = f"😊 **{dice_value}** - Ortalama skor"
            else:
                result_text = f"💔 **{dice_value}** - Kötü şans"
                
        elif dice_type == 'darts':
            if dice_value == 6:
                payout = bet_amount * 10
                result_text = "🎯 **BULLSEYE!** PERFECT! 🎯"
            elif dice_value >= 4:
                payout = bet_amount * 3
                result_text = f"⭐ **{dice_value}** - Hedefe yakın! ⭐"
            elif dice_value >= 2:
                payout = bet_amount
                result_text = f"😊 **{dice_value}** - Hedefi vurdun!"
            else:
                result_text = f"💔 **{dice_value}** - Tahtayı kaçırdın!"
                
        elif dice_type in ['basketball', 'football']:
            sport_name = "🏀 BASKET" if dice_type == 'basketball' else "⚽ GOL"
            if dice_value >= 4:
                payout = bet_amount * 5
                result_text = f"{sport_name} OLDU! 🎉"
            elif dice_value == 3:
                payout = bet_amount
                result_text = f"😊 **{dice_value}** - Yaklaştın!"
            else:
                result_text = f"💔 **{dice_value}** - Kaçırdın!"
                
        elif dice_type == 'bowling':
            if dice_value == 6:
                payout = bet_amount * 6
                result_text = "🎳 **STRIKE!** Tüm pinler! 🎳"
            elif dice_value >= 4:
                payout = bet_amount * 2
                result_text = f"⭐ **{dice_value}** - Çok pin!"
            elif dice_value == 3:
                payout = bet_amount
                result_text = f"😊 **{dice_value}** - Bazı pin"
            else:
                result_text = f"💔 **{dice_value}** - Gutter ball!"
                
        elif dice_type == 'slot_machine':
            if dice_value == 64:
                payout = bet_amount * 100
                result_text = "🎰 **MEGA JACKPOT!** Üçlü 7! 💎"
            elif dice_value in [1, 22, 43]:
                payout = bet_amount * 50
                result_text = f"🔥 **ÖZEL JACKPOT #{dice_value}!** 🔥"
            elif dice_value >= 50:
                payout = bet_amount * 10
                result_text = f"⭐ **Yüksek Kombinasyon #{dice_value}** ⭐"
            elif dice_value >= 30:
                payout = bet_amount * 5
                result_text = f"😊 **Orta Kombinasyon #{dice_value}**"
            elif dice_value >= 15:
                payout = bet_amount * 2
                result_text = f"🍀 **Küçük Kombinasyon #{dice_value}**"
            else:
                result_text = f"💔 **Kombinasyon #{dice_value}** - Kaybettin!"
        
        # Add winnings
        if payout > 0:
            casino.db.execute(
                "UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?",
                (payout, user['user_id'])
            )
            casino.db.commit()
        
        # Update stats
        casino.db.execute(
            "UPDATE users SET games_count = games_count + 1 WHERE user_id = ?",
            (user['user_id'],)
        )
        
        # Record game history
        try:
            chat_id = query.message.chat.id
            casino.db.execute("""
                INSERT OR IGNORE INTO game_history 
                (user_id, username, game_type, bet_amount, win_amount, won, chat_id, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                user['user_id'], user['username'], f"dice_{dice_type}", bet_amount, 
                payout, payout > 0, chat_id
            ))
            casino.db.commit()
        except:
            pass
        
        # Get updated user
        updated_user = casino.get_user(user['user_id'], user['username'])
        net_profit = payout - bet_amount
        
        # Create result message
        if payout > 0:
            final_text = f"""
🎉 **{game_name} - KAZANDIN!** 🎉

{dice_emoji} **Sonuç:** {dice_value}
{result_text}

🎮 **Bahis:** {bet_amount:,} 🐻
💰 **Kazanç:** {payout:,} 🐻
✨ **Net Kar:** +{net_profit:,} 🐻

💰 **Yeni Bakiye:** {updated_user['fun_coins']:,} 🐻
            """
        else:
            final_text = f"""
😔 **{game_name} - Kaybettin** 😔

{dice_emoji} **Sonuç:** {dice_value}
{result_text}

🎮 **Bahis:** {bet_amount:,} 🐻
💸 **Kayıp:** -{bet_amount:,} 🐻

💰 **Yeni Bakiye:** {updated_user['fun_coins']:,} 🐻

🍀 Bir dahaki sefere şansın olur!
            """
        
        # Create keyboard with URL button
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = [
            [InlineKeyboardButton("🔄 Tekrar Oyna", callback_data=f"group_dice_{dice_type}_100"), 
             InlineKeyboardButton("📊 İstatistikler", callback_data="group_stats")],
            [InlineKeyboardButton("🎮 Diğer Oyunlar", callback_data="game_menu_return"), 
             InlineKeyboardButton("💰 Günlük Bonus", callback_data="daily_bonus")],
            [InlineKeyboardButton("💬 Bot ile Özel Oyna", url=f"https://t.me/{query.get_bot().username}?start=fullgames")]
        ]
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        # Release group game lock
        bot.release_group_game_lock(chat_id, user_id)
        
        # Send private result to player and public summary to group (similar to solo games)
        private_result = f"""
🎯 **Zar Oyunu Sonucu - Sadece Sen Görüyorsun**

{final_text}

⚠️ Diğer grup üyeleri sadece genel durumu görebilir.
💡 Özel bilgilerin gizli kalması için bu mesaj sadece sana gönderildi.
        """
        
        try:
            # Prepare messages
            public_summary = f"""
🎮 **Grup Zar Oyunu Tamamlandı**

👤 **Oyuncu:** @{user['username']}  
🎯 **Oyun:** {game_name}
🎲 **Sonuç:** {result['dice_value']}
{'🎉 Kazandı!' if result['won'] else '😔 Kaybetti'}

💡 Detayları özel mesajda görebilirsin.
🎮 Sen de oynamak için: /game
            """
            
            # Send both messages in parallel for speed
            private_task = asyncio.create_task(
                query.get_bot().send_message(
                    chat_id=user['user_id'], 
                    text=private_result, 
                    parse_mode='Markdown',
                    reply_markup=casino.create_keyboard([
                        [("🔄 Tekrar Oyna", f"group_dice_{dice_type}_{bet_amount}")],
                        [("🎮 Tüm Oyunlar", "games")]
                    ])
                )
            )
            
            public_task = asyncio.create_task(
                query.edit_message_text(
                    public_summary,
                    reply_markup=casino.create_keyboard([
                        [("🎮 Oyun Oyna", "games")],
                        [("📊 Grup İstatistikleri", "group_stats")]
                    ]),
                    parse_mode='Markdown'
                )
            )
            
            # Wait for both to complete
            await asyncio.gather(private_task, public_task, return_exceptions=True)
            
        except Exception as pm_error:
            logger.error(f"Private message error: {pm_error}")
            # Fallback to group message if private message fails
            await query.edit_message_text(final_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Group dice game error: {e}")
        # Release lock on error
        try:
            bot.release_group_game_lock(query.message.chat.id, user['user_id'])
        except:
            pass
        await query.edit_message_text(
            "❌ Dice oyunu sırasında hata oluştu!\n"
            "🔄 Lütfen tekrar deneyin.",
            reply_markup=casino.create_keyboard([
                [("🔙 Geri", "game_menu_return")]
            ])
        )

async def send_big_win_notification(chat_id, username, game_name, win_amount, net_profit, special_effect):
    """Send big win notification in background - OPTIMIZED"""
    try:
        notification_text = f"""
🔥 **BÜYÜK KAZANÇ!** 🔥

👤 **{username}** oynadı **{game_name}**
💰 **Kazanç:** {win_amount:,} 🐻
✨ **Net Kar:** +{net_profit:,} 🐻

{special_effect}

🎮 Sen de şansını dene: /game
        """
        
        await bot.application.bot.send_message(
            chat_id=chat_id,
            text=notification_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Big win notification error: {e}")

async def safe_query_answer(query, text="", show_alert=False):
    """Safely answer a callback query, handling expired queries - ENHANCED"""
    try:
        from safe_telegram_handler import safe_answer_query
        return await safe_answer_query(query, text, show_alert)
    except ImportError:
        # Fallback to original implementation
        try:
            await query.answer(text, show_alert=show_alert)
            return True
        except Exception as e:
            err_str = str(e)
            if "too old" in err_str or "timeout" in err_str or "invalid" in err_str:
                return False
            logger.error(f"Callback query error: {e}")
            return False

async def safe_query_edit(query, text, reply_markup=None, parse_mode=None):
    """Safely edit a callback query message, handling expired queries - ENHANCED"""
    try:
        from safe_telegram_handler import safe_edit_message
        return await safe_edit_message(query, text, reply_markup, parse_mode)
    except ImportError:
        # Fallback to original implementation
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            return True
        except Exception as e:
            err_str = str(e).lower()
            if "query is too old" in err_str or "response timeout expired" in err_str or "query id is invalid" in err_str:
                logger.debug(f"Callback query expired, ignoring edit: {e}")
                return False
            elif "message is not modified" in err_str:
                logger.debug("Message content unchanged, ignoring")
                return True
            else:
                logger.error(f"Error editing callback query: {e}")
                return False

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries with enhanced error handling"""
    query = update.callback_query
    
    # Handle expired queries gracefully
    if not await safe_query_answer(query):
        return  # Query expired or failed


    

    try:
        # Check if bot is initialized
        if bot is None:
            await safe_query_edit(query, "❌ Bot not initialized. Please restart the bot.")
            return
            
        bot.total_commands_processed += 1
        data = query.data
        
        # Quick answer for immediate feedback - use safe handler
        await safe_query_answer(query)
        
        # Get user data only when needed (not for all callbacks)
        user = None
        if data not in ["main_menu", "game_menu_return"]:  # Skip user data for simple navigation
            user = bot.casino.get_user(query.from_user.id, query.from_user.username)
        
        # Group membership check removed - direct access to all features
        
        # Main menu
        if data == "main_menu":
            await show_main_menu(bot.casino, query, context, is_callback=True)
        elif data == "game_menu_return":
            # Return to group game menu
            if hasattr(query.message, 'chat') and query.message.chat.type in ['group', 'supergroup']:
                # Show simple return message
                await query.edit_message_text(
                    "🎮 **Oyunlara geri dönüyorsunuz...**\n\n"
                    "✨ Oyuna devam etmek için `/game` yazın!\n"
                    "🎯 Tüm oyunlar 100🐻 sabit bahisle oynanır.",
                    reply_markup=None,
                    parse_mode='Markdown'
                )
            else:
                await show_main_menu(bot.casino, query, context, is_callback=True)
            return
        
        # Language selection
        elif data == "language_selection":
            from language_handler import show_language_selection
            await show_language_selection(query, user, bot.casino)
        elif data == "check_membership":
            # Redirect directly to main menu since group membership is no longer required
            await show_main_menu(bot.casino, query, None, is_callback=True)
        elif data == "join_group":
            # Direct link to Telegram group
            from languages import get_text, DEFAULT_LANGUAGE
            username = query.from_user.username or "Player"
            user_id = query.from_user.id

            # Get user language
            user_lang = DEFAULT_LANGUAGE
            if hasattr(bot.casino.db, 'get_user_language'):
                try:
                    user_lang = bot.casino.db.get_user_language(user_id)
                except:
                    user_lang = DEFAULT_LANGUAGE

            group_title = get_text(user_lang, "group.our_telegram_group", "🎉 <b>Our Telegram Group!</b> 🎉")
            hello_text = get_text(user_lang, "group.hello", "Hello {username}! 👋", username=username)
            official_group = get_text(user_lang, "group.official_group", "🎮 <b>Our Official Telegram Group:</b> @{group_name}", group_name=REQUIRED_GROUP_USERNAME)
            whats_in_group = get_text(user_lang, "group.whats_in_group", "📋 <b>What's in the group?</b>")
            daily_bonuses = get_text(user_lang, "group.daily_bonuses", "• 🎉 Daily bonuses and giveaways")
            bot_updates = get_text(user_lang, "group.bot_updates", "• 📢 Bot updates and announcements")
            chat_players = get_text(user_lang, "group.chat_players", "• 👥 Chat with other players")
            tournament_notifications = get_text(user_lang, "group.tournament_notifications", "• 🎯 Tournament notifications")
            help_support = get_text(user_lang, "group.help_support", "• 🆘 Help and support")
            join_fun = get_text(user_lang, "group.join_fun", "🚀 Join now and have more fun at the casino!")
            join_group_btn = get_text(user_lang, "group.join_group", "👥 Join Group")
            back_main_btn = get_text(user_lang, "group.back_main_menu", "🏠 Back to Main Menu")

            await query.edit_message_text(
                f"{group_title}\n\n"
                f"{hello_text}\n\n"
                f"{official_group}\n\n"
                f"{whats_in_group}\n"
                f"{daily_bonuses}\n"
                f"{bot_updates}\n"
                f"{chat_players}\n"
                f"{tournament_notifications}\n"
                f"{help_support}\n\n"
                f"{join_fun}",
                reply_markup=bot.casino.create_keyboard([
                    [(join_group_btn, REQUIRED_GROUP_URL)],
                    [(back_main_btn, "main_menu")]
                ]),
                parse_mode='HTML'
            )
        elif data.startswith("set_language_"):
            language_code = data.split("_", 2)[2]
            from language_handler import handle_set_language
            await handle_set_language(query, user, language_code, bot.casino)
        
        # Payment system
        elif data == "payment_menu":
            if bot.payment_manager and PAYMENT_HANDLERS_AVAILABLE:
                await show_payment_menu(query, user, bot.casino)
            else:
                # Simple payment menu fallback
                await show_simple_payment_menu(query, user, bot.casino)

        elif data == "cryptobot_menu":
            await show_cryptobot_payment_menu(query, user, bot.casino)

        elif data == "deposit_menu" and bot.payment_manager:
            from payment_handlers import show_deposit_menu
            await show_deposit_menu(query, user, bot.casino)
        elif data == "withdraw_menu" and bot.payment_manager:
            from payment_handlers import show_withdraw_menu
            await show_withdraw_menu(query, user, bot.casino)
        elif data.startswith("select_deposit_") and bot.payment_manager:
            # Redirect directly to Solana deposit menu
            from payment_handlers import show_solana_deposit_menu
            await show_solana_deposit_menu(query, user, bot.casino)
        elif data.startswith("select_amount_") and bot.payment_manager:
            parts = data.split("_")
            crypto, amount = parts[2], parts[3]
            from payment_handlers import handle_amount_selection
            await handle_amount_selection(query, user, crypto, amount, bot.casino)
        elif data.startswith("confirm_deposit_") and bot.payment_manager:
            parts = data.split("_")
            if len(parts) >= 5:  # Has wallet info
                crypto, amount, wallet = parts[2], parts[3], parts[4]
                from payment_handlers import handle_confirm_deposit
                await handle_confirm_deposit(query, user, crypto, amount, wallet, bot.casino)
            else:  # Old format without wallet
                crypto, amount = parts[2], parts[3]
                from payment_handlers import handle_confirm_deposit
                await handle_confirm_deposit(query, user, crypto, amount, None, bot.casino)
        elif data.startswith("select_withdraw_") and bot.payment_manager:
            crypto = data.split("_", 2)[2]
            from payment_handlers import handle_withdraw_crypto_selection
            await handle_withdraw_crypto_selection(query, user, crypto, bot.casino)
        elif data.startswith("confirm_withdraw_") and bot.payment_manager:
            parts = data.split("_")
            crypto, amount = parts[2], parts[3]
            from payment_handlers import handle_confirm_withdraw
            await handle_confirm_withdraw(query, user, crypto, amount, bot.casino)
        elif data == "payment_history" and bot.payment_manager:
            from payment_handlers import show_payment_history
            await show_payment_history(query, user, bot.casino)
        elif data == "vip_info":
            from payment_handlers import show_vip_info
            await show_vip_info(query, user, bot.casino)
        elif data == "crypto_rates" and bot.payment_manager:
            from payment_handlers import show_crypto_rates
            await show_crypto_rates(query, bot.casino)
        elif data == "limits_info":
            from payment_handlers import show_limits_info
            await show_limits_info(query, user, bot.casino)
        elif data == "bonus_info":
            from payment_handlers import show_bonus_info
            await show_bonus_info(query, user, bot.casino)
        
        # Solana Payment Handlers (New Flow)
        elif data == "solana_deposit_direct":
            from payment_handlers import show_solana_deposit_direct
            await show_solana_deposit_direct(query, user, bot.casino)
        elif data == "solana_deposit_menu":
            from payment_handlers import show_solana_deposit_menu
            await show_solana_deposit_menu(query, user, bot.casino)
        elif data == "solana_withdraw_menu":
            from payment_handlers import show_solana_withdraw_menu
            await show_solana_withdraw_menu(query, user, bot.casino)
        elif data == "solana_rates":
            from payment_handlers import show_solana_rates
            await show_solana_rates(query, bot.casino)
        elif data.startswith("deposit_wallet_"):
            parts = data.split("_")
            wallet_id = parts[2]
            sol_amount = parts[3]
            from payment_handlers import handle_deposit_wallet_selected
            await handle_deposit_wallet_selected(query, user, wallet_id, sol_amount, bot.casino)
        elif data.startswith("deposit_wallet_direct_"):
            wallet_id = data.split("_")[3]
            from payment_handlers import handle_deposit_wallet_direct
            await handle_deposit_wallet_direct(query, user, wallet_id, bot.casino)
        elif data.startswith("notify_admin_deposit_"):
            wallet_id = data.split("_")[3]
            from payment_handlers import handle_notify_admin_deposit
            await handle_notify_admin_deposit(query, user, wallet_id, bot.casino)

        # Legacy Solana Payment Handlers (Keep for compatibility)
        elif data == "solana_payment":
            await show_solana_payment_menu(query, user, bot.casino)
        elif data == "solana_deposit":
            await show_solana_deposit_menu(query, user, bot.casino)
        elif data == "deposit_sol_custom":
            from solana_handlers import show_custom_sol_amount_input
            # Set waiting flag for custom amount input
            context.user_data['waiting_for_custom_sol_amount'] = True
            await show_custom_sol_amount_input(query, user, bot.casino)
        elif data.startswith("deposit_sol_"):
            sol_amount = data.split("_")[2]
            await handle_solana_deposit(query, user, sol_amount, bot.casino)
        elif data.startswith("select_sol_amount_"):
            sol_amount = data.split("_")[-1]
            from solana_handlers import show_sol_amount_confirmation
            await show_sol_amount_confirmation(query, user, sol_amount, bot.casino)
        elif data.startswith("wallet_"):
            # Handle wallet selection (e.g., wallet_phantom_0.5)
            parts = data.split("_")
            wallet_type = parts[1]
            sol_amount = parts[2]
            await handle_wallet_selection(query, user, wallet_type, sol_amount, bot.casino)
        elif data == "solana_withdraw":
            await show_solana_withdraw_menu(query, user, bot.casino)
        elif data == "withdraw_sol_custom":
            from solana_handlers import show_custom_withdrawal_amount_input
            # Set waiting flag for custom withdrawal amount input
            context.user_data['waiting_for_custom_withdrawal_amount'] = True
            await show_custom_withdrawal_amount_input(query, user, bot.casino)
        elif data.startswith("withdraw_sol_"):
            sol_amount = data.split("_")[2]
            await show_withdrawal_wallet_input(query, user, sol_amount, bot.casino)
        elif data == "solana_help":
            await show_solana_help(query, user, bot.casino)
        
        # Solana Admin Handlers
        elif data == "solana_admin":
            await show_solana_admin_panel(query, user, bot.casino)
        elif data == "solana_pending_withdrawals":
            await show_pending_withdrawals(query, user, bot.casino)
        elif data.startswith("approve_withdrawal_"):
            withdrawal_id = data.split("_")[2]
            await approve_withdrawal(query, user, withdrawal_id, bot.casino)
        elif data.startswith("reject_withdrawal_"):
            withdrawal_id = data.split("_")[2]
            await reject_withdrawal(query, user, withdrawal_id, bot.casino)
        elif data == "solana_update_rate":
            await show_solana_rate_update(query, user, bot.casino)
        elif data.startswith("update_rate_"):
            new_rate = data.split("_")[2]
            await update_solana_rate(query, user, new_rate, bot.casino)
        elif data == "solana_stats":
            await show_solana_stats(query, user, bot.casino)
        elif data.startswith("check_deposit_"):
            # Check Solana deposit status
            deposit_id = data.split("_")[2]
            await check_solana_deposit_status(query, user, deposit_id, bot.casino)
        elif data.startswith("check_withdrawal_"):
            # Check Solana withdrawal status  
            withdrawal_id = data.split("_")[2]
            await check_solana_withdrawal_status(query, user, withdrawal_id, bot.casino)
        elif data.startswith("wallet_stats_"):
            # Show user wallet statistics
            await show_user_wallet_stats(query, user, bot.casino)

        # Wallet selection system
        elif data == "wallet_selection":
            from wallet_selector import show_wallet_selection_menu
            await show_wallet_selection_menu(query, context)
        elif data.startswith("select_wallet_"):
            from wallet_selector import handle_wallet_selection
            await handle_wallet_selection(query, context)
        elif data.startswith("open_wallet_mobile_"):
            from wallet_selector import handle_wallet_mobile_open
            await handle_wallet_mobile_open(query, context)
        elif data.startswith("wallet_deposit_"):
            from wallet_selector import handle_wallet_deposit_amount
            await handle_wallet_deposit_amount(query, context)
        elif data.startswith("confirm_wallet_payment_"):
            from wallet_selector import handle_wallet_payment_confirmation
            await handle_wallet_payment_confirmation(query, context, user, bot.casino)

        # Admin ödeme onay sistemi
        elif data.startswith("admin_approve_deposit_"):
            if is_admin_user(query.from_user.id):
                from wallet_selector import handle_admin_approve_deposit
                await handle_admin_approve_deposit(query, context, bot.casino)
            else:
                await query.answer("❌ Admin yetkisi gerekli!", show_alert=True)
        elif data.startswith("admin_reject_deposit_"):
            if is_admin_user(query.from_user.id):
                from wallet_selector import handle_admin_reject_deposit
                await handle_admin_reject_deposit(query, context, bot.casino)
            else:
                await query.answer("❌ Admin yetkisi gerekli!", show_alert=True)
        elif data.startswith("admin_deposit_details_"):
            if is_admin_user(query.from_user.id):
                from wallet_selector import show_admin_deposit_details
                await show_admin_deposit_details(query, context, bot.casino)
            else:
                await query.answer("❌ Admin yetkisi gerekli!", show_alert=True)

        # Admin çekim onay sistemi
        elif data.startswith("admin_approve_withdrawal_"):
            if is_admin_user(query.from_user.id):
                from withdrawal_handlers import handle_admin_approve_withdrawal
                await handle_admin_approve_withdrawal(query, context, bot.casino)
            else:
                await query.answer("❌ Admin yetkisi gerekli!", show_alert=True)
        elif data.startswith("admin_reject_withdrawal_"):
            if is_admin_user(query.from_user.id):
                from withdrawal_handlers import handle_admin_reject_withdrawal
                await handle_admin_reject_withdrawal(query, context, bot.casino)
            else:
                await query.answer("❌ Admin yetkisi gerekli!", show_alert=True)
        elif data.startswith("admin_withdrawal_details_"):
            if is_admin_user(query.from_user.id):
                from withdrawal_handlers import show_admin_withdrawal_details
                await show_admin_withdrawal_details(query, context, bot.casino)
            else:
                await query.answer("❌ Admin yetkisi gerekli!", show_alert=True)

        # Solana deposit amount selection - show wallet selection
        elif data.startswith("select_deposit_amount_"):
            sol_amount = data.replace("select_deposit_amount_", "")
            from solana_wallet_flow import show_deposit_wallet_selection
            await show_deposit_wallet_selection(query, context, sol_amount)

        # Solana withdrawal amount selection - wallet seçimi için
        elif data.startswith("select_withdrawal_amount_"):
            sol_amount = data.replace("select_withdrawal_amount_", "")
            from solana_wallet_flow import show_withdrawal_wallet_selection
            await show_withdrawal_wallet_selection(query, context, sol_amount)

        # Deposit wallet selection
        elif data.startswith("deposit_select_wallet_"):
            parts = data.replace("deposit_select_wallet_", "").split("_")
            wallet_id = parts[0]
            sol_amount = parts[1]
            from solana_wallet_flow import handle_deposit_wallet_selection
            await handle_deposit_wallet_selection(query, context, wallet_id, sol_amount)

        # Withdrawal wallet selection
        elif data.startswith("withdrawal_select_wallet_"):
            parts = data.replace("withdrawal_select_wallet_", "").split("_")
            wallet_id = parts[0]
            sol_amount = parts[1]
            from solana_wallet_flow import handle_withdrawal_wallet_selection
            await handle_withdrawal_wallet_selection(query, context, wallet_id, sol_amount)

        # Automatic deposit detection
        elif data.startswith("start_auto_detection_"):
            sol_amount = data.replace("start_auto_detection_", "")
            from solana_flow_completion import start_automatic_deposit_detection
            await start_automatic_deposit_detection(query, context, user, bot.casino, sol_amount)

        # Check balance
        elif data == "check_balance":
            from payment_handlers import show_balance_info
            await show_balance_info(query, user, bot.casino)

        # Legacy: Deposit confirmation after wallet selection (keep for compatibility)
        elif data.startswith("confirm_deposit_sent_"):
            sol_amount = data.replace("confirm_deposit_sent_", "")
            # Redirect to automatic detection
            from solana_flow_completion import start_automatic_deposit_detection
            await start_automatic_deposit_detection(query, context, user, bot.casino, sol_amount)

        # Wallet address input for withdrawal
        elif data.startswith("input_wallet_address_"):
            sol_amount = data.replace("input_wallet_address_", "")
            from solana_flow_completion import show_wallet_address_input
            await show_wallet_address_input(query, context, sol_amount)
        
        # Enhanced CryptoBot deposit handlers
        elif data.startswith("deposit_") and len(data.split("_")) == 2:
            # Deposit crypto selection (e.g., deposit_usdt, deposit_ton)
            crypto = data.split("_")[1].upper()
            from payment_handlers import process_deposit_request
            await process_deposit_request(query, user, crypto, bot.casino)
        elif data.startswith("deposit_") and len(data.split("_")) >= 3:
            # Specific deposit amount selection (e.g., deposit_usdt_5)
            parts = data.split("_")
            crypto = parts[1].upper()
            try:
                amount = float(parts[2])
                from payment_handlers import handle_confirm_deposit
                await handle_confirm_deposit(query, user, crypto, amount, bot.casino)
            except (ValueError, IndexError):
                from payment_handlers import show_deposit_menu
                await show_deposit_menu(query, user, bot.casino)
        
        # Enhanced CryptoBot withdrawal handlers  
        elif data.startswith("withdraw_") and len(data.split("_")) == 2:
            # Withdraw crypto selection (e.g., withdraw_usdt, withdraw_ton)
            crypto = data.split("_")[1].upper()
            from payment_handlers import process_withdrawal_request
            await process_withdrawal_request(query, user, crypto, bot.casino)
        elif data.startswith("withdraw_") and len(data.split("_")) >= 3:
            # Specific withdrawal amount selection (e.g., withdraw_usdt_10)
            parts = data.split("_")
            crypto = parts[1].upper()
            try:
                if parts[2] == "all":
                    # Handle withdraw all balance
                    if hasattr(bot, 'payment_manager') and bot.payment_manager:
                        try:
                            user_balance = await bot.payment_manager._get_user_balance(user['user_id'], crypto)
                            amount = user_balance
                        except:
                            amount = 0
                    else:
                        amount = 0
                else:
                    amount = float(parts[2])
                from payment_handlers import handle_confirm_withdraw
                await handle_confirm_withdraw(query, user, crypto, amount, bot.casino)
            except (ValueError, IndexError):
                from payment_handlers import show_withdrawal_menu
                await show_withdrawal_menu(query, user, bot.casino)
        
        # Enhanced solo games with better functionality
        elif data == "solo_games":
            await show_enhanced_solo_games_menu(query, user, bot.casino, bot)
        elif data == "games":
            # Handle games callback - redirect to group game menu
            if hasattr(query.message, 'chat') and query.message.chat.type in ['group', 'supergroup']:
                # For group chats, recreate the group game menu
                # Get the user and chat information
                user_id = query.from_user.id
                username = query.from_user.username or "Anonymous"
                user = bot.casino.get_user(user_id, username)
                chat_id = query.message.chat.id
                
                # Get cached group data for performance
                group_members = await bot.get_cached_or_fetch_async(
                    f"group_members_{chat_id}", 
                    lambda: get_group_member_count(context.bot, chat_id), 
                    ttl=300  # 5 minutes cache for member count
                )
                group_bonus = calculate_group_bonus(group_members)
                
                # Get group statistics with short cache
                group_stats = await bot.get_cached_or_fetch_async(
                    f"group_stats_{chat_id}",
                    lambda: get_group_stats(context.bot, chat_id, bot.casino),
                    ttl=30  # 30 seconds cache for stats
                )
                
                # Create the same menu as in game_command function
                games_text = f"""
🎮 **GRUP SOLO OYUN MENÜSÜ** 🎮

👋 Hello {username}! Welcome to group solo gaming!

📊 **GROUP STATISTICS (Today):**
🎯 **Games Played:** {group_stats['games_today']} games
💰 **Total Winnings:** {group_stats['winnings_today']:,} 🐻
👑 **Most Active:** {group_stats['top_player']} ({group_stats['top_player_games']} games)
👥 **Member Count:** {group_members} members

🎯 **Classic Casino Games (4 games):**
• 🎰 **Slot Machine** - 3 reel luck!
• 🔴 **Roulette** - Red or black?
• ♠️ **Blackjack** - 21'e yaklaş!
• 🃏 **Baccarat** - Banker vs Player!

🚀 **Modern Oyunlar (3 oyun):**
• 🚀 **Crash** - Roket kaçmadan çık!
• ⛏️ **Mines** - Mayınları sakın!
• 🎯 **Keno** - Sayıları tahmin et!

🎲 **Telegram Dice Oyunları (6 oyun):**
• 🎲 **Klasik Zar** - 1-6 arası gerçek zar!
• 🎯 **Dart** - Bullseye vur! (x10)
• 🏀 **Basketbol** - Basket at! (x5)
• ⚽ **Futbol** - Gol vur! (x5)
• 🎳 **Bowling** - Strike! (x6)
• 🎰 **Dice Slot** - 64 kombinasyon!

🎪 **Eğlence Oyunları (4 oyun):**
• 🎪 **Lucky Wheel** - Şans çarkı!
• 🎲 **Solo Zar** - Basit zar oyunu!
• ✂️ **Taş-Kağıt-Makas** - Klasik!
• 🔢 **Sayı Tahmin** - 1-100 arası!

💰 **Bakiyeniz:** {user['fun_coins']:,} 🐻
🎮 **Oyun Sayınız:** {user['games_count'] if 'games_count' in user.keys() else 0}

⚠️ **NOT:** Tüm oyunlar 100🐻 sabit bahisle oynanır.
🔥 **Big wins are announced to the group!**
                """
                
                # Create complete game selection keyboard for groups - 6 GAMES
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                keyboard_buttons = [
                    # Telegram Dice Games (6 games)
                    [InlineKeyboardButton("🎰 Dice Slot (100🐻)", callback_data="group_dice_slot_100"),
                     InlineKeyboardButton("⚽ Futbol (100🐻)", callback_data="group_dice_football_100")],
                    [InlineKeyboardButton("🎳 Bowling (100🐻)", callback_data="group_dice_bowling_100")],
                    [InlineKeyboardButton("🎲 Klasik Zar (100🐻)", callback_data="group_dice_classic_100"),
                     InlineKeyboardButton("🎯 Dart (100🐻)", callback_data="group_dice_darts_100")],
                    [InlineKeyboardButton("🏀 Basketbol (100🐻)", callback_data="group_dice_basketball_100")],
                    # Menu Options - NO MAIN MENU BUTTON
                    [InlineKeyboardButton("⏳ Oyun Durumu", callback_data="group_game_status"),
                     InlineKeyboardButton("📊 Grup İstatistikleri", callback_data="group_stats")],
                    [InlineKeyboardButton("👤 Profilim", callback_data="my_stats"),
                     InlineKeyboardButton("💬 Bot ile Özel Oyna", url=f"https://t.me/{context.bot.username}?start=fullgames")]
                ]
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
                
                await query.edit_message_text(games_text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                # For private chats, show solo games menu
                await show_enhanced_solo_games_menu(query, user, bot.casino, bot)
        elif data.startswith("solo_"):
            game_type = data.split("_", 1)[1]
            await show_enhanced_solo_game_options(query, user, f"solo_{game_type}", bot.casino, bot)
        
        # Handle individual dice games directly
        elif data in ["dice_classic", "dice_darts", "dice_basketball", "dice_football", "dice_bowling", "dice_slot_machine"]:
            try:
                from dice_games import handle_dice_game_options
                await handle_dice_game_options(query, user, bot.casino, data.split("_", 1)[1])
            except ImportError:
                await query.edit_message_text(
                    "🎲 Dice game is currently unavailable.",
                    reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                )

        # Handle custom dice bet options
        elif data.startswith("custom_dice_"):
            dice_type = data.replace("custom_dice_", "")
            try:
                from dice_games import handle_custom_dice_bet
                await handle_custom_dice_bet(query, user, bot.casino, dice_type)
            except ImportError:
                await query.edit_message_text(
                    "💎 Custom bet feature is currently unavailable.",
                    reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                )
        
        # Tüm solo oyunlar için callback handler'ları
        elif data == "play_solo_slot":
            await handle_solo_game_menu(query, user, bot.casino, "solo_slots", "🎰 Slot Machine")
        elif data == "play_solo_roulette":
            await handle_solo_game_menu(query, user, bot.casino, "solo_roulette", "🔴 Roulette")
        elif data == "play_solo_blackjack":
            await handle_solo_game_menu(query, user, bot.casino, "solo_blackjack", "♠️ Blackjack")
        elif data == "play_solo_crash":
            await handle_solo_game_menu(query, user, bot.casino, "solo_crash", "🚀 Crash")
        elif data == "play_solo_mines":
            await handle_solo_game_menu(query, user, bot.casino, "solo_mines", "⛏️ Mines")
        elif data == "play_solo_baccarat":
            await handle_solo_game_menu(query, user, bot.casino, "solo_baccarat", "🃏 Baccarat")
        elif data == "play_solo_keno":
            await handle_solo_game_menu(query, user, bot.casino, "solo_keno", "🎯 Keno")
        elif data == "play_solo_dice":
            await handle_solo_game_menu(query, user, bot.casino, "solo_dice", "🎲 Dice")
        elif data == "play_rock_paper_scissors":
            await handle_new_solo_game_menu(query, user, bot.casino, "rock_paper_scissors", "✂️ Taş-Kağıt-Makas")
        elif data == "play_number_guess":
            await handle_new_solo_game_menu(query, user, bot.casino, "number_guess", "🔢 Sayı Tahmin")
        
        # Group Solo Game Handlers (Fixed 100 coin bets) - All Games Available
        
        # Telegram Dice Games Handlers (6 games)
        elif data == "group_dice_slot_100":
            await handle_group_dice_game(query, user, bot.casino, "slot_machine", 100, "🎰 Dice Slot")
        elif data == "group_dice_football_100":
            await handle_group_dice_game(query, user, bot.casino, "football", 100, "⚽ Futbol")
        elif data == "group_dice_bowling_100":
            await handle_group_dice_game(query, user, bot.casino, "bowling", 100, "🎳 Bowling")
        elif data == "group_dice_classic_100":
            await handle_group_dice_game(query, user, bot.casino, "classic", 100, "🎲 Klasik Zar")
        elif data == "group_dice_darts_100":
            await handle_group_dice_game(query, user, bot.casino, "darts", 100, "🎯 Dart")
        elif data == "group_dice_basketball_100":
            await handle_group_dice_game(query, user, bot.casino, "basketball", 100, "🏀 Basketbol")
        elif data == "group_game_status":
            # Show current group game status (who is playing)
            chat_id = query.message.chat.id
            current_game = bot.get_group_game_status(chat_id)
            
            if current_game:
                locked_user = bot.casino.get_user_by_id(current_game['user_id'])
                username = locked_user['username'] if locked_user else "Bilinmeyen Kullanıcı"
                time_passed = int(time.time() - current_game['timestamp'])
                
                status_text = f"""
⏳ **GRUP OYUN DURUMU** ⏳

🎮 **Şu An Oynayan:** @{username}
🎯 **Oyun Türü:** {current_game['game_type']}
⏰ **Süre:** {time_passed} saniye önce başladı

⚠️ Lütfen oyun bitene kadar bekleyiniz.
💡 Her seferinde sadece bir kişi oynayabilir!
                """
                
                await query.edit_message_text(
                    status_text,
                    reply_markup=bot.casino.create_keyboard([
                        [("🔄 Güncelle", "group_game_status")],
                        [("🎮 Oyunlara Dön", "games")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "✅ **GRUP OYUN DURUMU**\n\n"
                    "🆓 Grup şu an oyun için uygun!\n"
                    "🎮 Herhangi bir oyunu başlatabilirsin.\n\n"
                    "💡 İlk oynayan kişi grup oyununu kilitler.",
                    reply_markup=bot.casino.create_keyboard([
                        [("🎮 Oyun Oyna", "games")],
                        [("📊 Grup İstatistikleri", "group_stats")]
                    ]),
                    parse_mode='Markdown'
                )
            return
            
        elif data == "group_stats":
            # Show detailed group statistics
            chat_id = query.message.chat.id
            group_stats = await get_group_stats(context.bot, chat_id, bot.casino)
            member_count = await get_group_member_count(context.bot, chat_id)
            
            stats_text = f"""
📊 **DETAYLI GRUP İSTATİSTİKLERİ** 📊

🏆 **BUGÜNKÜ PERFORMANS:**
🎯 **Toplam Oyun:** {group_stats['games_today']} adet
💰 **Total Winnings:** {group_stats['winnings_today']:,} 🐻
👑 **En Aktif Oyuncu:** {group_stats['top_player']}
🎮 **En Aktif Oyun Sayısı:** {group_stats['top_player_games']} oyun

👥 **GRUP BİLGİLERİ:**
👤 **Toplam Üye:** {member_count} kişi
🎁 **Günlük Grup Bonusu:** {calculate_group_bonus(member_count):,} 🐻

🎰 **OYUN TİPLERİ (En Popüler):**
• Slot Machine
• Blackjack  
• Crash
• Roulette

🔥 **ÖZELLİKLER:**
• Büyük kazançlar otomatik duyurulur
• Günlük grup bonusu
• Canlı istatistikler
• Rekabet ortamı

📈 **SONUÇ:** Bu grup aktif bir casino topluluğu!
            """
            
            await query.edit_message_text(
                stats_text,
                reply_markup=bot.casino.create_keyboard([
                    [("🔄 Güncelle", "group_stats"), ("🎮 Oyunlara Dön", "game_menu_return")],
                    [("👤 Profilim", "my_stats")]
                ]),
                parse_mode='Markdown'
            )
        elif data == "play_lucky_wheel":
            await handle_new_solo_game_menu(query, user, bot.casino, "lucky_wheel", "🎪 Lucky Wheel")
        
        # Mevcut solo oyunlar için bahis callback'leri
        elif data.startswith("play_game_"):
            # Format: play_game_GAMETYPE_BETAMOUNT
            parts = data.split("_")
            if len(parts) >= 4:
                game_type = parts[2]  # slots, roulette, blackjack, etc.
                try:
                    bet_amount = int(parts[3])
                    await handle_solo_game_play(query, user, bot.casino, game_type, bet_amount)
                except ValueError:
                    await query.edit_message_text("❌ Invalid bet amount!")
        
        # Yeni oyunlar için callback'ler
        elif data.startswith("play_new_game_"):
            # Format: play_new_game_GAMETYPE_BETAMOUNT
            parts = data.split("_")
            if len(parts) >= 5:
                game_type = parts[3]  # rock_paper_scissors, number_guess, lucky_wheel
                try:
                    bet_amount = int(parts[4])
                    await handle_new_solo_game_play(query, user, bot.casino, game_type, bet_amount)
                except ValueError:
                    await query.edit_message_text("❌ Invalid bet amount!")
        
        # İstatistikler menüsü
        elif data == "my_stats":
            await show_user_stats(query, user, bot.casino)
        
        elif data.startswith("play_solo_"):
            parts = data.split("_")
            if len(parts) >= 4:
                game_type = f"{parts[1]}_{parts[2]}"
                try:
                    bet_amount = int(parts[3])
                except ValueError:
                    await query.edit_message_text(
                        "❌ Invalid bet amount!",
                        reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                    )
                    return
                
                # Enhanced bet validation
                validation = bot.validate_bet_amount(user['user_id'], bet_amount, user['fun_coins'])
                if not validation['valid']:
                    await query.edit_message_text(
                        validation['reason'],
                        reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                    )
                    return
                
                if HANDLERS_AVAILABLE:
                    await handle_enhanced_solo_game(query, user, game_type, bet_amount, bot.casino, bot)
                else:
                    await handle_simple_solo_game(query, user, game_type, bet_amount, bot.casino)
        
        # Enhanced profile and other features  
        elif data == "profile":
            await show_enhanced_profile(query, user, bot.casino, bot)
        elif data == "daily_quests":
            if HANDLERS_AVAILABLE:
                await show_daily_quests(query, user, bot.casino)
            else:
                await show_simple_daily_quests(query, user, bot.casino)
        elif data == "achievements":
            if HANDLERS_AVAILABLE:
                await show_achievements(query, user, bot.casino)
            else:
                await show_simple_achievements(query, user, bot.casino)
        elif data == "leaderboard":
            if HANDLERS_AVAILABLE:
                await show_leaderboard(query, bot.casino)
            else:
                await show_simple_leaderboard(query, bot.casino)
        elif data == "leaderboard_daily":
            if HANDLERS_AVAILABLE:
                await show_leaderboard(query, bot.casino, "daily")
            else:
                await show_simple_leaderboard(query, bot.casino)
        elif data == "leaderboard_weekly":
            if HANDLERS_AVAILABLE:
                await show_leaderboard(query, bot.casino, "weekly")
            else:
                await show_simple_leaderboard(query, bot.casino)
        elif data == "leaderboard_monthly":
            if HANDLERS_AVAILABLE:
                await show_leaderboard(query, bot.casino, "monthly")
            else:
                await show_simple_leaderboard(query, bot.casino)
        elif data == "leaderboard_all":
            if HANDLERS_AVAILABLE:
                await show_leaderboard(query, bot.casino, "all_time")
            else:
                await show_simple_leaderboard(query, bot.casino)
        elif data == "tournaments":
            await show_tournament_menu(query, user, bot.casino)
        elif data == "friends":
            if HANDLERS_AVAILABLE:
                from other_handlers import show_friends
                await show_friends(query, user, bot.casino)
            else:
                await show_simple_friends_menu(query, user, bot.casino)
        elif data == "events":
            await show_events_menu(query, user, bot.casino)
        elif data == "bonus_features":
            if BONUS_MENU_AVAILABLE:
                await show_bonus_features_menu(query, user, bot.casino)
            else:
                await query.edit_message_text(
                    "ERROR: Bonus features not available. Please try again later.",
                    reply_markup=bot.casino.create_keyboard([[("🏠 Main Menu", "main_menu")]])
                )
        elif data == "daily_spinner":
            if HANDLERS_AVAILABLE:
                await show_daily_spinner(query, user, bot.casino)
            else:
                await query.edit_message_text(
                    "ERROR: Bonus features not available. Please try again later.",
                    reply_markup=bot.casino.create_keyboard([[('🏠 Main Menu', 'main_menu')]])
                )
        elif data == "fortune_wheel":
            if HANDLERS_AVAILABLE:
                await show_fortune_wheel(query, user, bot.casino)
            else:
                await query.edit_message_text(
                    "ERROR: Bonus features not available. Please try again later.",
                    reply_markup=bot.casino.create_keyboard([[('🏠 Main Menu', 'main_menu')]])
                )
        elif data == "mystery_box":
            if HANDLERS_AVAILABLE:
                await show_mystery_box(query, user, bot.casino)
            else:
                await query.edit_message_text(
                    "ERROR: Bonus features not available. Please try again later.",
                    reply_markup=bot.casino.create_keyboard([[('🏠 Main Menu', 'main_menu')]])
                )
        elif data == "achievement_showcase":
            if HANDLERS_AVAILABLE:
                await show_achievement_showcase(query, user, bot.casino)
            else:
                await query.edit_message_text(
                    "ERROR: Bonus features not available. Please try again later.",
                    reply_markup=bot.casino.create_keyboard([[('🏠 Main Menu', 'main_menu')]])
                )
        elif data.startswith("create_tournament_"):
            tournament_type = data.split("_", 2)[2]
            await handle_create_tournament(query, user, tournament_type, bot.casino)
        elif data.startswith("join_tournament_"):
            tournament_id = data.split("_", 2)[2]
            await handle_join_tournament(query, user, tournament_id, bot.casino)
        elif data == "add_friend":
            from other_handlers import show_add_friend_menu
            await show_add_friend_menu(query, user, bot.casino)
        elif data == "friend_requests":
            from other_handlers import show_friend_requests_menu
            await show_friend_requests_menu(query, user, bot.casino)
        elif data == "referral_stats":
            from other_handlers import show_referral_stats
            await show_referral_stats(query, user, bot.casino)
        elif data == "copy_friend_code":
            await query.answer("📋 Your friend code copied to clipboard!")
        elif data == "share_friend_code":
            await query.answer("📤 Your friend code is ready for sharing!")
        elif data == "enter_friend_code":
            await query.edit_message_text(
                "🔍 **ENTER FRIEND CODE** 🔍\n\n"
                "📝 **How it works:**\n"
                "• Ask your friend for their 6-digit code\n"
                "• Type the code in this chat (e.g.: ABC123)\n"
                "• Friend request will be sent automatically\n\n"
                "💡 **Example code format:** ABC123\n"
                "🔤 **Note:** Case doesn't matter!\n\n"
                "👇 **Enter the friend code now:**",
                reply_markup=bot.casino.create_keyboard([
                    [("🔙 Back", "add_friend"), ("👥 My Friends", "friends")],
                    [("🏠 Main Menu", "main_menu")]
                ]),
                parse_mode='Markdown'
            )
        elif data.startswith("accept_friend_"):
            friend_id = int(data.split("_", 2)[2])
            await handle_accept_friend(query, user, friend_id, bot.casino)
        elif data.startswith("reject_friend_"):
            friend_id = int(data.split("_", 2)[2])
            await handle_reject_friend(query, user, friend_id, bot.casino)
        
        # Admin commands
        elif data == "admin_panel" and is_admin_user(user['user_id']):
            await show_admin_panel(query, user, bot.casino)
        elif data == "admin_stats" and is_admin_user(user['user_id']):
            await show_admin_statistics(query, user, bot.casino)
        elif data == "admin_users" and is_admin_user(user['user_id']):
            await show_admin_user_management(query, user, bot.casino)
        elif data == "admin_broadcast" and is_admin_user(user['user_id']):
            await show_admin_broadcast_menu(query, user, bot.casino)
        elif data == "admin_broadcast_general" and is_admin_user(user['user_id']):
            await handle_admin_broadcast_general(query, user, bot.casino)
        elif data == "admin_broadcast_maintenance" and is_admin_user(user['user_id']):
            await handle_admin_broadcast_maintenance(query, user, bot.casino)
        elif data == "admin_broadcast_custom" and is_admin_user(user['user_id']):
            await handle_admin_broadcast_custom(query, user, bot.casino)
        elif data == "admin_broadcast_templates" and is_admin_user(user['user_id']):
            await handle_admin_broadcast_templates(query, user, bot.casino)
        elif data == "admin_settings" and is_admin_user(user['user_id']):
            await show_admin_settings(query, user, bot.casino)
        elif data.startswith("admin_user_") and is_admin_user(user['user_id']):
            parts = data.split("_")
            if len(parts) >= 4:
                action = parts[2]
                target_user_id = int(parts[3])
                await handle_admin_user_action(query, user, action, target_user_id, bot.casino)
        
        # Duel system
        elif data == "create_duel":
            await query.edit_message_text(
                "🔜 **YAKINDA** 🔜\n\n⚔️ Düello sistemi yakında gelecek!\n\n🚧 Şu anda geliştirme aşamasında...",
                reply_markup=bot.casino.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
            )
        elif data == "join_duel":
            await query.edit_message_text(
                "🔜 **YAKINDA** 🔜\n\n🎯 Düelloya katılma özelliği yakında gelecek!\n\n🚧 Şu anda geliştirme aşamasında...",
                reply_markup=bot.casino.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
            )
        elif data.startswith("create_duel_"):
            game_type = data.split("_", 2)[2]
            await handle_create_duel(query, user, game_type, bot.casino)
        elif data.startswith("join_"):
            game_id = data.split("_", 1)[1]
            await handle_join_game(query, user, game_id, bot.casino)
        
        # Enhanced daily bonus
        elif data == "daily_bonus":
            try:
                bonus_result = bot.casino.get_daily_bonus(user['user_id'])
                if bonus_result['success']:
                    # VIP bonus ekle
                    vip_level = bot.get_user_vip_level(user['user_id'])
                    if vip_level > 0:
                        vip_bonus = VIP_LEVELS[vip_level]['daily_bonus']
                        with bot.casino.db.get_connection() as conn:
                            conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?', 
                                       (vip_bonus, user['user_id']))
                            conn.commit()
                        
                        text = f"🎁 **DAILY BONUS RECEIVED!** 🎁\n\n"
                        text += f"🐻 **Standard Bonus:** +{bonus_result['bonus']} 🐻\n"
                        text += f"👑 **VIP {vip_level} Bonus:** +{vip_bonus} 🐻\n"
                        text += f"✨ **Total:** +{bonus_result['bonus'] + vip_bonus} 🐻\n\n"
                        text += f"🌟 Take advantage of VIP benefits!"
                    else:
                        text = f"🎁 **DAILY BONUS RECEIVED!** 🎁\n\n🐻 +{bonus_result['bonus']} Fun Coins 🌟\n\n👑 Earn more bonuses as VIP!"
                else:
                    text = f"ERROR: {bonus_result['message']}"
                    
                # Achievement check
                if bonus_result.get('success'):
                    bot.casino.unlock_achievement(user['user_id'], "daily_login")
                    
            except Exception as e:
                logger.error(f"Daily bonus error: {e}")
                text = "ERROR: Failed to get bonus. Please try again later."
                
            await query.edit_message_text(
                text,
                reply_markup=bot.casino.create_keyboard([
                    [("🎮 Play Game", "solo_games"), ("📊 Profile", "profile")],
                    [("👑 Become VIP", "vip_info"), ("🏠 Main Menu", "main_menu")]
                ]),
                parse_mode='Markdown'
            )
        
        # Handle insufficient funds
        elif data == "insufficient_funds":
            await query.edit_message_text(
                "💸 Insufficient balance! To play games or make investments:",
                reply_markup=bot.casino.create_keyboard([
                    [("💳 Make Deposit", "deposit_menu"), ("🎁 Daily Bonus", "daily_bonus")],
                    [("🎮 Low Stake Games", "solo_games"), ("🏠 Main Menu", "main_menu")]
                ])
            )
        
        # Redirect dice_games to solo_games (merged)
        elif data == "dice_games":
            await show_enhanced_solo_games_menu(query, user, bot.casino, bot)
        elif data.startswith("dice_game_options_"):
            try:
                dice_type = data.split("_", 3)[3]
                from dice_games import handle_dice_game_options
                await handle_dice_game_options(query, user, bot.casino, dice_type)
            except (ImportError, IndexError):
                await query.edit_message_text(
                    "❌ Dice game error!",
                    reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                )
        elif data.startswith("play_dice_"):
            try:
                # Remove "play_dice_" prefix to get the remaining part
                remaining = data[10:]  # len("play_dice_") = 10
                
                # Find the last underscore which separates dice_type from bet_amount
                last_underscore = remaining.rfind("_")
                if last_underscore == -1:
                    raise ValueError("Invalid dice callback format")
                
                dice_type = remaining[:last_underscore]
                bet_amount = int(remaining[last_underscore + 1:])
                
                from dice_games import handle_play_dice_game
                await handle_play_dice_game(query, user, bot.casino, dice_type, bet_amount)
            except (ImportError, ValueError, IndexError) as e:
                logger.error(f"Dice play error: {e}")
                await query.edit_message_text(
                    "❌ Dice game error!",
                    reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                )
        elif data == "dice_stats":
            try:
                from dice_games import handle_dice_statistics
                await handle_dice_statistics(query, user, bot.casino)
            except ImportError:
                await query.edit_message_text(
                    "📊 Statistics are currently unavailable.",
                    reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                )
        elif data.startswith("dice_"):
            # Handle individual dice game types
            try:
                dice_type = data.split("_", 1)[1]
                from dice_games import handle_dice_game_options
                await handle_dice_game_options(query, user, bot.casino, dice_type)
            except (ImportError, IndexError):
                await query.edit_message_text(
                    "❌ Invalid dice game!",
                    reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                )
        
        # Handle play_ callbacks for different game types 
        elif data.startswith("play_"):
            parts = data.split("_")
            if len(parts) >= 3:
                try:
                    game_type = f"{parts[1]}_{parts[2]}" if len(parts) >= 3 else parts[1]
                    bet_amount = int(parts[-1]) if parts[-1].isdigit() else 10
                    
                    # Use simple game handler if enhanced not available
                    await handle_simple_solo_game(query, user, game_type, bet_amount, bot.casino)
                except (ValueError, IndexError) as e:
                    logger.error(f"Play callback error: {e}")
                    await query.edit_message_text(
                        "❌ Invalid game data!",
                        reply_markup=bot.casino.create_keyboard([[("🎮 Solo Games", "solo_games")]])
                    )
        
        # Handle VIP info
        elif data == "vip_info":
            await show_vip_info(query, user, bot)
        
        # Handle game history
        elif data == "game_history":
            await show_game_history(query, user, bot.casino)
        
        # Handle settings
        elif data == "settings":
            await show_settings_menu(query, user, bot.casino)
        
        # Handle language selection  
        elif data == "language":
            try:
                from language_handler import show_language_selection
                await show_language_selection(query, user, bot.casino)
            except ImportError:
                await query.edit_message_text(
                    "🌐 Language selection is currently unavailable.",
                    reply_markup=bot.casino.create_keyboard([[("🏠 Main Menu", "main_menu")]])
                )
        
        # Handle notifications settings
        elif data == "notifications":
            await show_notifications_settings(query, user, bot.casino)
        elif data == "notifications_off":
            await query.edit_message_text(
                "🔕 All notifications have been turned off!\n\n⚙️ You can turn them on anytime from settings.",
                reply_markup=bot.casino.create_keyboard([[("⚙️ Back to Settings", "settings"), ("🏠 Main Menu", "main_menu")]])
            )
        elif data == "notifications_on":
            await query.edit_message_text(
                "🔔 All notifications have been turned on!\n\n📱 You will now be notified of all updates.",
                reply_markup=bot.casino.create_keyboard([[("⚙️ Back to Settings", "settings"), ("🏠 Main Menu", "main_menu")]])
            )
        
        # Handle privacy settings
        elif data == "privacy":
            await show_privacy_settings(query, user, bot.casino)
        elif data == "privacy_private":
            await query.edit_message_text(
                "🔒 Your profile is now private!\n\n👤 Only your friends can see your information.",
                reply_markup=bot.casino.create_keyboard([[("⚙️ Back to Settings", "settings"), ("🏠 Main Menu", "main_menu")]])
            )
        elif data == "privacy_public":
            await query.edit_message_text(
                "🌐 Your profile is now public!\n\n📊 All users can see your statistics.",
                reply_markup=bot.casino.create_keyboard([[("⚙️ Back to Settings", "settings"), ("🏠 Main Menu", "main_menu")]])
            )
        
        elif data.startswith("https://") or data.startswith("http://"):
            import webbrowser
            try:
                webbrowser.open(data)
                await query.answer("🌐 Link opening in browser...")
            except Exception as e:
                logger.error(f"Error opening URL {data}: {e}")
                await query.answer("❌ Could not open link")
        
        # Group game callbacks - Fixed for "Tekrar Oyna" functionality
        elif data.startswith("group_") and "_" in data:
            parts = data.split("_")
            if len(parts) >= 3:
                try:
                    # Handle group_GAMETYPE_BETAMOUNT format
                    game_type = "_".join(parts[1:-1])  # Everything between "group_" and the last part (bet amount)
                    bet_amount = int(parts[-1])  # Last part is the bet amount
                    
                    # Check if we're in a group chat
                    if not is_group_chat(query):
                        await query.edit_message_text(
                            "❌ Grup oyunları sadece grup sohbetlerinde oynanabilir!",
                            reply_markup=bot.casino.create_keyboard([[("🎮 Solo Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]])
                        )
                        return
                    
                    # Use independent group game handler
                    from independent_group_game_handler import handle_independent_group_game
                    await handle_independent_group_game(query, user, bot.casino, game_type, bet_amount)
                    
                except ValueError:
                    logger.error(f"Invalid bet amount in group game callback: {data}")
                    await query.edit_message_text("❌ Geçersiz bahis miktarı!")
                except Exception as e:
                    logger.error(f"Group game callback error: {e}")
                    await query.edit_message_text("❌ Oyun başlatılamadı, tekrar deneyiniz!")
        
        else:
            logger.warning(f"Unknown callback data received: {data}")
            await query.edit_message_text(
                f"❌ Unknown command: '{data}'\n\n🔄 Redirecting to main menu...",
                reply_markup=bot.casino.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
            
    except Exception as e:
        # Check if the error is just "Message is not modified"
        if "Message is not modified" in str(e):
            logger.debug(f"Callback handler: Message content unchanged, skipping update - {e}")
            return
        
        logger.error(f"Callback handler error: {e}")
        await safe_query_edit(query,
            "ERROR: An error occurred! Returning to main menu...",
            reply_markup=bot.casino.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

# Simplified helper functions for basic functionality
async def show_simple_solo_games_menu(query, user, casino_bot):
    """Simple solo games menu"""
    try:
        buttons = [
            [("🎰 Dice Slots", "dice_slot_machine"), ("🎯 Dart Game", "dice_darts")],
            [("🎲 Classic Dice", "dice_classic"), ("🏀 Basketball", "dice_basketball")],
            [("⚽ Football", "dice_football"), ("🎳 Bowling", "dice_bowling")],
            [("🎯 Roulette", "solo_roulette"), ("🃏 Blackjack", "solo_blackjack")],
            [("🚀 Crash", "solo_crash"), ("💣 Mines", "solo_mines")],
            [("🎴 Baccarat", "solo_baccarat"), ("🔢 Keno", "solo_keno")],
            [("🏠 Main Menu", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        text = f"""
🎮 **SOLO GAMES** 🎮

🐻 **Current Balance:** {user['fun_coins']:,} 🐻

🎯 **TELEGRAM DICE GAMES:**
🎰 **Dice Slots** - 3 makara, 64 kombinasyon!
🎯 **Dart Game** - Bullseye target shooting!
🎲 **Classic Dice** - 6-sided classic die!
🏀 **Basketball** - Basketball shooting game!
⚽ **Football** - Goal shooting game!
🎳 **Bowling** - Pin knockdown game!

🎯 **CLASSIC CASINO GAMES:**
🎯 **Roulette** - Red or black?
🃏 **Blackjack** - Reach 21!
🚀 **Crash** - Cash out in time!
💣 **Mines** - Avoid the mines!
🎴 **Baccarat** - Banker vs Player
🔢 **Keno** - Pick your numbers!

🌟 Which game would you like to play?
        """
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Solo games menu error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading menu.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_simple_solo_game_options(query, user, game_type, casino_bot):
    """Simple game options"""
    try:
        from config import SOLO_GAMES
        
        game_config = SOLO_GAMES.get(game_type)
        if not game_config:
            await query.edit_message_text("❌ Invalid game type!", 
                reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]]))
            return
        
        # Basic bet options
        balance = user['fun_coins']
        min_bet = game_config['min_bet']
        
        buttons = []
        for multiplier in [1, 5, 10, 25, 50]:
            bet = min_bet * multiplier
            if bet <= balance:
                buttons.append([(f"🐻 {bet:,} 🐻", f"play_{game_type}_{bet}")])
            else:
                buttons.append([(f"❌ {bet:,} 🐻 (Insufficient)", "insufficient_funds")])
        
        buttons.append([("🔙 Back", "solo_games"), ("🏠 Main Menu", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        
        text = f"""
🎮 **{game_config['name'].upper()}** 🎮

🐻 **Mevcut Bakiye:** {balance:,} 🐻
💎 **Minimum Bet:** {min_bet:,} 🐻

🎲 **Choose your bet amount:**
        """
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solo game options error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading game options.",
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]])
        )

async def handle_simple_solo_game(query, user, game_type, bet_amount, casino_bot):
    """Basit solo oyun handler"""
    try:
        # Create solo game engine
        solo_engine = SoloGameEngine()
        
        # Play game based on type
        if game_type == "solo_slots":
            result = solo_engine.play_solo_slots(bet_amount, user['user_id'])
        elif game_type == "solo_roulette":
            result = solo_engine.play_solo_roulette(bet_amount, "color", "red", user['user_id'])
        elif game_type == "solo_blackjack":
            result = solo_engine.play_solo_blackjack(bet_amount, user['user_id'])
        elif game_type == "solo_crash":
            result = solo_engine.play_solo_crash(bet_amount, 2.0, user['user_id'])
        elif game_type == "solo_mines":
            result = solo_engine.play_solo_mines(bet_amount, 3, 5, user['user_id'])
        elif game_type == "solo_baccarat":
            result = solo_engine.play_solo_baccarat(bet_amount, "player", user['user_id'])
        elif game_type == "solo_keno":
            result = solo_engine.play_solo_keno(bet_amount, [1, 2, 3, 4, 5], user['user_id'])
        elif game_type == "solo_dice":
            result = solo_engine.play_solo_dice(bet_amount, 4, user['user_id'])
        else:
            await query.edit_message_text("❌ Unknown game type!")
            return
        
        # Update user balance and stats
        casino_bot.update_user_stats(user['user_id'], bet_amount, result['win_amount'], result['won'])
        casino_bot.save_solo_game(user['user_id'], game_type, bet_amount, result)
        
        # Show result
        if result['won']:
            emoji = "🎉"
            status = "YOU WON!"
        else:
            emoji = "😢"
            status = "You lost!"
        
        result_text = f"""
{emoji} **{status}** {emoji}

🎮 **Game:** {game_type.replace('solo_', '').title()}
🐻 **Bet:** {bet_amount:,} 🐻
🎯 **Winnings:** {result['win_amount']:,} 🐻
📊 **Multiplier:** {result['multiplier'] if 'multiplier' in result else 0:.2f}x

💵 **New Balance:** {user['fun_coins'] - bet_amount + result['win_amount']:,} 🐻
        """
        
        buttons = [
            [("🎮 Play Again", f"solo_{game_type.split('_')[1]}"), ("🎯 Other Game", "solo_games")],
            [("📊 Profile", "profile"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Simple solo game error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while playing the game.",
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]])
        )

async def show_simple_profile(query, user, casino_bot):
    """Simple profile display"""
    try:
        stats = casino_bot.get_user_stats(user['user_id'])
        
        text = f"""
👤 **PROFILE** 👤

🆔 **User:** @{user['username'] or 'Anonymous'}
🐻 **Balance:** {user['fun_coins']:,} 🐻
⭐ **Level:** {user['level'] if 'level' in user else 1}
🎯 **XP:** {user['xp'] if 'xp' in user else 0:,}
🏆 **Win Rate:** {stats['win_rate'] if 'win_rate' in stats else 0:.1f}%

📊 **Statistics:**
Total Games: {stats['total_games'] if 'total_games' in stats else 0:,}
🏆 Won: {stats['games_won'] if 'games_won' in stats else 0:,}
💸 Lost: {stats['games_lost'] if 'games_lost' in stats else 0:,}
💎 Biggest Win: {stats['biggest_win'] if 'biggest_win' in stats else 0:,} 🐻
        """
        
        buttons = [
            [("🎁 Daily Bonus", "daily_bonus"), ("🏆 Achievements", "achievements")],
            [("🎮 Back to Games", "solo_games"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Simple profile error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading profile.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_simple_daily_quests(query, user, casino_bot):
    """Simple daily quests"""
    try:
        quests = casino_bot.get_daily_quests(user['user_id'])
        
        text = "🎁 <b>DAILY QUESTS</b> 🎁\n\n"
        
        for quest in quests:
            progress = quest['progress']
            target = quest['target']
            reward = quest['reward']
            completed = quest['completed']
            
            if completed:
                status = "Completed"
            else:
                status = f"📊 {progress}/{target}"
            
            text += f"• <b>{quest['quest_type']}</b>: {status} - {reward} 🐻\n"
        
        buttons = [
            [("🎮 Play Game", "solo_games"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Daily quests error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading quests.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_simple_achievements(query, user, casino_bot):
    """Basit achievementslar"""
    try:
        achievements = casino_bot.get_user_achievements(user['user_id'])
        
        text = f"🏆 **YOUR ACHIEVEMENTS** 🏆\n\n"
        text += f"📊 **Toplam:** {len(achievements)} achievements\n\n"
        
        if achievements:
            for ach in achievements[:5]:  # Show first 5
                text += f"🏅 **{ach['name'] if 'name' in ach else 'Achievement'}** - {ach['reward'] if 'reward' in ach else 0} 🐻\n"
            
            if len(achievements) > 5:
                text += f"... ve {len(achievements)-5} tane daha\n"
        else:
            text += "No achievements yet. Play games to earn achievements!\n"
        
        buttons = [
            [("🎮 Play Game", "solo_games"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Achievements error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading achievements.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_simple_leaderboard(query, casino_bot):
    """Basit liderlik tablosu"""
    try:
        with casino_bot.db.get_connection() as conn:
            top_users = conn.execute('''SELECT username, fun_coins, level 
                FROM users ORDER BY fun_coins DESC LIMIT 10''').fetchall()
        
        text = "🏆 **LEADERBOARD** 🏆\n\n"
        
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} **@{user['username'] or 'Anonim'}** - {user['fun_coins']:,} 🐻 (Lv.{user['level']})\n"
        
        buttons = [
            [("📊 Profil", "profile"), ("🎮 Play Game", "solo_games")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading leaderboard.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

# Original enhanced functions (keep for compatibility)
async def show_enhanced_solo_games_menu(query, user, casino_bot, bot_instance):
    """Enhanced solo games menu with VIP info"""
    try:
        vip_level = bot_instance.get_user_vip_level(user['user_id'])
        max_bet = bot_instance.get_user_max_bet(user['user_id'])
        
        buttons = [
            [("🎰 Dice Slots", "dice_slot_machine"), ("🎯 Dart Game", "dice_darts"), ("🎲 Classic Dice", "dice_classic")],
            [("🏀 Basketball", "dice_basketball"), ("⚽ Football", "dice_football"), ("🎳 Bowling", "dice_bowling")],
            [("🎯 Roulette", "solo_roulette"), ("🃏 Blackjack", "solo_blackjack"), ("🚀 Crash", "solo_crash")],
            [("💣 Mines", "solo_mines"), ("🎴 Baccarat", "solo_baccarat"), ("🔢 Keno", "solo_keno")],
            [("📊 Game History", "solo_history"), ("🏠 Main Menu", "main_menu")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        vip_text = f"👑 VIP {vip_level}" if vip_level > 0 else "🆕 Standart"
        
        text = f"""
🎮 **SOLO GAMES** 🎮

🐻 **Current Coins:** {user['fun_coins']:,}
🎯 **VIP Level:** {vip_text}
🚫 **Maximum Bet:** {max_bet:,} 🐻

┌──────── TELEGRAM DICE GAMES ────────┐
│ 🎰 **Dice Slots** - 64 kombinasyon! │
│ 🎯 **Dart Game** - Bullseye x10!    │
│ 🎲 **Classic Dice** - 6 sided die!  │
│ 🏀 **Basketball** - Basket shooting!   │
│ ⚽ **Football** - Gol shot!         │
│ 🎳 **Bowling** - Strike bonusu!     │
└──────────────────────────────────────┘

┌──────── CLASSIC CASINO GAMES ───────┐
│ 🎯 **Roulette** - Red/Black?    │
│ 🃏 **Blackjack** - Reach 21!       │
│ 🚀 **Crash** - Timing is key!    │
│ 💣 **Mines** - Dodge the mines!     │
│ 🎴 **Baccarat** - Banker or Player?        │
│ 🔢 **Keno** - Pick the numbers!         │
└──────────────────────────────────────┘

💡 **VIP Advantages:**
• Higher bet limits
• Bonus multipliers
• Priority support

🌟 Which solo adventure are you ready for?
        """
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Enhanced solo games menu error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading menu.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_enhanced_solo_game_options(query, user, game_type, casino_bot, bot_instance):
    """Enhanced solo game options with smart bet suggestions"""
    try:
        from config import SOLO_GAMES
        
        game_config = SOLO_GAMES.get(game_type)
        if not game_config:
            await query.edit_message_text("❌ Invalid game type!", 
                reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]]))
            return
        
        vip_level = bot_instance.get_user_vip_level(user['user_id'])
        max_bet = bot_instance.get_user_max_bet(user['user_id'])
        
        # Get smart bet suggestions
        suggestions = bot_instance.get_bet_suggestion(user['fun_coins'], vip_level)
        
        buttons = []
        for bet in suggestions:
            if user['fun_coins'] >= bet:
                percentage = (bet / user['fun_coins']) * 100
                buttons.append([(f"🐻 {bet:,} 🐻 ({percentage:.1f}%)", f"play_{game_type}_{bet}")])
            else:
                buttons.append([(f"❌ {bet:,} 🐻 (Insufficient)", "insufficient_funds")])
        
        # Add custom amount option
        min_bet = game_config['min_bet']
        if len(buttons) < 6:
            for multiplier in [1, 2, 5, 10]:
                custom_bet = min_bet * multiplier
                if custom_bet not in suggestions and custom_bet <= user['fun_coins'] and custom_bet <= max_bet:
                    buttons.append([(f"🎲 {custom_bet:,} 🐻", f"play_{game_type}_{custom_bet}")])
        
        # Add navigation buttons
        buttons.append([("🔙 Back", "solo_games"), ("🏠 Main Menu", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        
        game_name = game_config['name']
        game_description = game_config.get('description', 'Fun casino game!')
        
        text = f"""
🎮 **{game_name.upper()}** 🎮

📝 **Description:** {game_description}

🐻 **Current Balance:** {user['fun_coins']:,} 🐻
🎯 **VIP Level:** {vip_level}
🚫 **Maximum Bet:** {max_bet:,} 🐻
💎 **Minimum Bet:** {min_bet:,} 🐻

🎲 **BAHIS AMOUNT CHOOSE:**

💡 **Tips:**
• With small bets start
• VIP olarak higher limits
• Determine your winning strategy

🌟 Hangi miktarla oynamak istiyorsunz?
        """
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Enhanced solo game options error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading game options.",
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]])
        )

async def show_enhanced_profile(query, user, casino_bot, bot_instance):
    """Enhanced profile with VIP and payment info"""
    try:
        # Helper function to safely get values from user (handles both dict and sqlite3.Row)
        def safe_get(obj, key, default=None):
            try:
                # Check if it's a dictionary with get method
                if hasattr(obj, 'get') and not hasattr(obj, 'keys'):
                    return obj.get(key, default)
                # For sqlite3.Row or dict-like objects
                elif hasattr(obj, 'keys'):
                    return obj[key] if key in obj.keys() and obj[key] is not None else default
                else:
                    return obj[key] if key in dict(obj) else default
            except:
                return default
        
        vip_level = bot_instance.get_user_vip_level(user['user_id'])
        max_bet = bot_instance.get_user_max_bet(user['user_id'])
        
        # Get user stats
        stats = casino_bot.get_user_stats(user['user_id'])
        
        # Get payment stats if available
        if bot_instance.payment_manager:
            try:
                payment_stats = bot_instance.payment_manager.get_user_payment_stats(user['user_id'])
                total_deposited = payment_stats['total_deposits'] if 'total_deposits' in payment_stats else 0
                total_withdrawn = payment_stats['total_withdrawals'] if 'total_withdrawals' in payment_stats else 0
                net_position = total_deposited - total_withdrawn
            except:
                total_deposited = 0
                total_withdrawn = 0
                net_position = 0
        else:
            total_deposited = 0
            total_withdrawn = 0
            net_position = 0
        
        # Calculate next VIP level requirements
        next_vip_level = vip_level + 1
        next_vip_requirement = 0
        remaining_for_next_vip = 0
        
        if next_vip_level <= 5 and next_vip_level in VIP_LEVELS:
            next_vip_requirement = VIP_LEVELS[next_vip_level]['min_deposit']
            remaining_for_next_vip = max(0, next_vip_requirement - total_deposited)
        
        vip_status = f"👑 VIP {vip_level}" if vip_level > 0 else "🆕 Standart Member"
        
        text = f"""
👤 **PROFILE INFORMATION** 👤

🆔 **User:** @{user['username'] or 'Anonymous'}
🐻 **Bakiye:** {user['fun_coins']:,} Fun Coins
⭐ **Seviye:** {safe_get(user, 'level', 1)}
🎯 **XP:** {safe_get(user, 'xp', 0) or 0:,}
🏆 **VIP Durumu:** {vip_status}

📊 **GAME STATISTICS**
┌─────────────────────────────────┐
Total Games: {stats.get('total_games', 0) or 0:,}
🏆 Won: {stats.get('games_won', 0) or 0:,}
💸 Lost: {stats.get('games_lost', 0) or 0:,}
📈 Win Rate: {stats.get('win_rate', 0) or 0:.1f}%
💎 Biggest Win: {stats.get('biggest_win', 0) or 0:,} 🐻
📉 Biggest Loss: {stats.get('biggest_loss', 0) or 0:,} 🐻
└─────────────────────────────────┘

💳 **PAYMENT STATISTICS**
┌─────────────────────────────────┐
📥 Total Deposits: {total_deposited:,} 🐻
📤 Total Withdrawals: {total_withdrawn:,} 🐻
📊 Net Pozisyon: {net_position:+,} 🐻
└─────────────────────────────────┘

🎲 **BET LIMITS**
┌─────────────────────────────────┐
🚫 Maksimum Bahis: {max_bet:,} 🐻
🎯 Daily Limit: Unlimited
💎 VIP Advantages: {'Active' if vip_level > 0 else 'Inactive'}
└─────────────────────────────────┘
"""
        
        if next_vip_level <= 5:
            text += f"""
🎯 **SONRAKİ VIP SEVİYE**
┌─────────────────────────────────┐
🏆 Hedef: VIP {next_vip_level}
🐻 Gerekli: {next_vip_requirement:,} 🐻
📈 Kalan: {remaining_for_next_vip:,} 🐻
└─────────────────────────────────┘
"""
        
        # Get achievements
        achievements = casino_bot.get_user_achievements(user['user_id'])
        if achievements:
            text += f"\n🏅 **ACHIEVEMENTS** ({len(achievements)} items)\n"
            for ach in achievements[:3]:  # Show first 3
                text += f"• {safe_get(ach, 'name', 'Achievement')}\n"
            if len(achievements) > 3:
                text += f"• ... ve {len(achievements)-3} tane daha\n"
        
        buttons = [
            [("🎁 Daily Bonus", "daily_bonus"), ("🏆 Achievements", "achievements")],
            [("💳 Payment Transactions", "payment_menu"), ("👑 Become VIP", "vip_info")],
            [("📊 Liderlik Tablosu", "leaderboard"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Enhanced profile error: {e}")
        await query.edit_message_text(
            "❌ Error occurred while loading profile.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
**CASINO BOT HELP**

🎯 **Main Commands:**
• /start - Start the bot
• /help - This help message
• /profile - View your profile

🎲 **Game Types:**
• **Solo Games**: Slots, Roulette, Blackjack, Crash, Mines, Baccarat, Keno
• **Duel Games**: 1v1 battles with your friends
• **Tournaments**: Competitions with big prizes

🐻 **Payment System:**
• Crypto deposit/withdrawal (USDT, TON, BTC, etc.)
• Instant transaction confirmation
• VIP membership system
• Bonuses and promotions

🏆 **VIP Advantages:**
• Higher bet limits
• Special bonuses
• Priority support
• Low commission rates

📞 **Destek:**
• 24/7 automatic system
• Fast response guarantee

🎁 **Tips:**
• Don't forget to claim daily bonus
• With small bets start
• Earn more as VIP
• Play responsibly

Good luck! 🍀
    """
    
    try:
        keyboard = bot.casino.create_keyboard([
            [("🎮 Games", "solo_games"), ("🐻 Payment", "payment_menu")],
            [("👑 Become VIP", "vip_info"), ("🏠 Main Menu", "main_menu")]
        ])
        
        await update.message.reply_text(help_text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await update.message.reply_text("❌ Error occurred while sending help message.")

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Support command handler"""
    support_text = """
🆘 **DESTEK MERKEZİ**

📞 **İletişim:**
• Telegram: @admin_username
• Email: support@casino.com

❓ **Sık Sorulan Sorular:**
• Ödemeler 24 saat içinde işlenir
• Minimum çekim miktarı 10 USDT
• VIP üyelik otomatik aktif edilir

🔧 **Teknik Destek:**
• Bot çalışmıyor mu? /start deneyin
• Ödeme sorunu? SS gönderin
• Oyun hatası? Detay verin

⏰ **Destek Saatleri:**
• 7/24 Otomatik sistem
• Canlı destek: 09:00-21:00
    """

    try:
        keyboard = bot.casino.create_keyboard([
            [("💬 Canlı Destek", "contact_support"), ("📋 SSS", "faq")],
            [("🔙 Ana Menü", "main_menu")]
        ])

        await update.message.reply_text(support_text, reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Support command error: {e}")
        await update.message.reply_text("❌ Destek mesajı gönderilirken hata oluştu.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats command handler"""
    try:
        # Get bot stats
        uptime = datetime.now() - bot.bot_start_time
        uptime_str = f"{uptime.days}g {uptime.seconds//3600}s {(uptime.seconds//60)%60}d"
        
        # Get database stats
        with bot.casino.db.get_connection() as conn:
            total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            total_games = conn.execute('SELECT COUNT(*) FROM game_results').fetchone()[0]
            total_coins = conn.execute('SELECT SUM(fun_coins) FROM users').fetchone()[0] or 0
            
            # Active users (played in last 24h)
            active_users = conn.execute('''
                SELECT COUNT(DISTINCT user_id) FROM game_results 
                WHERE datetime(created_at) > datetime('now', '-1 day')
            ''').fetchone()[0]
        
        # Payment stats if available
        if bot.payment_manager:
            try:
                with bot.casino.db.get_connection() as conn:
                    total_deposits = conn.execute('SELECT COUNT(*) FROM deposits WHERE status = "paid"').fetchone()[0]
                    total_withdrawals = conn.execute('SELECT COUNT(*) FROM withdrawals WHERE status = "completed"').fetchone()[0]
                    deposit_volume = conn.execute('SELECT SUM(fun_coins) FROM deposits WHERE status = "paid"').fetchone()[0] or 0
                    withdrawal_volume = conn.execute('SELECT SUM(fun_coins) FROM withdrawals WHERE status = "completed"').fetchone()[0] or 0
            except:
                total_deposits = total_withdrawals = deposit_volume = withdrawal_volume = 0
        else:
            total_deposits = total_withdrawals = deposit_volume = withdrawal_volume = 0
        
        stats_text = f"""
📊 **BOT STATISTICS** 📊

⏰ **System Status**
┌─────────────────────────────────┐
🟢 Status: Active and Running
⏲️ Uptime: {uptime_str}
🔄 İşlenen Komut: {bot.total_commands_processed:,}
└─────────────────────────────────┘

👥 **Kullanıcı Statisticsi**
┌─────────────────────────────────┐
👤 Toplam Kullanıcı: {total_users:,}
🎮 Active Kullanıcı (24s): {active_users:,}
🎲 Toplam Oyun: {total_games:,}
🐻 Toplam Coin: {total_coins:,} 🐻
└─────────────────────────────────┘

💳 **Payment Statisticsi**
┌─────────────────────────────────┐
📥 Total Deposits: {total_deposits:,}
📤 Total Withdrawals: {total_withdrawals:,}
💎 Yatırım Hacmi: {deposit_volume:,} 🐻
💸 Çekim Hacmi: {withdrawal_volume:,} 🐻
└─────────────────────────────────┘

🔧 **Sistem Bilgileri**
┌─────────────────────────────────┐
🐍 Python: {sys.version.split()[0]}
💾 Veritabanı: SQLite
🔐 Payment: CryptoBot {'✅' if bot.payment_manager else '❌'}
🤖 Bot Versiyonu: 2.5.1
└─────────────────────────────────┘
        """
        
        keyboard = bot.casino.create_keyboard([
            [("📊 Liderlik", "leaderboard"), ("🏆 Achievements", "achievements")],
            [("🐻 Payment", "payment_menu"), ("🏠 Main Menu", "main_menu")]
        ])
        
        await update.message.reply_text(stats_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await update.message.reply_text("❌ Statistics yüklenirken error occurred.")

async def show_simple_payment_menu(query, user, casino_bot):
    """Simple payment menu fallback"""
    try:
        text = "💳 <b>PAYMENT OPTIONS</b> 💳\n\n"
        text += "🔹 <b>CryptoBot Integration</b>\n"
        text += "• Fast and secure crypto payments\n"
        text += "• Automatic Fun Coins credit\n\n"
        text += "🔹 <b>Solana Payments</b>\n"
        text += "• Native SOL deposits/withdrawals\n"
        text += "• Low transaction fees\n\n"
        text += "💎 Current Balance: <code>{}</code> FC\n".format(user['fun_coins'] if isinstance(user, dict) else user.get('fun_coins', 0) if hasattr(user, 'get') else 0)

        buttons = [
            [("🤖 CryptoBot", "cryptobot_menu"), ("🔮 Solana", "solana_payment")],
            [("💰 Balance", "profile"), ("🏠 Main Menu", "main_menu")]
        ]

        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Simple payment menu error: {e}")
        await query.edit_message_text(
            "❌ Payment menu loading error.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def get_group_member_count(bot, chat_id):
    """Get group member count - OPTIMIZED"""
    try:
        return await bot.get_chat_member_count(chat_id)
    except:
        return 1  # Default to 1 if can't get count

def calculate_group_bonus(member_count):
    """Calculate bonus based on group size"""
    if member_count >= 1000:
        return 500  # Large group bonus
    elif member_count >= 500:
        return 300  # Medium group bonus  
    elif member_count >= 100:
        return 200  # Small group bonus
    elif member_count >= 50:
        return 100  # Mini group bonus
    else:
        return 50   # Default bonus

async def get_group_stats(bot, chat_id, casino):
    """Get group gaming statistics - OPTIMIZED"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Single optimized query to get all stats at once
        casino.db.execute("""
            WITH today_games AS (
                SELECT user_id, username, win_amount, won 
                FROM solo_game_history 
                WHERE chat_id = ? AND date(created_at) = ?
            ),
            user_stats AS (
                SELECT username, COUNT(*) as game_count
                FROM today_games 
                GROUP BY user_id 
                ORDER BY game_count DESC 
                LIMIT 1
            )
            SELECT 
                (SELECT COUNT(*) FROM today_games) as games_today,
                (SELECT COALESCE(SUM(win_amount), 0) FROM today_games WHERE won = 1) as winnings_today,
                (SELECT COALESCE(username, 'Henüz yok') FROM user_stats) as top_player,
                (SELECT COALESCE(game_count, 0) FROM user_stats) as top_player_games
        """, (chat_id, today))
        
        result = casino.db.fetchone()
        
        return {
            'games_today': result[0] or 0,
            'winnings_today': result[1] or 0, 
            'top_player': result[2] or "Henüz yok",
            'top_player_games': result[3] or 0
        }
    except Exception as e:
        logger.error(f"Group stats error: {e}")
        return {
            'games_today': 0,
            'winnings_today': 0,
            'top_player': "Henüz yok", 
            'top_player_games': 0
        }

async def slots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Slots game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_slots", "🎰 Slot Machine")
    except Exception as e:
        logger.error(f"Slots command error: {e}")
        await update.message.reply_text("❌ Slot oyunu başlatılırken hata oluştu.")

async def roulette_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roulette game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_roulette", "🔴 Roulette")
    except Exception as e:
        logger.error(f"Roulette command error: {e}")
        await update.message.reply_text("❌ Roulette oyunu başlatılırken hata oluştu.")

async def blackjack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Blackjack game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_blackjack", "♠️ Blackjack")
    except Exception as e:
        logger.error(f"Blackjack command error: {e}")
        await update.message.reply_text("❌ Blackjack oyunu başlatılırken hata oluştu.")

async def crash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Crash game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_crash", "🚀 Crash")
    except Exception as e:
        logger.error(f"Crash command error: {e}")
        await update.message.reply_text("❌ Crash oyunu başlatılırken hata oluştu.")

async def mines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mines game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_mines", "⛏️ Mines")
    except Exception as e:
        logger.error(f"Mines command error: {e}")
        await update.message.reply_text("❌ Mines oyunu başlatılırken hata oluştu.")

async def baccarat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baccarat game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_baccarat", "🃏 Baccarat")
    except Exception as e:
        logger.error(f"Baccarat command error: {e}")
        await update.message.reply_text("❌ Baccarat oyunu başlatılırken hata oluştu.")

async def keno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Keno game command handler"""
    try:
        await handle_solo_game_menu_command(update, "solo_keno", "🎯 Keno")
    except Exception as e:
        logger.error(f"Keno command error: {e}")
        await update.message.reply_text("❌ Keno oyunu başlatılırken hata oluştu.")

async def handle_solo_game_menu_command(update: Update, game_type: str, game_name: str):
    """Handle solo game menu for command shortcuts"""
    user = await get_or_create_user(update.effective_user)
    if not user:
        await update.message.reply_text("❌ Kullanıcı bilgileri alınamadı!")
        return

    text = f"""
{game_name}

🎯 **Bahis Miktarı Seçin:**

💰 **Mevcut Bakiye:** {user['fun_coins']:,} Coins
🎮 **Oyun:** {game_name}
⚡ **Hızlı Oyna:** Bahis seçip oynayın!
    """

    buttons = [
        [("💰 10", f"solo_bet_{game_type}_10"), ("💰 50", f"solo_bet_{game_type}_50")],
        [("💰 100", f"solo_bet_{game_type}_100"), ("💰 500", f"solo_bet_{game_type}_500")],
        [("💰 1K", f"solo_bet_{game_type}_1000"), ("💰 5K", f"solo_bet_{game_type}_5000")],
        [("🎮 Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]
    ]

    keyboard = bot.casino.create_keyboard(buttons)
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Game command handler - Only works in groups"""
    try:
        # Check if this is a group chat
        if not is_group_chat(update):
            await update.message.reply_text(
                "🚫 Bu komut sadece grup chatlerinde kullanılabilir!\n\n"
                "💡 Özel mesajda oyun oynamak için bot ile direkt konuşun ve /start yazın.",
                parse_mode='Markdown'
            )
            return
            
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"
        
        # Get or create user
        user = bot.casino.get_user(user_id, username)
        
        # Calculate group bonus
        chat_id = update.effective_chat.id
        group_members = await get_group_member_count(context.bot, chat_id)
        group_bonus = calculate_group_bonus(group_members)
        
        # Apply group bonus if eligible
        bonus_applied = False
        if group_bonus > 0:
            # Check if user already got bonus today
            today = datetime.now().strftime('%Y-%m-%d')
            bonus_key = f"group_bonus_{chat_id}_{user_id}_{today}"
            
            try:
                # Check if bonus already given today
                bot.casino.db.execute(
                    "SELECT id FROM user_bonuses WHERE user_id = ? AND bonus_type = ? AND date(created_at) = date('now')",
                    (user_id, f"group_bonus_{chat_id}")
                )
                if not bot.casino.db.fetchone():
                    # Give group bonus
                    bot.casino.db.execute(
                        "UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?",
                        (group_bonus, user_id)
                    )
                    bot.casino.db.execute(
                        "INSERT INTO user_bonuses (user_id, bonus_type, amount, created_at) VALUES (?, ?, ?, datetime('now'))",
                        (user_id, f"group_bonus_{chat_id}", group_bonus)
                    )
                    bot.casino.db.commit()
                    bonus_applied = True
                    user = bot.casino.get_user(user_id, username)  # Refresh user data
            except:
                pass  # Ignore bonus errors
        
        # Get group statistics
        group_stats = await get_group_stats(context.bot, chat_id, bot.casino)
        
        # Create enhanced solo games menu for groups
        bonus_text = ""
        if bonus_applied:
            bonus_text = f"🎁 **GRUP BONUSU ALDIN!** +{group_bonus:,} 🐻\n\n"
        elif group_bonus > 0:
            bonus_text = f"🎁 **Grup Bonusu:** {group_bonus:,} 🐻 (günlük)\n\n"
        
        games_text = f"""
🎮 **GRUP SOLO OYUN MENÜSÜ** 🎮

👋 Hello {username}! Welcome to group solo gaming!

{bonus_text}📊 **GROUP STATISTICS (Today):**
🎯 **Games Played:** {group_stats['games_today']} games
💰 **Total Winnings:** {group_stats['winnings_today']:,} 🐻
👑 **Most Active:** {group_stats['top_player']} ({group_stats['top_player_games']} games)
👥 **Member Count:** {group_members} members

🎯 **Classic Casino Games (4 games):**
• 🎰 **Slot Machine** - 3 reel luck!
• 🔴 **Roulette** - Red or black?
• ♠️ **Blackjack** - 21'e yaklaş!
• 🃏 **Baccarat** - Banker vs Player!

🚀 **Modern Oyunlar (3 oyun):**
• 🚀 **Crash** - Roket kaçmadan çık!
• ⛏️ **Mines** - Mayınları sakın!
• 🎯 **Keno** - Sayıları tahmin et!

🎲 **Telegram Dice Oyunları (6 oyun):**
• 🎲 **Klasik Zar** - 1-6 arası gerçek zar!
• 🎯 **Dart** - Bullseye vur! (x10)
• 🏀 **Basketbol** - Basket at! (x5)
• ⚽ **Futbol** - Gol vur! (x5)
• 🎳 **Bowling** - Strike! (x6)
• 🎰 **Dice Slot** - 64 kombinasyon!

🎪 **Eğlence Oyunları (4 oyun):**
• 🎪 **Lucky Wheel** - Şans çarkı!
• 🎲 **Solo Zar** - Basit zar oyunu!
• ✂️ **Taş-Kağıt-Makas** - Klasik!
• 🔢 **Sayı Tahmin** - 1-100 arası!

💰 **Bakiyeniz:** {user['fun_coins']:,} 🐻
🎮 **Oyun Sayınız:** {user['games_count'] if 'games_count' in user.keys() else 0}

⚠️ **NOT:** Tüm oyunlar 100🐻 sabit bahisle oynanır.
🔥 **Big wins are announced to the group!**
        """
        
        # Create complete game selection keyboard for groups - 6 GAMES
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard_buttons = [
            # Telegram Dice Games (6 games)
            [InlineKeyboardButton("🎰 Dice Slot (100🐻)", callback_data="group_dice_slot_100"),
             InlineKeyboardButton("⚽ Futbol (100🐻)", callback_data="group_dice_football_100")],
            [InlineKeyboardButton("🎳 Bowling (100🐻)", callback_data="group_dice_bowling_100")],
            [InlineKeyboardButton("🎲 Klasik Zar (100🐻)", callback_data="group_dice_classic_100"),
             InlineKeyboardButton("🎯 Dart (100🐻)", callback_data="group_dice_darts_100")],
            [InlineKeyboardButton("🏀 Basketbol (100🐻)", callback_data="group_dice_basketball_100")],
            # Menu Options
            [InlineKeyboardButton("📊 Grup İstatistikleri", callback_data="group_stats"),
             InlineKeyboardButton("👤 Profilim", callback_data="my_stats")],
            [InlineKeyboardButton("💬 Bot ile Özel Oyna", url=f"https://t.me/{context.bot.username}?start=fullgames")]
        ]
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await update.message.reply_text(games_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Game command error: {e}")
        await update.message.reply_text("❌ Oyun menüsü yüklenirken hata oluştu.")

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Games command handler - Full games menu (private chats)"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"
        
        # Get or create user
        user = bot.casino.get_user(user_id, username)
        
        # Create games menu with fun emojis
        games_text = f"""
🎮 **SOLO GAMES MENU** 🎮

👋 Hey {username}! Bireysel oyunlar menüsüne hoş geldin!

🎯 **Hızlı Oyunlar:**
• 🎰 **Slot Machine** - Şansını dene!
• 🔴 **Roulette** - Red or black?
• ♠️ **Blackjack** - 21'e yakın!
• 🚀 **Crash** - Rocket game!

🧠 **Zeka Oyunları:**
• ⛏️ **Mines** - Mayınları bul!
• 🎲 **Dice** - Zarları at!
• 🃏 **Baccarat** - Kart oyunu!
• 🎯 **Keno** - Sayı tahmin et!

🆕 **Yeni Eklenen:**
• ✂️ **Taş-Kağıt-Makas** - Klasik!
• 🔢 **Sayı Tahmin** - 1-100 arası!
• 🎪 **Lucky Wheel** - Döndür kazın!

💰 **Bakiyeniz:** {user['fun_coins']:,} 🐻
🎮 **Oyun Sayınız:** {user['games_count'] if 'games_count' in user.keys() else 0}

Hangi oyunu oynamak istiyorsun?
        """
        
        # Create game selection keyboard
        keyboard = bot.casino.create_keyboard([
            [("🎰 Slot", "play_solo_slot"), ("🔴 Roulette", "play_solo_roulette")],
            [("♠️ Blackjack", "play_solo_blackjack"), ("🚀 Crash", "play_solo_crash")],
            [("⛏️ Mines", "play_solo_mines"), ("🃏 Baccarat", "play_solo_baccarat")],
            [("🎯 Keno", "play_solo_keno"), ("🎲 Dice", "play_solo_dice")],
            [("✂️ Taş-Kağıt-Makas", "play_rock_paper_scissors"), ("🔢 Sayı Tahmin", "play_number_guess")],
            [("🎪 Lucky Wheel", "play_lucky_wheel"), ("📊 İstatistikler", "my_stats")],
            [("🏠 Ana Menü", "main_menu")]
        ])
        
        await update.message.reply_text(games_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Games command error: {e}")
        await update.message.reply_text("❌ Oyunlar menüsü yüklenirken hata oluştu.")


# GROUP-ONLY SLASH COMMANDS FOR DICE GAMES
async def diceslots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dice Slots command - Group only"""
    if not is_group_chat(update):
        await update.message.reply_text("🚫 Bu komut sadece grup chatlerinde kullanılabilir!")
        return
    await play_group_dice_game(update, context, "slot_machine", "🎰 Dice Slots")

async def dartgame_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dart Game command - Group only"""
    if not is_group_chat(update):
        await update.message.reply_text("🚫 Bu komut sadece grup chatlerinde kullanılabilir!")
        return
    await play_group_dice_game(update, context, "darts", "🎯 Dart Game")

async def classicdice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Classic Dice command - Group only"""
    if not is_group_chat(update):
        await update.message.reply_text("🚫 Bu komut sadece grup chatlerinde kullanılabilir!")
        return
    await play_group_dice_game(update, context, "classic_dice", "🎲 Classic Dice")

async def basketball_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basketball command - Group only"""
    if not is_group_chat(update):
        await update.message.reply_text("🚫 Bu komut sadece grup chatlerinde kullanılabilir!")
        return
    await play_group_dice_game(update, context, "basketball", "🏀 Basketball")

async def football_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Football command - Group only"""
    if not is_group_chat(update):
        await update.message.reply_text("🚫 Bu komut sadece grup chatlerinde kullanılabilir!")
        return
    await play_group_dice_game(update, context, "football", "⚽ Football")

async def bowling_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bowling command - Group only"""
    if not is_group_chat(update):
        await update.message.reply_text("🚫 Bu komut sadece grup chatlerinde kullanılabilir!")
        return
    await play_group_dice_game(update, context, "bowling", "🎳 Bowling")

# Additional command wrappers for private chat features
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Profile command - redirects to main menu profile section"""
    await start_command(update, context)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Balance command - redirects to main menu"""
    await start_command(update, context)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Daily bonus command - redirects to main menu"""
    await start_command(update, context)

async def spinner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Daily spinner command - redirects to main menu"""
    await start_command(update, context)

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deposit command - redirects to main menu"""
    await start_command(update, context)

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Withdraw command - redirects to main menu"""
    await start_command(update, context)

async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Achievements command - redirects to main menu"""
    await start_command(update, context)

async def friends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Friends command - redirects to main menu"""
    await start_command(update, context)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leaderboard command - redirects to main menu"""
    await start_command(update, context)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command - redirects to main menu"""
    await start_command(update, context)

async def play_group_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE, dice_type: str, game_name: str):
    """Play a dice game directly in group with 100 coins bet"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"

        # Get user data
        user = bot.casino.get_user(user_id, username)

        # Check balance (100 coins fixed bet)
        bet_amount = 100
        if user['fun_coins'] < bet_amount:
            await update.message.reply_text(
                f"💸 Yetersiz bakiye!\n\n"
                f"{game_name} oynamak için {bet_amount} 🐻 gerekli.\n"
                f"🐻 **Bakiyeniz:** {user['fun_coins']} 🐻\n\n"
                f"💡 /start ile günlük bonus alabilirsiniz!"
            )
            return

        # Import dice games handler
        from dice_games import get_dice_games_instance
        dice_games = get_dice_games_instance(bot.casino)

        # Create a mock query object for dice game handler
        class MockQuery:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user

            async def edit_message_text(self, text, **kwargs):
                await self.message.reply_text(text, **kwargs)

        mock_query = MockQuery(update.message)

        # Play the dice game
        await dice_games.play_dice_game(mock_query, user, dice_type, bet_amount)

    except Exception as e:
        logger.error(f"Group dice game error ({dice_type}): {e}")
        await update.message.reply_text(f"❌ {game_name} oynanırken hata oluştu!")

async def handle_custom_sol_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user):
    """Handle custom SOL amount input from user"""
    try:
        # Clear the waiting flag
        context.user_data['waiting_for_custom_sol_amount'] = False

        # Try to parse the SOL amount
        try:
            # Replace comma with dot if user used comma
            text = text.replace(',', '.')
            sol_amount = float(text)

            # Validate amount
            if sol_amount < 0.01:
                await update.message.reply_text(
                    "❌ **Minimum miktar hatası!**\n\n"
                    "💰 **Minimum:** 0.01 SOL\n"
                    "📝 **Girdiğiniz:** {:.4f} SOL\n\n"
                    "💡 Lütfen minimum 0.01 SOL girin.".format(sol_amount),
                    reply_markup=bot.casino.create_keyboard([
                        [("💎 Tekrar Dene", "deposit_sol_custom")],
                        [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return

            if sol_amount > 100:
                await update.message.reply_text(
                    "❌ **Maksimum miktar hatası!**\n\n"
                    "💰 **Maksimum:** 100 SOL\n"
                    "📝 **Girdiğiniz:** {:.4f} SOL\n\n"
                    "💡 Lütfen maksimum 100 SOL girin.".format(sol_amount),
                    reply_markup=bot.casino.create_keyboard([
                        [("💎 Tekrar Dene", "deposit_sol_custom")],
                        [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return

            # Valid amount - show confirmation
            from solana_handlers import show_sol_amount_confirmation

            # Create a fake query object for compatibility
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user

                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    # Send new message instead of editing
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

                async def answer(self, text="", show_alert=False):
                    pass

            fake_query = FakeQuery(update.message)
            await show_sol_amount_confirmation(fake_query, user, sol_amount, bot.casino)

        except ValueError:
            await update.message.reply_text(
                "❌ **Geçersiz format!**\n\n"
                "💡 **Doğru format örnekleri:**\n"
                "• 0.5 (yarım SOL)\n"
                "• 1.25 (bir buçuk SOL)\n"
                "• 2.75 (iki üçte dört SOL)\n\n"
                "⚠️ **Dikkat:**\n"
                "• Sadece sayı girin\n"
                "• Nokta kullanın (virgül değil)\n"
                "• SOL yazmayın",
                reply_markup=bot.casino.create_keyboard([
                    [("💎 Tekrar Dene", "deposit_sol_custom")],
                    [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
                ]),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Custom SOL amount input error: {e}")
        await update.message.reply_text(
            "❌ İşlem sırasında hata oluştu.\n\n"
            "Lütfen tekrar deneyin veya önceden tanımlanmış miktarları kullanın.",
            reply_markup=bot.casino.create_keyboard([
                [("🔙 Geri", "solana_deposit"), ("🏠 Ana Menü", "main_menu")]
            ])
        )

async def handle_custom_withdrawal_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user):
    """Handle custom withdrawal SOL amount input from user"""
    try:
        # Clear the waiting flag
        context.user_data['waiting_for_custom_withdrawal_amount'] = False

        # Try to parse the SOL amount
        try:
            # Replace comma with dot if user used comma
            text = text.replace(',', '.')
            sol_amount = float(text)

            # Get current rate and calculate max withdrawal
            from solana_payment import get_solana_payment
            solana_system = get_solana_payment()
            current_rate = solana_system.get_sol_to_fc_rate()
            user_balance = user['fun_coins']
            max_sol = user_balance / current_rate

            # Validate amount
            if sol_amount < 0.01:
                await update.message.reply_text(
                    "❌ **Minimum miktar hatası!**\n\n"
                    "💰 **Minimum:** 0.01 SOL\n"
                    "📝 **Girdiğiniz:** {:.4f} SOL\n\n"
                    "💡 Lütfen minimum 0.01 SOL girin.".format(sol_amount),
                    reply_markup=bot.casino.create_keyboard([
                        [("💎 Tekrar Dene", "withdraw_sol_custom")],
                        [("🔙 Geri", "solana_withdraw"), ("🏠 Ana Menü", "main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return

            if sol_amount > max_sol:
                await update.message.reply_text(
                    "❌ **Yetersiz bakiye!**\n\n"
                    "💰 **Maksimum çekim:** {:.4f} SOL\n"
                    "💸 **Mevcut bakiye:** {:.0f} FC\n"
                    "📝 **Girdiğiniz:** {:.4f} SOL\n\n"
                    "💡 Bakiyenizden fazla çekemezsiniz.".format(max_sol, user_balance, sol_amount),
                    reply_markup=bot.casino.create_keyboard([
                        [("💎 Tekrar Dene", "withdraw_sol_custom")],
                        [("💰 Bakiye Yükle", "solana_deposit")],
                        [("🔙 Geri", "solana_withdraw"), ("🏠 Ana Menü", "main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
                return

            # Valid amount - show wallet input
            from solana_handlers import show_withdrawal_wallet_input

            # Create a fake query object for compatibility
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.from_user = message.from_user

                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    # Send new message instead of editing
                    await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)

                async def answer(self, text="", show_alert=False):
                    pass

            fake_query = FakeQuery(update.message)
            await show_withdrawal_wallet_input(fake_query, user, sol_amount, bot.casino)

        except ValueError:
            await update.message.reply_text(
                "❌ **Geçersiz format!**\n\n"
                "💡 **Doğru format örnekleri:**\n"
                "• 0.5 (yarım SOL)\n"
                "• 1.25 (bir buçuk SOL)\n"
                "• 2.75 (iki üçte dört SOL)\n\n"
                "⚠️ **Dikkat:**\n"
                "• Sadece sayı girin\n"
                "• Nokta kullanın (virgül değil)\n"
                "• SOL yazmayın",
                reply_markup=bot.casino.create_keyboard([
                    [("💎 Tekrar Dene", "withdraw_sol_custom")],
                    [("🔙 Geri", "solana_withdraw"), ("🏠 Ana Menü", "main_menu")]
                ]),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Custom withdrawal amount input error: {e}")
        await update.message.reply_text(
            "❌ İşlem sırasında hata oluştu.\n\n"
            "Lütfen tekrar deneyin veya önceden tanımlanmış miktarları kullanın.",
            reply_markup=bot.casino.create_keyboard([
                [("🔙 Geri", "solana_withdraw"), ("🏠 Ana Menü", "main_menu")]
            ])
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (like friend codes and wallet addresses)"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        text = update.message.text.strip()

        # Get user data
        user = bot.casino.get_user(user_id, username)

        # Check if user is waiting for wallet address input
        if context.user_data.get('waiting_for_withdrawal_address'):
            from solana_flow_completion import handle_withdrawal_address_input
            await handle_withdrawal_address_input(update, context, text)
            return

        # Check if user is waiting for custom SOL amount input
        if context.user_data.get('waiting_for_custom_sol_amount'):
            await handle_custom_sol_amount_input(update, context, text, user)
            return

        # Check if user is waiting for custom withdrawal amount input
        if context.user_data.get('waiting_for_custom_withdrawal_amount'):
            await handle_custom_withdrawal_amount_input(update, context, text, user)
            return

        # Check if text looks like a friend code (6 characters, alphanumeric)
        # Auto-convert to uppercase for easier user experience
        if len(text) == 6 and text.isalnum():
            friend_code = text.upper()
            result = bot.casino.add_friend_by_code(user_id, friend_code)
            
            if result['success']:
                await update.message.reply_text(
                    f"✅ {result['message']}\n\n"
                    "📬 Arkadaşlık isteği gönderildi!\n"
                    "👥 Kabul edildiğinde arkadaş listenizde görünecek.",
                    reply_markup=bot.casino.create_keyboard([
                        [("👥 Arkadaşlarım", "friends"), ("📬 İstekler", "friend_requests")],
                        [("🏠 Main Menu", "main_menu")]
                    ])
                )
            else:
                await update.message.reply_text(
                    f"❌ {result['message']}\n\n"
                    "💡 **Tips:**\n"
                    "• 6 haneli kod olmalı (örn: ABC123)\n"
                    "• Büyük/küçük harf önemli değil\n"
                    "• Geçerli bir arkadaş kodu olmalı",
                    reply_markup=bot.casino.create_keyboard([
                        [("➕ Arkadaş Ekle", "add_friend")],
                        [("🏠 Main Menu", "main_menu")]
                    ])
                )
        else:
            # Not a friend code, ignore or provide help
            await update.message.reply_text(
                "🤔 Anlayamadım!\n\n"
                "💡 **Yapabilecekleriniz:**\n"
                "• 6 haneli arkadaş kodu girin (örn: ABC123)\n"
                "• /start - Start the botın\n"
                "• /help - Yardım alın",
                reply_markup=bot.casino.create_keyboard([
                    [("🎮 Oyuna Başla", "main_menu")],
                    [("❓ Yardım", "help")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Text message handler error: {e}")
        await update.message.reply_text(
            "❌ Mesajınız işlenirken error occurred!\n"
            "🔄 Lütfen tekrar deneyin veya /start yazın."
        )

async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot added/removed from groups"""
    try:
        result = update.my_chat_member
        chat = update.effective_chat
        user = update.effective_user
        
        old_status = result.old_chat_member.status
        new_status = result.new_chat_member.status
        
        logger.info(f"Bot status change in chat {chat.id} ({chat.title}): {old_status} -> {new_status}")
        
        # Bot was added to a group/channel
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator']:
            if chat.type in ['group', 'supergroup']:
                # Send welcome message to the group
                welcome_text = f"""
🎰 **Casino Bot'a Hoş Geldiniz!** 🎰

Hello! I'm a casino bot and I've been added to your group! 🎉

🎮 **What I can do:**
• Slot machines, roulette and more casino games
• Multiplayer duels and tournaments
• Daily bonuses and VIP system
• Secure crypto payments
• Friends system and leaderboard

🚀 **To get started:**
• Start private chat with bot: /start
• Oyunları görüntülemek için burada /start yazın
• Grup üyeleriniz de bot ile oynayabilir!

⚡ **Hızlı başlangıç:** /start komutu ile oyuna başlayın!

📝 Not: Bot'un çalışması için bot ile özel mesajlaşma başlatmanız gerekir.
                """
                
                keyboard = bot.casino.create_keyboard([
                    [("🎮 Oyuna Başla", f"https://t.me/{context.bot.username}?start=group")],
                    [("📊 Bot Hakkında", "about_bot")]
                ])
                
                try:
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=welcome_text,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Welcome message sent to group {chat.title} ({chat.id})")
                except Exception as e:
                    logger.error(f"Failed to send welcome message to group {chat.id}: {e}")
        
        # Bot was removed from group
        elif old_status in ['member', 'administrator'] and new_status in ['left', 'kicked']:
            logger.info(f"Bot removed from group {chat.title} ({chat.id}) by user {user.username if user else 'Unknown'}")
            
    except Exception as e:
        logger.error(f"Error handling my_chat_member update: {e}")

async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user join/leave events in groups where bot is present"""
    try:
        result = update.chat_member
        chat = update.effective_chat
        user = result.from_user
        
        old_status = result.old_chat_member.status
        new_status = result.new_chat_member.status
        
        # User joined the group
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
            if chat.type in ['group', 'supergroup']:
                welcome_text = f"""👋 Hoş geldin {user.first_name}!

🎰 Bu grupta Casino Bot var!
Bot ile oynayarak eğlenebilir ve ödüller kazanabilirsin!

🎮 Oyuna başlamak için:
• Bot ile özel mesaj başlat: @{context.bot.username}
• Veya buraya /start yaz

🎁 İlk kez katıldığın için bonus kazanabilirsin!"""
                
                keyboard = bot.casino.create_keyboard([
                    [("🎮 Bot ile Oyna", f"https://t.me/{context.bot.username}?start=welcome")]
                ])

                try:
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=welcome_text,
                        reply_markup=keyboard,
                        parse_mode=None
                    )
                except Exception as e:
                    logger.error(f"Failed to send user welcome message: {e}")
        
    except Exception as e:
        logger.error(f"Error handling chat_member update: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Beklenmeyen bir error occurred!\n\n"
                "🔄 Lütfen /start komutu ile botunu yeniden başlatın."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

def check_instance():
    """Check if another bot instance is already running"""
    pid_file = "casino_bot.pid"
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running on Windows
            try:
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'], 
                                      capture_output=True, text=True, shell=True)
                if str(old_pid) in result.stdout:
                    logger.error(f"Another bot instance is already running with PID {old_pid}")
                    logger.error("Please stop the other instance before starting a new one")
                    sys.exit(1)
                else:
                    # Process not running, remove stale PID file
                    os.remove(pid_file)
            except Exception:
                # If we can't check, remove the PID file and continue
                os.remove(pid_file)
        except (ValueError, FileNotFoundError):
            # Invalid or missing PID file, remove it
            if os.path.exists(pid_file):
                os.remove(pid_file)
    
    # Write current PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    return pid_file

def cleanup_pid_file(pid_file):
    """Remove PID file on exit"""
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception as e:
        logger.warning(f"Could not remove PID file: {e}")

async def setup_bot_commands(bot):
    """Setup bot commands with different visibility for groups vs private chats"""
    try:
        from telegram import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats

        # Commands for private chats (DM) - kişisel özellikler
        private_commands = [
            BotCommand("start", "🚀 Botu başlat"),
            BotCommand("help", "❓ Yardım menüsü"),
            BotCommand("support", "🆘 Destek al"),
            BotCommand("stats", "📊 İstatistiklerim"),
            BotCommand("games", "🎮 Oyunlar menüsü"),
            BotCommand("profile", "👤 Profilim"),
            BotCommand("balance", "💰 Bakiyem"),
            BotCommand("daily", "🎁 Günlük bonus"),
            BotCommand("spinner", "🎡 Günlük çark"),
            BotCommand("deposit", "💳 Para yatır"),
            BotCommand("withdraw", "💸 Para çek"),
            BotCommand("achievements", "🏆 Başarılarım"),
            BotCommand("friends", "👥 Arkadaşlarım"),
            BotCommand("leaderboard", "🥇 Liderlik tablosu"),
            BotCommand("settings", "⚙️ Ayarlar")
        ]

        # Commands for group chats - sadece support ve dice oyunları
        group_commands = [
            BotCommand("support", "🆘 Destek al"),
            BotCommand("diceslots", "🎲 Dice Slots"),
            BotCommand("dartgame", "🎯 Dart Game"),
            BotCommand("classicdice", "🎲 Classic Dice"),
            BotCommand("basketball", "🏀 Basketball"),
            BotCommand("football", "⚽ Football"),
            BotCommand("bowling", "🎳 Bowling")
        ]

        # Set commands for private chats
        # await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        # logger.info("SUCCESS: Private chat commands set (no /game)")

        # Set commands for group chats
        # await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
        # logger.info("SUCCESS: Group chat commands set (with /game)")

        # Clear all commands temporarily
        await bot.set_my_commands([])
        logger.info("SUCCESS: All commands cleared")

    except Exception as e:
        logger.error(f"ERROR: Failed to setup bot commands: {e}")

async def run_main_bot():
    """Async function to run the bot properly"""
    try:
        # Create HTTPx request with proper configuration
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connection_pool_size=512,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=60,
            pool_timeout=30,
            http_version="1.1"
        )

        application = Application.builder().token(BOT_TOKEN).request(request).build()

        # Add handlers - All available commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("support", support_command))
        application.add_handler(CommandHandler("games", games_command))
        application.add_handler(CommandHandler("slots", slots_command))
        application.add_handler(CommandHandler("roulette", roulette_command))
        application.add_handler(CommandHandler("blackjack", blackjack_command))
        application.add_handler(CommandHandler("crash", crash_command))
        application.add_handler(CommandHandler("mines", mines_command))
        application.add_handler(CommandHandler("baccarat", baccarat_command))
        application.add_handler(CommandHandler("keno", keno_command))
        application.add_handler(CommandHandler("diceslots", diceslots_command))
        application.add_handler(CommandHandler("dartgame", dartgame_command))
        application.add_handler(CommandHandler("classicdice", classicdice_command))
        application.add_handler(CommandHandler("basketball", basketball_command))
        application.add_handler(CommandHandler("football", football_command))
        application.add_handler(CommandHandler("bowling", bowling_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("daily", daily_command))
        application.add_handler(CommandHandler("spinner", spinner_command))
        application.add_handler(CommandHandler("deposit", deposit_command))
        application.add_handler(CommandHandler("withdraw", withdraw_command))
        application.add_handler(CommandHandler("achievements", achievements_command))
        application.add_handler(CommandHandler("friends", friends_command))
        application.add_handler(CommandHandler("leaderboard", leaderboard_command))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

        # Add group event handlers for automatic bot startup
        from telegram.ext import ChatMemberHandler
        application.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
        application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER))

        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot with proper polling
        await application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Bot run error: {e}")
        raise

def main():
    """Main function to run the bot with robust error handling"""
    global bot

    # Ensure we start with a clean event loop
    import asyncio
    try:
        # Close any existing event loop that might be corrupted
        try:
            current_loop = asyncio.get_running_loop()
            if current_loop and not current_loop.is_closed():
                current_loop.close()
        except RuntimeError:
            pass  # No running loop, which is what we want

        # Create a fresh event loop for the entire application
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except Exception as e:
        print(f"Warning: Could not set up fresh event loop: {e}")

    # Check for running instances
    pid_file = check_instance()
    
    try:
        # Initialize enhanced bot with network error handling
        max_init_retries = 3
        init_delay = 2
        
        for init_attempt in range(max_init_retries):
            try:
                bot = EnhancedCasinoBot()
                logger.info("Enhanced Casino Bot initialized successfully")
                break
            except Exception as init_error:
                if "Timed out" in str(init_error) or "ConnectTimeout" in str(init_error):
                    if init_attempt < max_init_retries - 1:
                        logger.warning(f"Bot initialization failed (attempt {init_attempt + 1}). Retrying in {init_delay} seconds...")
                        time.sleep(init_delay)
                        init_delay *= 2
                        continue
                    else:
                        logger.error("Failed to initialize bot after multiple attempts")
                        raise
                else:
                    raise
        
        # Initialize CryptoBot payment database tables
        if bot.payment_manager:
            try:
                from cryptobot_payment import create_payment_tables
                # Initialize tables synchronously to avoid event loop conflict
                import asyncio
                try:
                    # Try to run in existing event loop
                    try:
                        loop = asyncio.get_running_loop()
                        # Loop is running - schedule the coroutine
                        asyncio.create_task(create_payment_tables(bot.casino.db))
                    except RuntimeError:
                        # No event loop is running, run it
                        asyncio.run(create_payment_tables(bot.casino.db))
                except Exception as e:
                    # Handle case where no event loop exists
                    asyncio.run(create_payment_tables(bot.casino.db))
                logger.info("CryptoBot payment tables initialized successfully")
            except Exception as e:
                logger.error(f"Payment tables initialization error: {e}")
        else:
            logger.info("Payment system not available - skipping payment table creation")
        
        # Initialize advanced features
        try:
            from advanced_features import initialize_advanced_features
            initialize_advanced_features(bot.casino.db)
            logger.info("Advanced features initialized successfully")
        except ImportError:
            logger.warning("Advanced features module not found - running with basic functionality")
        
        # Initialize Solana systems
        try:
            from solana_integration_init import initialize_solana_integration

            # Initialize enhanced Solana integration
            logger.info("Starting enhanced Solana integration...")
            # Note: Full initialization should be run separately via solana_integration_init.py

            # Start webhook server for automatic payments
            try:
                from webhook_server import start_webhook_server_thread
                start_webhook_server_thread(host='0.0.0.0', port=8080)
                logger.info("✅ Webhook server started for automatic payments")
            except ImportError:
                logger.warning("Webhook server not available")

            logger.info("Solana integration system ready")
        except ImportError:
            logger.warning("Enhanced Solana integration not found")
        except Exception as e:
            logger.error(f"Failed to initialize Solana integration: {e}")
        
        # Create application
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.error("ERROR: BOT_TOKEN not configured! Please set your bot token in config.py")
            sys.exit(1)
        
        # Configure request settings with timeout and retry logic
        from telegram.request import HTTPXRequest
        import httpx
        
        # Create custom request object with longer timeout
        request = HTTPXRequest(
            connection_pool_size=8,
            read_timeout=60,
            write_timeout=60,
            connect_timeout=60,
            pool_timeout=30,
            http_version="1.1"
        )
        
        application = Application.builder().token(BOT_TOKEN).request(request).build()
        
        # Add handlers - Support and dice game commands only
        application.add_handler(CommandHandler("support", support_command))
        application.add_handler(CommandHandler("diceslots", diceslots_command))
        application.add_handler(CommandHandler("dartgame", dartgame_command))
        application.add_handler(CommandHandler("classicdice", classicdice_command))
        application.add_handler(CommandHandler("basketball", basketball_command))
        application.add_handler(CommandHandler("football", football_command))
        application.add_handler(CommandHandler("bowling", bowling_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        # Add group event handlers for automatic bot startup
        from telegram.ext import ChatMemberHandler
        application.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
        application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER))
        
        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("Casino Bot is starting...")
        logger.info("Payment system: " + ("Enabled" if bot.payment_manager else "Disabled (Offline mode)"))
        logger.info("Bot is ready to receive messages!")

        # Run the bot
        logger.info("SUCCESS: Casino system initialized")
        logger.info("SUCCESS: CryptoBot integration initialized")

        # Run polling mode with retry logic for connection issues
        max_retries = 5
        retry_delay = 10

        # Use asyncio.run to handle event loop properly
        async def run_bot():
            """Run the bot in a proper async context"""
            await application.initialize()

            # Setup bot commands after initialization
            try:
                await setup_bot_commands(application.bot)
            except Exception as cmd_error:
                logger.error(f"Failed to setup bot commands: {cmd_error}")

            # Start the bot using the modern approach
            await application.run_polling(drop_pending_updates=True)

        # Create HTTPx request with proper configuration
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connection_pool_size=512,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=60,
            pool_timeout=30,
            http_version="1.1"
        )

        application = Application.builder().token(BOT_TOKEN).request(request).build()

        # Add startup callback for async initialization
        async def startup_callback(application):
            """Initialize async components after bot starts"""
            try:
                await bot.async_init_solana()
            except Exception as e:
                logger.error(f"Solana async initialization failed: {e}")

        application.post_init = startup_callback

        # Add handlers - Support and dice game commands only
        application.add_handler(CommandHandler("support", support_command))
        application.add_handler(CommandHandler("diceslots", diceslots_command))
        application.add_handler(CommandHandler("dartgame", dartgame_command))
        application.add_handler(CommandHandler("classicdice", classicdice_command))
        application.add_handler(CommandHandler("basketball", basketball_command))
        application.add_handler(CommandHandler("football", football_command))
        application.add_handler(CommandHandler("bowling", bowling_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

        # Add group event handlers for automatic bot startup
        from telegram.ext import ChatMemberHandler
        application.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
        application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER))

        # Add error handler
        application.add_error_handler(error_handler)

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Starting polling attempt {attempt + 1}/{max_retries + 1}")

                # Ensure we have an event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop, create new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Run the bot using the synchronous method
                application.run_polling(drop_pending_updates=True)
                break  # If successful, exit the retry loop

            except RuntimeError as e:
                if "There is no current event loop" in str(e) or "Event loop is closed" in str(e):
                    logger.warning(f"Event loop issue on attempt {attempt + 1}: {e}")
                    # Let the application handle event loop creation on retry

                    if attempt < max_retries:
                        logger.info(f"Created new event loop, retrying...")
                        continue
                    else:
                        logger.error("Max retries reached for event loop errors")
                        raise
                else:
                    raise
            except (TimedOut, NetworkError, httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_retries:
                    logger.warning(f"Network error on attempt {attempt + 1}: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, 60)  # Exponential backoff with cap
                    continue
                else:
                    logger.error("Max retries reached. Network connection failed.")
                    raise
            except Exception as e:
                if "Timed out" in str(e) or "TimedOut" in str(e) or "ConnectTimeout" in str(e) or "ReadTimeout" in str(e):
                    if attempt < max_retries:
                        logger.warning(f"Connection timeout on attempt {attempt + 1}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 60)  # Exponential backoff with cap
                        continue
                    else:
                        logger.error("Max retries reached. Connection failed.")
                        raise
                else:
                    raise
        
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        cleanup_pid_file(pid_file)
        raise
    finally:
        cleanup_pid_file(pid_file)

# Enhanced game handler with animations and detailed feedback
async def handle_enhanced_solo_game(query, user, game_type, bet_amount, casino_bot, bot_instance):
    """Enhanced solo game with animations and detailed results"""
    try:
        import asyncio
        import random
        
        # Clear previous game content and show loading animation
        await query.edit_message_text("🎮 Yeni oyun hazırlanıyor...")
        await asyncio.sleep(0.2)
        
        loading_frames = ["⏳", "⏰", "⏱️", "⏲️"]
        for frame in loading_frames:
            await query.edit_message_text(f"{frame} Oyun başlıyor...")
            await asyncio.sleep(0.3)
        
        # Create solo game engine if not exists
        if not hasattr(casino_bot, 'solo_engine'):
            from solo_games import SoloGameEngine
            casino_bot.solo_engine = SoloGameEngine()
        
        # Play the game based on type
        result = None
        
        # Safety check for solo engine
        if not hasattr(casino_bot.solo_engine, 'play_solo_slots'):
            raise AttributeError("Solo engine methods not available")
            
        if game_type == "solo_slots":
            result = casino_bot.solo_engine.play_solo_slots(bet_amount)
            if result is None:
                # Fallback result if engine returns None
                result = {
                    'reels': ['❌', '❌', '❌'],
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0
                }
            result_text = f"""
🎰 **SLOT MAKİNESİ** 🎰

🎮 **Bahis:** {bet_amount:,} 🐻
🎯 **Sonuç:** {' '.join(result['reels'])}
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

🌟 Muhteşem! Devam et!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

🍀 Şansın bir dahaki sefere!
"""
        
        elif game_type == "solo_roulette":
            bet_choice = "red"
            result = casino_bot.solo_engine.play_solo_roulette(bet_amount, "color", bet_choice)
            if result is None:
                # Fallback result if engine returns None
                result = {
                    'number': 0,
                    'color': 'green',
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0
                }
            color_emoji = "🔴" if result['color'] == "red" else "⚫" if result['color'] == "black" else "🟢"
            
            result_text = f"""
🎯 **RULET** 🎯

🎮 **Bahis:** {bet_amount:,} 🐻 ({bet_choice})
🎲 **Sonuç:** {result['number']} {color_emoji}
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

🎯 Mükemmel tahmin!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

🎲 Bir dahaki sefere şansın!
"""
                
        elif game_type == "solo_blackjack":
            result = casino_bot.solo_engine.play_solo_blackjack(bet_amount)
            if result is None:
                # Fallback result if engine returns None
                result = {
                    'player_cards': [1, 10],
                    'dealer_cards': [5, 10],
                    'player_value': 21,
                    'dealer_value': 15,
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0
                }
            card_display = lambda cards: ' '.join([{1: 'A', 11: 'J', 12: 'Q', 13: 'K'}.get(c, str(c)) for c in cards])
            
            result_text = f"""
🃏 **BLACKJACK** 🃏

🎮 **Bahis:** {bet_amount:,} 🐻
👤 **Sen:** {card_display(result['player_cards'])} (Değer: {result['player_value']})
🎪 **Krupiye:** {card_display(result['dealer_cards'])} (Değer: {result['dealer_value']})
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

🃏 Harika oynama!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

🎯 Stratejini geliştir!
"""
        
        elif game_type == "solo_crash":
            result = casino_bot.solo_engine.play_solo_crash(bet_amount)
            if result is None:
                result = {
                    'crash_point': 1.0,
                    'cashout_multiplier': 2.0,
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0,
                    'result_text': 'Engine Error'
                }
            result_text = f"""
🚀 **CRASH GAME** 🚀

🎮 **Bahis:** {bet_amount:,} 🐻
🎯 **Sonuç:** {result['result_text']}
💥 **Crash Point:** {result['crash_point']:.1f}x
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

🚀 Harika zamanlama!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

🍀 Bir dahaki sefere daha erken çık!
"""
        
        elif game_type == "solo_mines":
            result = casino_bot.solo_engine.play_solo_mines(bet_amount)
            if result is None:
                result = {
                    'mines_count': 3,
                    'gems_found': 0,
                    'hit_mine': True,
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0,
                    'result_text': 'Engine Error'
                }
            result_text = f"""
💎 **MINES GAME** 💎

🎮 **Bahis:** {bet_amount:,} 🐻
⛏️ **Sonuç:** {result['result_text']}
💣 **Mayın Sayısı:** {result['mines_count']}
💎 **Bulunan Mücevher:** {result['gems_found']}
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

💎 Mükemmel kazı!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

💣 Mayına bastın! Daha dikkatli ol!
"""
        
        elif game_type == "solo_baccarat":
            result = casino_bot.solo_engine.play_solo_baccarat(bet_amount)
            if result is None:
                result = {
                    'winner': 'banker',
                    'player_val': 5,
                    'banker_val': 7,
                    'bet_on': 'player',
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0,
                    'result_text': 'Engine Error'
                }
            result_text = f"""
🃏 **BACCARAT** 🃏

🎮 **Bahis:** {bet_amount:,} 🐻 ({result['bet_on']})
👤 **Oyuncu:** {result['player_val']}
🏦 **Banker:** {result['banker_val']}
🏆 **Kazanan:** {result['winner'].title()}
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

🃏 Profesyonel tahmin!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

🎯 Şansın bir dahaki sefere!
"""
        
        elif game_type == "solo_keno":
            result = casino_bot.solo_engine.play_solo_keno(bet_amount)
            if result is None:
                result = {
                    'hits': 0,
                    'numbers_chosen': list(range(1, 11)),
                    'hit_numbers': [],
                    'won': False,
                    'win_amount': 0,
                    'multiplier': 0,
                    'result_text': 'Engine Error'
                }
            result_text = f"""
🎲 **KENO** 🎲

🎮 **Bahis:** {bet_amount:,} 🐻
🎯 **Seçilen:** {', '.join(map(str, result['numbers_chosen'][:5]))}...
🎰 **Eşleşen:** {result['hits']} sayı
💎 **Eşleşenler:** {', '.join(map(str, result['hit_numbers']))}
"""
            if result['won']:
                result_text += f"""
🎉 **YOU WON!** 🎉
🐻 **Kazanç:** {result['win_amount']:,} 🐻
⚡ **Multiplier:** {result['multiplier']:.2f}x
✨ **Net Kar:** +{result['win_amount'] - bet_amount:,} 🐻

🎲 Harika tahminler!
"""
            else:
                result_text += f"""
😢 **Kaybettin** 😢
💸 **Loss:** -{bet_amount:,} 🐻

🍀 Daha fazla eşleşme için şansını dene!
"""
        
        # Fallback for unhandled game types
        if result is None:
            result = {
                'won': False,
                'win_amount': 0,
                'multiplier': 0
            }
            result_text = f"""
❌ **OYUN HATASI** ❌

🎮 **Bahis:** {bet_amount:,} 🐻
⚠️ **Status:** Game engine error
💸 **Loss:** -{bet_amount:,} 🐻

🔄 Please try again.
"""
        
        # Update user stats and save game
        casino_bot.update_user_stats(user['user_id'], bet_amount, result['win_amount'], result['won'])
        casino_bot.save_solo_game(user['user_id'], game_type, bet_amount, result)
        
        # Get updated balance
        updated_user = casino_bot.get_user(user['user_id'])
        result_text += f"\n🐻 **Yeni Bakiye:** {updated_user['fun_coins']:,} 🐻"
        
        # Interactive buttons
        buttons = [
            [("🔄 Tekrar Oyna", f"solo_{game_type.split('_')[1]}"), ("🎮 Başka Oyun", "solo_games")],
            [("📊 Detaylı Profil", "profile"), ("🐻 Para İşlemleri", "payment_menu")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Enhanced solo game error: {e}")
        await query.edit_message_text(
            "❌ Oyun sırasında error occurred!\n\n🔄 Please try again.",
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games")]])
        )

# Complete tournament system functions
async def show_tournament_menu(query, user, casino_bot):
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
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def handle_create_tournament(query, user, tournament_type, casino_bot):
    """Handle tournament creation"""
    try:
        from advanced_features import tournament_manager
        
        if not tournament_manager:
            await query.edit_message_text(
                "❌ Turnuva sistemi şu anda kullanılamıyor.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
            return
        
        result = tournament_manager.create_tournament(tournament_type, user['user_id'])
        
        if result["success"]:
            tournament = result["tournament"]
            text = f"""
✅ **TURNUVA OLUŞTURULDU!** ✅

🏆 **{tournament['name']}**
🐻 **Buy-in:** {tournament['buy_in']:,} 🐻
👥 **Max Oyuncu:** {tournament['max_players']}
⏰ **Başlama:** 2 dakika sonra
🎮 **Oyun Türü:** {tournament['game_type'].title()}

📋 **Turnuva ID:** {tournament['id']}

🌟 Diğer oyuncuların katılmasını bekleyin!
💡 Minimum 2 oyuncu gerekli.
            """
            
            buttons = [
                [("🔄 Turnuvalar", "tournaments"), ("👥 Arkadaş Davet Et", "friends")],
                [("📊 Profil", "profile"), ("🏠 Main Menu", "main_menu")]
            ]
        else:
            text = f"❌ **Turnuva oluşturulamadı:** {result['error']}"
            buttons = [
                [("🔄 Tekrar Dene", "tournaments"), ("🏠 Main Menu", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Create tournament error: {e}")

async def handle_join_tournament(query, user, tournament_id, casino_bot):
    """Handle joining tournament"""
    try:
        from advanced_features import tournament_manager
        
        if not tournament_manager:
            await query.edit_message_text(
                "❌ Turnuva sistemi şu anda kullanılamıyor.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
            return
        
        result = tournament_manager.join_tournament(tournament_id, user['user_id'], user['fun_coins'])
        
        if result["success"]:
            tournament = result["tournament"]
            participants_count = len(tournament["participants"])
            
            text = f"""
🎉 **TURNUVAYA KATILDIN!** 🎉

🏆 **{tournament['name']}**
🐻 **Buy-in Ödendi:** {tournament['buy_in']:,} 🐻
👥 **Katılımcı:** {participants_count}/{tournament['max_players']}
🏆 **Güncel Ödül Havuzu:** {tournament['prize_pool']:,} 🐻

⏰ **Durum:** {'Başlıyor...' if participants_count >= 2 else 'Daha fazla oyuncu bekleniyor'}

🎯 **Ödül Dağılımı:**
🥇 1. - %50 ({int(tournament['prize_pool'] * 0.5):,} 🐻)
🥈 2. - %30 ({int(tournament['prize_pool'] * 0.3):,} 🐻)
🥉 3. - %20 ({int(tournament['prize_pool'] * 0.2):,} 🐻)
            """
            
            # Auto-start tournament if enough players
            if participants_count >= 2:
                start_result = tournament_manager.start_tournament(tournament_id)
                if start_result["success"]:
                    text += f"\n🚀 **TURNUVA BAŞLADI!**\n"
                    results = start_result["results"]
                    winner_id = start_result["winner_id"]
                    
                    text += "\n📊 **SONUÇLAR:**\n"
                    for i, result in enumerate(results[:3]):
                        position_emoji = ["🥇", "🥈", "🥉"][i]
                        user_info = casino_bot.get_user(result["user_id"])
                        username = user_info['username'] or f"Oyuncu{result['user_id']}"
                        prize = result['prize'] if 'prize' in result else 0
                        text += f"{position_emoji} {username} - {result['score']} puan"
                        if prize > 0:
                            text += f" (+{prize:,} 🐻)"
                        text += "\n"
            
        else:
            text = f"❌ **Turnuvaya katılamadın:** {result['error']}"
        
        buttons = [
            [("🔄 Turnuvalar", "tournaments"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Join tournament error: {e}")

# Complete friend system functions
async def show_simple_friends_menu(query, user, casino_bot):
    """Show simple friends menu"""
    try:
        with casino_bot.db.get_connection() as conn:
            # Get friends
            friends = conn.execute('''
                SELECT u.username, u.level, u.fun_coins, u.last_active FROM friendships f 
                JOIN users u ON (CASE WHEN f.user1_id = ? THEN f.user2_id ELSE f.user1_id END) = u.user_id 
                WHERE (f.user1_id = ? OR f.user2_id = ?) AND f.status = "accepted"
                ORDER BY u.last_active DESC
            ''', (user['user_id'], user['user_id'], user['user_id'])).fetchall()
            
            # Get pending requests
            pending_requests = conn.execute('''
                SELECT COUNT(*) FROM friendships 
                WHERE user2_id = ? AND status = "pending"
            ''', (user['user_id'],)).fetchone()[0]
        
        text = "👥 **ARKADAŞ SİSTEMİ** 👥\n\n"
        
        if friends:
            text += f"👫 **Arkadaşların ({len(friends)}):**\n\n"
            for friend in friends[:5]:  # Show first 5
                status = "🟢" if friend['last_active'] and (datetime.now() - datetime.fromisoformat(friend['last_active'])).days < 1 else "🔴"
                text += f"{status} **{friend['username'] or 'Anonim'}** (Lv.{friend['level']})\n"
                text += f"    🐻 {friend['fun_coins']:,} 🐻\n\n"
            
            if len(friends) > 5:
                text += f"... ve {len(friends) - 5} arkadaşın daha\n\n"
        else:
            text += "😔 Henüz arkadaşın yok!\n\n"
        
        if pending_requests > 0:
            text += f"📬 **{pending_requests} bekleyen arkadaşlık isteğin var!**\n\n"
        
        text += f"🆔 **Senin Arkadaş Kodun:** `{user['friend_code'] if 'friend_code' in user.keys() else 'ERROR'}`\n\n"
        text += "💡 **Nasıl Çalışır:**\n"
        text += "• Arkadaş kodunu paylaş\n"
        text += "• Başkalarının kodunu gir\n"
        text += "• Beraber turnuvalara katıl\n"
        text += "• Günlük bonuslar kazan!\n"
        
        buttons = [
            [("➕ Arkadaş Ekle", "add_friend"), ("📬 İstekler", "friend_requests")],
            [("🎮 Arkadaşlarla Oyna", "tournaments"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Friends menu error: {e}")

async def show_add_friend_menu(query, user, casino_bot):
    """Show add friend menu"""
    try:
        text = f"""
➕ **ARKADAŞ EKLE** ➕

🆔 **Senin Kodun:** `{user['friend_code'] if 'friend_code' in user.keys() else 'ERROR'}`

📝 **Arkadaş Kodu Gir:**
Arkadaşının 6 haneli kodunu gir ve arkadaşlık isteği gönder!

💡 **Tips:**
• Kod 6 hane ve harf-rakam karışımı
• Büyük-küçük harf duyarlı değil
• Kendi kodunu giremezsin

🎁 **Referans Sistemi:**
• Referans kodunla kayıt: +1000 🐻
• Referans eden kişi: +500 🐻
• Referansların oynadıkça %5 komisyon

🔗 **Paylaşım Metni:**
🎮 Casino Bot'ta eğlenelim! Kodum: `{user['friend_code'] if 'friend_code' in user.keys() else 'ERROR'}`

📱 **Referans Linki:**
https://t.me/bot_username?start=friend_{user['friend_code'] if 'friend_code' in user.keys() else 'ERROR'}
        """
        
        buttons = [
            [("📝 Manuel Kod Gir", "enter_friend_code")],
            [("📋 Kodu Kopyala", "copy_friend_code"), ("📤 Paylaş", "share_friend_code")],
            [("👥 Arkadaşlarım", "friends"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Add friend menu error: {e}")

async def show_friend_requests_menu(query, user, casino_bot):
    """Show friend requests menu"""
    try:
        requests = casino_bot.get_friend_requests(user['user_id'])
        
        text = "📬 **ARKADAŞLIK İSTEKLERİ** 📬\n\n"
        
        if requests:
            text += f"📥 **{len(requests)} bekleyen istek:**\n\n"
            buttons = []
            
            for request in requests[:5]:  # Show max 5
                username = request['username'] or f"Oyuncu{request['user1_id']}"
                date = request['created_at'][:10]
                
                text += f"👤 **{username}** (Lv.{request['level']})\n"
                text += f"📅 Gönderim: {date}\n\n"
                
                buttons.append([
                    (f"✅ Kabul: {username[:10]}", f"accept_friend_{request['user1_id']}"),
                    (f"❌ Reddet", f"reject_friend_{request['user1_id']}")
                ])
            
            buttons.append([("🔄 Yenile", "friend_requests"), ("👥 Arkadaşlar", "friends")])
            
        else:
            text += "😊 Bekleyen arkadaşlık isteğin yok!\n\n"
            text += "💡 **Arkadaş Bulmak İçin:**\n"
            text += "• Kodunu arkadaşlarınla paylaş\n"
            text += "• Turnuvalarda tanış\n"
            text += "• Liderlik tablosundaki oyuncuları takip et\n"
            
            buttons = [
                [("➕ Arkadaş Ekle", "add_friend"), ("🏆 Turnuvalar", "tournaments")],
                [("📊 Liderlik", "leaderboard"), ("🏠 Main Menu", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Friend requests error: {e}")

async def handle_accept_friend(query, user, friend_id, casino_bot):
    """Handle accepting friend request"""
    try:
        success = casino_bot.accept_friend_request(user['user_id'], friend_id)
        
        if success:
            # Get friend info
            friend = casino_bot.get_user(friend_id)
            friend_name = friend['username'] or f"Oyuncu{friend_id}"
            
            # Give bonus coins
            with casino_bot.db.get_connection() as conn:
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?', (300, user['user_id']))
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?', (300, friend_id))
                conn.commit()
            
            # Unlock achievement
            casino_bot.unlock_achievement(user['user_id'], "social_butterfly")
            
            text = f"""
🎉 **ARKADAŞLIK KABUL EDİLDİ!** 🎉

👥 **{friend_name}** artık arkadaşın!

🎁 **Bonuslar:**
• +300 🐻 (Sen)
• +300 🐻 ({friend_name})

🌟 **Artık yapabileceklerin:**
• Beraber turnuvalara katılın
• Birbirinizi düelloya davet edin
• Referans komisyonları kazanın
• Achievementmları paylaşın

🏆 **Achievementm Açıldı:** Sosyal Kelebek!
            """
        else:
            text = "❌ Arkadaşlık isteği kabul edilemedi!"
        
        buttons = [
            [("📬 Diğer İstekler", "friend_requests"), ("👥 Arkadaşlar", "friends")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Accept friend error: {e}")

async def handle_reject_friend(query, user, friend_id, casino_bot):
    """Handle rejecting friend request"""
    try:
        with casino_bot.db.get_connection() as conn:
            conn.execute('DELETE FROM friendships WHERE user1_id = ? AND user2_id = ? AND status = "pending"',
                        (friend_id, user['user_id']))
            conn.commit()
        
        text = "❌ Arkadaşlık isteği reddedildi."
        
        buttons = [
            [("📬 Diğer İstekler", "friend_requests"), ("👥 Arkadaşlar", "friends")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Reject friend error: {e}")

# Events system
async def show_events_menu(query, user, casino_bot):
    """Show events and special content"""
    try:
        from advanced_features import event_manager
        
        # Get current date for seasonal events
        now = datetime.now()
        seasonal_events = []
        
        # Check for seasonal events
        if now.month == 12:
            seasonal_events.append({
                "name": "🎄 Noel Casino Festivali",
                "description": "Tüm günlük bonuslar 2x!",
                "active": True,
                "bonus": "2x günlük bonus"
            })
        
        if now.month == 1 and now.day <= 7:
            seasonal_events.append({
                "name": "🎊 Yeni Yıl Şans Haftası",
                "description": "3x XP ve özel achievementslar!",
                "active": True,
                "bonus": "3x XP"
            })
        
        if now.month in [6, 7, 8]:
            seasonal_events.append({
                "name": "☀️ Yaz Casino Festivali",
                "description": "Plaj temalı oyunlar ve bonuslar!",
                "active": True,
                "bonus": "1.5x tüm bonuslar"
            })
        
        # Daily challenges
        win_streak = user['win_streak'] if user['win_streak'] is not None else 0
        daily_challenge = {
            "name": "🎯 Günlük Meydan Okuma",
            "description": "5 oyun art arda kazan",
            "reward": "2,000 🐻",
            "progress": f"{win_streak}/5",
            "completed": win_streak >= 5
        }
        
        text = "🎉 **ETKİNLİKLER VE ÖZEL İÇERİK** 🎉\n\n"
        
        if seasonal_events:
            text += "🌟 **Active Mevsimsel Etkinlikler:**\n\n"
            for event in seasonal_events:
                text += f"🎪 **{event['name']}**\n"
                text += f"📝 {event['description']}\n"
                text += f"🎁 Bonus: {event['bonus']}\n\n"
        
        text += "🎯 **Günlük Meydan Okuma:**\n\n"
        status = "✅ Tamamlandı!" if daily_challenge['completed'] else f"📊 İlerleme: {daily_challenge['progress']}"
        text += f"🏆 **{daily_challenge['name']}**\n"
        text += f"📋 {daily_challenge['description']}\n"
        text += f"🐻 Ödül: {daily_challenge['reward']}\n"
        text += f"🎯 Durum: {status}\n\n"
        
        text += "🎪 **Özel Etkinlikler:**\n"
        text += "• 🏁 Haftalık Yarış (Pazartesi başlıyor)\n"
        text += "• 🎰 Jackpot Saatleri (Her gün 20:00-22:00)\n"
        text += "• 🎊 Hafta Sonu Bonusu (%50 ekstra)\n"
        text += "• 🎯 Aylık Büyük Turnuva (Her ayın 1'i)\n\n"
        
        text += "📅 **Yaklaşan Etkinlikler:**\n"
        text += "• 🏆 Mega Turnuva (Gelecek Hafta)\n"
        text += "• 🎁 Özel Bonus Günü (Cuma)\n"
        text += "• 🎪 VIP Özel Etkinliği (Ayın 15'i)\n\n"
        text += f"🕐 **Son Güncelleme:** {now.strftime('%H:%M:%S')}\n"
        
        buttons = [
            [("🎯 Günlük Görevler", "daily_quests"), ("🏆 Turnuvalar", "tournaments")],
            [("🎁 Daily Bonus", "daily_bonus"), ("👑 VIP Bilgisi", "vip_info")],
            [("🔄 Yenile", "events"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        
        try:
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as telegram_error:
            # Handle "message not modified" error silently
            if "Message is not modified" in str(telegram_error):
                logger.debug("Events menu: Message content unchanged, skipping update")
            else:
                raise telegram_error
        
    except Exception as e:
        logger.error(f"Events menu error: {e}")
        await query.edit_message_text(
            "❌ Etkinlik menüsü yüklenirken error occurred!",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

# Duel system functions
async def show_create_duel_menu(query, user, casino_bot):
    """Show create duel menu"""
    try:
        text = f"""
⚔️ **DÜELLO OLUŞTUR** ⚔️

🐻 **Current Balance:** {user['fun_coins']:,} 🐻

🎮 **Düello Türleri:**

🪙 **Coin Flip** (Min: 10 🐻)
• Yazı-tura tahmin et
• %50 kazanma şansı
• 2x ödeme

🎲 **Zar Düelloları:**
• 🎲 Standart Zar (Min: 10 🐻)
• 🏀 Basketbol Zar (Min: 15 🐻)
• ⚽ Futbol Zar (Min: 15 🐻)
• 🎰 Slot Zar (Min: 20 🐻)
• 🎳 Bowling Zar (Min: 12 🐻)
• 🎯 Dart Zar (Min: 10 🐻)

✊ **Rock-Paper-Scissors** (Min: 20 🐻)
• Klasik taş-kağıt-makas
• Strateji gerektirir
• 2x ödeme

💡 **Düello Kuralları:**
• Her oyuncu aynı miktarı yatırır
• Kazanan tüm parayı alır
• Berabere durumda paralar iade edilir
• Otomatik sonuç hesaplama
        """
        
        buttons = []
        
        # Check balance for each game
        if user['fun_coins'] >= 10:
            buttons.append([("🪙 Coin Flip (10 🐻)", "create_duel_duel_coinflip")])
        else:
            buttons.append([("🪙 Coin Flip (Yetersiz)", "insufficient_funds")])
        
        # Dice game buttons
        dice_games = [
            ("🎲 Standart Zar (10 🐻)", "create_duel_duel_dice_standard", 10),
            ("🏀 Basketbol Zar (15 🐻)", "create_duel_duel_dice_basketball", 15),
            ("⚽ Futbol Zar (15 🐻)", "create_duel_duel_dice_football", 15),
            ("🎰 Slot Zar (20 🐻)", "create_duel_duel_dice_slot", 20),
            ("🎳 Bowling Zar (12 🐻)", "create_duel_duel_dice_bowling", 12),
            ("🎯 Dart Zar (10 🐻)", "create_duel_duel_dice_darts", 10)
        ]
        
        for button_text, callback, min_bet in dice_games:
            if user['fun_coins'] >= min_bet:
                buttons.append([(button_text, callback)])
            else:
                buttons.append([(button_text.replace("FC)", "Yetersiz)"), "insufficient_funds")])
        
        if user['fun_coins'] >= 20:
            buttons.append([("✊ Rock-Paper-Scissors (20 🐻)", "create_duel_duel_rockpaper")])
        else:
            buttons.append([("✊ Rock-Paper-Scissors (Yetersiz)", "insufficient_funds")])
        
        buttons.extend([
            [("🎯 Düelloya Katıl", "join_duel"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Create duel menu error: {e}")

async def show_join_duel_menu(query, user, casino_bot):
    """Show join duel menu"""
    try:
        with casino_bot.db.get_connection() as conn:
            active_duels = conn.execute('''
                SELECT ag.*, u.username FROM active_games ag 
                LEFT JOIN users u ON ag.creator_id = u.user_id 
                WHERE ag.status = "waiting" 
                AND ag.creator_id != ?
                ORDER BY ag.created_at DESC 
                LIMIT 10
            ''', (user['user_id'],)).fetchall()
        
        text = "🎯 **AKTİF DÜELLOLAR** 🎯\n\n"
        
        if active_duels:
            text += f"⚔️ **{len(active_duels)} aktif düello bulundu:**\n\n"
            buttons = []
            
            for duel in active_duels:
                creator = duel['username'] or f"Oyuncu{duel['creator_id']}"
                game_name = GAMES.get(duel['game_type'], {}).get('name', duel['game_type'])
                
                text += f"🎮 **{game_name}**\n"
                text += f"👤 Oluşturan: {creator}\n"
                text += f"🐻 Bahis: {duel['bet_amount']:,} 🐻\n"
                text += f"⏰ Oluşturulma: {duel['created_at'][:16]}\n\n"
                
                if user['fun_coins'] >= duel['bet_amount']:
                    buttons.append([(f"⚔️ Katıl: {game_name[:12]}...", f"join_{duel['game_id']}")])
                else:
                    buttons.append([(f"❌ Yetersiz Bakiye", "insufficient_funds")])
            
            buttons.extend([
                [("🔄 Yenile", "join_duel"), ("⚔️ Yeni Düello", "create_duel")],
                [("🏠 Main Menu", "main_menu")]
            ])
            
        else:
            text += "😔 Şu anda aktif düello yok!\n\n"
            text += "💡 **Yapabileceklerin:**\n"
            text += "• Kendi düellonu oluştur\n"
            text += "• Arkadaşlarını davet et\n"
            text += "• Turnuvalara katıl\n"
            text += "• Solo oyunları oyna\n"
            
            buttons = [
                [("⚔️ Düello Oluştur", "create_duel"), ("🏆 Turnuvalar", "tournaments")],
                [("👥 Arkadaş Davet Et", "friends"), ("🎮 Solo Games", "solo_games")],
                [("🔄 Yenile", "join_duel"), ("🏠 Main Menu", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Join duel menu error: {e}")

async def handle_create_duel(query, user, game_type, casino_bot):
    """Handle creating a duel"""
    try:
        from config import GAMES
        
        game_config = GAMES.get(game_type)
        if not game_config:
            await query.edit_message_text(
                "❌ Invalid game type!",
                reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
            return
        
        min_bet = game_config['min_bet']
        
        if user['fun_coins'] < min_bet:
            await query.edit_message_text(
                f"❌ Yetersiz bakiye!\n\nGerekli: {min_bet:,} 🐻\nMevcut: {user['fun_coins']:,} 🐻",
                reply_markup=casino_bot.create_keyboard([
                    [("🐻 Para Yatır", "deposit_menu"), ("🎁 Daily Bonus", "daily_bonus")],
                    [("🏠 Main Menu", "main_menu")]
                ])
            )
            return
        
        # Create duel
        game_id = casino_bot.create_duel(user['user_id'], game_type, min_bet)
        
        text = f"""
⚔️ **DÜELLO OLUŞTURULDU!** ⚔️

🎮 **Oyun:** {game_config['name']}
🐻 **Bahis:** {min_bet:,} 🐻
🆔 **ID:** {game_id}
👤 **Oluşturan:** {user['username'] or 'Sen'}

⏳ **Durum:** Rakip bekleniyor...

📋 **Kurallar:**
• İlk katılan rakip olur
• Otomatik oyun başlatma
• Kazanan tüm parayı alır
• Sonuç anında belli olur

🔗 **Arkadaşlarını davet et!**
Arkadaş kodun: `{user['friend_code'] if user['friend_code'] else 'ERROR'}`
        """
        
        buttons = [
            [("🔄 Düello Durumu", "join_duel"), ("👥 Arkadaş Davet Et", "friends")],
            [("📊 Profil", "profile"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Create duel error: {e}")

async def handle_join_game(query, user, game_id, casino_bot):
    """Handle joining a game"""
    try:
        # Check if game exists and is available
        with casino_bot.db.get_connection() as conn:
            game = conn.execute('SELECT * FROM active_games WHERE game_id = ?', (game_id,)).fetchone()
            
            if not game:
                await query.edit_message_text(
                    "❌ Oyun bulunamadı!",
                    reply_markup=casino_bot.create_keyboard([[("🎯 Düellolar", "join_duel")]])
                )
                return
            
            if game['status'] != 'waiting':
                await query.edit_message_text(
                    "❌ Bu oyun artık mevcut değil!",
                    reply_markup=casino_bot.create_keyboard([[("🎯 Düellolar", "join_duel")]])
                )
                return
            
            if user['fun_coins'] < game['bet_amount']:
                await query.edit_message_text(
                    f"❌ Yetersiz bakiye!\n\nGerekli: {game['bet_amount']:,} 🐻\nMevcut: {user['fun_coins']:,} 🐻",
                    reply_markup=casino_bot.create_keyboard([
                        [("🐻 Para Yatır", "deposit_menu"), ("🎁 Daily Bonus", "daily_bonus")],
                        [("🎯 Düellolar", "join_duel")]
                    ])
                )
                return
        
        # Join the duel
        success = casino_bot.join_duel(game_id, user['user_id'])
        
        if success:
            # Show loading animation
            for i in range(3):
                await query.edit_message_text(f"⏳ Oyun başlıyor{'.' * (i + 1)}")
                await asyncio.sleep(0.5)
            
            # Start the game
            await start_duel_game(query, game_id, user, casino_bot)
            
        else:
            await query.edit_message_text(
                "❌ Oyuna katılamadın! Oyun dolu olabilir.",
                reply_markup=casino_bot.create_keyboard([[("🎯 Düellolar", "join_duel")]])
            )
            
    except Exception as e:
        logger.error(f"Join game error: {e}")

# Admin system functions
def is_admin_user(user_id: int) -> bool:
    """Check if user is admin - reads from config.py"""
    from config import ADMIN_USER_IDS
    return user_id in ADMIN_USER_IDS

async def show_admin_panel(query, user, casino_bot):
    """Show admin control panel - only for authorized admins"""
    try:
        # Double check admin permissions
        if not is_admin_user(user['user_id']):
            await query.edit_message_text(
                "❌ **Yetkisiz Erişim!** ❌\n\n🚫 Bu bölüme erişim yetkiniz yok.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
            return
        text = f"""
🔧 **ADMIN CONTROL PANEL** 🔧

👋 Hoş geldin, {user['username']}!

🎮 **Bot Durumu:** Online ✅
📊 **Sistem Sağlığı:** Normal ✅
🌐 **Veritabanı:** Bağlı ✅
💳 **Payment Sistemi:** {"Active" if hasattr(casino_bot, 'payment_manager') else "Inactive"}

⚙️ **YÖNETİM SEÇENEKLERİ:**

📊 **Statistics:**
• Bot kullanım verileri
• Oyuncu aktiviteleri
• Finansal veriler
• Performans metrikleri

👥 **Kullanıcı Yönetimi:**
• Kullanıcı listesi
• Hesap düzenleme
• Para işlemleri
• Yasak işlemleri

📢 **Duyurular:**
• Tüm kullanıcılara mesaj
• Sistem bakım bildirimi
• Özel etkinlik duyurusu

⚠️ **UYARI:** Admin yetkileri dikkatli kullanın!
        """
        
        buttons = [
            [("📊 Statistics", "admin_stats"), ("👥 Kullanıcılar", "admin_users")],
            [("📢 Duyuru Gönder", "admin_broadcast"), ("⚙️ Sistem Ayarları", "admin_settings")],
            [("🔄 Yenile", "admin_panel"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        try:
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as edit_error:
            # Ignore "message not modified" errors
            if "Message is not modified" in str(edit_error):
                logger.debug("Admin panel: Message content unchanged, skipping update")
            else:
                raise edit_error
        
    except Exception as e:
        logger.error(f"Admin panel error: {e}")
        try:
            await query.edit_message_text(
                "❌ **Admin Panel Hatası**\n\n🔄 Please try again.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
        except:
            pass

async def show_admin_statistics(query, user, casino_bot):
    """Show detailed bot statistics"""
    try:
        with casino_bot.db.get_connection() as conn:
            # User statistics
            total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            active_today = conn.execute('''
                SELECT COUNT(*) FROM users 
                WHERE date(last_active) >= date('now', '-1 day')
            ''').fetchone()[0]
            
            # Game statistics
            total_games = conn.execute('SELECT COUNT(*) FROM solo_game_history').fetchone()[0]
            games_today = conn.execute('''
                SELECT COUNT(*) FROM solo_game_history 
                WHERE date(played_at) >= date('now')
            ''').fetchone()[0]
            
            # Financial statistics
            total_coins = conn.execute('SELECT SUM(fun_coins) FROM users').fetchone()[0] or 0
            total_bets = conn.execute('SELECT SUM(bet_amount) FROM solo_game_history').fetchone()[0] or 0
            total_winnings = conn.execute('SELECT SUM(win_amount) FROM solo_game_history').fetchone()[0] or 0
            
            # Active duels and tournaments
            active_duels = conn.execute('SELECT COUNT(*) FROM active_games WHERE status = "waiting"').fetchone()[0]
            active_tournaments = conn.execute('SELECT COUNT(*) FROM tournaments WHERE status IN ("open", "registration")').fetchone()[0]
            
            # Top players
            top_players = conn.execute('''
                SELECT username, fun_coins FROM users 
                ORDER BY fun_coins DESC LIMIT 5
            ''').fetchall()
        
        house_edge = ((total_bets - total_winnings) / total_bets * 100) if total_bets > 0 else 0
        activity_rate = (active_today / total_users * 100) if total_users > 0 else 0
        
        text = f"""
📊 **BOT STATISTICS** 📊

👥 **KULLANICILAR:**
• Toplam Kullanıcı: {total_users:,}
• Active (24h): {active_today:,} (%{activity_rate:.1f})
• Ortalama/Gün: {total_users//30:,}

🎮 **OYUNLAR:**
• Toplam Oyun: {total_games:,}
• Bugün Oynanan: {games_today:,}
• Ortalama/Kullanıcı: {total_games//total_users if total_users > 0 else 0:.1f}

🐻 **FİNANSAL:**
• Toplam Para: {total_coins:,} 🐻
• Toplam Bahis: {total_bets:,} 🐻
• Toplam Kazanç: {total_winnings:,} 🐻
• House Edge: %{house_edge:.2f}

🎯 **AKTİF İÇERİK:**
• Bekleyen Düello: {active_duels}
• Açık Turnuva: {active_tournaments}

🏆 **TOP 5 OYUNCU:**
"""
        
        for i, player in enumerate(top_players, 1):
            text += f"{i}. {player['username'] or 'Anonim'}: {player['fun_coins']:,} 🐻\n"
        
        text += f"""

⚡ **PERFORMANS:**
• Bot Çalışma Süresi: Online ✅
• Veritabanı Boyutu: ~{total_users * 2}KB
• Son Güncellenme: Bugün
        """
        
        buttons = [
            [("🔄 Yenile", "admin_stats"), ("📈 Detaylı Rapor", "admin_detailed_stats")],
            [("👥 Kullanıcı Yönetimi", "admin_users"), ("🔧 Admin Panel", "admin_panel")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        try:
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as edit_error:
            # Ignore "message not modified" errors
            if "Message is not modified" in str(edit_error):
                logger.debug("Admin statistics: Message content unchanged, skipping update")
            else:
                raise edit_error
        
    except Exception as e:
        logger.error(f"Admin statistics error: {e}")
        try:
            await query.edit_message_text(
                "❌ **İstatistik Hatası**\n\n🔄 Please try again.",
                reply_markup=casino_bot.create_keyboard([[("🔧 Admin Panel", "admin_panel"), ("🏠 Main Menu", "main_menu")]])
            )
        except:
            pass

async def show_admin_user_management(query, user, casino_bot):
    """Show user management interface"""
    try:
        with casino_bot.db.get_connection() as conn:
            # Recent users
            recent_users = conn.execute('''
                SELECT user_id, username, fun_coins, level, last_active 
                FROM users 
                ORDER BY last_active DESC 
                LIMIT 10
            ''').fetchall()
            
            # Problem users (negative balance, high activity, etc.)
            problem_users = conn.execute('''
                SELECT user_id, username, fun_coins 
                FROM users 
                WHERE fun_coins < 0 OR fun_coins > 10000000
                LIMIT 5
            ''').fetchall()
        
        text = """
👥 **KULLANICI YÖNETİMİ** 👥

🔍 **ARAMA VE FİLTRELEME:**
• User ID ile arama
• Username ile arama
• Bakiye aralığı filtresi
• Aktivite durumu filtresi

📋 **SON AKTİF KULLANICILAR:**

"""
        
        for i, user_data in enumerate(recent_users[:5], 1):
            status = "🟢" if user_data['last_active'] else "🔴"
            username = user_data['username'] or f'User{user_data["user_id"]}'
            text += f"{i}. {status} {username}\n"
            text += f"   🐻 {user_data['fun_coins']:,} 🐻 | Lv.{user_data['level']}\n\n"
        
        if problem_users:
            text += "⚠️ **DİKKAT GEREKTİREN KULLANICILAR:**\n\n"
            for prob_user in problem_users:
                username = prob_user['username'] or f'User{prob_user["user_id"]}'
                text += f"🚨 {username}\n"
                text += f"   🐻 {prob_user['fun_coins']:,} 🐻\n\n"
        
        text += """
⚙️ **YÖNETİM İŞLEMLERİ:**
• Para ekleme/çıkarma
• Hesap sıfırlama
• Kullanıcı yasaklama
• Seviye düzenleme
• Achievementm verme

💡 **Kullanıcı ID girerek işlem yapabilirsiniz.**
        """
        
        buttons = [
            [("🔍 Kullanıcı Ara", "admin_search_user"), ("📊 Detaylı Liste", "admin_user_list")],
            [("🐻 Para İşlemleri", "admin_money_ops"), ("🚫 Yasaklama", "admin_ban_ops")],
            [("🔄 Yenile", "admin_users"), ("🔧 Admin Panel", "admin_panel")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Admin user management error: {e}")

async def show_admin_broadcast_menu(query, user, casino_bot):
    """Show broadcast message interface"""
    try:
        with casino_bot.db.get_connection() as conn:
            total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            active_users = conn.execute('''
                SELECT COUNT(*) FROM users 
                WHERE date(last_active) >= date('now', '-7 days')
            ''').fetchone()[0]
        
        text = f"""
📢 **DUYURU SİSTEMİ** 📢

📊 **HEDEFLENEBİLİR KULLANICILAR:**
• Toplam Kullanıcı: {total_users:,}
• Active (7 gün): {active_users:,}
• Tahmini Ulaşım: %85-95

🎯 **DUYURU TÜRLERİ:**

📣 **Genel Duyuru**
• Tüm kullanıcılara gönderilir
• Sistem bildirimleri için ideal
• Etkinlik duyuruları

🔧 **Bakım Bildirimi**
• Sistem bakım mesajı
• Otomatik format
• Süre bildirimi

🎉 **Etkinlik Duyurusu**
• Özel etkinlik formatı
• Bonus bilgileri
• Katılım çağrısı

⚠️ **UYARI:** 
• Duyurular geri alınamaz!
• Spam yapmayın
• Net ve açık yazın

💡 **İpucu:** Kısa ve etkili mesajlar daha iyi sonuç verir.
        """
        
        buttons = [
            [("📣 Genel Duyuru", "admin_broadcast_general"), ("🔧 Bakım Bildirimi", "admin_broadcast_maintenance")],
            [("🎉 Etkinlik Duyurusu", "admin_broadcast_event"), ("📊 Hedefli Mesaj", "admin_broadcast_targeted")],
            [("📝 Özel Mesaj", "admin_broadcast_custom"), ("📋 Mesaj Geçmişi", "admin_broadcast_history")],
            [("🔄 Yenile", "admin_broadcast"), ("🔧 Admin Panel", "admin_panel")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Admin broadcast menu error: {e}")

async def handle_admin_user_action(query, user, action, target_user_id, casino_bot):
    """Handle admin actions on users"""
    try:
        from advanced_features import admin_panel
        
        if not admin_panel:
            await query.edit_message_text(
                "❌ Admin sistemi kullanılamıyor.",
                reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
            )
            return
        
        # Get target user info
        target_user = casino_bot.get_user(target_user_id)
        if not target_user:
            await query.edit_message_text(
                f"❌ Kullanıcı bulunamadı: {target_user_id}",
                reply_markup=casino_bot.create_keyboard([[("👥 Kullanıcılar", "admin_users")]])
            )
            return
        
        username = target_user['username'] or f"User{target_user_id}"
        
        if action == "info":
            text = f"""
👤 **KULLANICI BİLGİLERİ** 👤

🆔 **ID:** {target_user_id}
👤 **Username:** {username}
🐻 **Bakiye:** {target_user['fun_coins']:,} 🐻
🏆 **Level:** {target_user['level']}
⭐ **XP:** {target_user['xp']:,}
🔥 **Win Streak:** {target_user['win_streak']}
🎮 **Toplam Oyun:** {target_user['games_count']}
💸 **Toplam Bahis:** {target_user['total_bet']:,} 🐻
💎 **Toplam Kazanç:** {target_user['total_won']:,} 🐻
📅 **Son Active:** {target_user['last_active'] if 'last_active' in target_user else 'Bilinmiyor'}
🆔 **Arkadaş Kodu:** {target_user['friend_code'] if 'friend_code' in target_user and target_user['friend_code'] else 'None'}

⚙️ **YÖNETİM İŞLEMLERİ:**
            """
            
            buttons = [
                [("🐻 +10K 🐻", f"admin_user_addmoney_{target_user_id}"), ("💸 -5K 🐻", f"admin_user_removemoney_{target_user_id}")],
                [("🔄 Hesap Sıfırla", f"admin_user_reset_{target_user_id}"), ("🚫 Yasakla", f"admin_user_ban_{target_user_id}")],
                [("🏆 Level +1", f"admin_user_levelup_{target_user_id}"), ("⭐ +1000 XP", f"admin_user_addxp_{target_user_id}")],
                [("👥 Kullanıcılar", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
            ]
            
        elif action == "addmoney":
            result = admin_panel.manage_user(user['user_id'], target_user_id, "add_coins", 10000)
            if result["success"]:
                text = f"✅ {username} hesabına 10,000 🐻 eklendi!"
            else:
                text = f"❌ İşlem başarısız: {result['error']}"
            
            buttons = [
                [("👤 Kullanıcı Bilgisi", f"admin_user_info_{target_user_id}")],
                [("👥 Kullanıcılar", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
            ]
            
        elif action == "removemoney":
            result = admin_panel.manage_user(user['user_id'], target_user_id, "remove_coins", 5000)
            if result["success"]:
                text = f"✅ {username} hesabından 5,000 🐻 çıkarıldı!"
            else:
                text = f"❌ İşlem başarısız: {result['error']}"
            
            buttons = [
                [("👤 Kullanıcı Bilgisi", f"admin_user_info_{target_user_id}")],
                [("👥 Kullanıcılar", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
            ]
            
        elif action == "reset":
            result = admin_panel.manage_user(user['user_id'], target_user_id, "reset_user")
            if result["success"]:
                text = f"✅ {username} hesabı sıfırlandı!"
            else:
                text = f"❌ İşlem başarısız: {result['error']}"
            
            buttons = [
                [("👤 Kullanıcı Bilgisi", f"admin_user_info_{target_user_id}")],
                [("👥 Kullanıcılar", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
            ]
            
        else:
            text = f"❌ Geçersiz işlem: {action}"
            buttons = [
                [("👥 Kullanıcılar", "admin_users"), ("🔧 Admin Panel", "admin_panel")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Admin user action error: {e}")

# Missing duel game function
async def start_duel_game(query, game_id, user, casino_bot):
    """Start and complete a duel game"""
    try:
        with casino_bot.db.get_connection() as conn:
            game = conn.execute('SELECT * FROM active_games WHERE game_id = ?', (game_id,)).fetchone()
            if not game:
                return
            
            players = json.loads(game['players'])
            if len(players) != 2:
                return
            
            player1_id, player2_id = players[0], players[1]
            player1 = casino_bot.get_user(player1_id)
            player2 = casino_bot.get_user(player2_id)
            
            bet_amount = game['bet_amount']
            game_type = game['game_type']
            
            # Play the specific duel game
            result = None
            if game_type == 'duel_coinflip':
                p1_choice = random.choice(['heads', 'tails'])
                p2_choice = random.choice(['heads', 'tails'])
                flip_result = random.choice(['heads', 'tails'])
                
                if p1_choice == flip_result and p2_choice != flip_result:
                    winner = 1
                elif p2_choice == flip_result and p1_choice != flip_result:
                    winner = 2
                else:
                    winner = 0  # Tie
                
                result_text = f"""
🪙 **COIN FLIP DÜELLO SONUCU** 🪙

🎮 **Bahis:** {bet_amount:,} 🐻
👤 **{player1['username'] or f'Oyuncu{player1_id}'}:** {p1_choice}
👤 **{player2['username'] or f'Oyuncu{player2_id}'}:** {p2_choice}

🪙 **Sonuç:** {flip_result.upper()}!

"""
                
            elif game_type.startswith('duel_dice'):
                # Extract dice type from game_type
                if game_type == 'duel_dice':
                    dice_type = 'standard'
                    dice_emoji = '🎲'
                elif game_type == 'duel_dice_standard':
                    dice_type = 'standard'
                    dice_emoji = '🎲'
                elif game_type == 'duel_dice_basketball':
                    dice_type = 'basketball'
                    dice_emoji = '🏀'
                elif game_type == 'duel_dice_football':
                    dice_type = 'football'
                    dice_emoji = '⚽'
                elif game_type == 'duel_dice_slot':
                    dice_type = 'slot_machine'
                    dice_emoji = '🎰'
                elif game_type == 'duel_dice_bowling':
                    dice_type = 'bowling'
                    dice_emoji = '🎳'
                elif game_type == 'duel_dice_darts':
                    dice_type = 'darts'
                    dice_emoji = '🎯'
                else:
                    dice_type = 'standard'
                    dice_emoji = '🎲'
                
                # Use game engine for dice duel
                from game_engine import GameEngine
                dice_result = GameEngine.play_duel_dice_with_type(dice_type.replace('_machine', ''))
                
                p1_dice = dice_result['dice1']
                p2_dice = dice_result['dice2']
                winner = dice_result['winner']
                
                game_name = {
                    'standard': 'STANDART ZAR',
                    'basketball': 'BASKETBOL ZAR',
                    'football': 'FUTBOL ZAR',
                    'slot_machine': 'SLOT ZAR',
                    'bowling': 'BOWLING ZAR',
                    'darts': 'DART ZAR'
                }.get(dice_type, 'ZAR BATTLE')
                
                result_text = f"""
{dice_emoji} **{game_name} DÜELLO SONUCU** {dice_emoji}

🎮 **Bahis:** {bet_amount:,} 🐻
👤 **{player1['username'] or f'Oyuncu{player1_id}'}:** {dice_emoji} {p1_dice}
👤 **{player2['username'] or f'Oyuncu{player2_id}'}:** {dice_emoji} {p2_dice}

"""
                
            elif game_type == 'duel_rockpaper':
                choices = ['rock', 'paper', 'scissors']
                p1_choice = random.choice(choices)
                p2_choice = random.choice(choices)
                
                choice_emojis = {'rock': '🗿', 'paper': '📄', 'scissors': '✂️'}
                
                # Determine winner
                if p1_choice == p2_choice:
                    winner = 0  # Tie
                elif (p1_choice == 'rock' and p2_choice == 'scissors') or \
                     (p1_choice == 'paper' and p2_choice == 'rock') or \
                     (p1_choice == 'scissors' and p2_choice == 'paper'):
                    winner = 1
                else:
                    winner = 2
                
                result_text = f"""
✊ **ROCK-PAPER-SCISSORS SONUCU** ✊

🎮 **Bahis:** {bet_amount:,} 🐻
👤 **{player1['username'] or f'Oyuncu{player1_id}'}:** {choice_emojis[p1_choice]} {p1_choice}
👤 **{player2['username'] or f'Oyuncu{player2_id}'}:** {choice_emojis[p2_choice]} {p2_choice}

"""
            
            # Determine final result and distribute winnings
            if winner == 1:
                result_text += f"🏆 **KAZANAN: {player1['username'] or f'Oyuncu{player1_id}'}!**\n"
                result_text += f"🐻 **Kazanç:** {bet_amount * 2:,} 🐻\n"
                
                # Update balances
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                           (bet_amount * 2, player1_id))
                
                # Update stats
                casino_bot.update_user_stats(player1_id, bet_amount, bet_amount * 2, True)
                casino_bot.update_user_stats(player2_id, bet_amount, 0, False)
                
            elif winner == 2:
                result_text += f"🏆 **KAZANAN: {player2['username'] or f'Oyuncu{player2_id}'}!**\n"
                result_text += f"🐻 **Kazanç:** {bet_amount * 2:,} 🐻\n"
                
                # Update balances
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                           (bet_amount * 2, player2_id))
                
                # Update stats
                casino_bot.update_user_stats(player1_id, bet_amount, 0, False)
                casino_bot.update_user_stats(player2_id, bet_amount, bet_amount * 2, True)
                
            else:
                result_text += "🤝 **BERABERE!**\n"
                result_text += f"🐻 **Para İadesi:** {bet_amount:,} 🐻 (her oyuncuya)\n"
                
                # Refund bets
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                           (bet_amount, player1_id))
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                           (bet_amount, player2_id))
                
                # Update stats (no win/loss for ties)
                casino_bot.update_user_stats(player1_id, bet_amount, bet_amount, False)
                casino_bot.update_user_stats(player2_id, bet_amount, bet_amount, False)
            
            result_text += "\n🎯 **Başka bir düelloya hazır mısın?**"
            
            # Complete the duel
            casino_bot.complete_duel(game_id)
            conn.commit()
        
        buttons = [
            [("🔄 Yeni Düello", "create_duel"), ("🎯 Düelloya Katıl", "join_duel")],
            [("🎮 Solo Games", "solo_games"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Start duel game error: {e}")

# Missing handler functions - Added to fix button functionality issues

async def show_vip_info(query, user, bot_instance):
    """Show VIP information and benefits"""
    try:
        vip_level = bot_instance.get_user_vip_level(user['user_id'])
        
        from config import VIP_LEVELS
        
        text = f"""
👑 **VIP BİLGİLERİ** 👑

🌟 **Mevcut Seviye:** {"VIP " + str(vip_level) if vip_level > 0 else "Standart"}

💎 **VIP Advantages:**
"""
        
        if vip_level > 0:
            vip_data = VIP_LEVELS[vip_level]
            text += f"""
🔥 **VIP {vip_level} Advantages:**
• 🐻 Daily Bonus: +{vip_data['daily_bonus']} 🐻
• 🎯 Maksimum Bahis: {vip_data['max_bet']:,} 🐻
• 🚀 Bonus Multiplier: {vip_data['multiplier_bonus']}x
• 🎁 Özel Bonuslar
• ⚡ Öncelikli Destek
"""
        else:
            text += """
🆕 **Standart Hesap:**
• 🐻 Daily Bonus: 50-200 🐻
• 🎯 Maksimum Bahis: 100,000 🐻
• 🚀 Standart Multiplierlar

👑 **Become VIPmak için:**
• Yatırım yapın ve VIP seviyenizi yükseltin!
• Her seviye yeni avantajlar getirir
"""
        
        buttons = [
            [("💳 Yatırım Yap", "deposit_menu"), ("📊 Profil", "profile")],
            [("🎮 Play Game", "solo_games"), ("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = bot_instance.casino.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"VIP info error: {e}")
        await query.edit_message_text(
            "❌ VIP bilgileri yüklenirken error occurred.",
            reply_markup=bot_instance.casino.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_game_history(query, user, casino_bot):
    """Show user's game history"""
    try:
        with casino_bot.db.get_connection() as conn:
            games = conn.execute('''
                SELECT game_type, bet_amount, win_amount, won, played_at
                FROM solo_game_history 
                WHERE user_id = ? 
                ORDER BY played_at DESC LIMIT 10
            ''', (user['user_id'],)).fetchall()
        
        if not games:
            text = """
📊 **OYUN GEÇMİŞİ** 📊

📝 Henüz oyun geçmişin yok!

🎮 Hemen oyun oynamaya başla:
            """
            buttons = [
                [("🎮 Solo Games", "solo_games"), ("🎯 Düello", "create_duel")],
                [("🏠 Main Menu", "main_menu")]
            ]
        else:
            text = """
📊 **OYUN GEÇMİŞİ** 📊

🎯 **Son 10 Oyunun:**

"""
            for game in games:
                status = "🏆 KAZANDIN" if game['won'] else "💸 Kaybettin"
                game_name = game['game_type'].replace('solo_', '').title()
                text += f"• {status} - {game_name} - {game['bet_amount']:,} 🐻 → {game['win_amount']:,} 🐻\n"
            
            total_games = len(games)
            wins = sum(1 for g in games if g['won'])
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            text += f"""
📈 **Statistics:**
• Toplam Oyun: {total_games}
• Win Rate: {win_rate:.1f}%
            """
            
            buttons = [
                [("🎮 Daha Fazla Oyna", "solo_games"), ("📊 Profil", "profile")],
                [("🏠 Main Menu", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Game history error: {e}")
        await query.edit_message_text(
            "❌ Oyun geçmişi yüklenirken error occurred.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_settings_menu(query, user, casino_bot):
    """Show settings menu"""
    try:
        text = """
⚙️ **AYARLAR** ⚙️

🔧 **Mevcut Ayarlar:**

🌐 **Dil:** Türkçe
🔔 **Bildirimler:** Açık
🎵 **Sesler:** Açık
👤 **Profil:** Herkese Açık

⚡ **Hızlı Ayarlar:**
        """
        
        buttons = [
            [("🌐 Dil Değiştir", "language"), ("🔔 Bildirimler", "notifications")],
            [("👤 Gizlilik", "privacy"), ("📊 Profil", "profile")],
            [("🏠 Main Menu", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Settings menu error: {e}")
        await query.edit_message_text(
            "❌ Ayarlar yüklenirken error occurred.",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def show_notifications_settings(query, user, casino_bot):
    """Show notification settings"""
    text = """
🔔 **BİLDİRİM AYARLARI** 🔔

📱 **Bildirim Türleri:**
• 🎁 Daily Bonus Hatırlatıcı: ✅
• 🎮 Oyun Daveteleri: ✅  
• 👥 Arkadaş İstekleri: ✅
• 🏆 Achievementm Bildirimleri: ✅
• 🐻 Bakiye Uyarıları: ✅

⚡ **Hızlı Ayarlar:**
    """
    
    buttons = [
        [("🔕 Tümünü Kapat", "notifications_off"), ("🔔 Tümünü Aç", "notifications_on")],
        [("⚙️ Back to Settings", "settings"), ("🏠 Main Menu", "main_menu")]
    ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def show_privacy_settings(query, user, casino_bot):
    """Show privacy settings"""
    text = """
👤 **GİZLİLİK AYARLARI** 👤

🔒 **Gizlilik Seçenekleri:**
• 📊 Profil Görünürlüğü: Herkese Açık
• 🎮 Oyun Durumu: Görünür
• 👥 Arkadaş Listesi: Yalnızca Arkadaşlar
• 📈 Statistics: Herkese Açık
• 🏆 Achievementmlar: Herkese Açık

🛡️ **Güvenlik:**
    """
    
    buttons = [
        [("🔒 Özel Yap", "privacy_private"), ("🌐 Herkese Aç", "privacy_public")],
        [("⚙️ Back to Settings", "settings"), ("🏠 Main Menu", "main_menu")]
    ]
    
    keyboard = casino_bot.create_keyboard(buttons)
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')


# Import required modules at the top
import asyncio
import random
import json

# Tüm solo oyunlar için handler fonksiyonları
async def handle_solo_game_menu(query, user, casino_bot, game_type, game_name):
    """Mevcut solo oyunlar için bahis menüsü gösterir"""
    try:
        balance = user['fun_coins']
        
        bet_text = f"""
🎮 **{game_name}**

💰 **Bakiyeniz:** {balance:,} 🐻

Bahis miktarınızı seçin:
        """
        
        # Dinamik bahis butonları
        bet_amounts = []
        if balance >= 10:
            bet_amounts.append(10)
        if balance >= 50:
            bet_amounts.append(50)
        if balance >= 100:
            bet_amounts.append(100)
        if balance >= 500:
            bet_amounts.append(500)
        if balance >= 1000:
            bet_amounts.append(1000)
        if balance >= 5000:
            bet_amounts.append(5000)
        
        if not bet_amounts:
            await query.edit_message_text(
                "❌ Yetersiz bakiye! En az 10 🐻 gerekli.",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyunlar", "games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
            
        buttons = []
        for i in range(0, len(bet_amounts), 2):
            row = []
            for j in range(2):
                if i + j < len(bet_amounts):
                    amount = bet_amounts[i + j]
                    # game_type'dan solo_ prefix'ini kaldır
                    clean_game_type = game_type.replace("solo_", "")
                    row.append((f"💰 {amount} 🐻", f"play_game_{clean_game_type}_{amount}"))
            buttons.append(row)
        
        buttons.append([("🔙 Geri", "games"), ("🏠 Ana Menü", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(bet_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Solo game menu error: {e}")

async def handle_solo_game_play(query, user, casino_bot, game_type, bet_amount):
    """Mevcut solo oyunları oynatır"""
    try:
        from solo_games import SoloGameEngine
        
        # Bahis doğrulama
        if user['fun_coins'] < bet_amount:
            await query.edit_message_text(
                "❌ Yetersiz bakiye!",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyunlar", "games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
        
        # Oyunu oyna
        solo_engine = SoloGameEngine()
        full_game_type = f"solo_{game_type}"
        
        if game_type == "slots":
            result = solo_engine.play_solo_slots(bet_amount, user['user_id'])
        elif game_type == "roulette":
            result = solo_engine.play_solo_roulette(bet_amount, "color", "red", user['user_id'])
        elif game_type == "blackjack":
            result = solo_engine.play_solo_blackjack(bet_amount, user['user_id'])
        elif game_type == "crash":
            result = solo_engine.play_solo_crash(bet_amount, 2.0, user['user_id'])
        elif game_type == "mines":
            result = solo_engine.play_solo_mines(bet_amount, 3, 5, user['user_id'])
        elif game_type == "baccarat":
            result = solo_engine.play_solo_baccarat(bet_amount, "player", user['user_id'])
        elif game_type == "keno":
            result = solo_engine.play_solo_keno(bet_amount, [1, 2, 3, 4, 5], user['user_id'])
        elif game_type == "dice":
            result = solo_engine.play_solo_dice(bet_amount, 4, user['user_id'])
        else:
            await query.edit_message_text("❌ Bilinmeyen oyun türü!")
            return
        
        # Bakiye güncelle
        old_balance = user['fun_coins']
        new_balance = old_balance - bet_amount + result['win_amount']
        casino_bot.update_user_balance(user['user_id'], new_balance)
        
        # Sonuç mesajı
        if result['won']:
            status_emoji = "🎉"
            status_text = "KAZANDINIZ!"
        else:
            status_emoji = "😔"
            status_text = "Kaybettiniz"
        
        # Oyun detaylarını ekle
        game_details = ""
        if game_type == "slots" and 'reels' in result:
            game_details = f"\n🎰 **Sonuç:** {' | '.join(result['reels'])}"
        elif game_type == "roulette" and 'number' in result:
            game_details = f"\n🔴 **Sayı:** {result['number']} {result.get('color_emoji', '')}"
        elif game_type == "blackjack":
            game_details = f"\n♠️ **Sizin kartlarınız:** {result.get('player_value', 0)}\n🎲 **Krupiye:** {result.get('dealer_value', 0)}"
        elif game_type == "crash" and 'crash_point' in result:
            game_details = f"\n🚀 **Crash Noktası:** {result['crash_point']}x"
        elif game_type == "dice" and 'dice_result' in result:
            game_details = f"\n🎲 **Zar Sonucu:** {result.get('dice_emoji', '')} {result['dice_result']}"
        
        result_text = f"""
{status_emoji} **{status_text}** {status_emoji}

{result.get('special_effect', '')}

{result['result_text']}
{game_details}

💰 **Bahis:** {bet_amount:,} 🐻
🎁 **Kazanç:** {result['win_amount']:,} 🐻
📊 **Eski Bakiye:** {old_balance:,} 🐻
📊 **Yeni Bakiye:** {new_balance:,} 🐻
        """
        
        buttons = [
            [("🔄 Tekrar Oyna", f"play_solo_{game_type}"), ("🎮 Diğer Oyunlar", "games")],
            [("📊 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
        
        # İstatistikleri kaydet
        casino_bot.save_solo_game(user['user_id'], full_game_type, bet_amount, result)
        
    except Exception as e:
        logger.error(f"Solo game play error: {e}")
        await query.edit_message_text(
            f"❌ Oyun oynanırken hata oluştu: {e}",
            reply_markup=casino_bot.create_keyboard([
                [("🎮 Oyunlar", "games"), ("🏠 Ana Menü", "main_menu")]
            ])
        )

async def show_user_stats(query, user, casino_bot):
    """Kullanıcı istatistiklerini gösterir"""
    try:
        # Kullanıcı verilerini al
        user_id = user['user_id']
        
        # Veritabanından oyun istatistiklerini al
        with casino_bot.db.get_connection() as conn:
            # Toplam oyun sayısı
            total_games = conn.execute(
                'SELECT COUNT(*) FROM solo_game_history WHERE user_id = ?', 
                (user_id,)
            ).fetchone()[0]
            
            # Toplam bahis miktarı
            total_bet = conn.execute(
                'SELECT SUM(bet_amount) FROM solo_game_history WHERE user_id = ?', 
                (user_id,)
            ).fetchone()[0] or 0
            
            # Toplam kazanç
            total_winnings = conn.execute(
                'SELECT SUM(win_amount) FROM solo_game_history WHERE user_id = ?', 
                (user_id,)
            ).fetchone()[0] or 0
            
            # Kazanılan oyun sayısı
            won_games = conn.execute(
                'SELECT COUNT(*) FROM solo_game_history WHERE user_id = ? AND win_amount > bet_amount',
                (user_id,)
            ).fetchone()[0]
            
            # En çok oynanan oyun
            favorite_game = conn.execute('''
                SELECT game_type, COUNT(*) as count FROM solo_game_history 
                WHERE user_id = ? 
                GROUP BY game_type 
                ORDER BY count DESC 
                LIMIT 1
            ''', (user_id,)).fetchone()
            
            # En yüksek kazanç
            highest_win = conn.execute(
                'SELECT MAX(win_amount) FROM solo_game_history WHERE user_id = ?',
                (user_id,)
            ).fetchone()[0] or 0
        
        # Win rate hesapla
        win_rate = (won_games / total_games * 100) if total_games > 0 else 0
        net_profit = total_winnings - total_bet
        
        # Seviye hesapla (basit sistem)
        level = min(50, max(1, total_games // 10 + 1))
        
        # Prepare conditional values to avoid markdown issues
        profit_emoji = "💚" if net_profit >= 0 else "❤️"
        
        # Achievement emojis and titles
        if total_games >= 100:
            games_emoji = "🥇"
            games_title = "Deneyimli"
        elif total_games >= 10:
            games_emoji = "🥉"  
            games_title = "Yeni Başlayan"
        else:
            games_emoji = "🔰"
            games_title = "Acemi"
            
        if win_rate >= 60:
            winrate_emoji = "💎"
            winrate_title = "Şanslı"
        elif win_rate >= 40:
            winrate_emoji = "🎯"
            winrate_title = "Dengeli" 
        else:
            winrate_emoji = "🍀"
            winrate_title = "Gelişen"
        
        # Favorite game info
        fav_game_text = f"{favorite_game[0]} ({favorite_game[1]} kez)" if favorite_game else "Henüz oyun oynamamış (0 kez)"

        # Escape markdown characters and simplify formatting
        escaped_username = user['username'].replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`', '\\`')
        escaped_fav_game = fav_game_text.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`', '\\`')

        stats_text = f"""📊 {escaped_username}'in İstatistikleri 📊

🎮 Oyun İstatistikleri:
🎯 Toplam Oyun: {total_games:,}
🏆 Kazanılan: {won_games:,}
📈 Kazanma Oranı: {win_rate:.1f}%
⭐ Seviye: {level}

💰 Finansal Durum:
🐻 Güncel Bakiye: {user['fun_coins']:,} 🐻
💸 Toplam Bahis: {total_bet:,} 🐻
🎁 Toplam Kazanç: {total_winnings:,} 🐻
{profit_emoji} Net Kar/Zarar: {net_profit:+,} 🐻
💎 En Büyük Kazanç: {highest_win:,} 🐻

🎯 Favori Oyun:
{escaped_fav_game}

🏅 Başarılar:
{games_emoji} {games_title} Oyuncu
{winrate_emoji} {winrate_title} Oyuncu"""
        
        # Check if we're in a group chat context to determine the right menu
        is_group = hasattr(query.message, 'chat') and query.message.chat.type in ['group', 'supergroup']
        games_button = ("🎮 Oyunlar", "games") if is_group else ("🎮 Solo Oyunlar", "solo_games")
        
        # Create keyboard based on context - no main menu button in group chats
        if is_group:
            keyboard = casino_bot.create_keyboard([
                [games_button, ("📊 Leaderboard", "leaderboard")],
                [("📈 Profil", "profile")]
            ])
        else:
            keyboard = casino_bot.create_keyboard([
                [games_button, ("📊 Leaderboard", "leaderboard")],
                [("📈 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
            ])
        
        await query.edit_message_text(stats_text, reply_markup=keyboard, parse_mode=None)
        
    except Exception as e:
        logger.error(f"Show user stats error: {e}")
        
        # Check if we're in a group chat context for error handling too
        is_group = hasattr(query.message, 'chat') and query.message.chat.type in ['group', 'supergroup']
        games_button = ("🎮 Oyunlar", "games") if is_group else ("🎮 Solo Oyunlar", "solo_games")
        
        # Create error keyboard based on context - no main menu button in group chats
        if is_group:
            error_keyboard = casino_bot.create_keyboard([[games_button]])
        else:
            error_keyboard = casino_bot.create_keyboard([[games_button, ("🏠 Ana Menü", "main_menu")]])
        
        await query.edit_message_text(
            "❌ İstatistikler yüklenemedi!",
            reply_markup=error_keyboard
        )

# Yeni solo oyunlar için handler fonksiyonları
async def handle_new_solo_game_menu(query, user, casino_bot, game_type, game_name):
    """Yeni solo oyunlar için bahis menüsü gösterir"""
    try:
        # Bahis miktarları
        balance = user['fun_coins']
        
        bet_text = f"""
🎮 **{game_name}**

💰 **Bakiyeniz:** {balance:,} 🐻

Bahis miktarınızı seçin:
        """
        
        # Dinamik bahis butonları
        bet_amounts = []
        if balance >= 10:
            bet_amounts.append(10)
        if balance >= 50:
            bet_amounts.append(50)
        if balance >= 100:
            bet_amounts.append(100)
        if balance >= 500:
            bet_amounts.append(500)
        if balance >= 1000:
            bet_amounts.append(1000)
        
        if not bet_amounts:
            await query.edit_message_text(
                "❌ Yetersiz bakiye! En az 10 🐻 gerekli.",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyunlar", "games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
            
        buttons = []
        for i in range(0, len(bet_amounts), 2):
            row = []
            for j in range(2):
                if i + j < len(bet_amounts):
                    amount = bet_amounts[i + j]
                    row.append((f"💰 {amount} 🐻", f"play_new_game_{game_type}_{amount}"))
            buttons.append(row)
        
        buttons.append([("🔙 Geri", "games"), ("🏠 Ana Menü", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(bet_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"New solo game menu error: {e}")

async def handle_new_solo_game_play(query, user, casino_bot, game_type, bet_amount):
    """Yeni solo oyunları oynatır"""
    try:
        from solo_games import SoloGameEngine
        
        # Bahis doğrulama
        if user['fun_coins'] < bet_amount:
            await query.edit_message_text(
                "❌ Yetersiz bakiye!",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Oyunlar", "games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
        
        # Oyunu oyna
        solo_engine = SoloGameEngine()
        
        if game_type == "rock_paper_scissors":
            result = solo_engine.play_rock_paper_scissors(bet_amount, None, user['user_id'])
        elif game_type == "number_guess":
            result = solo_engine.play_number_guess(bet_amount, None, user['user_id'])
        elif game_type == "lucky_wheel":
            result = solo_engine.play_lucky_wheel(bet_amount, user['user_id'])
        else:
            await query.edit_message_text("❌ Bilinmeyen oyun türü!")
            return
        
        # Bakiye güncelle
        old_balance = user['fun_coins']
        new_balance = old_balance - bet_amount + result['win_amount']
        casino_bot.update_user_balance(user['user_id'], new_balance)
        
        # Sonuç mesajı
        if result['won']:
            status_emoji = "🎉"
            status_text = "KAZANDINIZ!"
        else:
            status_emoji = "😔"
            status_text = "Kaybettiniz"
        
        result_text = f"""
{status_emoji} **{status_text}** {status_emoji}

{result.get('special_effect', '')}

{result['result_text']}

💰 **Bahis:** {bet_amount:,} 🐻
🎁 **Kazanç:** {result['win_amount']:,} 🐻
📊 **Eski Bakiye:** {old_balance:,} 🐻
📊 **Yeni Bakiye:** {new_balance:,} 🐻
        """
        
        buttons = [
            [("🔄 Tekrar Oyna", f"play_{game_type}"), ("🎮 Diğer Oyunlar", "games")],
            [("📊 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
        ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
        
        # İstatistikleri kaydet
        casino_bot.save_solo_game(user['user_id'], f"new_{game_type}", bet_amount, result)
        
    except Exception as e:
        logger.error(f"New solo game play error: {e}")
        await query.edit_message_text(
            f"❌ Oyun oynanırken hata oluştu: {e}",
            reply_markup=casino_bot.create_keyboard([
                [("🎮 Oyunlar", "games"), ("🏠 Ana Menü", "main_menu")]
            ])
        )

if __name__ == "__main__":
    # Set proper event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run the main function
    main()