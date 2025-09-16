#!/usr/bin/env python3
"""
🎮 Enhanced Casino Bot Game Handlers with Animations
"""

import json
import random
import asyncio
from config import GAMES, SOLO_GAMES
from safe_telegram_handler import safe_edit_message

async def handle_enhanced_solo_game(query, user, game_type, bet_amount, casino_bot):
    """Enhanced Solo game with animations and visual effects"""
    
    # Validate bet amount
    try:
        validation = casino_bot.validate_bet_amount(user['user_id'], bet_amount, user['fun_coins'])
        if not validation['valid']:
            await safe_edit_message(query, 
                f"❌ **BET ERROR** ❌\n\n{validation['reason']}\n\n💡 **Tip:** Start with smaller bets!",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Solo Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
    except:
        # Fallback validation
        if bet_amount > user['fun_coins']:
            await safe_edit_message(query, 
                f"❌ **INSUFFICIENT FUNDS** ❌\n\n🐻 **Balance:** {user['fun_coins']:,} FC\n💸 **Bet:** {bet_amount:,} FC\n\n💡 **Need more coins!**",
                reply_markup=casino_bot.create_keyboard([
                    [("🎮 Solo Oyunlar", "solo_games"), ("🏠 Ana Menü", "main_menu")]
                ])
            )
            return
    
    # Clear previous game content and show loading animation
    await safe_edit_message(query, "🎮 Yeni oyun hazırlanıyor...")
    await asyncio.sleep(0.3)
    
    game_name = SOLO_GAMES.get(game_type, {}).get('name', 'GAME')
    loading_text = f"""
🎮 **{game_name}** 🎮

🐻 **Bet:** {bet_amount:,} FC
🎲 **Loading...** 🎲

⚡ Game starting in 3...
    """
    
    await safe_edit_message(query, loading_text, parse_mode='Markdown')
    await asyncio.sleep(0.8)
    
    # Initialize result variables
    result_text = ""
    result = {}
    animation_frames = []
    
    # Game logic with enhanced animations
    if game_type == "solo_slots":
        result = casino_bot.solo_engine.play_solo_slots(bet_amount)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play slot animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
🎰 **ULTIMATE SLOTS** 🎰

🐻 **Bet:** {bet_amount:,} FC

{frame}

{f'⚡ Step {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '🎯 FINAL RESULT!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.0)  # Increased timing to prevent premature emoji deletion
        
        # Final result with enhanced display
        result_text = f"""
🎰 **ULTIMATE SLOTS** 🎰

🐻 **Bet:** {bet_amount:,} FC
🎯 **Result:** {' '.join(result['reels'])}

{result['special_effect'] if 'special_effect' in result else ''}

        """
        
        if result['won']:
            result_text += f"🎉 **WINNER!** 🎉\n💎 **Multiplier:** x{result['multiplier']}\n🐻 **Won:** {result['win_amount']:,} FC"
        else:
            result_text += "😔 **No luck this time!**\n🍀 **Try again for better luck!**"
    
    elif game_type == "solo_roulette":
        bet_choice = random.choice(["red", "black", "even", "odd"])
        bet_type = "color" if bet_choice in ["red", "black"] else "even_odd"
        result = casino_bot.solo_engine.play_solo_roulette(bet_amount, bet_type, bet_choice)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play roulette animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
🎯 **PREMIUM ROULETTE** 🎯

🐻 **Bet:** {bet_amount:,} FC on {bet_choice.upper()}

{frame}

{f'🔄 Spinning... {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '🏆 FINAL RESULT!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.2)  # Increased timing to prevent premature emoji deletion
        
        result_text = f"""
🎯 **PREMIUM ROULETTE** 🎯

🐻 **Bet:** {bet_amount:,} FC on {bet_choice.upper()}
🎲 **Result:** {result['number']} ({result['color'].upper()}) {result['color_emoji']}

{result['special_effect'] if 'special_effect' in result else ''}

        """
        
        if result['won']:
            result_text += f"🎉 **{result['win_type'] if 'win_type' in result else 'WIN'}** 🎉\n💎 **Multiplier:** x{result['multiplier']}\n🐻 **Won:** {result['win_amount']:,} FC"
        else:
            result_text += f"😔 **Better luck next spin!**\n🎯 **Your bet:** {bet_choice.upper()} | **Result:** {result['color'].upper()}"
    
    elif game_type == "solo_blackjack":
        result = casino_bot.solo_engine.play_solo_blackjack(bet_amount)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play blackjack animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
🃏 **PROFESSIONAL BLACKJACK** 🃏

🐻 **Bet:** {bet_amount:,} FC

{frame}

{f'🎴 Dealing... {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '🏆 GAME COMPLETE!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.5)  # Increased timing to prevent premature emoji deletion
        
        # Use enhanced result text from solo_games.py
        result_text = result.get('result_text', '')
        if not result_text:
            # Fallback if no enhanced result text
            result_text = f"""
🃏 **PROFESSIONAL BLACKJACK** 🃏

🐻 **Bet:** {bet_amount:,} FC

🎯 **FINAL HANDS:**
👤 **You:** {result['player_display']} = **{result['player_value']}**
🎩 **Dealer:** {result['dealer_display']} = **{result['dealer_value']}**

{result['special_effect'] if 'special_effect' in result else ''}

            """
        
        if result['won']:
            result_text += f"🎉 **VICTORY!** 🎉\n💎 **Multiplier:** x{result['multiplier']}\n🐻 **Won:** {result['win_amount']:,} FC"
        elif result['multiplier'] == 1:
            result_text += f"🤝 **PUSH - TIE GAME!** 🤝\n🐻 **Bet returned:** {bet_amount:,} FC"
        else:
            result_text += f"😔 **House wins this hand!**\n🎯 **Final scores:** You {result['player_value']} vs Dealer {result['dealer_value']}"
    
    elif game_type == "solo_crash":
        cashout_target = random.uniform(1.5, 5.0)
        result = casino_bot.solo_engine.play_solo_crash(bet_amount, cashout_target)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play crash animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
🚀 **ROCKET CRASH** 🚀

🐻 **Bet:** {bet_amount:,} FC
🎯 **Auto-cashout:** {cashout_target:.1f}x

{frame}

{f'🚀 Flying... {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '🎯 FLIGHT COMPLETE!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.3)  # Increased timing to prevent premature emoji deletion
        
        result_text = f"""
🚀 **ROCKET CRASH** 🚀

🐻 **Bet:** {bet_amount:,} FC
🎯 **Auto-cashout:** {cashout_target:.1f}x
🔥 **Crash Point:** {result['crash_point']:.1f}x

{result['special_effect'] if 'special_effect' in result else ''}
{result['result_text'] if 'result_text' in result else ''}

        """
        
        if result['won']:
            result_text += f"🎉 **SUCCESSFUL FLIGHT!** 🎉\n🚀 **Cashed out at:** {cashout_target:.1f}x\n🐻 **Won:** {result['win_amount']:,} FC"
        else:
            result_text += f"💥 **ROCKET CRASHED!** 💥\n🔥 **Crashed at:** {result['crash_point']:.1f}x\n😔 **Better timing next flight!**"
    
    elif game_type == "solo_mines":
        mines_count = random.randint(3, 5)
        picks_count = random.randint(3, 6)
        result = casino_bot.solo_engine.play_solo_mines(bet_amount, mines_count, picks_count)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play mines animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
💣 **MINESWEEPER EXTREME** ⛏️

🐻 **Bet:** {bet_amount:,} FC
💣 **Mines:** {mines_count} | 🔍 **Picks:** {picks_count}

{frame}

{f'⛏️ Mining... {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '💎 MINING COMPLETE!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.0)  # Increased timing to prevent premature emoji deletion
        
        # Show grid result
        grid_text = "\n".join(result['grid_display'] if 'grid_display' in result else [])
        
        result_text = f"""
💣 **MINESWEEPER EXTREME** ⛏️

🐻 **Bet:** {bet_amount:,} FC
💣 **Mines:** {mines_count} | 🔍 **Picks:** {picks_count}

**MINEFIELD RESULT:**
```
{grid_text}
```

{result['special_effect'] if 'special_effect' in result else ''}
{result['result_text'] if 'result_text' in result else ''}

        """
        
        if result['won']:
            result_text += f"🎉 **SAFE MINING!** 🎉\n💎 **Gems found:** {result['gems_found']}\n🐻 **Won:** {result['win_amount']:,} FC"
        else:
            result_text += f"💥 **MINE EXPLOSION!** 💥\n💣 **Hit {result['hit_mines_count']} mine(s)**\n⚠️ **Better luck next excavation!**"
    
    elif game_type == "solo_baccarat":
        bet_choice = random.choice(["player", "banker", "tie"])
        result = casino_bot.solo_engine.play_solo_baccarat(bet_amount, bet_choice)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play baccarat animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
🎴 **PREMIUM BACCARAT** 🏛️

🐻 **Bet:** {bet_amount:,} FC on {bet_choice.upper()}

{frame}

{f'🎴 Dealing... {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '🏆 GAME COMPLETE!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.2)  # Increased timing to prevent premature emoji deletion
        
        result_text = f"""
🎴 **PREMIUM BACCARAT** 🏛️

🐻 **Bet:** {bet_amount:,} FC on {bet_choice.upper()}

🎯 **FINAL HANDS:**
👤 **Player:** {result['player_display']} = **{result['player_val']}**
🏛️ **Banker:** {result['banker_display']} = **{result['banker_val']}**

{result['special_effect'] if 'special_effect' in result else ''}
{result['winner_text'] if 'winner_text' in result else ''}

        """
        
        if result['won']:
            result_text += f"🎉 **BACCARAT WIN!** 🎉\n🎯 **Your bet:** {bet_choice.upper()} ✅\n🐻 **Won:** {result['win_amount']:,} FC"
        else:
            result_text += f"😔 **House wins this hand!**\n🎯 **Winner:** {result['winner'].upper()} | **Your bet:** {bet_choice.upper()}"
    
    elif game_type == "solo_keno":
        numbers_to_pick = random.randint(5, 10)
        chosen = random.sample(range(1, 81), numbers_to_pick)
        result = casino_bot.solo_engine.play_solo_keno(bet_amount, chosen)
        animation_frames = result['animation_frames'] if 'animation_frames' in result else []
        
        # Play keno animation
        for i, frame in enumerate(animation_frames):
            animation_text = f"""
🔢 **PREMIUM KENO** 🎰

🐻 **Bet:** {bet_amount:,} FC
🎯 **Numbers picked:** {len(chosen)}

{frame}

{f'🎲 Drawing... {i+1}/{len(animation_frames)}' if i < len(animation_frames)-1 else '🏆 DRAW COMPLETE!'}
            """
            await safe_edit_message(query, animation_text, parse_mode='Markdown')
            if i < len(animation_frames) - 1:
                await asyncio.sleep(1.2)  # Increased timing to prevent premature emoji deletion
        
        drawn_display = ', '.join(map(str, result['drawn'][:10])) + '...' if len(result['drawn']) > 10 else ', '.join(map(str, result['drawn']))
        chosen_display = ', '.join(map(str, result['numbers_chosen']))
        hits_display = ', '.join(map(str, result['hit_numbers'])) if result['hit_numbers'] else 'None'
        
        result_text = f"""
🔢 **PREMIUM KENO** 🎰

🐻 **Bet:** {bet_amount:,} FC
🎯 **Your numbers:** {chosen_display}
🎲 **Drawn numbers:** {drawn_display}
✨ **Matches:** {hits_display}

{result['special_effect'] if 'special_effect' in result else ''}
{result['result_text'] if 'result_text' in result else ''}

        """
        
        if result['won']:
            result_text += f"🎉 **KENO WIN!** 🎉\n🎯 **Hits:** {result['hits']}/{len(chosen)}\n🐻 **Won:** {result['win_amount']:,} FC"
        else:
            result_text += f"😔 **Not enough matches!**\n🎯 **Hits:** {result['hits']}/{len(chosen)} (need 2+ to win)"
    
    # Update statistics and save game
    casino_bot.update_user_stats(user['user_id'], bet_amount, result['win_amount'], result['won'])
    casino_bot.save_solo_game(user['user_id'], game_type, bet_amount, result)
    
    # Calculate and display net result with enhanced formatting
    net_result = result['win_amount'] - bet_amount
    if net_result > 0:
        result_text += f"\n🐻 **NET PROFIT:** +{net_result:,} FC 🌟\n⭐ **Great job!**"
    elif net_result == 0:
        result_text += f"\n🤝 **BREAK EVEN:** {net_result:,} FC 🎯\n💫 **No loss, no gain!**"
    else:
        result_text += f"\n💸 **NET LOSS:** {net_result:,} FC 😔\n🍀 **Better luck next time!**"
    
    # Enhanced buttons with more options
    game_name = game_type.split('_')[1] if '_' in game_type else game_type
    buttons = [
        [("🔄 Play Again", f"solo_{game_name}"), ("🎮 Other Games", "solo_games")],
        [("📊 Stats", "profile"), ("🏆 Leaderboard", "leaderboard")],
        [("🐻 Balance Check", "profile"), ("🏠 Main Menu", "main_menu")]
    ]
    
    # Add achievement check notification if applicable
    if result['won'] and net_result > bet_amount * 5:  # Big win
        result_text += "\n\n🏆 **Achievement progress updated!**"
    
    # Final sleep for dramatic effect - wait for complete animation
    await asyncio.sleep(1.5)  # Extended delay to ensure complete animation display
    
    # Display final result
    keyboard = casino_bot.create_keyboard(buttons)
    await safe_edit_message(query, result_text, reply_markup=keyboard, parse_mode='Markdown')