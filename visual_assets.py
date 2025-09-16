"""
Visual Assets - Stickers, Emojis and Animations for Casino Bot
Contains animated stickers and emoji combinations for enhanced user experience
"""

# Casino Game Stickers (Popular Telegram Sticker Sets)
CASINO_STICKERS = {
    # Slot Machine Results
    'slot_jackpot': 'CAACAgIAAxkBAAICBmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI4FAACzL8xSq5mCgAB7RzHRy0E',
    'slot_win': 'CAACAgIAAxkBAAICB2NkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI5FAACzL8xSoFwCgAB6dzJRy0E',
    'slot_lose': 'CAACAgIAAxkBAAICCGNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI6FAACzL8xSlNzCgAB2RwKSC0E',
    
    # Dice Games
    'dice_win': 'CAACAgIAAxkBAAICCWNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI7FAACzL8xSjF4CgAB8ByLSS0E',
    'dice_lose': 'CAACAgIAAxkBAAICCmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI8FAACzL8xSgR5CgAB7VyMSS0E',
    
    # Roulette
    'roulette_red': 'CAACAgIAAxkBAAICC2NkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI9FAACzL8xSvh6CgAB8NyNSS0E',
    'roulette_black': 'CAACAgIAAxkBAAICDGNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI-FAACzL8xShR7CgAB6hyOSS0E',
    'roulette_green': 'CAACAgIAAxkBAAICDWNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAI_FAACzL8xSgh8CgAB7ZyPSS0E',
    
    # Card Games
    'blackjack_win': 'CAACAgIAAxkBAAICDmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJAFAACzL8xSuR8CgAB8hyQSS0E',
    'blackjack_lose': 'CAACAgIAAxkBAAICDWNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJBFAACzL8xStN9CgAB6ZyRSS0E',
    'poker_win': 'CAACAgIAAxkBAAICEGNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJCFAACzL8xSsB-CgAB7VySS0E',
    
    # General Casino
    'casino_welcome': 'CAACAgIAAxkBAAICEWNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJDFAACzL8xSqF_CgAB8hyTSS0E',
    'big_win': 'CAACAgIAAxkBAAICEmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJEFAACzL8xSoOACgAB6ZyUSS0E',
    'mega_win': 'CAACAgIAAxkBAAICE2NkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJFFAACzL8xStGBCgAB7VyVSS0E',
    
    # Money/Payment
    'money_in': 'CAACAgIAAxkBAAICFGNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJGFAACzL8xSuOCCgAB8hyWSS0E',
    'money_out': 'CAACAgIAAxkBAAICFWNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJHFAACzL8xSvGDCgAB6ZyXSS0E',
    'vip_upgrade': 'CAACAgIAAxkBAAICFmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJIFAACzL8xSgOFCgAB7VyYSS0E',
    
    # Emotions
    'celebration': 'CAACAgIAAxkBAAICF2NkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJJFAACzL8xSvWFCgAB8hyZSS0E',
    'disappointment': 'CAACAgIAAxkBAAICGGNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJKFAACzL8xSgOHCgAB6ZyaSS0E',
    'thinking': 'CAACAgIAAxkBAAICGWNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJLFAACzL8xSuWHCgAB7VybSS0E',
    
    # Bonus Features
    'daily_bonus': 'CAACAgIAAxkBAAICGmNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJMFAACzL8xStOICgAB8hycSS0E',
    'free_spin': 'CAACAgIAAxkBAAICG2NkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJNFAACzL8xSsGJCgAB6ZydSS0E',
    'mystery_box': 'CAACAgIAAxkBAAICHGNkYzQ3M2Y2NGM2ZGY0ZjQ3YjQ1YjU5AAJOFAACzL8xSq-KCgAB7VyeSS0E',
}

# Telegram Dice Emoji Configuration (Official Core API Specs)
TELEGRAM_DICE = {
    'classic_dice': {
        'emoji': '🎲',
        'min_value': 1,
        'max_value': 6,
        'name': 'Klasik Zar',
        'description': 'Standart 6 yüzlü zar oyunu',
        'win_values': [6],  # 6 = maximum value jackpot
        'good_values': [4, 5],  # above average
        'bad_values': [1, 2],  # below average
        'neutral_values': [3],  # average
        'api_behavior': 'Standard 1-6 dice roll'
    },
    'darts': {
        'emoji': '🎯',
        'min_value': 1,
        'max_value': 6,
        'name': 'Dart Atma',
        'description': 'Dart tahtasına atış oyunu',
        'win_values': [6],  # bullseye (exact center)
        'good_values': [4, 5],  # close to center
        'bad_values': [1],  # completely missed dartboard
        'neutral_values': [2, 3],  # hit dartboard but not close
        'api_behavior': 'Value 6 = bullseye, value 1 = missed dartboard'
    },
    'basketball': {
        'emoji': '🏀',
        'min_value': 1,
        'max_value': 5,
        'name': 'Basketbol',
        'description': 'Basketbol pota atış oyunu',
        'win_values': [4, 5],  # successful shots (ball goes in)
        'good_values': [3],  # close miss, hits rim
        'bad_values': [1, 2],  # complete miss, airball
        'neutral_values': [],
        'api_behavior': 'Values 4-5 = successful basket, 1-2 = miss'
    },
    'football': {
        'emoji': '⚽',
        'min_value': 1,
        'max_value': 5,
        'name': 'Futbol',
        'description': 'Futbol kale atış oyunu',
        'win_values': [4, 5],  # goal scored
        'good_values': [3],  # hits goalpost
        'bad_values': [1, 2],  # completely off target
        'neutral_values': [],
        'api_behavior': 'Values 4-5 = goal, 3 = hits post, 1-2 = miss'
    },
    'slot_machine': {
        'emoji': '🎰',
        'min_value': 1,
        'max_value': 64,
        'name': 'Slot Makinesi',
        'description': '3 makaralı slot makinesi (64 kombinasyon)',
        'win_values': [1, 22, 43, 64],  # Special winning combinations
        'jackpot_values': [64],  # Ultimate jackpot (777)
        'good_values': list(range(50, 64)),  # High value combinations
        'bad_values': list(range(1, 15)),  # Low value combinations
        'neutral_values': list(range(15, 50)),  # Medium combinations
        'api_behavior': '3 reels with 2-bit values each (2^6 = 64 combinations), value 64 = jackpot'
    },
    'bowling': {
        'emoji': '🎳',
        'min_value': 1,
        'max_value': 6,
        'name': 'Bowling',
        'description': 'Bowling pini devirmece oyunu',
        'win_values': [6],  # strike (all pins down)
        'good_values': [4, 5],  # spare potential (most pins)
        'bad_values': [1, 2],  # gutter ball / few pins
        'neutral_values': [3],  # some pins down
        'api_behavior': 'Value 6 = strike, 1 = gutter ball'
    }
}

# Dice Game Results Messages (Updated for Official API Behavior)
DICE_RESULTS = {
    'classic_dice': {
        6: "🎉 JACKPOT! En yüksek skor! 🎉",
        5: "⭐ Çok iyi! Beş! ⭐",
        4: "👍 İyi! Dört! 👍",
        3: "😐 Ortalama. Üç. 😐",
        2: "😔 Düşük. İki. 😔",
        1: "💔 En düşük! Bir! 💔"
    },
    'darts': {
        6: "🎯 BULLSEYE! Tam merkez! 🎯",
        5: "⭐ Merkeze çok yakın! ⭐",
        4: "👍 İyi atış! Hedefe yakın! 👍",
        3: "😐 Hedefi vurdun ama merkez değil. 😐",
        2: "😔 Hedefi vurdun ama uzak. 😔",
        1: "💔 Dart tahtasını tamamen kaçırdın! 💔"
    },
    'basketball': {
        5: "🏀 SWOOSH! Mükemmel basket! 🏀",
        4: "⭐ BASKET! Top içeri girdi! ⭐",
        3: "😐 Çembere çarptı ama girmedi. 😐",
        2: "😔 Hava atışı - yaklaşamadın. 😔",
        1: "💔 Tamamen kaçırdın! 💔"
    },
    'football': {
        5: "⚽ GOOOOOL! Üst köşeye harika gol! ⚽",
        4: "⭐ GOL! Top ağlara gitti! ⭐", 
        3: "😐 Direğe çarpıp çıktı! 😐",
        2: "😔 Kale dışına gitti. 😔",
        1: "💔 Tamamen ıska! 💔"
    },
    'slot_machine': {
        64: "🎰💎 MEGA JACKPOT! Üçlü yedili! 💎🎰",
        43: "🎰🔥 BÜYÜK JACKPOT! Süper kombinasyon! 🔥🎰",
        22: "🎰⭐ JACKPOT! Harika kombinasyon! ⭐🎰",
        1: "🎰✨ ÖZE JACKPOT! Özel kombinasyon! ✨🎰",
        # High value results (50-63)
        **{i: f"🎰🐻 Büyük kazanç! Kombinasyon: {i} 🐻🎰" for i in range(50, 64)},
        # Medium value results (15-49)  
        **{i: f"🎰😊 Kazanç! Kombinasyon: {i} 😊🎰" for i in range(15, 50)},
        # Low value results (2-14)
        **{i: f"🎰😔 Düşük kombinasyon: {i} 😔🎰" for i in range(2, 15)}
    },
    'bowling': {
        6: "🎳 STRIKE! Tüm pinleri tek atışta devir! 🎳",
        5: "⭐ Harika! Çoğu pini devir! ⭐",
        4: "👍 İyi! Çok pin devir! 👍",
        3: "😐 Bazı pinleri devir. 😐",
        2: "😔 Az pin devir. 😔",
        1: "💔 Gutter ball! Hiç pin devirmedi! 💔"
    }
}

# Animated Emoji Sequences
EMOJI_ANIMATIONS = {
    # Slot Machine Animation
    'slot_spinning': ['🎰', '🎯', '🎲', '🎰', '🎯', '🎲'],
    'slot_result': ['💫', '⭐', '✨', '💫', '⭐'],
    
    # Classic Dice Rolling
    'dice_rolling': ['🎲', '🎯', '🎲', '🎯', '🎲'],
    'dice_numbers': ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣'],
    
    # Darts Animation
    'darts_throwing': ['🎯', '🏹', '🎯', '🏹', '🎯'],
    'darts_result': ['💫', '⭐', '🎯', '💫', '⭐'],
    
    # Basketball Animation  
    'basketball_shooting': ['🏀', '🏐', '🏀', '🏐', '🏀'],
    'basketball_result': ['💫', '⭐', '🏀', '💫', '⭐'],
    
    # Football Animation
    'football_kicking': ['⚽', '🥅', '⚽', '🥅', '⚽'],
    'football_result': ['💫', '⭐', '⚽', '💫', '⭐'],
    
    # Bowling Animation
    'bowling_rolling': ['🎳', '🎱', '🎳', '🎱', '🎳'],
    'bowling_result': ['💫', '⭐', '🎳', '💫', '⭐'],
    
    # Roulette Wheel
    'roulette_spinning': ['🔴', '⚫', '🟢', '🔴', '⚫', '🟢'],
    'roulette_result': ['🎯', '💫', '⭐', '✨'],
    
    # Money Animations
    'money_flow': ['🐻', '💸', '💵', '💴', '💶', '💷'],
    'coins_falling': ['🪙', '🐻', '🤑', '💎', '🐻', '🪙'],
    
    # Win Celebrations
    'big_win': ['🎉', '🎊', '🥳', '🎉', '🎊', '🥳'],
    'mega_win': ['💥', '🌟', '🎆', '🎇', '✨', '💫'],
    'jackpot': ['👑', '💎', '🏆', '🎖️', '🥇', '👑'],
    
    # Card Games
    'card_dealing': ['🂠', '🃏', '🂡', '🂢', '🂣', '🂤'],
    'card_flip': ['🂠', '🃏', '🂮', '🃞', '🂭'],
    
    # Loading/Thinking
    'loading': ['⏳', '⌛', '⏳', '⌛', '⏳'],
    'thinking': ['🤔', '💭', '🧠', '💡', '🤔'],
    
    # VIP Status
    'vip_upgrade': ['👑', '💎', '✨', '🌟', '👑'],
    'level_up': ['📈', '⬆️', '🔥', '💪', '🚀'],
}

# Complex Emoji Combinations
EMOJI_COMBOS = {
    # Game Results
    'slot_jackpot': '🎰💎👑✨🎉',
    'slot_big_win': '🎰🐻🎊⭐🔥',
    'slot_win': '🎰💵😊👍✨',
    'slot_lose': '🎰😔👎💸😢',
    
    'dice_big_win': '🎲🐻🎉👍🔥',
    'dice_win': '🎲💵😊👌✨',
    'dice_lose': '🎲😔👎💸😕',
    
    'roulette_win': '🎡🐻🎊⭐✨',
    'roulette_lose': '🎡😔👎💸😢',
    
    'blackjack_win': '🃏🐻🎉👍⭐',
    'blackjack_lose': '🃏😔👎💸😕',
    
    # Payment Status
    'payment_success': '💳✅🐻🎉👍',
    'payment_pending': '💳⏳🔄⌛💭',
    'payment_failed': '💳❌😔💸👎',
    
    # VIP & Levels
    'vip_bronze': '🥉💼🎯📈✨',
    'vip_silver': '🥈💎🎯📈⭐',
    'vip_gold': '🥇👑🎯📈🌟',
    'vip_platinum': '💎👑🏆🌟🔥',
    
    # Daily Features
    'daily_bonus': '📅🐻🎁✨😊',
    'daily_quest': '📋🎯🏆⭐💪',
    'streak_bonus': '🔥📈🐻🎊👑',
    
    # Social Features
    'friend_added': '👥➕😊🤝🎉',
    'tournament_win': '🏆🥇👑🎉🐻',
    'leaderboard_top': '📊🥇👑⭐🔥',
    
    # Achievements
    'achievement_unlock': '🏅✨🎉👍🔓',
    'milestone_reached': '🎯📈🏆⭐💪',
    'level_up': '📈⬆️🔥💪🚀',
}

# Progressive Animations (for step-by-step reveals)
PROGRESSIVE_ANIMATIONS = {
    'slot_reveal': [
        '🎰 Spinning...',
        '🎰🎯 Almost there...',
        '🎰🎯🎲 One more...',
        '🎰🎯🎲 RESULT!'
    ],
    
    'big_win_buildup': [
        '🐻 Nice win!',
        '🐻🐻 Great win!',
        '🐻🐻🐻 Amazing win!',
        '🐻🐻🐻🐻 INCREDIBLE WIN!',
        '🎉🐻🐻🐻🐻🎉 MEGA WIN!'
    ],
    
    'jackpot_buildup': [
        '⭐ Special result...',
        '⭐✨ Something big...',
        '⭐✨💫 Getting closer...',
        '⭐✨💫🌟 Almost there...',
        '👑💎🏆💥 JACKPOT! 💥🏆💎👑'
    ],
    
    'level_up_sequence': [
        '📈 Experience gained!',
        '📈⬆️ Leveling up...',
        '📈⬆️🔥 New level!',
        '📈⬆️🔥💪 Level up complete!',
        '🎉📈⬆️🔥💪🚀 Congratulations!'
    ]
}

# Game-specific sticker collections
GAME_STICKER_SETS = {
    'slots': {
        'spinning': CASINO_STICKERS['casino_welcome'],
        'win': CASINO_STICKERS['slot_win'],
        'big_win': CASINO_STICKERS['big_win'],
        'jackpot': CASINO_STICKERS['mega_win'],
        'lose': CASINO_STICKERS['slot_lose']
    },
    
    'dice': {
        'rolling': CASINO_STICKERS['thinking'],
        'win': CASINO_STICKERS['dice_win'],
        'lose': CASINO_STICKERS['dice_lose']
    },
    
    'roulette': {
        'spinning': CASINO_STICKERS['casino_welcome'],
        'red_win': CASINO_STICKERS['roulette_red'],
        'black_win': CASINO_STICKERS['roulette_black'],
        'green_win': CASINO_STICKERS['roulette_green'],
        'lose': CASINO_STICKERS['disappointment']
    },
    
    'blackjack': {
        'dealing': CASINO_STICKERS['thinking'],
        'win': CASINO_STICKERS['blackjack_win'],
        'lose': CASINO_STICKERS['blackjack_lose'],
        'blackjack': CASINO_STICKERS['celebration']
    }
}

# Menu and UI Emojis
UI_EMOJIS = {
    'menu_main': '🎰',
    'menu_games': '🎮',
    'menu_profile': '👤',
    'menu_payment': '💳',
    'menu_vip': '👑',
    'menu_bonus': '🎁',
    'menu_friends': '👥',
    'menu_settings': '⚙️',
    'menu_help': '❓',
    'menu_back': '⬅️',
    'menu_close': '❌',
    'menu_refresh': '🔄',
    
    'button_play': '▶️',
    'button_stop': '⏹️',
    'button_pause': '⏸️',
    'button_next': '⏭️',
    'button_prev': '⏮️',
    
    'status_online': '🟢',
    'status_offline': '🔴',
    'status_away': '🟡',
    
    'currency_coin': '🪙',
    'currency_dollar': '💵',
    'currency_euro': '💶',
    'currency_crypto': '₿',
}

def get_random_celebration():
    """Get random celebration emoji combo"""
    import random
    celebrations = [
        '🎉🎊🥳',
        '🎆🎇✨',
        '🌟💫⭐',
        '🏆🥇👑',
        '💎🐻🤑'
    ]
    return random.choice(celebrations)

def get_win_sticker(win_amount, bet_amount):
    """Get appropriate sticker based on win ratio"""
    if win_amount == 0:
        return CASINO_STICKERS['slot_lose']
    
    ratio = win_amount / bet_amount
    
    if ratio >= 100:  # 100x or more
        return CASINO_STICKERS['mega_win']
    elif ratio >= 10:  # 10x or more
        return CASINO_STICKERS['big_win']
    elif ratio >= 2:   # 2x or more
        return CASINO_STICKERS['slot_win']
    else:
        return CASINO_STICKERS['slot_win']

def create_animated_message(animation_key, delay=1):
    """Create animated message sequence"""
    if animation_key in PROGRESSIVE_ANIMATIONS:
        return PROGRESSIVE_ANIMATIONS[animation_key]
    elif animation_key in EMOJI_ANIMATIONS:
        frames = EMOJI_ANIMATIONS[animation_key]
        return [f"{''.join(frames[:i+1])}" for i in range(len(frames))]
    else:
        return ["🎰 Loading..."]

def get_progressive_animation(animation_key):
    """Get progressive animation sequence"""
    if animation_key in PROGRESSIVE_ANIMATIONS:
        return PROGRESSIVE_ANIMATIONS[animation_key]
    else:
        return PROGRESSIVE_ANIMATIONS.get('level_up_sequence', ["🎰 Loading..."])

def get_dice_result_message(dice_type, value):
    """Get result message for dice value"""
    if dice_type in DICE_RESULTS and value in DICE_RESULTS[dice_type]:
        return DICE_RESULTS[dice_type][value]
    return f"Sonuç: {value}"

def calculate_dice_payout(dice_type, value, bet_amount):
    """Calculate payout based on dice result (Official Telegram API behavior)"""
    dice_config = TELEGRAM_DICE.get(dice_type, {})
    win_values = dice_config.get('win_values', [])
    good_values = dice_config.get('good_values', [])
    bad_values = dice_config.get('bad_values', [])
    neutral_values = dice_config.get('neutral_values', [])
    
    if dice_type == 'slot_machine':
        # EXTREMELY BALANCED slot machine payouts - massive house edge
        if value == 64:  # Ultimate jackpot (777) - very rare
            return bet_amount * 8   # Drastically reduced from 20
        elif value in [1, 22, 43]:  # Special jackpot combinations
            return bet_amount * 4   # Drastically reduced from 12
        elif value >= 50:  # High value combinations
            return bet_amount * 1.5 # Drastically reduced from 3
        elif value >= 30:  # Medium-high combinations
            return bet_amount * 1.1 # Drastically reduced from 2
        elif value >= 15:  # Medium combinations  
            return bet_amount * 0.8 # Now loses money
        else:  # Low combinations
            return 0
    elif dice_type == 'darts':
        if value == 6:  # Bullseye - very rare
            return bet_amount * 1.8 # Drastically reduced from 3
        elif value in [4, 5]:  # Close to center
            return bet_amount * 1.1 # Drastically reduced from 1.6
        elif value in [2, 3]:  # Hit dartboard
            return bet_amount * 0.4 # Drastically reduced from 0.6
        else:  # Missed dartboard (value 1)
            return 0
    elif dice_type == 'basketball':
        if value in [4, 5]:  # Successful shots
            return bet_amount * 1.4  # Drastically reduced from 2.2
        elif value == 3:  # Close miss
            return bet_amount * 0.3  # Drastically reduced from 0.5
        else:  # Complete miss
            return 0
    elif dice_type == 'football':
        if value in [4, 5]:  # Goal scored
            return bet_amount * 1.4  # Drastically reduced from 2.2
        elif value == 3:  # Hit goalpost
            return bet_amount * 0.3  # Drastically reduced from 0.5
        else:  # Miss
            return 0
    elif dice_type == 'bowling':
        if value == 6:  # Strike
            return bet_amount * 1.8  # Drastically reduced from 2.8
        elif value in [4, 5]:  # Many pins
            return bet_amount * 1.0  # Break even only
        elif value == 3:  # Some pins
            return bet_amount * 0.4  # Drastically reduced from 0.6
        else:  # Few/no pins
            return 0
    elif dice_type == 'classic_dice':
        if value == 6:  # Maximum - only 16.7% chance
            return bet_amount * 1.8  # Drastically reduced from 2.8
        elif value in [4, 5]:  # Above average - 33.3% chance
            return bet_amount * 1.0  # Break even only
        elif value == 3:  # Average - 16.7% chance  
            return bet_amount * 0.4  # Drastically reduced from 0.6
        else:  # Below average - 33.3% chance
            return 0
    
    # Fallback
    return bet_amount if value not in bad_values else 0

def get_dice_celebration(dice_type, value):
    """Get celebration emoji combo for dice result (Official API behavior)"""
    dice_config = TELEGRAM_DICE.get(dice_type, {})
    
    if dice_type == 'slot_machine':
        if value == 64:  # Ultimate jackpot
            return EMOJI_COMBOS['slot_jackpot'] + "\n🎰💎👑 ULTIMATE JACKPOT! 👑💎🎰"
        elif value in [1, 22, 43]:  # Special jackpots
            return EMOJI_COMBOS['slot_jackpot']
        elif value >= 50:  # High combinations
            return EMOJI_COMBOS['slot_big_win']
        elif value >= 15:  # Medium combinations
            return EMOJI_COMBOS['slot_win']
        else:  # Low combinations
            return EMOJI_COMBOS['slot_lose']
    elif dice_type == 'darts':
        if value == 6:  # Bullseye
            return EMOJI_COMBOS['slot_jackpot'] + "\n🎯💥 BULLSEYE PERFECT! 💥🎯"
        elif value in [4, 5]:  # Close shots
            return EMOJI_COMBOS['slot_big_win']
        elif value in [2, 3]:  # Hit dartboard
            return EMOJI_COMBOS['slot_win']
        else:  # Missed
            return EMOJI_COMBOS['slot_lose']
    elif dice_type in ['basketball', 'football']:
        if value in [4, 5]:  # Success
            return EMOJI_COMBOS['slot_jackpot']
        elif value == 3:  # Close
            return EMOJI_COMBOS['slot_win']
        else:  # Miss
            return EMOJI_COMBOS['slot_lose']
    elif dice_type == 'bowling':
        if value == 6:  # Strike
            return EMOJI_COMBOS['slot_jackpot'] + "\n🎳💥 STRIKE PERFECT! 💥🎳"
        elif value in [4, 5]:  # Many pins
            return EMOJI_COMBOS['slot_big_win']
        elif value == 3:  # Some pins
            return EMOJI_COMBOS['slot_win']
        else:  # Few/no pins
            return EMOJI_COMBOS['slot_lose']
    elif dice_type == 'classic_dice':
        if value == 6:  # Maximum
            return EMOJI_COMBOS['slot_jackpot']
        elif value in [4, 5]:  # Above average
            return EMOJI_COMBOS['slot_big_win']
        elif value == 3:  # Average
            return EMOJI_COMBOS['slot_win']
        else:  # Below average
            return EMOJI_COMBOS['slot_lose']
    
    # Fallback
    return EMOJI_COMBOS['slot_win']

def get_dice_animation_sequence(dice_type):
    """Get animation sequence for dice type"""
    animation_map = {
        'classic_dice': 'dice_rolling',
        'darts': 'darts_throwing',
        'basketball': 'basketball_shooting',
        'football': 'football_kicking',
        'bowling': 'bowling_rolling',
        'slot_machine': 'slot_spinning'
    }
    
    return EMOJI_ANIMATIONS.get(animation_map.get(dice_type, 'dice_rolling'), ['🎲'])