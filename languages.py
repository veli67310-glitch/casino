#!/usr/bin/env python3
"""
🌍 Multi-Language Support System
"""

LANGUAGES = {
    "en": {
        "name": "English",
        "flag": "🇺🇸",
        "main_menu": {
            "title": "🎮 ULTIMATE CASINO BOT 🎮\n💎 CryptoBot Edition 💎",
            "welcome": "🌟 Welcome, {username}! 🌟",
            "balance": "🐻 Fun Coins: {coins:,} FC",
            "level": "🏆 Level: {level}",
            "xp": "⭐ XP: {current_xp}/1000",
            "streak": "🔥 Winning Streak: {streak}",
            "games": "🎯 Total Games: {games:,}",
            "best_streak": "📈 Best Streak: {best_streak}",
            "greeting_morning": "🌅 Good morning",
            "greeting_afternoon": "🌞 Good afternoon", 
            "greeting_evening": "🌆 Good evening",
            "greeting_night": "🌙 Good night",
            "status_on_fire": "ON FIRE!",
            "status_hot": "Hot Streak!",
            "status_good": "Good Run!",
            "status_ready": "Ready to Play!",
            "buttons": {
                "create_duel": "⚔️ Create Duel",
                "join_duel": "🎯 Join Duel", 
                "solo_games": "🎮 Solo Games",
                "tournaments": "🏆 Tournaments",
                "payment": "💳 Payments",
                "profile": "📊 Profile",
                "friends": "👥 Friends",
                "daily_quests": "🎁 Daily Quests",
                "achievements": "🏅 Achievements",
                "leaderboard": "🏆 Leaderboard",
                "bonus_features": "🎪 Bonus Features",
                "events": "🎉 Events"
            }
        },
        "games": {
            "solo_games_title": "🎮 PREMIUM SOLO GAMES 🎮",
            "balance": "🐻 Balance: {coins:,} FC",
            "favorite": "🌟 Favorite: {game}",
            "last_win": "🎉 Last Win: {amount:,} FC from {game}",
            "explore": "🎮 Explore all games!",
            "first_win": "🍀 Ready for your first big win!",
            "game_names": {
                "slots": "Ultimate Slots",
                "roulette": "Premium Roulette", 
                "blackjack": "Pro Blackjack",
                "crash": "Rocket Crash",
                "mines": "Extreme Mines",
                "baccarat": "Royal Baccarat",
                "keno": "Mega Keno"
            },
            "game_descriptions": {
                "slots": "50x jackpots!",
                "roulette": "Live betting",
                "blackjack": "2.5x payouts", 
                "crash": "100x multipliers",
                "mines": "Strategic mining",
                "baccarat": "Casino classic",
                "keno": "1000x potential"
            }
        },
        "bonus": {
            "title": "🎪 BONUS FEATURES HUB 🎪",
            "daily_spinner": "🎰 Daily Spinner",
            "fortune_wheel": "🎡 Fortune Wheel", 
            "mystery_box": "📦 Mystery Box",
            "achievement_showcase": "🎖️ Achievement Showcase",
            "available": "🆕 Available!",
            "tomorrow": "⏰ Tomorrow",
            "cost": "500 FC to open",
            "anytime": "Spin anytime!"
        },
        "profile": {
            "title": "👤 {username} PROFILE 👤",
            "wealth_status": "🐻 WEALTH & STATUS 🐻",
            "balance": "💎 Balance: {coins:,} FC",
            "level": "🏆 Level: {level} ({next_xp} XP to next)",
            "rank": "📊 Global Rank: #{rank}/{total} (Top {percentage:.1f}%)",
            "game_stats": "🎯 GAME STATS 🎯",
            "current_streak": "🔥 Current Streak: {streak} games",
            "best_streak": "🏆 Best Streak: {best_streak} games",
            "total_games": "🎮 Total Games: {games:,}",
            "wagered": "💸 Total Wagered: {wagered:,} FC",
            "won": "🐻 Total Won: {won:,} FC",
            "win_rate": "📈 Win Rate: {rate:.1f}%",
            "favorite_game": "🎯 Favorite Game: {game}",
            "achievements_badges": "🏅 ACHIEVEMENTS & BADGES 🏅",
            "achievements_count": "🏆 Achievements: {count} unlocked",
            "badges": "🎖️ Badges: {badges}",
            "friend_code": "🆔 Friend Code: `{code}`"
        },
        "payments": {
            "title": "💳 CRYPTO PAYMENTS 💳",
            "deposit": "🐻 Deposit",
            "withdraw": "💸 Withdraw", 
            "convert": "🔄 Convert",
            "history": "📊 History",
            "rates": "💱 Exchange Rates"
        },
        "errors": {
            "insufficient_funds": "❌ Insufficient funds!",
            "invalid_amount": "❌ Invalid amount!",
            "bet_too_high": "❌ Bet too high!",
            "bet_too_low": "❌ Minimum bet: {min} FC",
            "max_bet_exceeded": "❌ Maximum bet: {max:,} FC"
        },
        "success": {
            "game_win": "🎉 WINNER! 🎉",
            "game_loss": "😔 Better luck next time!",
            "achievement_unlocked": "🏆 Achievement Unlocked!",
            "level_up": "🎊 Level Up!",
            "deposit_success": "✅ Deposit successful!",
            "withdraw_success": "✅ Withdrawal successful!",
            "language_changed": "Language changed to {language}!"
        },
        "game_animations": {
            "slots_spinning": "🎰 Slots spinning...",
            "roulette_spinning": "🔄 Roulette spinning...",
            "rocket_launching": "🚀 Rocket launching...",
            "cards_dealing": "🃏 Dealing cards...",
            "dice_rolling": "🎲 Rolling dice...",
            "wheel_spinning": "🎡 Wheel spinning..."
        },
        "game_results": {
            "blackjack_win": "🎉 Blackjack! You win!",
            "blackjack_lose": "😔 Dealer wins!",
            "blackjack_push": "🤝 Push! It's a tie!",
            "slot_jackpot": "🐻 JACKPOT! Amazing win!",
            "slot_bigwin": "🎊 Big Win!",
            "slot_smallwin": "✨ You win!",
            "roulette_win": "🎯 Perfect prediction!",
            "crash_safe": "✅ Cashed out safely!",
            "crash_exploded": "💥 Rocket exploded!"
        },
        "notifications": {
            "insufficient_balance": "💸 Insufficient balance! 😢",
            "invalid_bet": "❌ Invalid bet amount!",
            "game_error": "⚠️ Game error occurred!",
            "loading": "⏳ Loading...",
            "processing": "🔄 Processing...",
            "completed": "✅ Completed!"
        },
        "daily": {
            "quest_title": "🎁 Daily Quests",
            "quest_invite": "Invite a friend!",
            "quest_play": "Play 5 games!",
            "quest_win": "Win 3 games!",
            "bonus_claimed": "✅ Daily bonus claimed!",
            "bonus_available": "🎁 Daily bonus available!",
            "comeback_tomorrow": "⏰ Come back tomorrow!"
        },
        "admin": {
            "panel_title": "👑 Admin Panel",
            "user_stats": "📊 User Statistics", 
            "system_stats": "⚙️ System Statistics",
            "user_management": "👥 User Management",
            "total_users": "Total Users: {count}",
            "active_users": "Active Users: {count}",
            "total_games": "Total Games: {count}"
        }
    },
    "ru": {
        "name": "Русский",
        "flag": "🇷🇺",
        "main_menu": {
            "title": "🎮 ULTIMATE CASINO BOT 🎮\n💎 CryptoBot Edition 💎",
            "welcome": "🌟 Добро пожаловать, {username}! 🌟",
            "balance": "🐻 Fun Coins: {coins:,} FC",
            "level": "🏆 Уровень: {level}",
            "xp": "⭐ XP: {current_xp}/1000",
            "streak": "🔥 Серия побед: {streak}",
            "games": "🎯 Всего игр: {games:,}",
            "best_streak": "📈 Лучшая серия: {best_streak}",
            "greeting_morning": "🌅 Доброе утро",
            "greeting_afternoon": "🌞 Добрый день",
            "greeting_evening": "🌆 Добрый вечер",
            "greeting_night": "🌙 Спокойной ночи",
            "status_on_fire": "В ОГНЕ!",
            "status_hot": "Горячая серия!",
            "status_good": "Хороший ход!",
            "status_ready": "Готов играть!",
            "buttons": {
                "create_duel": "⚔️ Создать дуэль",
                "join_duel": "🎯 Присоединиться к дуэли",
                "solo_games": "🎮 Одиночные игры",
                "tournaments": "🏆 Турниры",
                "payment": "💳 Платежи",
                "profile": "📊 Профиль",
                "friends": "👥 Друзья",
                "daily_quests": "🎁 Ежедневные задания",
                "achievements": "🏅 Достижения",
                "leaderboard": "🏆 Рейтинг",
                "bonus_features": "🎪 Бонусные функции",
                "events": "🎉 События"
            }
        },
        "games": {
            "solo_games_title": "🎮 ПРЕМИУМ ОДИНОЧНЫЕ ИГРЫ 🎮",
            "balance": "🐻 Баланс: {coins:,} FC",
            "favorite": "🌟 Любимая: {game}",
            "last_win": "🎉 Последний выигрыш: {amount:,} FC из {game}",
            "explore": "🎮 Исследуй все игры!",
            "first_win": "🍀 Готов к первому большому выигрышу!",
            "game_names": {
                "slots": "Ultimate Slots",
                "roulette": "Premium Рулетка",
                "blackjack": "Pro Blackjack",
                "crash": "Rocket Crash",
                "mines": "Extreme Mines",
                "baccarat": "Royal Baccarat",
                "keno": "Mega Keno"
            },
            "game_descriptions": {
                "slots": "50x джекпот!",
                "roulette": "Живые ставки",
                "blackjack": "2.5x выплаты",
                "crash": "100x множители",
                "mines": "Стратегическая добыча",
                "baccarat": "Классика казино",
                "keno": "1000x потенциал"
            }
        },
        "bonus": {
            "title": "🎪 БОНУСНЫЕ ФУНКЦИИ ХАБ 🎪",
            "daily_spinner": "🎰 Ежедневный спиннер",
            "fortune_wheel": "🎡 Колесо фортуны",
            "mystery_box": "📦 Таинственная коробка",
            "achievement_showcase": "🎖️ Витрина достижений",
            "available": "🆕 Доступно!",
            "tomorrow": "⏰ Завтра",
            "cost": "500 FC открыть",
            "anytime": "Крути когда угодно!"
        },
        "profile": {
            "title": "👤 ПРОФИЛЬ {username} 👤",
            "wealth_status": "🐻 БОГАТСТВО И СТАТУС 🐻",
            "balance": "💎 Баланс: {coins:,} FC",
            "level": "🏆 Уровень: {level} ({next_xp} XP до следующего)",
            "rank": "📊 Глобальный ранг: #{rank}/{total} (Топ {percentage:.1f}%)",
            "game_stats": "🎯 ИГРОВАЯ СТАТИСТИКА 🎯",
            "current_streak": "🔥 Текущая серия: {streak} игр",
            "best_streak": "🏆 Лучшая серия: {best_streak} игр",
            "total_games": "🎮 Всего игр: {games:,}",
            "wagered": "💸 Всего поставлено: {wagered:,} FC",
            "won": "🐻 Всего выиграно: {won:,} FC",
            "win_rate": "📈 Процент побед: {rate:.1f}%",
            "favorite_game": "🎯 Любимая игра: {game}",
            "achievements_badges": "🏅 ДОСТИЖЕНИЯ И ЗНАЧКИ 🏅",
            "achievements_count": "🏆 Достижения: {count} открыто",
            "badges": "🎖️ Значки: {badges}",
            "friend_code": "🆔 Код друга: `{code}`"
        },
        "payments": {
            "title": "💳💎 ПЛАТЕЖНАЯ СИСТЕМА 💎💳",
            "deposit": "◎ SOL Депозит",
            "withdraw": "◎ SOL Вывод",
            "convert": "🔄 Конвертация",
            "history": "📊 История транзакций",
            "rates": "💱 Курсы валют",
            "vip_info": "👑 VIP Информация",
            "limits": "ℹ️ Лимиты",
            "bonus_info": "🎁 Информация о бонусах",
            "main_menu": "🏠 Главное меню",
            "solana_payment": "◎ SOLANA ПЛАТЕЖИ ◎",
            "current_balance": "💰 Текущий баланс",
            "exchange_rate": "💱 Курс обмена",
            "suggested_amounts": "🎯 Рекомендуемые суммы",
            "select_amount": "1. Выберите сумму",
            "send_to_address": "2. Отправьте на центральный SOL адрес",
            "manual_approval": "3. Ручное одобрение администратором",
            "balance_updated": "4. Ваш FC баланс будет обновлен",
            "fast_network": "⚡ Сеть Solana очень быстрая!",
            "custom_amount": "💎 Пользовательская сумма",
            "back": "🔙 Назад",
            "wallet_selection": "🔗 Выбор кошелька",
            "transaction_history": "📊 История транзакций",
            "rate_info": "💱 Информация о курсе",
            "how_to_use": "❓ Как использовать",
            "settings": "📊 Настройки",
            "limits_removed": "Лимиты: Убраны (любая сумма)",
            "withdrawal_fee": "Комиссия за вывод",
            "features": "🚀 Возможности",
            "fast_solana_network": "⚡ Быстрая сеть Solana",
            "manual_deposit_approval": "🔄 Ручное одобрение депозита",
            "manual_withdrawal_security": "👨‍💼 Ручной вывод (безопасность)",
            "sol_support_only": "💎 Поддержка только SOL",
            "solana_only": "Только Solana!"
        },
        "errors": {
            "insufficient_funds": "❌ Недостаточно средств!",
            "invalid_amount": "❌ Неверная сумма!",
            "bet_too_high": "❌ Ставка слишком высока!",
            "bet_too_low": "❌ Минимальная ставка: {min} FC",
            "max_bet_exceeded": "❌ Максимальная ставка: {max:,} FC"
        },
        "success": {
            "game_win": "🎉 ПОБЕДА! 🎉",
            "game_loss": "😔 Удача в следующий раз!",
            "achievement_unlocked": "🏆 Достижение разблокировано!",
            "level_up": "🎊 Повышение уровня!",
            "deposit_success": "✅ Депозит успешен!",
            "withdraw_success": "✅ Вывод успешен!",
            "language_changed": "Язык изменен на {language}!"
        },
        "game_animations": {
            "slots_spinning": "🎰 Слоты крутятся...",
            "roulette_spinning": "🔄 Рулетка крутится...",
            "rocket_launching": "🚀 Ракета запускается...",
            "cards_dealing": "🃏 Раздача карт...",
            "dice_rolling": "🎲 Бросок кубиков...",
            "wheel_spinning": "🎡 Колесо крутится..."
        },
        "game_results": {
            "blackjack_win": "🎉 Блэкджек! Ты выиграл!",
            "blackjack_lose": "😔 Дилер выиграл!",
            "blackjack_push": "🤝 Ничья!",
            "slot_jackpot": "🐻 ДЖЕКПОТ! Потрясающий выигрыш!",
            "slot_bigwin": "🎊 Большой выигрыш!",
            "slot_smallwin": "✨ Ты выиграл!",
            "roulette_win": "🎯 Идеальное предсказание!",
            "crash_safe": "✅ Безопасно обналичено!",
            "crash_exploded": "💥 Ракета взорвалась!"
        },
        "notifications": {
            "insufficient_balance": "💸 Недостаточно баланса! 😢",
            "invalid_bet": "❌ Неверная сумма ставки!",
            "game_error": "⚠️ Произошла ошибка игры!",
            "loading": "⏳ Загрузка...",
            "processing": "🔄 Обработка...",
            "completed": "✅ Завершено!"
        },
        "daily": {
            "quest_title": "🎁 Ежедневные задания",
            "quest_invite": "Пригласи друга!",
            "quest_play": "Сыграй 5 игр!",
            "quest_win": "Выиграй 3 игры!",
            "bonus_claimed": "✅ Ежедневный бонус получен!",
            "bonus_available": "🎁 Ежедневный бонус доступен!",
            "comeback_tomorrow": "⏰ Возвращайся завтра!"
        },
        "admin": {
            "panel_title": "👑 Панель администратора",
            "user_stats": "📊 Статистика пользователей",
            "system_stats": "⚙️ Статистика системы",
            "user_management": "👥 Управление пользователями",
            "total_users": "Всего пользователей: {count}",
            "active_users": "Активных пользователей: {count}",
            "total_games": "Всего игр: {count}"
        },
        "group": {
            "welcome": "👋 Привет {username}! Добро пожаловать в групповые одиночные игры!",
            "our_telegram_group": "🎉 Наша Telegram группа! 🎉",
            "hello": "Привет {username}! 👋",
            "official_group": "🎮 Наша официальная Telegram группа: @{group_name}",
            "whats_in_group": "📋 Что есть в группе?",
            "daily_bonuses": "• 🎉 Ежедневные бонусы и розыгрыши",
            "bot_updates": "• 📢 Обновления бота и объявления",
            "chat_players": "• 👥 Общение с другими игроками",
            "tournament_notifications": "• 🎯 Уведомления о турнирах",
            "help_support": "• 🆘 Помощь и поддержка",
            "join_fun": "🚀 Присоединяйся сейчас и получи больше удовольствия от казино!",
            "join_group": "👥 Присоединиться к группе",
            "back_main_menu": "🏠 Назад в главное меню",
            "group_statistics": "📊 СТАТИСТИКА ГРУППЫ (Сегодня):",
            "games_played": "🎯 Игр сыграно: {count} игр",
            "total_winnings": "💰 Общий выигрыш: {amount:,} 🐻",
            "most_active": "👑 Самый активный: {player} ({games} игр)",
            "member_count": "👥 Количество участников: {count} участников",
            "classic_casino_games": "🎯 Классические казино игры (4 игры):",
            "slot_machine": "• 🎰 Слот-машина - Удача на 3 барабанах!",
            "roulette": "• 🔴 Рулетка - Красное или черное?",
            "big_wins_announced": "🔥 Большие выигрыши объявляются в группе!",
            "bot_added_to_group": "Привет! Я бот казино и меня добавили в вашу группу! 🎉",
            "what_i_can_do": "🎮 Что я могу делать:",
            "slot_roulette_games": "• Слот-машины, рулетка и больше казино игр",
            "multiplayer_duels": "• Многопользовательские дуэли и турниры",
            "daily_bonuses_vip": "• Ежедневные бонусы и VIP система",
            "secure_crypto": "• Безопасные крипто платежи",
            "friends_leaderboard": "• Система друзей и таблица лидеров",
            "to_get_started": "🚀 Чтобы начать:",
            "start_private_chat": "• Начните приватный чат с ботом: /start"
        },
        "language": {
            "selection_title": "🌍 ВЫБОР ЯЗЫКА 🌍",
            "current_language": "🎯 Текущий язык:",
            "select_preferred": "🗣️ Выберите предпочитаемый язык:",
            "choose_language": "Выберите ваш язык, чтобы наслаждаться казино на родном языке!",
            "available_languages": "Доступные языки:",
            "language_changed": "✅ ЯЗЫК ИЗМЕНЕН ✅",
            "selected_successfully": "выбран успешно!",
            "all_menus_display": "🎮 Все меню и игры теперь будут отображаться на {language}.",
            "enjoy_playing": "🎯 Приятной игры!"
        }
    },
}

DEFAULT_LANGUAGE = "en"

def get_text(lang_code: str, key_path: str, default_text: str = None, **kwargs):
    """Get translated text for given language and key path"""
    if lang_code not in LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    lang_data = LANGUAGES[lang_code]
    
    # Navigate through nested keys (e.g., "main_menu.welcome")
    keys = key_path.split('.')
    text = lang_data
    
    for key in keys:
        if isinstance(text, dict) and key in text:
            text = text[key]
        else:
            # Try fallback to English if key not found
            if lang_code != DEFAULT_LANGUAGE:
                return get_text(DEFAULT_LANGUAGE, key_path, default_text, **kwargs)
            # If still not found, use default_text or error message
            return default_text if default_text else f"[Missing: {key_path}]"
    
    # Format with provided arguments
    if isinstance(text, str) and kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    
    return text

def get_available_languages():
    """Get list of available languages"""
    return {code: {"name": data["name"], "flag": data["flag"]} 
            for code, data in LANGUAGES.items()}