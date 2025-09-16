#!/usr/bin/env python3
"""
🌍 Language Selection Handler
"""

import logging
from languages import LANGUAGES, get_text, get_available_languages

logger = logging.getLogger(__name__)

async def show_language_selection(query, user, casino_bot):
    """Show language selection menu"""
    try:
        # Get user's current language
        current_lang = casino_bot.db.get_user_language(user['user_id']) if hasattr(casino_bot.db, 'get_user_language') else 'en'
        
        text = f"""
🌍 **LANGUAGE SELECTION** 🌍

🎯 **Current Language:** {LANGUAGES.get(current_lang, {}).get('name', 'English')} {LANGUAGES.get(current_lang, {}).get('flag', '🇺🇸')}

🗣️ **Select your preferred language:**
Choose your language to enjoy the casino in your native tongue!

Dilinizi seçin ve casinoyu ana dilinizde deneyimleyin!

Available languages:
        """
        
        buttons = []
        available_languages = get_available_languages()
        
        # Create buttons for each available language
        for lang_code, lang_info in available_languages.items():
            status = "✅" if lang_code == current_lang else "🌐"
            button_text = f"{status} {lang_info['flag']} {lang_info['name']}"
            buttons.append([(button_text, f"set_language_{lang_code}")])
        
        # Add back button
        buttons.append([("🔙 Back / Geri", "main_menu")])
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Language selection error: {e}")
        await query.edit_message_text(
            "❌ Error loading language menu / Dil menüsü yüklenirken hata!",
            reply_markup=casino_bot.create_keyboard([[("🏠 Main Menu", "main_menu")]])
        )

async def handle_set_language(query, user, language_code, casino_bot):
    """Handle language selection"""
    try:
        # Validate language code
        if language_code not in LANGUAGES:
            await query.edit_message_text(
                "❌ Invalid language / Geçersiz dil!",
                reply_markup=casino_bot.create_keyboard([[("🌍 Languages", "language_selection")]])
            )
            return
        
        # Set user language in database
        success = False
        if hasattr(casino_bot.db, 'set_user_language'):
            success = casino_bot.db.set_user_language(user['user_id'], language_code)
        
        if success:
            lang_info = LANGUAGES[language_code]
            
            # Get welcome text in the selected language
            welcome_text = get_text(language_code, "main_menu.welcome", username=user['username'] if user['username'] else 'Player')
            success_msg = get_text(language_code, "success.language_changed", language=lang_info['name'])
            
            text = f"""
✅ **LANGUAGE CHANGED** ✅

{lang_info['flag']} **{lang_info['name']}** selected successfully!

{welcome_text}

🎮 All menus and games will now be displayed in {lang_info['name']}.

🎯 Enjoy playing!
            """
            
            buttons = [
                [(get_text(language_code, "main_menu.buttons.solo_games", "🎮 Solo Games"), "solo_games")],
                [(get_text(language_code, "main_menu.buttons.payment", "💳 Payments"), "payment_menu")],
                [("🌍 Change Language / Dil Değiştir", "language_selection")],
                [(get_text(language_code, "main_menu.buttons.profile", "📊 Profile"), "profile")]
            ]
            
        else:
            text = """
❌ **ERROR / HATA** ❌

Failed to change language.
Dil değiştirilemedi.

Please try again later.
Lütfen daha sonra tekrar deneyin.
            """
            buttons = [
                [("🔄 Try Again / Tekrar Dene", "language_selection")],
                [("🏠 Main Menu / Ana Menü", "main_menu")]
            ]
        
        keyboard = casino_bot.create_keyboard(buttons)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Set language error: {e}")
        await query.edit_message_text(
            "❌ Error changing language / Dil değiştirme hatası!",
            reply_markup=casino_bot.create_keyboard([
                [("🌍 Languages", "language_selection")],
                [("🏠 Main Menu", "main_menu")]
            ])
        )

async def get_localized_text(user_id, key_path, casino_bot, **kwargs):
    """Get localized text for user"""
    try:
        user_lang = 'en'  # Default
        if hasattr(casino_bot.db, 'get_user_language'):
            user_lang = casino_bot.db.get_user_language(user_id)
        
        return get_text(user_lang, key_path, **kwargs)
    except Exception as e:
        logger.error(f"Localization error: {e}")
        return get_text('en', key_path, **kwargs)  # Fallback to English