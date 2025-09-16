#!/usr/bin/env python3
"""
🎮 Advanced Casino Bot Features - Tournaments, Admin Panel, Events
"""

import json
import random
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from config import GAMES, ACHIEVEMENTS, VIP_LEVELS

logger = logging.getLogger(__name__)

class TournamentManager:
    """Advanced tournament management system"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.active_tournaments = {}
        self.tournament_types = {
            "quick_slots": {
                "name": "⚡ Hızlı Slots Turnuvası",
                "duration": 300,  # 5 minutes
                "buy_in": 1000,
                "max_players": 16,
                "prize_multiplier": 0.9,  # 90% of total buy-ins as prize
                "game_type": "slots"
            },
            "weekly_blackjack": {
                "name": "🃏 Haftalık Blackjack Championship",
                "duration": 604800,  # 1 week
                "buy_in": 5000,
                "max_players": 64,
                "prize_multiplier": 0.95,
                "game_type": "blackjack"
            },
            "royal_roulette": {
                "name": "👑 Royal Roulette Showdown",
                "duration": 1800,  # 30 minutes
                "buy_in": 2500,
                "max_players": 32,
                "prize_multiplier": 0.92,
                "game_type": "roulette"
            },
            "mega_crash": {
                "name": "🚀 Mega Crash Tournament",
                "duration": 900,  # 15 minutes
                "buy_in": 10000,
                "max_players": 20,
                "prize_multiplier": 0.88,
                "game_type": "crash"
            }
        }
    
    def create_tournament(self, tournament_type: str, creator_id: int) -> Dict:
        """Create a new tournament"""
        if tournament_type not in self.tournament_types:
            return {"success": False, "error": "Invalid tournament type"}
        
        config = self.tournament_types[tournament_type]
        tournament_id = f"TOUR_{tournament_type}_{int(datetime.now().timestamp())}"
        
        start_time = datetime.now() + timedelta(minutes=2)  # Start in 2 minutes
        end_time = start_time + timedelta(seconds=config["duration"])
        
        tournament_data = {
            "id": tournament_id,
            "type": tournament_type,
            "name": config["name"],
            "creator_id": creator_id,
            "buy_in": config["buy_in"],
            "max_players": config["max_players"],
            "prize_multiplier": config["prize_multiplier"],
            "game_type": config["game_type"],
            "participants": [],
            "status": "registration",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "created_at": datetime.now().isoformat(),
            "prize_pool": 0,
            "winner_id": None,
            "results": []
        }
        
        try:
            with self.db.get_connection() as conn:
                conn.execute('''INSERT INTO tournaments 
                    (tournament_id, name, game_type, buy_in, participants, status, start_time, prize_pool, creator_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tournament_id, config["name"], config["game_type"], config["buy_in"], 
                     json.dumps([]), "registration", start_time.isoformat(), 0, creator_id))
                conn.commit()
            
            self.active_tournaments[tournament_id] = tournament_data
            return {"success": True, "tournament": tournament_data}
            
        except Exception as e:
            logger.error(f"Tournament creation error: {e}")
            return {"success": False, "error": str(e)}
    
    def join_tournament(self, tournament_id: str, user_id: int, user_balance: int) -> Dict:
        """Join a tournament"""
        if tournament_id not in self.active_tournaments:
            return {"success": False, "error": "Tournament not found"}
        
        tournament = self.active_tournaments[tournament_id]
        
        if tournament["status"] != "registration":
            return {"success": False, "error": "Registration closed"}
        
        if user_id in tournament["participants"]:
            return {"success": False, "error": "Already registered"}
        
        if len(tournament["participants"]) >= tournament["max_players"]:
            return {"success": False, "error": "Tournament full"}
        
        if user_balance < tournament["buy_in"]:
            return {"success": False, "error": "Insufficient balance"}
        
        try:
            # Add participant
            tournament["participants"].append(user_id)
            tournament["prize_pool"] += tournament["buy_in"]
            
            # Update database
            with self.db.get_connection() as conn:
                conn.execute('''UPDATE tournaments 
                    SET participants = ?, prize_pool = ? 
                    WHERE tournament_id = ?''',
                    (json.dumps(tournament["participants"]), tournament["prize_pool"], tournament_id))
                
                # Deduct buy-in from user
                conn.execute('UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?',
                           (tournament["buy_in"], user_id))
                conn.commit()
            
            return {"success": True, "tournament": tournament}
            
        except Exception as e:
            logger.error(f"Tournament join error: {e}")
            return {"success": False, "error": str(e)}
    
    def start_tournament(self, tournament_id: str) -> Dict:
        """Start a tournament"""
        if tournament_id not in self.active_tournaments:
            return {"success": False, "error": "Tournament not found"}
        
        tournament = self.active_tournaments[tournament_id]
        
        if len(tournament["participants"]) < 2:
            return {"success": False, "error": "Not enough participants"}
        
        tournament["status"] = "active"
        
        # Simulate tournament gameplay
        results = self._simulate_tournament_games(tournament)
        tournament["results"] = results
        
        # Determine winner
        winner_id = results[0]["user_id"] if results else None
        tournament["winner_id"] = winner_id
        tournament["status"] = "completed"
        
        # Distribute prizes
        self._distribute_prizes(tournament)
        
        try:
            with self.db.get_connection() as conn:
                conn.execute('''UPDATE tournaments 
                    SET status = ?, winner_id = ? 
                    WHERE tournament_id = ?''',
                    ("completed", winner_id, tournament_id))
                conn.commit()
            
            return {"success": True, "results": results, "winner_id": winner_id}
            
        except Exception as e:
            logger.error(f"Tournament start error: {e}")
            return {"success": False, "error": str(e)}
    
    def _simulate_tournament_games(self, tournament: Dict) -> List[Dict]:
        """Simulate tournament games and generate results"""
        results = []
        participants = tournament["participants"]
        game_type = tournament["game_type"]
        
        for user_id in participants:
            # Simulate game performance
            base_score = random.randint(50, 100)
            
            # Add some skill/luck variation
            skill_bonus = random.randint(-20, 30)
            luck_factor = random.uniform(0.8, 1.3)
            
            final_score = int((base_score + skill_bonus) * luck_factor)
            
            # Game-specific scoring
            if game_type == "slots":
                wins = random.randint(0, 10)
                final_score = wins * 100 + random.randint(0, 500)
            elif game_type == "blackjack":
                hands_won = random.randint(0, 15)
                final_score = hands_won * 50 + random.randint(0, 200)
            elif game_type == "roulette":
                correct_bets = random.randint(0, 8)
                final_score = correct_bets * 150 + random.randint(0, 300)
            elif game_type == "crash":
                successful_cashouts = random.randint(0, 12)
                final_score = successful_cashouts * 80 + random.randint(0, 400)
            
            results.append({
                "user_id": user_id,
                "score": max(0, final_score),
                "position": 0  # Will be set after sorting
            })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Set positions
        for i, result in enumerate(results):
            result["position"] = i + 1
        
        return results
    
    def _distribute_prizes(self, tournament: Dict):
        """Distribute tournament prizes"""
        results = tournament["results"]
        total_prize = int(tournament["prize_pool"] * tournament["prize_multiplier"])
        
        if not results:
            return
        
        # Prize distribution: 50% to winner, 30% to 2nd, 20% to 3rd
        prize_distribution = [0.5, 0.3, 0.2]
        
        try:
            with self.db.get_connection() as conn:
                for i, result in enumerate(results[:3]):  # Top 3 only
                    if i < len(prize_distribution):
                        prize = int(total_prize * prize_distribution[i])
                        conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                                   (prize, result["user_id"]))
                        result["prize"] = prize
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Prize distribution error: {e}")

class EventManager:
    """Special events and seasonal content"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.active_events = {}
        
    def create_daily_challenge(self, date_str: str) -> Dict:
        """Create daily challenge"""
        challenges = [
            {
                "type": "win_streak",
                "name": "🔥 Winning Streak",
                "description": "Win 5 games in a row",
                "target": 5,
                "reward": 2000,
                "emoji": "🔥"
            },
            {
                "type": "big_win",
                "name": "💎 Big Winner",
                "description": "Win 10,000+ FC in a single game",
                "target": 10000,
                "reward": 3000,
                "emoji": "💎"
            },
            {
                "type": "play_games",
                "name": "🎮 Game Master",
                "description": "Play 20 games today",
                "target": 20,
                "reward": 1500,
                "emoji": "🎮"
            },
            {
                "type": "spend_coins",
                "name": "💸 High Roller",
                "description": "Bet 50,000 FC total today",
                "target": 50000,
                "reward": 2500,
                "emoji": "💸"
            }
        ]
        
        return random.choice(challenges)
    
    def check_seasonal_events(self) -> List[Dict]:
        """Check for active seasonal events"""
        now = datetime.now()
        events = []
        
        # Christmas Event (December)
        if now.month == 12:
            events.append({
                "name": "🎄 Christmas Casino",
                "description": "Double daily bonuses and special rewards!",
                "bonus_multiplier": 2.0,
                "special_games": ["christmas_slots", "winter_roulette"]
            })
        
        # New Year Event (January 1-7)
        if now.month == 1 and now.day <= 7:
            events.append({
                "name": "🎊 New Year Lucky Week",
                "description": "Triple XP and bonus achievements!",
                "xp_multiplier": 3.0,
                "bonus_achievements": True
            })
        
        # Summer Event (June-August)
        if now.month in [6, 7, 8]:
            events.append({
                "name": "☀️ Summer Casino Festival",
                "description": "Beach-themed games and cool rewards!",
                "special_games": ["beach_slots", "summer_crash"],
                "bonus_multiplier": 1.5
            })
        
        return events

class AdminPanel:
    """Administrative functions for bot management"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        from config import ADMIN_USER_IDS
        self.admin_users = ADMIN_USER_IDS  # Load from config.py
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_users
    
    def get_bot_statistics(self) -> Dict:
        """Get comprehensive bot statistics"""
        try:
            with self.db.get_connection() as conn:
                # User stats
                total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
                active_today = conn.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE date(last_active) = date('now')
                ''').fetchone()[0]
                
                # Game stats
                total_games = conn.execute('SELECT COUNT(*) FROM solo_game_history').fetchone()[0]
                games_today = conn.execute('''
                    SELECT COUNT(*) FROM solo_game_history 
                    WHERE date(played_at) = date('now')
                ''').fetchone()[0]
                
                # Financial stats
                total_coins = conn.execute('SELECT SUM(fun_coins) FROM users').fetchone()[0] or 0
                total_bets = conn.execute('SELECT SUM(bet_amount) FROM solo_game_history').fetchone()[0] or 0
                total_winnings = conn.execute('SELECT SUM(win_amount) FROM solo_game_history').fetchone()[0] or 0
                
                # Top players
                top_players = conn.execute('''
                    SELECT username, fun_coins, level FROM users 
                    ORDER BY fun_coins DESC LIMIT 5
                ''').fetchall()
                
                # Achievement stats
                total_achievements = conn.execute('SELECT COUNT(*) FROM user_achievements').fetchone()[0]
                
                return {
                    "users": {
                        "total": total_users,
                        "active_today": active_today,
                        "retention_rate": (active_today / total_users * 100) if total_users > 0 else 0
                    },
                    "games": {
                        "total": total_games,
                        "today": games_today,
                        "avg_per_user": total_games / total_users if total_users > 0 else 0
                    },
                    "economy": {
                        "total_coins": total_coins,
                        "total_bets": total_bets,
                        "total_winnings": total_winnings,
                        "house_edge": ((total_bets - total_winnings) / total_bets * 100) if total_bets > 0 else 0
                    },
                    "engagement": {
                        "total_achievements": total_achievements,
                        "avg_achievements": total_achievements / total_users if total_users > 0 else 0
                    },
                    "top_players": [dict(p) for p in top_players]
                }
                
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {}
    
    def manage_user(self, admin_id: int, target_user_id: int, action: str, amount: int = 0) -> Dict:
        """Manage user account (admin only)"""
        if not self.is_admin(admin_id):
            return {"success": False, "error": "Unauthorized"}
        
        try:
            with self.db.get_connection() as conn:
                user = conn.execute('SELECT * FROM users WHERE user_id = ?', (target_user_id,)).fetchone()
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if action == "add_coins":
                    conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                               (amount, target_user_id))
                    message = f"Added {amount:,} coins to user {target_user_id}"
                
                elif action == "remove_coins":
                    conn.execute('UPDATE users SET fun_coins = MAX(0, fun_coins - ?) WHERE user_id = ?',
                               (amount, target_user_id))
                    message = f"Removed {amount:,} coins from user {target_user_id}"
                
                elif action == "reset_user":
                    conn.execute('''UPDATE users SET 
                        fun_coins = 1000, level = 1, xp = 0, win_streak = 0, 
                        total_bet = 0, total_won = 0, games_count = 0 
                        WHERE user_id = ?''', (target_user_id,))
                    message = f"Reset user {target_user_id} to default state"
                
                elif action == "ban_user":
                    # Mark user as banned (you'd need to add a banned column)
                    conn.execute('UPDATE users SET fun_coins = 0 WHERE user_id = ?', (target_user_id,))
                    message = f"Banned user {target_user_id}"
                
                else:
                    return {"success": False, "error": "Invalid action"}
                
                conn.commit()
                return {"success": True, "message": message}
                
        except Exception as e:
            logger.error(f"User management error: {e}")
            return {"success": False, "error": str(e)}
    
    def broadcast_message(self, admin_id: int, message: str) -> Dict:
        """Broadcast message to all users (admin only)"""
        if not self.is_admin(admin_id):
            return {"success": False, "error": "Unauthorized"}
        
        # This would need to be implemented with the bot instance
        # to send messages to all users
        return {"success": True, "message": "Broadcast functionality needs bot integration"}

class AchievementSystem:
    """Enhanced achievement system with dynamic unlocking"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Enhanced achievements
        self.achievements = {
            **ACHIEVEMENTS,  # Include original achievements
            "social_master": {"name": "Social Master", "reward": 2000, "emoji": "👥"},
            "tournament_king": {"name": "Tournament King", "reward": 5000, "emoji": "👑"},
            "perfect_week": {"name": "Perfect Week", "reward": 10000, "emoji": "⭐"},
            "crypto_whale": {"name": "Crypto Whale", "reward": 15000, "emoji": "🐋"},
            "game_collector": {"name": "Game Collector", "reward": 3000, "emoji": "🎯"},
            "lucky_sevens": {"name": "Lucky Sevens", "reward": 7777, "emoji": "🍀"},
            "night_owl": {"name": "Night Owl", "reward": 1000, "emoji": "🦉"},
            "early_bird": {"name": "Early Bird", "reward": 1000, "emoji": "🐦"},
            "comeback_kid": {"name": "Comeback Kid", "reward": 2500, "emoji": "🔄"},
            "risk_taker": {"name": "Risk Taker", "reward": 4000, "emoji": "⚡"}
        }
    
    def check_advanced_achievements(self, user_id: int, user_data: Dict, game_data: Dict = None):
        """Check for advanced achievement unlocks"""
        try:
            with self.db.get_connection() as conn:
                unlocked = set(row[0] for row in conn.execute(
                    'SELECT achievement_id FROM user_achievements WHERE user_id = ?', 
                    (user_id,)).fetchall())
                
                # Time-based achievements
                now = datetime.now()
                hour = now.hour
                
                if hour >= 22 or hour <= 4:  # Night gaming
                    if "night_owl" not in unlocked:
                        self._unlock_achievement(user_id, "night_owl")
                
                if 5 <= hour <= 8:  # Early morning gaming
                    if "early_bird" not in unlocked:
                        self._unlock_achievement(user_id, "early_bird")
                
                # Game variety achievement
                games_played = conn.execute('''
                    SELECT DISTINCT game_type FROM solo_game_history WHERE user_id = ?
                ''', (user_id,)).fetchall()
                
                if len(games_played) >= 5 and "game_collector" not in unlocked:
                    self._unlock_achievement(user_id, "game_collector")
                
                # Tournament achievements
                tournament_wins = conn.execute('''
                    SELECT COUNT(*) FROM tournaments WHERE winner_id = ?
                ''', (user_id,)).fetchone()[0]
                
                if tournament_wins >= 3 and "tournament_king" not in unlocked:
                    self._unlock_achievement(user_id, "tournament_king")
                
                # Comeback achievement (big win after losses)
                if game_data and ('won' in game_data.keys() and game_data['won']) and (user_data['win_streak'] if 'win_streak' in user_data else 0) == 0:
                    recent_losses = conn.execute('''
                        SELECT COUNT(*) FROM solo_game_history 
                        WHERE user_id = ? AND win_amount < bet_amount 
                        AND datetime(played_at) > datetime('now', '-1 hour')
                    ''', (user_id,)).fetchone()[0]
                    
                    if recent_losses >= 5 and "comeback_kid" not in unlocked:
                        self._unlock_achievement(user_id, "comeback_kid")
                
        except Exception as e:
            logger.error(f"Advanced achievement check error: {e}")
    
    def _unlock_achievement(self, user_id: int, achievement_id: str):
        """Unlock an achievement for a user"""
        try:
            with self.db.get_connection() as conn:
                # Check if already unlocked
                existing = conn.execute(
                    'SELECT 1 FROM user_achievements WHERE user_id = ? AND achievement_id = ?',
                    (user_id, achievement_id)).fetchone()
                
                if not existing:
                    reward = self.achievements[achievement_id]['reward']
                    
                    conn.execute('''INSERT INTO user_achievements 
                        (user_id, achievement_id) VALUES (?, ?)''',
                        (user_id, achievement_id))
                    
                    conn.execute('UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?',
                               (reward, user_id))
                    
                    conn.commit()
                    logger.info(f"Achievement unlocked: {achievement_id} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Achievement unlock error: {e}")

# Global instances (to be initialized with database)
tournament_manager = None
event_manager = None
admin_panel = None
achievement_system = None

def initialize_advanced_features(db_manager):
    """Initialize all advanced features with database connection"""
    global tournament_manager, event_manager, admin_panel, achievement_system
    
    tournament_manager = TournamentManager(db_manager)
    event_manager = EventManager(db_manager)
    admin_panel = AdminPanel(db_manager)
    achievement_system = AchievementSystem(db_manager)
    
    logger.info("Advanced features initialized successfully")