#!/usr/bin/env python3
"""
🎮 Casino Bot Veritabanı Yöneticisi
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gelişmiş veritabanı yöneticisi"""
    
    def __init__(self, db_path: str = 'fun_casino.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Performance optimizations
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL') 
        conn.execute('PRAGMA cache_size=10000')
        conn.execute('PRAGMA temp_store=MEMORY')
        return conn
    
    def init_database(self):
        with self.get_connection() as conn:
            # Kullanıcılar tablosu - Enhanced with language support
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                fun_coins INTEGER DEFAULT 1000,
                total_bet INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                games_count INTEGER DEFAULT 0,
                win_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                language_code TEXT DEFAULT 'en',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                friend_code TEXT UNIQUE,
                last_daily_bonus DATETIME DEFAULT NULL
            )''')
            
            # Aktif oyunlar tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS active_games (
                game_id TEXT PRIMARY KEY,
                game_type TEXT,
                creator_id INTEGER,
                bet_amount INTEGER,
                players TEXT,
                status TEXT DEFAULT 'waiting',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Turnuvalar tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS tournaments (
                tournament_id TEXT PRIMARY KEY,
                name TEXT,
                game_type TEXT,
                buy_in INTEGER,
                prize_pool INTEGER DEFAULT 0,
                participants TEXT,
                status TEXT DEFAULT 'open',
                start_time DATETIME,
                winner_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Başarımlar tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )''')
            
            # Arkadaşlık sistemi
            conn.execute('''CREATE TABLE IF NOT EXISTS friendships (
                user1_id INTEGER,
                user2_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            )''')
            
            # Günlük görevler
            conn.execute('''CREATE TABLE IF NOT EXISTS daily_quests (
                user_id INTEGER,
                quest_type TEXT,
                progress INTEGER DEFAULT 0,
                target INTEGER,
                reward INTEGER,
                completed BOOLEAN DEFAULT 0,
                date TEXT,
                PRIMARY KEY (user_id, quest_type, date)
            )''')
            
            # Referral system
            conn.execute('''CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_user_id INTEGER,
                referred_user_id INTEGER,
                signup_bonus INTEGER DEFAULT 1000,
                referrer_bonus INTEGER DEFAULT 500,
                commission_rate REAL DEFAULT 0.05,
                total_commission_earned INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_user_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_user_id) REFERENCES users(user_id)
            )''')
            
            # Referral commissions tracking
            conn.execute('''CREATE TABLE IF NOT EXISTS referral_commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referral_id INTEGER,
                game_bet_amount INTEGER,
                commission_amount INTEGER,
                game_type TEXT,
                earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referral_id) REFERENCES referrals(id)
            )''')
            
            # Solo oyun geçmişi tablosu - Enhanced schema
            conn.execute('''CREATE TABLE IF NOT EXISTS solo_game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_type TEXT,
                bet_amount INTEGER,
                win_amount INTEGER,
                multiplier REAL,
                won BOOLEAN DEFAULT 0,
                result_data TEXT,
                played_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Oyun sonuçları tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS game_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_type TEXT,
                bet_amount INTEGER,
                win_amount INTEGER,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Ödeme tabloları (crypto için)
            conn.execute('''CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                invoice_id TEXT,
                currency TEXT,
                amount REAL,
                fun_coins INTEGER,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                paid_at DATETIME
            )''')
            
            conn.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                currency TEXT,
                amount REAL,
                fun_coins INTEGER,
                wallet_address TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )''')
            
            # Günlük limitler tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS daily_limits (
                user_id INTEGER,
                date TEXT,
                deposited_amount INTEGER DEFAULT 0,
                withdrawn_amount INTEGER DEFAULT 0,
                bet_amount INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )''')
            
            # Kullanıcı aktivite tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')

            # Bekleyen işlemler tablosu - Helius webhook entegrasyonu için
            conn.execute('''CREATE TABLE IF NOT EXISTS pending_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                expected_amount REAL NOT NULL,
                wallet_address TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                transaction_signature TEXT,
                confirmed_at DATETIME,
                fc_amount INTEGER,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')

            # Index'ler oluştur - performans için
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_pending_transactions_user_id
                           ON pending_transactions(user_id)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_pending_transactions_status
                           ON pending_transactions(status)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_pending_transactions_wallet
                           ON pending_transactions(wallet_address)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_pending_transactions_signature
                           ON pending_transactions(transaction_signature)''')
            
            # Add missing columns to existing tables if they don't exist
            try:
                conn.execute('ALTER TABLE solo_game_history ADD COLUMN won BOOLEAN DEFAULT 0')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add total_bets column to daily_limits if it doesn't exist
            try:
                conn.execute('ALTER TABLE daily_limits ADD COLUMN total_bets INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Add new referral system columns
            referral_columns = [
                'signup_bonus INTEGER DEFAULT 1000',
                'referrer_bonus INTEGER DEFAULT 500', 
                'commission_rate REAL DEFAULT 0.05',
                'total_commission_earned INTEGER DEFAULT 0',
                'is_active BOOLEAN DEFAULT 1'
            ]
            
            for column in referral_columns:
                try:
                    conn.execute(f'ALTER TABLE referrals ADD COLUMN {column}')
                except sqlite3.OperationalError:
                    pass  # Column already exists
            
            conn.commit()
        print("SUCCESS: Casino database initialized!")
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(
                    'SELECT language_code FROM users WHERE user_id = ?', 
                    (user_id,)
                ).fetchone()
                return result['language_code'] if result else 'en'
        except Exception as e:
            logger.error(f"Error getting user language: {e}")
            return 'en'
    
    def set_user_language(self, user_id: int, language_code: str) -> bool:
        """Set user's preferred language"""
        try:
            with self.get_connection() as conn:
                # Add language column if it doesn't exist
                try:
                    conn.execute('ALTER TABLE users ADD COLUMN language_code TEXT DEFAULT "en"')
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                # Ensure user exists, if not create with default language
                user_exists = conn.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
                if not user_exists:
                    conn.execute(
                        'INSERT INTO users (user_id, language_code) VALUES (?, ?)',
                        (user_id, language_code)
                    )
                
                conn.execute(
                    'UPDATE users SET language_code = ? WHERE user_id = ?',
                    (language_code, user_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
            return False
    
    def execute(self, query: str, params=None):
        """Execute a query and return cursor for backwards compatibility"""
        self._connection = self.get_connection()
        cursor = self._connection.execute(query, params or [])
        return cursor
    
    def fetchone(self):
        """Fetch one row from the last query"""
        if hasattr(self, '_connection') and self._connection:
            return self._connection.fetchone()
        return None
    
    def commit(self):
        """Commit the current transaction"""
        if hasattr(self, '_connection') and self._connection:
            self._connection.commit()
    
    def close(self):
        """Close the connection"""
        if hasattr(self, '_connection') and self._connection:
            self._connection.close()
            del self._connection

    # Pending Transactions Methods
    def add_pending_transaction(self, user_id: int, expected_amount: float, wallet_address: str, notes: str = None) -> int:
        """Bekleyen işlem ekle"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO pending_transactions
                    (user_id, expected_amount, wallet_address, notes)
                    VALUES (?, ?, ?, ?)
                """, (user_id, expected_amount, wallet_address, notes))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding pending transaction: {e}")
            return None

    def get_pending_transaction_by_criteria(self, wallet_address: str, amount: float, tolerance: float = 0.001):
        """Kriterlere göre bekleyen işlem bul"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM pending_transactions
                    WHERE wallet_address = ?
                    AND status = 'pending'
                    AND ABS(expected_amount - ?) <= ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (wallet_address, amount, tolerance))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting pending transaction: {e}")
            return None

    def confirm_transaction(self, transaction_id: int, transaction_signature: str, fc_amount: int) -> bool:
        """İşlemi onayla"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE pending_transactions
                    SET status = 'confirmed',
                        transaction_signature = ?,
                        confirmed_at = CURRENT_TIMESTAMP,
                        fc_amount = ?
                    WHERE id = ?
                """, (transaction_signature, fc_amount, transaction_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error confirming transaction: {e}")
            return False

    def get_user_pending_transactions(self, user_id: int):
        """Kullanıcının bekleyen işlemlerini al"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM pending_transactions
                    WHERE user_id = ? AND status = 'pending'
                    ORDER BY timestamp DESC
                """, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting user pending transactions: {e}")
            return []

    def get_confirmed_transactions(self, user_id: int, limit: int = 10):
        """Kullanıcının onaylanan işlemlerini al"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM pending_transactions
                    WHERE user_id = ? AND status = 'confirmed'
                    ORDER BY confirmed_at DESC
                    LIMIT ?
                """, (user_id, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting confirmed transactions: {e}")
            return []

    def cleanup_old_transactions(self, days_old: int = 7) -> int:
        """Eski işlemleri temizle"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM pending_transactions
                    WHERE status = 'confirmed'
                    AND confirmed_at < datetime('now', '-{} days')
                """.format(days_old))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up old transactions: {e}")
            return 0