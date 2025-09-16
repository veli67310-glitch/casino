#!/usr/bin/env python3
"""
🎮 Casino Bot Main Class
"""

import json
import random
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import GAMES, ACHIEVEMENTS, SOLO_GAMES, FRIEND_CODE_CHARS
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class MultiplayerCasino:
    """Multiplayer casino system"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.active_games = {}
        self.waiting_players = {}
        
        # Initialize solo game engine
        try:
            from solo_games import SoloGameEngine
            self.solo_engine = SoloGameEngine()
            logger.info("Solo game engine initialized successfully")
        except ImportError as e:
            logger.warning(f"Solo game engine not available: {e}")
            self.solo_engine = None
    
    def generate_friend_code(self):
        """Generate 6-digit unique friend code"""
        while True:
            code = ''.join(random.choices(FRIEND_CODE_CHARS, k=6))
            with self.db.get_connection() as conn:
                existing = conn.execute('SELECT user_id FROM users WHERE friend_code = ?', (code,)).fetchone()
                if not existing:
                    return code
    
    def get_user(self, user_id: int, username: str = None) -> sqlite3.Row:
        """Get or create user information"""
        with self.db.get_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            
            if not user:
                friend_code = self.generate_friend_code()
                conn.execute('''INSERT INTO users 
                    (user_id, username, fun_coins, friend_code) VALUES (?, ?, ?, ?)''', 
                    (user_id, username, 1000, friend_code))
                conn.commit()
                user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            elif not user['friend_code']:
                friend_code = self.generate_friend_code()
                conn.execute('UPDATE users SET friend_code = ? WHERE user_id = ?', (friend_code, user_id))
                conn.commit()
                user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            
            return user
    
    def update_user_stats(self, user_id: int, bet_amount: int, won_amount: int, won: bool):
        """Update user statistics"""
        with self.db.get_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            
            # If user doesn't exist, create them first
            if user is None:
                user = self.get_user(user_id)
            
            new_streak = user['win_streak'] + 1 if won else 0
            max_streak = max(user['max_streak'], new_streak)
            xp_gain = bet_amount // 10 if won else bet_amount // 20
            new_xp = user['xp'] + xp_gain
            new_level = (new_xp // 1000) + 1
            
            conn.execute('''UPDATE users SET 
                fun_coins = fun_coins - ? + ?,
                total_bet = total_bet + ?,
                total_won = total_won + ?,
                games_count = games_count + 1,
                win_streak = ?,
                max_streak = ?,
                xp = ?,
                level = ?,
                last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?''',
                (bet_amount, won_amount, bet_amount, won_amount, 
                 new_streak, max_streak, new_xp, new_level, user_id))
            conn.commit()
            self.check_achievements(user_id, new_streak, bet_amount, won)
    
    def check_achievements(self, user_id: int, streak: int, bet_amount: int, won: bool):
        """Check and award achievements"""
        with self.db.get_connection() as conn:
            unlocked = [row['achievement_id'] for row in conn.execute('SELECT achievement_id FROM user_achievements WHERE user_id = ?', (user_id,))]
            
            if won and "first_win" not in unlocked:
                self.unlock_achievement(user_id, "first_win")
            
            if streak >= 5 and "streak_5" not in unlocked:
                self.unlock_achievement(user_id, "streak_5")
            
            if streak >= 10 and "streak_10" not in unlocked:
                self.unlock_achievement(user_id, "streak_10")
            
            if bet_amount >= 1000 and "high_roller" not in unlocked:
                self.unlock_achievement(user_id, "high_roller")
    
    def unlock_achievement(self, user_id: int, ach_id: str):
        """Unlock achievement"""
        with self.db.get_connection() as conn:
            conn.execute('INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?, ?)', (user_id, ach_id))
            reward = ACHIEVEMENTS[ach_id]['reward']
            conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?', (reward, user_id))
            conn.commit()
    
    def create_duel(self, creator_id: int, game_type: str, bet_amount: int) -> str:
        """Create duel"""
        game_id = f"DUEL_{int(time.time())}_{random.randint(1000, 9999)}"
        
        with self.db.get_connection() as conn:
            players_data = json.dumps([creator_id])
            conn.execute('''INSERT INTO active_games 
                (game_id, game_type, creator_id, bet_amount, players) 
                VALUES (?, ?, ?, ?, ?)''',
                (game_id, game_type, creator_id, bet_amount, players_data))
            conn.commit()
        
        return game_id
    
    def join_duel(self, game_id: str, player_id: int) -> bool:
        """Join duel"""
        with self.db.get_connection() as conn:
            game = conn.execute('SELECT * FROM active_games WHERE game_id = ?', (game_id,)).fetchone()
            
            if not game or game['status'] != 'waiting':
                return False
            
            players = json.loads(game['players'])
            if len(players) >= GAMES[game['game_type']]['players'] or player_id in players:
                return False
            
            players.append(player_id)
            status = 'ready' if len(players) == GAMES[game['game_type']]['players'] else 'waiting'
            conn.execute('UPDATE active_games SET players = ?, status = ? WHERE game_id = ?',
                        (json.dumps(players), status, game_id))
            conn.commit()
            
            return True
    
    def get_daily_quests(self, user_id: int) -> List[dict]:
        """Get daily quests"""
        today = datetime.now().date().isoformat()
        
        with self.db.get_connection() as conn:
            quests = conn.execute('''SELECT * FROM daily_quests 
                WHERE user_id = ? AND date = ?''', (user_id, today)).fetchall()
            
            if not quests:
                daily_quests = [
                    {'quest_type': 'play_games', 'target': 5, 'reward': 100},
                    {'quest_type': 'win_games', 'target': 3, 'reward': 150},
                    {'quest_type': 'spend_coins', 'target': 100, 'reward': 200},
                    {'quest_type': 'invite_friend', 'target': 1, 'reward': 300}
                ]
                
                for quest in daily_quests:
                    conn.execute('''INSERT INTO daily_quests 
                        (user_id, quest_type, target, reward, date) VALUES (?, ?, ?, ?, ?)''',
                        (user_id, quest['quest_type'], quest['target'], quest['reward'], today))
                
                conn.commit()
                quests = conn.execute('''SELECT * FROM daily_quests 
                    WHERE user_id = ? AND date = ?''', (user_id, today)).fetchall()
            
            return [dict(q) for q in quests]
    
    def create_keyboard(self, buttons: List[List[tuple]]) -> InlineKeyboardMarkup:
        """Keyboard builder"""
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button_text, callback_data in row:
                # Ensure callback_data is properly set and not confused with URL
                if isinstance(callback_data, str) and not callback_data.startswith('http'):
                    keyboard_row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                elif isinstance(callback_data, str) and callback_data.startswith('http'):
                    # If it's a URL, use url parameter instead
                    keyboard_row.append(InlineKeyboardButton(button_text, url=callback_data))
                else:
                    # Fallback to string conversion
                    keyboard_row.append(InlineKeyboardButton(button_text, callback_data=str(callback_data)))
            keyboard.append(keyboard_row)
        return InlineKeyboardMarkup(keyboard)
    
    def save_solo_game(self, user_id: int, game_type: str, bet_amount: int, result: dict):
        """Save solo game history and process referral commission"""
        with self.db.get_connection() as conn:
            conn.execute('''INSERT INTO solo_game_history 
                (user_id, game_type, bet_amount, win_amount, multiplier, result_data) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, game_type, bet_amount, result['win_amount'], 
                 result.get('multiplier', 0), json.dumps(result)))
            conn.commit()
            
            # Process referral commission
            commission = self.process_referral_commission(user_id, bet_amount, game_type)
            if commission > 0:
                logger.info(f"Referral commission: {commission} FC for user {user_id}'s bet of {bet_amount} FC")
    
    def add_friend_by_code(self, user_id: int, friend_code: str) -> dict:
        """Add friend by friend code"""
        with self.db.get_connection() as conn:
            friend = conn.execute('SELECT user_id, username FROM users WHERE friend_code = ?', (friend_code,)).fetchone()
            
            if not friend:
                return {"success": False, "message": "Friend code not found!"}
            
            if friend['user_id'] == user_id:
                return {"success": False, "message": "Kendini ekleyemezsin!"}
            
            existing = conn.execute('''SELECT * FROM friendships 
                WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)''',
                (user_id, friend['user_id'], friend['user_id'], user_id)).fetchone()
            
            if existing:
                if existing['status'] == 'accepted':
                    return {"success": False, "message": "This person is already your friend!"}
                else:
                    return {"success": False, "message": "Pending friend request exists!"}
            
            conn.execute('''INSERT INTO friendships (user1_id, user2_id, status) 
                VALUES (?, ?, 'pending')''', (user_id, friend['user_id']))
            conn.commit()
            
            return {"success": True, "message": f"Friend request sent to {friend['username']}!"}
    
    def create_referral(self, referrer_code: str, new_user_id: int) -> dict:
        """Create referral relationship when new user signs up"""
        with self.db.get_connection() as conn:
            # Find referrer by code
            referrer = conn.execute('SELECT user_id, username FROM users WHERE friend_code = ?', (referrer_code,)).fetchone()
            
            if not referrer:
                return {"success": False, "message": "Invalid referral code!"}
            
            if referrer['user_id'] == new_user_id:
                return {"success": False, "message": "Cannot refer yourself!"}
            
            # Check if referral already exists
            existing = conn.execute('SELECT id FROM referrals WHERE referred_user_id = ?', (new_user_id,)).fetchone()
            if existing:
                return {"success": False, "message": "User already has a referrer!"}
            
            # Create referral relationship
            conn.execute('''INSERT INTO referrals (referrer_user_id, referred_user_id) 
                VALUES (?, ?)''', (referrer['user_id'], new_user_id))
            
            # Give signup bonus to new user
            conn.execute('UPDATE users SET fun_coins = fun_coins + 1000 WHERE user_id = ?', (new_user_id,))
            
            # Give referrer bonus
            conn.execute('UPDATE users SET fun_coins = fun_coins + 500 WHERE user_id = ?', (referrer['user_id'],))
            
            conn.commit()
            
            return {
                "success": True, 
                "message": f"Referral created! You got 1000 FC, {referrer['username']} got 500 FC!",
                "referrer_name": referrer['username']
            }
    
    def process_referral_commission(self, user_id: int, bet_amount: int, game_type: str):
        """Process commission for referrer when referred user plays"""
        with self.db.get_connection() as conn:
            # Check if this user was referred
            referral = conn.execute('''SELECT id, referrer_user_id, commission_rate 
                FROM referrals WHERE referred_user_id = ? AND is_active = 1''', (user_id,)).fetchone()
            
            if referral:
                commission = int(bet_amount * referral['commission_rate'])
                if commission > 0:
                    # Add commission to referrer
                    conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?', 
                               (commission, referral['referrer_user_id']))
                    
                    # Update total commission in referrals table
                    conn.execute('UPDATE referrals SET total_commission_earned = total_commission_earned + ? WHERE id = ?',
                               (commission, referral['id']))
                    
                    # Log commission
                    conn.execute('''INSERT INTO referral_commissions 
                        (referral_id, game_bet_amount, commission_amount, game_type) 
                        VALUES (?, ?, ?, ?)''', 
                        (referral['id'], bet_amount, commission, game_type))
                    
                    conn.commit()
                    return commission
            return 0
    
    def get_referral_stats(self, user_id: int) -> dict:
        """Get referral statistics for user"""
        with self.db.get_connection() as conn:
            # Get referrals made by this user
            referrals = conn.execute('''SELECT u.username, r.total_commission_earned, r.created_at
                FROM referrals r JOIN users u ON r.referred_user_id = u.user_id 
                WHERE r.referrer_user_id = ?''', (user_id,)).fetchall()
            
            # Get total commission earned
            total_commission = conn.execute('''SELECT COALESCE(SUM(total_commission_earned), 0) 
                FROM referrals WHERE referrer_user_id = ?''', (user_id,)).fetchone()[0]
            
            # Check if this user was referred
            referred_by = conn.execute('''SELECT u.username FROM referrals r 
                JOIN users u ON r.referrer_user_id = u.user_id 
                WHERE r.referred_user_id = ?''', (user_id,)).fetchone()
            
            return {
                "referrals": [dict(r) for r in referrals],
                "total_commission": total_commission,
                "total_referrals": len(referrals),
                "referred_by": referred_by['username'] if referred_by else None
            }
    
    def get_friend_requests(self, user_id: int) -> list:
        """Get pending friend requests"""
        with self.db.get_connection() as conn:
            requests = conn.execute('''SELECT f.user1_id, u.username, u.level, f.created_at 
                FROM friendships f 
                JOIN users u ON f.user1_id = u.user_id 
                WHERE f.user2_id = ? AND f.status = 'pending'
                ORDER BY f.created_at DESC''', (user_id,)).fetchall()
            return [dict(req) for req in requests]
    
    def accept_friend_request(self, user_id: int, requester_id: int) -> bool:
        """Accept friend request"""
        with self.db.get_connection() as conn:
            result = conn.execute('''UPDATE friendships SET status = 'accepted' 
                WHERE user1_id = ? AND user2_id = ? AND status = 'pending' ''',
                (requester_id, user_id))
            conn.commit()
            return result.rowcount > 0
    
    def get_daily_bonus(self, user_id: int) -> dict:
        """Give daily bonus"""
        with self.db.get_connection() as conn:
            user = conn.execute('SELECT last_daily_bonus FROM users WHERE user_id = ?', (user_id,)).fetchone()
            last_bonus = user['last_daily_bonus']
            if last_bonus and datetime.fromisoformat(last_bonus).date() == datetime.now().date():
                return {"success": False, "message": "You already received today's bonus!"}
            
            bonus = random.randint(50, 200)
            conn.execute('UPDATE users SET fun_coins = fun_coins + ?, last_daily_bonus = CURRENT_TIMESTAMP WHERE user_id = ?', (bonus, user_id))
            conn.commit()
            return {"success": True, "bonus": bonus}
    
    def get_daily_quests(self, user_id: int) -> list:
        """Get user's daily quests"""
        today = datetime.now().date().isoformat()
        with self.db.get_connection() as conn:
            quests = conn.execute('''
                SELECT * FROM daily_quests 
                WHERE user_id = ? AND date = ?
            ''', (user_id, today)).fetchall()
            
            if not quests:
                # Create default daily quests
                default_quests = [
                    {"quest_type": "play_games", "target": 5, "reward": 100, "progress": 0},
                    {"quest_type": "win_games", "target": 3, "reward": 150, "progress": 0},
                    {"quest_type": "bet_coins", "target": 1000, "reward": 200, "progress": 0}
                ]
                
                for quest in default_quests:
                    conn.execute('''
                        INSERT INTO daily_quests 
                        (user_id, quest_type, progress, target, reward, date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, quest["quest_type"], quest["progress"], 
                         quest["target"], quest["reward"], today))
                
                conn.commit()
                quests = conn.execute('''
                    SELECT * FROM daily_quests 
                    WHERE user_id = ? AND date = ?
                ''', (user_id, today)).fetchall()
            
            return [dict(q) for q in quests]
    
    def save_solo_game(self, user_id: int, game_type: str, bet_amount: int, result: dict):
        """Save solo game result to history and process referral commission"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT INTO solo_game_history 
                    (user_id, game_type, bet_amount, win_amount, multiplier, won, played_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, game_type, bet_amount, 
                     result.get('win_amount', 0), 
                     result.get('multiplier', 0), 
                     result.get('won', False)))
                conn.commit()
                
                # Process referral commission
                commission = self.process_referral_commission(user_id, bet_amount, game_type)
                if commission > 0:
                    logger.info(f"Referral commission: {commission} FC for user {user_id}'s bet of {bet_amount} FC")
                    
        except Exception as e:
            logger.error(f"Error saving solo game: {e}")
    
    def create_tournament(self, creator_id: int, game_type: str, buy_in: int, name: str) -> str:
        """Create tournament"""
        tournament_id = f"TOUR_{int(time.time())}_{random.randint(1000, 9999)}"
        with self.db.get_connection() as conn:
            participants = json.dumps([creator_id])
            conn.execute('''INSERT INTO tournaments 
                (tournament_id, name, game_type, buy_in, participants, start_time) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (tournament_id, name, game_type, buy_in, participants, (datetime.now() + timedelta(minutes=5)).isoformat()))
            conn.commit()
        return tournament_id
    
    def join_tournament(self, tournament_id: str, player_id: int) -> bool:
        """Join tournament"""
        with self.db.get_connection() as conn:
            tour = conn.execute('SELECT * FROM tournaments WHERE tournament_id = ?', (tournament_id,)).fetchone()
            if not tour or tour['status'] != 'open':
                return False
            
            participants = json.loads(tour['participants'])
            if player_id in participants:
                return False
            
            max_players = GAMES[tour['game_type']]['players']
            if len(participants) >= max_players:
                return False
            
            participants.append(player_id)
            prize_pool = tour['prize_pool'] + tour['buy_in']
            conn.execute('UPDATE tournaments SET participants = ?, prize_pool = ? WHERE tournament_id = ?',
                         (json.dumps(participants), prize_pool, tournament_id))
            conn.commit()
            return True
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        with self.db.get_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
            if not user:
                return {}
            
            # Solo oyun istatistikleri
            solo_stats = conn.execute('''SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN win_amount > bet_amount THEN 1 ELSE 0 END) as games_won,
                SUM(CASE WHEN win_amount <= bet_amount THEN 1 ELSE 0 END) as games_lost,
                MAX(win_amount) as biggest_win,
                MAX(bet_amount) as biggest_loss
                FROM solo_game_history WHERE user_id = ?''', (user_id,)).fetchone()
            
            if solo_stats and solo_stats['total_games'] > 0:
                win_rate = (solo_stats['games_won'] / solo_stats['total_games']) * 100
            else:
                win_rate = 0
            
            return {
                'total_games': solo_stats['total_games'] if solo_stats else 0,
                'games_won': solo_stats['games_won'] if solo_stats else 0,
                'games_lost': solo_stats['games_lost'] if solo_stats else 0,
                'win_rate': win_rate,
                'biggest_win': solo_stats['biggest_win'] if solo_stats else 0,
                'biggest_loss': solo_stats['biggest_loss'] if solo_stats else 0
            }
    
    def get_user_achievements(self, user_id: int) -> list:
        """Get user achievements"""
        with self.db.get_connection() as conn:
            achievements = conn.execute('''SELECT achievement_id, unlocked_at 
                FROM user_achievements WHERE user_id = ? 
                ORDER BY unlocked_at DESC''', (user_id,)).fetchall()
            
            result = []
            for ach in achievements:
                if ach['achievement_id'] in ACHIEVEMENTS:
                    ach_data = ACHIEVEMENTS[ach['achievement_id']].copy()
                    ach_data['unlocked_at'] = ach['unlocked_at']
                    result.append(ach_data)
            
            return result
    
    def get_friend_requests(self, user_id: int):
        """Get pending friend requests for user"""
        try:
            with self.db.get_connection() as conn:
                requests = conn.execute('''
                    SELECT f.*, u.username, u.level FROM friendships f
                    JOIN users u ON f.user1_id = u.user_id
                    WHERE f.user2_id = ? AND f.status = "pending"
                    ORDER BY f.created_at DESC
                ''', (user_id,)).fetchall()
                return [dict(req) for req in requests]
        except Exception as e:
            logger.error(f"Get friend requests error: {e}")
            return []
    
    def accept_friend_request(self, user_id: int, friend_id: int) -> bool:
        """Accept a friend request"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('''UPDATE friendships 
                    SET status = "accepted" 
                    WHERE user1_id = ? AND user2_id = ? AND status = "pending"''',
                    (friend_id, user_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Accept friend error: {e}")
            return False
    
    def create_duel(self, creator_id: int, game_type: str, bet_amount: int) -> str:
        """Create a new duel"""
        try:
            game_id = f"DUEL_{int(datetime.now().timestamp())}_{creator_id}"
            
            with self.db.get_connection() as conn:
                # Deduct bet from creator
                conn.execute('UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?',
                           (bet_amount, creator_id))
                
                # Create game
                conn.execute('''INSERT INTO active_games 
                    (game_id, game_type, creator_id, bet_amount, players, status) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (game_id, game_type, creator_id, bet_amount, json.dumps([creator_id]), "waiting"))
                conn.commit()
            
            return game_id
            
        except Exception as e:
            logger.error(f"Create duel error: {e}")
            return ""
    
    def join_duel(self, game_id: str, user_id: int) -> bool:
        """Join an existing duel"""
        try:
            with self.db.get_connection() as conn:
                game = conn.execute('SELECT * FROM active_games WHERE game_id = ?', (game_id,)).fetchone()
                
                if not game or game['status'] != 'waiting':
                    return False
                
                players = json.loads(game['players'])
                if len(players) >= 2 or user_id in players:
                    return False
                
                # Deduct bet from joiner
                conn.execute('UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?',
                           (game['bet_amount'], user_id))
                
                # Add player and start game
                players.append(user_id)
                conn.execute('''UPDATE active_games 
                    SET players = ?, status = "active" 
                    WHERE game_id = ?''',
                    (json.dumps(players), game_id))
                conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Join duel error: {e}")
            return False
    
    def complete_duel(self, game_id: str):
        """Complete a duel and clean up"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('UPDATE active_games SET status = "completed" WHERE game_id = ?', (game_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Complete duel error: {e}")
    
    def validate_bet_amount(self, user_id: int, bet_amount: int, user_balance: int) -> dict:
        """Validate bet amount against user balance and limits"""
        try:
            # Check minimum bet
            if bet_amount < 1:
                return {"valid": False, "reason": "❌ Minimum bahis 1 FC!"}
            
            # Check balance
            if bet_amount > user_balance:
                return {"valid": False, "reason": f"❌ Yetersiz bakiye! Mevcut: {user_balance:,} FC"}
            
            # Check if payment manager exists for advanced limits
            if hasattr(self, 'payment_manager') and self.payment_manager:
                limit_check = self.payment_manager.check_bet_limits(user_id, bet_amount, user_balance)
                if not limit_check["allowed"]:
                    return {"valid": False, "reason": f"❌ {limit_check['reason']}"}
            else:
                # Basic limits without payment manager
                max_bet = min(user_balance // 10, 100000)  # Max 10% of balance or 100k
                if bet_amount > max_bet:
                    return {"valid": False, "reason": f"❌ Maksimum bahis: {max_bet:,} FC"}
            
            return {"valid": True, "reason": ""}
            
        except Exception as e:
            logger.error(f"Bet validation error: {e}")
            return {"valid": False, "reason": "❌ Bet could not be validated!"}
    
    def get_user_vip_level(self, user_id: int) -> int:
        """Get user's VIP level based on deposits"""
        try:
            if hasattr(self, 'payment_manager') and self.payment_manager:
                stats = self.payment_manager.get_user_payment_stats(user_id)
                total_deposited = stats['total_deposits'] if 'total_deposits' in stats else 0
                
                from config import VIP_LEVELS
                for level in sorted(VIP_LEVELS.keys(), reverse=True):
                    if total_deposited >= VIP_LEVELS[level]['min_deposit']:
                        return level
            
            return 0  # Default level
            
        except Exception as e:
            logger.error(f"VIP level error: {e}")
            return 0
    
    def get_user_max_bet(self, user_id: int) -> int:
        """Get user's maximum bet based on VIP level"""
        try:
            vip_level = self.get_user_vip_level(user_id)
            
            # VIP bet limits
            vip_limits = {
                0: 100000,      # Standard
                1: 250000,      # VIP 1
                2: 500000,      # VIP 2
                3: 1000000,     # VIP 3
                4: 2000000,     # VIP 4
                5: 5000000      # VIP 5
            }
            
            return vip_limits.get(vip_level, 100000)
            
        except Exception as e:
            logger.error(f"Max bet error: {e}")
            return 100000
    
    def update_user_balance(self, user_id: int, amount: int):
        """Update user's balance by adding/subtracting amount"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?', 
                           (amount, user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Update user balance error: {e}")