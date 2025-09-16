#!/usr/bin/env python3
"""
🎮 Casino Bot Game Handlers
"""

import json
import random
import asyncio
from config import GAMES, SOLO_GAMES
from languages import get_text
from visual_assets import (
    CASINO_STICKERS, EMOJI_ANIMATIONS, EMOJI_COMBOS, 
    PROGRESSIVE_ANIMATIONS, get_win_sticker, get_random_celebration,
    create_animated_message, UI_EMOJIS
)
from safe_telegram_handler import safe_edit_message
from game_error_handler import safe_game_edit, safe_animation, robust_game_operation

@robust_game_operation("Solo game completed! Check your balance.")
async def handle_solo_game(query, user, game_type, bet_amount, casino_bot):
    """Handle solo game play"""
    if user['fun_coins'] < bet_amount:
        await safe_game_edit(query,
            get_text(casino_bot.db.get_user_language(user['user_id']) if hasattr(casino_bot.db, 'get_user_language') else 'en', 'notifications.insufficient_balance'),
            reply_markup=casino_bot.create_keyboard([[("🎮 Solo Games", "solo_games"), ("🏠 Main Menu", "main_menu")]])
        )
        return
    
    # Play the game
    result_text = ""
    result = {}
    
    if game_type == "solo_slots":
        # Show spinning animation
        spinning_msg = await query.edit_message_text(
            f"🎰 {EMOJI_ANIMATIONS['slot_spinning'][0]} {get_text(casino_bot.db.get_user_language(user['user_id']) if hasattr(casino_bot.db, 'get_user_language') else 'en', 'game_animations.slots_spinning')}",
            reply_markup=None
        )
        
        # Safe animated spinning sequence
        base_text = f"🎰 {get_text(casino_bot.db.get_user_language(user['user_id']) if hasattr(casino_bot.db, 'get_user_language') else 'en', 'game_animations.slots_spinning')}"
        await safe_animation(spinning_msg, EMOJI_ANIMATIONS['slot_spinning'], base_text, delay=1.5)
        
        # Play the game
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_slots(bet_amount)
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_slots(bet_amount)
        
        # Show result with animation
        result_text = f"🎰 **Slot Result:** {' '.join(result['reels'])}\n"
        
        if result['won']:
            win_sticker = get_win_sticker(result.get('win_amount', bet_amount * result['multiplier']), bet_amount)
            celebration = get_random_celebration()
            
            # Big win animation
            if result['multiplier'] >= 10:
                result_text += f"\n{EMOJI_COMBOS['slot_jackpot']}\n"
                result_text += f"🏆 **BIG WIN!** 🏆\n"
                # Send sticker for big wins
                try:
                    await query.message.reply_sticker(win_sticker)
                except:
                    pass
            elif result['multiplier'] >= 5:
                result_text += f"\n{EMOJI_COMBOS['slot_big_win']}\n"
                result_text += f"⭐ **Great Win!** ⭐\n"
            else:
                result_text += f"\n{EMOJI_COMBOS['slot_win']}\n"
            
            result_text += f"🎉 You won! Multiplier: x{result['multiplier']} {celebration}"
        else:
            result_text += f"\n{EMOJI_COMBOS['slot_lose']}\n💔 You lost! Better luck next time..."
            
    elif game_type == "solo_roulette":
        # Show spinning animation
        spinning_msg = await query.edit_message_text(
            f"🎡 {EMOJI_ANIMATIONS['roulette_spinning'][0]} Roulette spinning...",
            reply_markup=None
        )
        
        # Safe animated spinning sequence
        await safe_animation(spinning_msg, EMOJI_ANIMATIONS['roulette_spinning'], "🎡", delay=1.8, final_text="🎡 Roulette spinning...")
        
        # Final spin effect
        await asyncio.sleep(2.0)  # Extended timing to prevent premature deletion
        try:
            await spinning_msg.edit_text("🎡 ⭐ Ball stopping...")
        except Exception:
            # Continue if edit fails
            pass
        
        # Play the game
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_roulette(bet_amount, "color", "red")
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_roulette(bet_amount, "color", "red")
        
        color_emoji = "🟥" if result['color'] == "red" else "⬛" if result['color'] == "black" else "🟩"
        result_text = f"🎯 **Roulette Result:** {result['number']} {color_emoji}\n"
        
        if result['won']:
            if result['color'] == 'green':
                result_text += f"\n{EMOJI_COMBOS['slot_jackpot']}\n"
                result_text += f"💚 **GREEN JACKPOT!** 💚\n"
                try:
                    await query.message.reply_sticker(CASINO_STICKERS['roulette_green'])
                except:
                    pass
            else:
                result_text += f"\n{EMOJI_COMBOS['roulette_win']}\n"
            
            celebration = get_random_celebration()
            result_text += f"🎉 You won! Multiplier: x{result['multiplier']} {celebration}"
        else:
            result_text += f"\n{EMOJI_COMBOS['roulette_lose']}\n💔 You lost! Better luck next time..."
            
    elif game_type == "solo_blackjack":
        # Show card dealing animation
        dealing_msg = await query.edit_message_text(
            f"🃏 {EMOJI_ANIMATIONS['card_dealing'][0]} Dealing cards...",
            reply_markup=None
        )
        
        # Safe animated card dealing
        await safe_animation(dealing_msg, EMOJI_ANIMATIONS['card_dealing'], "🃏", delay=1.5, final_text="🃏 Dealing cards...")
        
        # Play the game
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_blackjack(bet_amount)
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_blackjack(bet_amount)
        
        card_emojis = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
        player_cards = ' '.join([card_emojis.get(c, str(c)) for c in result['player_cards']])
        dealer_cards = ' '.join([card_emojis.get(c, str(c)) for c in result['dealer_cards']])
        
        result_text = f"🃏 **You:** {player_cards} ({result['player_value']})\n"
        result_text += f"🎪 **Dealer:** {dealer_cards} ({result['dealer_value']})\n"
        
        if result['won']:
            if result.get('blackjack', False):
                result_text += f"\n{EMOJI_COMBOS['slot_jackpot']}\n"
                result_text += f"♠️ **BLACKJACK!** ♠️\n"
                try:
                    await query.message.reply_sticker(CASINO_STICKERS['celebration'])
                except:
                    pass
            else:
                result_text += f"\n{EMOJI_COMBOS['blackjack_win']}\n"
            
            celebration = get_random_celebration()
            result_text += f"🎉 Kazandın! {celebration}"
        else:
            result_text += f"\n{EMOJI_COMBOS['blackjack_lose']}\n💔 You lost! Better luck next time..."
            
    elif game_type == "solo_crash":
        # Show rocket launching animation
        launch_msg = await query.edit_message_text(
            "🚀 Rocket launching...",
            reply_markup=None
        )
        
        # Safe animated rocket flight
        rocket_sequence = ["🚀 x1.00... Rising!", "🚀💨 x1.00... Rising!", "🚀💨✨ x1.00... Rising!", "🚀💨✨⭐ x1.00... Rising!"]
        await safe_animation(launch_msg, rocket_sequence, delay=1.5)
        
        # Safe multiplier increase simulation
        multiplier_sequence = [f"🚀💨✨ x{mult:.1f}... When to cash out?" for mult in [1.5, 2.0, 2.5]]
        await safe_animation(launch_msg, multiplier_sequence, delay=1.2)
        
        # Play the game
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_crash(bet_amount, 2.0)
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_crash(bet_amount, 2.0)
        
        result_text = f"🚀 **Crash Point:** x{result['crash_point']:.2f}\n"
        
        if result['won']:
            result_text += f"\n{EMOJI_COMBOS['big_win']}\n"
            result_text += f"✅ Cashed out! Multiplier: x{result['multiplier']:.2f}"
            celebration = get_random_celebration()
            result_text += f" {celebration}"
        else:
            result_text += f"\n💥🔥💨\n❌ Crashed! You lost! Better luck next time..."
            
    elif game_type == "solo_mines":
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_mines(bet_amount, 3)
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_mines(bet_amount, 3)
        result_text = f"💣 **Mines:** {'Exploded!' if result['hit_mine'] else 'Safe!'}\n"
        if result['won']:
            result_text += f"🎉 You won! Multiplier: x{result['multiplier']:.2f} 💥"
        else:
            result_text += "💥 Hit a mine! You lost! 😢"
            
    elif game_type == "solo_baccarat":
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_baccarat(bet_amount, "player")
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_baccarat(bet_amount, "player")
        result_text = f"🎴 **Oyuncu:** {result['player_hand']} (Değer: {sum(result['player_hand'])})\n"
        result_text += f"🏦 **Banker:** {result['banker_hand']} (Değer: {sum(result['banker_hand'])})\n"
        if result['won']:
            result_text += f"🎉 Kazandın! ({result['winner'].title()}) 💥"
        else:
            result_text += "💔 Kaybettin! 😢"
            
    elif game_type == "solo_keno":
        chosen = random.sample(range(1, 80), 5)
        if hasattr(casino_bot, 'casino') and hasattr(casino_bot.casino, 'solo_engine'):
            result = casino_bot.casino.solo_engine.play_solo_keno(bet_amount, chosen)
        else:
            from solo_games import SoloGameEngine
            engine = SoloGameEngine()
            result = engine.play_solo_keno(bet_amount, chosen)
        result_text = f"🔢 **Çekilen Sayılar:** {result['drawn'][:5]}...\n"
        result_text += f"✅ **Uyuşan:** {result['hits']}\n"
        if result['won']:
            result_text += f"🎉 You won! Multiplier: x{result['multiplier']:.2f} 💥"
        else:
            result_text += "💔 Kaybettin! 😢"
    
    # İstatistikleri güncelle
    if hasattr(casino_bot, 'casino'):
        casino_bot.casino.update_user_stats(user['user_id'], bet_amount, result['win_amount'], result['won'])
        # Save solo game if method exists
        if hasattr(casino_bot.casino, 'save_solo_game'):
            casino_bot.casino.save_solo_game(user['user_id'], game_type, bet_amount, result)
    else:
        # Fallback: update stats directly if casino not available
        casino_bot.update_user_stats(user['user_id'], bet_amount, result['win_amount'], result['won'])
    
    net_result = result['win_amount'] - bet_amount
    if net_result > 0:
        result_text += f"\n🐻 **Net Kazanç:** +{net_result} Coins 🌟"
    else:
        result_text += f"\n💸 **Net Kayıp:** {net_result} Coins 😢"
    
    buttons = [
        [("🔄 Tekrar Oyna", f"solo_{game_type.split('_')[1]}"), ("🎮 Başka Oyun", "solo_games")],
        [("📊 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    # Use robust game error handler for final result
    await safe_game_edit(query, result_text, reply_markup=keyboard, parse_mode='Markdown')

@robust_game_operation("Duel creation completed!")
async def handle_create_duel(query, user, game_type, casino_bot):
    """Düello oluştur"""
    game_config = GAMES.get(game_type)
    min_bet = game_config['min_bet']
    if user['fun_coins'] < min_bet:
        success = await safe_edit_message(query,
            f"💸 Yetersiz! Gerekli: {min_bet}", 
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        if not success:
            try:
                await query.message.reply_text(
                    f"💸 Yetersiz! Gerekli: {min_bet}", 
                    reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
                )
            except Exception:
                pass
        return
    
    game_id = casino_bot.create_duel(user['user_id'], game_type, min_bet)
    text = f"⚔️ Düello oluşturuldu! ID: {game_id} 🎮 {game_config['name']}"
    await query.edit_message_text(text, reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]]))

@robust_game_operation("Game join completed!")
async def handle_join_game(query, user, game_id, casino_bot):
    """Oyuna katıl"""
    if casino_bot.join_duel(game_id, user['user_id']):
        success = await safe_edit_message(query, "✅ Katıldın! Oyun başlıyor...")
        if not success:
            try:
                await query.message.reply_text("✅ Katıldın! Oyun başlıyor...")
            except Exception:
                pass
        await asyncio.sleep(3.0)  # Extended timing to ensure game completes before deletion
        await start_duel_game(query, game_id, user, casino_bot)
    else:
        success = await safe_edit_message(query,
            "❌ Katılamadın!", 
            reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
        )
        if not success:
            try:
                await query.message.reply_text(
                    "❌ Katılamadın!", 
                    reply_markup=casino_bot.create_keyboard([[("🏠 Ana Menü", "main_menu")]])
                )
            except Exception:
                pass

@robust_game_operation("Duel completed!")
async def start_duel_game(query, game_id, user, casino_bot):
    """Düello başlat"""
    with casino_bot.db.get_connection() as conn:
        game = conn.execute('SELECT * FROM active_games WHERE game_id = ?', (game_id,)).fetchone()
        players = json.loads(game['players'])
        player1 = conn.execute('SELECT * FROM users WHERE user_id = ?', (players[0],)).fetchone()
        player2 = conn.execute('SELECT * FROM users WHERE user_id = ?', (players[1],)).fetchone()
    
    if game['game_type'] == 'duel_coinflip':
        p1_choice = random.choice(['heads', 'tails'])
        p2_choice = random.choice(['heads', 'tails'])
        result = casino_bot.engine.play_duel_coinflip(p1_choice, p2_choice)
        text = f"🪙 Sonuç: {result['result']} 🏆 Kazanan: {'P1' if result['winner'] == 1 else 'P2' if result['winner'] == 2 else 'Berabere'}"
        
    elif game['game_type'] == 'duel_dice':
        result = casino_bot.engine.play_duel_dice()
        text = f"🎲 P1: {result['dice1']} P2: {result['dice2']} 🏆 Kazanan: {'P1' if result['winner'] == 1 else 'P2' if result['winner'] == 2 else 'Berabere'}"
        
    elif game['game_type'] == 'duel_rockpaper':
        choices = ['rock', 'paper', 'scissors']
        p1_choice = random.choice(choices)
        p2_choice = random.choice(choices)
        result = casino_bot.engine.play_duel_rockpaper(p1_choice, p2_choice)
        text = f"✊ P1: {p1_choice} P2: {p2_choice} 🏆 Kazanan: {'P1' if result['winner'] == 1 else 'P2' if result['winner'] == 2 else 'Berabere'}"
    
    # Ödül dağıt
    bet = game['bet_amount']
    if result['winner'] == 1:
        casino_bot.update_user_stats(player1['user_id'], bet, bet*2, True)
        casino_bot.update_user_stats(player2['user_id'], bet, 0, False)
    elif result['winner'] == 2:
        casino_bot.update_user_stats(player1['user_id'], bet, 0, False)
        casino_bot.update_user_stats(player2['user_id'], bet, bet*2, True)
    else:
        casino_bot.update_user_stats(player1['user_id'], bet, bet, False)
        casino_bot.update_user_stats(player2['user_id'], bet, bet, False)
    
    # Oyunu tamamla
    casino_bot.complete_duel(game_id)
    
    buttons = [
        [("🔄 Yeni Düello", "create_duel"), ("🎮 Solo Oyunlar", "solo_games")],
        [("📊 Profil", "profile"), ("🏠 Ana Menü", "main_menu")]
    ]
    keyboard = casino_bot.create_keyboard(buttons)
    
    # Use robust game handler to prevent timeout errors
    await safe_game_edit(query, text, reply_markup=keyboard)