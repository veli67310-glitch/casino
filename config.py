#!/usr/bin/env python3
"""
🎮 Casino Bot Konfigürasyon Dosyası - COMPLETE WORKING VERSION
"""

import os
from datetime import datetime, timedelta

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Bot token - Replace with your actual bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# CryptoBot API settings
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
CRYPTO_TESTNET = os.getenv("CRYPTO_TESTNET", "True").lower() == "true"

# Group membership requirement - ENABLED
REQUIRED_GROUP_USERNAME = "BetBearSolana"  # Group username without @
REQUIRED_GROUP_URL = "https://t.me/BetBearSolana"  # Group URL for user display
REQUIRED_GROUP_ID = None  # Will be determined automatically or set manually if known

# Admin user IDs - Only these users can access admin panel
ADMIN_USER_IDS = [
    1690376317,  # Admin 1
    5479510218,  # Admin 2
    # Add more admin Telegram IDs here
]

# Enhanced payment settings
PAYMENT_SETTINGS = {
    # Maximum limits (Fun Coins)
    "max_daily_deposit": 10000000,     # Daily max deposit (increased)
    "max_daily_withdrawal": 5000000,   # Daily max withdrawal (increased)
    "max_single_bet": 1000000,         # Single bet maximum (increased)
    "max_bet_ratio": 0.10,             # Max 10% of balance can be bet
    
    # Minimum amounts
    "min_deposit": 1000,               # Minimum deposit (Fun Coins)
    "min_withdrawal": 5000,            # Minimum withdrawal (Fun Coins)
    
    # Fees (%)
    "deposit_fee": 0.0,                # Deposit fee %
    "withdrawal_fee": 2.0,             # Withdrawal fee %
    
    # Bonus system
    "first_deposit_bonus": 0.20,       # First deposit 20% bonus
    "vip_withdrawal_discount": 0.50,   # VIP members 50% fee discount
    "weekend_bonus": 0.50,             # Weekend 50% extra bonus
    "referral_bonus": 500,             # Friend referral bonus
    
    # Risk management
    "daily_bet_multiplier": 10,        # Daily bet = deposit x 10
    "anti_fraud_enabled": True,        # Anti-fraud protection
    "max_consecutive_losses": 10,      # Max consecutive losses
}

# Enhanced crypto rates with better conversion
CRYPTO_RATES = {
    "USDT": {
        "rate": 0.001,           # 1000 Fun Coins = 1 USDT
        "min_amount": 1.0,       # Minimum 1 USDT
        "decimals": 2,
        "emoji": "💲",
        "name": "Tether USD",
        "network": "TRC20"
    },
    "TON": {
        "rate": 0.0002,          # 5000 Fun Coins = 1 TON
        "min_amount": 0.1,       # Minimum 0.1 TON
        "decimals": 4,
        "emoji": "💎",
        "name": "Toncoin",
        "network": "TON"
    },
    "BTC": {
        "rate": 0.000000015,     # ~66,667 Fun Coins = 1 BTC
        "min_amount": 0.0001,    # Minimum 0.0001 BTC
        "decimals": 8,
        "emoji": "₿",
        "name": "Bitcoin",
        "network": "BTC"
    },
    "ETH": {
        "rate": 0.0000003,       # ~3,333 Fun Coins = 1 ETH
        "min_amount": 0.001,     # Minimum 0.001 ETH
        "decimals": 6,
        "emoji": "Ξ",
        "name": "Ethereum",
        "network": "ERC20"
    },
    "TRX": {
        "rate": 0.01,            # 100 Fun Coins = 1 TRX
        "min_amount": 10.0,      # Minimum 10 TRX
        "decimals": 0,
        "emoji": "🔴",
        "name": "TRON",
        "network": "TRC20"
    },
    "BNB": {
        "rate": 0.0000015,       # ~667 Fun Coins = 1 BNB
        "min_amount": 0.01,      # Minimum 0.01 BNB
        "decimals": 4,
        "emoji": "🟡",
        "name": "BNB",
        "network": "BSC"
    }
}

# Enhanced VIP levels with better progression
VIP_LEVELS = {
    1: {
        "min_deposit": 10000, 
        "bet_bonus": 1.05, 
        "withdrawal_discount": 0.1,
        "daily_bonus": 200,
        "max_bet_multiplier": 2.5
    },
    2: {
        "min_deposit": 50000, 
        "bet_bonus": 1.10, 
        "withdrawal_discount": 0.2,
        "daily_bonus": 500,
        "max_bet_multiplier": 5.0
    },
    3: {
        "min_deposit": 100000, 
        "bet_bonus": 1.15, 
        "withdrawal_discount": 0.3,
        "daily_bonus": 1000,
        "max_bet_multiplier": 10.0
    },
    4: {
        "min_deposit": 500000, 
        "bet_bonus": 1.20, 
        "withdrawal_discount": 0.4,
        "daily_bonus": 2500,
        "max_bet_multiplier": 20.0
    },
    5: {
        "min_deposit": 1000000, 
        "bet_bonus": 1.25, 
        "withdrawal_discount": 0.5,
        "daily_bonus": 5000,
        "max_bet_multiplier": 50.0
    }
}

# 🎨 Enhanced Animation & Visual Elements
LOADING_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
BATTLE_FRAMES = ["⚔️", "🛡️", "💥", "✨", "🎆", "💫", "🌟", "⭐"]
TOURNAMENT_EMOJIS = ["🏆", "🥇", "🥈", "🥉", "🏅", "👑", "🎊", "🎉"]
ACHIEVEMENT_EMOJIS = ["🎯", "💎", "🔥", "⚡", "🌟", "💫", "🎨", "🎭", "🎪", "🎰"]
PAYMENT_EMOJIS = ["🐻", "💳", "💸", "💵", "💎", "🏦", "💹", "📈", "💲", "🪙"]
GAME_EMOJIS = ["🎲", "🎰", "🃏", "♠️", "♥️", "♦️", "♣️", "🎯", "🎪", "🎭"]
LUCKY_EMOJIS = ["🍀", "🌈", "🎁", "💝", "✨", "🌟", "⭐", "💫", "🎆", "🎇"]
STATUS_EMOJIS = {
    "success": "✅",
    "error": "❌", 
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳",
    "fire": "🔥",
    "diamond": "💎",
    "crown": "👑"
}

# Enhanced game types with better balance
GAMES = {
    "duel_coinflip": {
        "name": "Duel: Coin Flip", 
        "min_bet": 10, 
        "max_bet": 50000, 
        "players": 2,
        "house_edge": 0.02,
        "description": "Coin flip duel"
    },
    "duel_dice": {
        "name": "Duel: Dice Battle", 
        "min_bet": 15, 
        "max_bet": 75000, 
        "players": 2,
        "house_edge": 0.015,
        "description": "Dice battle duel"
    },
    "duel_dice_standard": {
        "name": "Duel: Standard Dice", 
        "min_bet": 10, 
        "max_bet": 50000, 
        "players": 2,
        "house_edge": 0.01,
        "description": "Highest dice wins"
    },
    "duel_dice_basketball": {
        "name": "Duel: Basketball Dice", 
        "min_bet": 15, 
        "max_bet": 75000, 
        "players": 2,
        "house_edge": 0.01,
        "description": "Basketball dice duel"
    },
    "duel_dice_football": {
        "name": "Duel: Football Dice", 
        "min_bet": 15, 
        "max_bet": 75000, 
        "players": 2,
        "house_edge": 0.01,
        "description": "Football dice duel"
    },
    "duel_dice_slot": {
        "name": "Duel: Slot Dice", 
        "min_bet": 20, 
        "max_bet": 100000, 
        "players": 2,
        "house_edge": 0.02,
        "description": "Slot machine dice duel"
    },
    "duel_dice_bowling": {
        "name": "Duel: Bowling Dice", 
        "min_bet": 12, 
        "max_bet": 60000, 
        "players": 2,
        "house_edge": 0.01,
        "description": "Bowling dice duel"
    },
    "duel_dice_darts": {
        "name": "Duel: Dart Dice", 
        "min_bet": 10, 
        "max_bet": 50000, 
        "players": 2,
        "house_edge": 0.01,
        "description": "Dart dice duel"
    },
    "duel_rockpaper": {
        "name": "Duel: Rock-Paper-Scissors", 
        "min_bet": 20, 
        "max_bet": 100000, 
        "players": 2,
        "house_edge": 0.01,
        "description": "Rock-paper-scissors duel"
    },
    "tournament_slots": {
        "name": "Tournament: Slots", 
        "min_bet": 20, 
        "max_bet": 50000, 
        "players": 8,
        "house_edge": 0.05,
        "description": "Slot machine tournament"
    },
    "tournament_dice": {
        "name": "Tournament: Dice", 
        "min_bet": 25, 
        "max_bet": 75000, 
        "players": 8,
        "house_edge": 0.03,
        "description": "Dice tournament"
    },
    "battle_royale": {
        "name": "Battle Royale", 
        "min_bet": 25, 
        "max_bet": 100000, 
        "players": 16,
        "house_edge": 0.025,
        "description": "Last one standing wins"
    },
    "team_poker": {
        "name": "Team Poker", 
        "min_bet": 30, 
        "max_bet": 150000, 
        "players": 4,
        "house_edge": 0.02,
        "description": "Team poker"
    },
    "team_trivia": {
        "name": "Team Trivia",
        "min_bet": 35, 
        "max_bet": 75000, 
        "players": 4,
        "house_edge": 0.0,
        "description": "Trivia competition"
    }
}

# Enhanced achievement system
ACHIEVEMENTS = {
    "first_win": {"name": "First Victory", "reward": 100, "emoji": "🎯"},
    "streak_5": {"name": "5 Win Streak", "reward": 250, "emoji": "🔥"},
    "streak_10": {"name": "10 Win Streak", "reward": 500, "emoji": "⚡"},
    "streak_25": {"name": "25 Win Streak", "reward": 1500, "emoji": "🌟"},
    "tournament_winner": {"name": "Tournament Champion", "reward": 500, "emoji": "🏆"},
    "high_roller": {"name": "High Roller", "reward": 1000, "emoji": "💎"},
    "social_butterfly": {"name": "Social Butterfly", "reward": 200, "emoji": "🦋"},
    "trivia_master": {"name": "Trivia Master", "reward": 300, "emoji": "🧠"},
    "first_deposit": {"name": "First Deposit", "reward": 1000, "emoji": "🐻"},
    "big_depositor": {"name": "Big Investor", "reward": 2500, "emoji": "💎"},
    "crypto_master": {"name": "Crypto Master", "reward": 5000, "emoji": "₿"},
    "vip_member": {"name": "VIP Member", "reward": 10000, "emoji": "👑"},
    "whale": {"name": "Whale", "reward": 25000, "emoji": "🐋"},
    "lucky_seven": {"name": "Lucky Seven", "reward": 777, "emoji": "🍀"},
    "diamond_hands": {"name": "Diamond Hands", "reward": 5000, "emoji": "💎"},
    "speed_demon": {"name": "Speed Demon", "reward": 1000, "emoji": "⚡"},
    "big_win": {"name": "Big Win", "reward": 500, "emoji": "🐻"},
    "daily_login": {"name": "Daily Login", "reward": 50, "emoji": "📅"}
}

# Enhanced solo game configuration
SOLO_GAMES = {
    "solo_slots": {
        "name": "🎰 Slot Machine", 
        "min_bet": 5, 
        "max_bet": 25000, 
        "players": 1, 
        "house_edge": 0.03,
        "max_multiplier": 10.0,
        "volatility": "medium",
        "description": "Classic slot machine game"
    },
    "solo_roulette": {
        "name": "🎯 Roulette", 
        "min_bet": 10, 
        "max_bet": 50000, 
        "players": 1, 
        "house_edge": 0.027,
        "max_multiplier": 35.0,
        "volatility": "high",
        "description": "European roulette game"
    },
    "solo_blackjack": {
        "name": "🃏 Blackjack", 
        "min_bet": 15, 
        "max_bet": 75000, 
        "players": 1, 
        "house_edge": 0.005,
        "max_multiplier": 2.5,
        "volatility": "low",
        "description": "21 card game"
    },
    "solo_crash": {
        "name": "🚀 Crash Game", 
        "min_bet": 20, 
        "max_bet": 100000, 
        "players": 1, 
        "house_edge": 0.01,
        "max_multiplier": 100.0,
        "volatility": "very_high",
        "description": "Cash out before crash"
    },
    "solo_mines": {
        "name": "💣 Mines", 
        "min_bet": 25, 
        "max_bet": 50000, 
        "players": 1, 
        "house_edge": 0.02,
        "max_multiplier": 50.0,
        "volatility": "high",
        "description": "Avoid the mines"
    },
    "solo_baccarat": {
        "name": "🎴 Baccarat", 
        "min_bet": 30, 
        "max_bet": 150000, 
        "players": 1, 
        "house_edge": 0.012,
        "max_multiplier": 8.0,
        "volatility": "medium",
        "description": "Banker vs Player"
    },
    "solo_keno": {
        "name": "🔢 Keno", 
        "min_bet": 5, 
        "max_bet": 25000, 
        "players": 1, 
        "house_edge": 0.25,
        "max_multiplier": 20.0,
        "volatility": "very_high",
        "description": "Number guessing game"
    },
    "solo_dice": {
        "name": "🎲 Dice Game", 
        "min_bet": 10, 
        "max_bet": 30000, 
        "players": 1, 
        "house_edge": 0.02,
        "max_multiplier": 6.0,
        "volatility": "medium",
        "description": "Roll the dice and guess"
    },
    "rock_paper_scissors": {
        "name": "✂️ Rock-Paper-Scissors", 
        "min_bet": 5, 
        "max_bet": 20000, 
        "players": 1, 
        "house_edge": 0.01,
        "max_multiplier": 2.0,
        "volatility": "low",
        "description": "Classic hand game vs bot"
    },
    "number_guess": {
        "name": "🔢 Number Guess", 
        "min_bet": 10, 
        "max_bet": 50000, 
        "players": 1, 
        "house_edge": 0.05,
        "max_multiplier": 100.0,
        "volatility": "very_high",
        "description": "Guess the number 1-100"
    },
    "lucky_wheel": {
        "name": "🎪 Lucky Wheel", 
        "min_bet": 15, 
        "max_bet": 40000, 
        "players": 1, 
        "house_edge": 0.03,
        "max_multiplier": 50.0,
        "volatility": "high",
        "description": "Spin the wheel of fortune"
    }
}

# Friend code generation
FRIEND_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Enhanced trivia questions
TRIVIA_QUESTIONS = [
    {"question": "What is the world's largest ocean?", "answers": ["Pacific", "Atlantic", "Indian", "Arctic"], "correct": 0},
    {"question": "What year was the Python programming language released?", "answers": ["1991", "1989", "2000", "1995"], "correct": 0},
    {"question": "What is the highest mountain?", "answers": ["Everest", "K2", "Kangchenjunga", "Lhotse"], "correct": 0},
    {"question": "Who created Bitcoin?", "answers": ["Satoshi Nakamoto", "Vitalik Buterin", "Charlie Lee", "Gavin Andresen"], "correct": 0},
]

# Solana Configuration - Enhanced with better RPC endpoints and rate limiting
SOLANA_CONFIG = {
    # Primary RPC endpoints (use premium for better reliability)
    "rpc_url": os.getenv("SOLANA_RPC_URL", "https://solana-api.projectserum.com"),
    "fallback_rpc_urls": [
        "https://api.mainnet-beta.solana.com",
        "https://rpc.ankr.com/solana",
        "https://solana-mainnet.phantom.app",
    ],
    "devnet_url": os.getenv("SOLANA_DEVNET_URL", "https://api.devnet.solana.com"),
    "admin_wallet": os.getenv("SOLANA_ADMIN_WALLET", "DsJd8pDi44f82dRjG3zBnxrv2t32ZyfKUjz5cqFkdrY9"),
    "admin_private_key": os.getenv("SOLANA_ADMIN_PRIVATE_KEY", ""),
    "network": os.getenv("SOLANA_NETWORK", "mainnet"),
    "websocket_url": os.getenv("SOLANA_WEBSOCKET_URL", "wss://api.mainnet-beta.solana.com"),
    "commitment": "confirmed",
    "timeout": 45,  # Increased timeout
    "max_retries": 5,  # Increased retries
    "retry_delay": 2.0,  # Increased delay
    "min_sol_amount": 0.001,
    "transaction_fee": 0.000005,
    "confirmation_timeout": 90,  # Increased confirmation timeout

    # Rate limiting settings
    "requests_per_second": 5,  # Max requests per second
    "burst_limit": 10,  # Max burst requests
    "rate_limit_window": 60,  # Rate limit window in seconds
}