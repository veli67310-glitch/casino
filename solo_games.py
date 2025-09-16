#!/usr/bin/env python3
"""
🎮 Casino Bot Solo Oyun Sistemi
"""

import random

class SoloGameEngine:
    """Solo oyun motoru"""
    
    @staticmethod
    def _apply_admin_bonus(result: dict, user_id: int) -> dict:
        """Admin kullanıcıları için bonus sistemi"""
        # Admin kontrolü - config.py'den admin listesini al
        try:
            from config import ADMIN_USER_IDS
            is_admin = user_id in ADMIN_USER_IDS
        except ImportError:
            is_admin = False
        
        if is_admin:
            # Admin kullanıcıları için %30 daha fazla kazanma şansı
            import random
            bonus_chance = random.random()
            
            if not result['won'] and bonus_chance < 0.3:  # %30 şans
                # Kaybedenken kazanana çevir
                result['won'] = True
                result['win_amount'] = int(result.get('bet_amount', 100) * 1.5)  # 1.5x bonus
                result['special_effect'] = "👑 ADMIN BONUS! 👑"
                result['result_text'] = "👑 Admin şansınız devreye girdi!"
                
            elif result['won']:
                # Zaten kazanıyorsa %50 daha fazla ver
                result['win_amount'] = int(result['win_amount'] * 1.5)
                if result.get('special_effect'):
                    result['special_effect'] += " 👑 ADMIN BOOST!"
                else:
                    result['special_effect'] = "👑 ADMIN BOOST!"
        else:
            # Normal kullanıcılar için kazanma şansını düşür
            import random
            reduce_chance = random.random()
            
            if result['won'] and reduce_chance < 0.15:  # %15 şansla kazancı düşür
                result['win_amount'] = int(result['win_amount'] * 0.7)  # %30 azalt
                
        return result
    
    @staticmethod
    def play_solo_slots(bet_amount: int, user_id: int = None) -> dict:
        """Enhanced Solo slot oyunu with animations"""
        symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "🎰", "⭐", "🌟"]
        weights = [20, 18, 15, 15, 12, 8, 6, 4, 2]
        
        # Enhanced reel generation with special combinations
        reels = [random.choices(symbols, weights=weights, k=1)[0] for _ in range(3)]
        
        # Much rarer special bonus chance
        bonus_chance = random.random()
        if bonus_chance < 0.003:  # 0.3% mega jackpot chance (Much reduced)
            reels = ["🌟", "🌟", "🌟"]
        elif bonus_chance < 0.008:   # 0.5% diamond chance (Much reduced)
            reels = ["💎", "💎", "💎"]
        
        # Casino realistic win calculation (BALANCED RATES)
        if reels[0] == reels[1] == reels[2]:
            if reels[0] == "🌟":
                multiplier = 10.0  # MEGA JACKPOT! (Realistic casino rate)
            elif reels[0] == "💎":
                multiplier = 6.0   # DIAMOND JACKPOT! (Realistic casino rate)
            elif reels[0] == "🎰":
                multiplier = 4.0   # SLOT JACKPOT! (Realistic casino rate)
            elif reels[0] == "⭐":
                multiplier = 2.5   # STAR JACKPOT! (Realistic casino rate)
            elif reels[0] == "🔔":
                multiplier = 2.0   # BELL BONUS! (Realistic casino rate)
            else:
                multiplier = 1.8   # FRUIT COMBO! (Realistic casino rate)
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            multiplier = 0.8   # PAIR BONUS! (Significantly reduced)
        else:
            # Very rare consolation prizes
            if "💎" in reels or "⭐" in reels or "🌟" in reels:
                multiplier = 0.05  # Tiny consolation (Much reduced from 0.2)
            else:
                multiplier = 0
        
        win_amount = int(bet_amount * multiplier)
        
        # Add special effects text
        special_effect = ""
        if multiplier >= 50:
            special_effect = "🌟💥 MEGA JACKPOT! 💥🌟"
        elif multiplier >= 25:
            special_effect = "💎✨ DIAMOND JACKPOT! ✨💎"
        elif multiplier >= 15:
            special_effect = "🎰🔥 SLOT JACKPOT! 🔥🎰"
        elif multiplier >= 10:
            special_effect = "⭐🎉 STAR JACKPOT! 🎉⭐"
        elif multiplier >= 5:
            special_effect = "🎊 BIG WIN! 🎊"
        elif multiplier >= 2:
            special_effect = "🎈 NICE WIN! 🎈"
        elif multiplier > 0:
            special_effect = "🍀 Lucky! 🍀"
        
        # Enhanced result text based on outcome
        if multiplier >= 10:
            result_text = f"🌟💥 MEGA JACKPOT! 💥🌟\n🎰 [ {reels[0]} | {reels[1]} | {reels[2]} ] 🎰\n\n💰 AMAZING WIN!"
        elif multiplier >= 6:
            result_text = f"💎✨ DIAMOND JACKPOT! ✨💎\n🎰 [ {reels[0]} | {reels[1]} | {reels[2]} ] 🎰\n\n🔥 INCREDIBLE!"
        elif multiplier >= 2:
            result_text = f"🎉 JACKPOT! 🎉\n🎰 [ {reels[0]} | {reels[1]} | {reels[2]} ] 🎰\n\n⭐ Great win!"
        elif multiplier > 0:
            result_text = f"🍀 Lucky spin! 🍀\n🎰 [ {reels[0]} | {reels[1]} | {reels[2]} ] 🎰\n\n🎈 Small win!"
        else:
            result_text = f"😔 No luck this time\n🎰 [ {reels[0]} | {reels[1]} | {reels[2]} ] 🎰\n\n🎯 Try again!"

        result = {
            'reels': reels,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': multiplier > 0,
            'special_effect': special_effect,
            'bet_amount': bet_amount,
            'result_text': result_text,
            'animation_frames': [
                "🎰 Spinning the reels... 🎰",
                "🎰 [ 🎲 | ? | ? ] 🎰",
                "🎰 [ 🎲 | 🎲 | ? ] 🎰",
                f"🎰 [ {reels[0]} | {reels[1]} | {reels[2]} ] 🎰",
                result_text
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_roulette(bet_amount: int, bet_type: str = "color", bet_value: str = "red", user_id: int = None) -> dict:
        """Enhanced Solo roulette with animations and multiple bet types"""
        number = random.randint(0, 36)
        
        # Color determination with special green for 0
        if number == 0:
            color = "green"
            color_emoji = "🟢"
        elif number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
            color = "red"
            color_emoji = "🔴"
        else:
            color = "black"
            color_emoji = "⚫"
        
        won = False
        multiplier = 0
        win_type = ""
        
        # Enhanced betting system (FURTHER REDUCED RATES)
        if bet_type == "number":
            if int(bet_value) == number:
                multiplier = 15  # Reduced for balance (realistic casino rate)
                won = True
                win_type = "NUMBER HIT!"
        elif bet_type == "color":
            if bet_value == color and number != 0:
                multiplier = 1.3  # Reduced for balance (more realistic)
                won = True
                win_type = "COLOR WIN!"
        elif bet_type == "even_odd":
            if bet_value == "even" and number != 0 and number % 2 == 0:
                multiplier = 1.3  # Reduced for balance
                won = True
                win_type = "EVEN WIN!"
            elif bet_value == "odd" and number % 2 == 1:
                multiplier = 1.3  # Reduced for balance
                won = True
                win_type = "ODD WIN!"
        elif bet_type == "high_low":
            if bet_value == "high" and 19 <= number <= 36:
                multiplier = 1.3  # Reduced for balance
                won = True
                win_type = "HIGH WIN!"
            elif bet_value == "low" and 1 <= number <= 18:
                multiplier = 1.3  # Reduced for balance
                won = True
                win_type = "LOW WIN!"
        
        # Special zero bonus
        if number == 0 and not won:
            multiplier = 0.1  # Minimal consolation for hitting zero (Reduced from 0.2)
            win_type = "ZERO BONUS!"
        
        win_amount = int(bet_amount * multiplier)
        
        # Special effects for big wins
        special_effect = ""
        if multiplier >= 36:
            special_effect = "🎆💥 STRAIGHT UP WIN! 💥🎆"
        elif number == 0:
            special_effect = "🟢✨ ZERO LANDED! ✨🟢"
        elif won:
            special_effect = f"🎉 {win_type} 🎉"
        
        # Enhanced result text
        if won and multiplier >= 15:
            result_text = f"🎆💥 STRAIGHT NUMBER WIN! 💥🎆\n\n🎯 Number: **{number}** {color_emoji}\n🏆 {win_type}\n\n💰 INCREDIBLE PAYOUT!"
        elif number == 0:
            result_text = f"🟢✨ ZERO LANDED! ✨🟢\n\n🎯 Number: **{number}** {color_emoji}\n🎊 House number hit!\n\n{('💰 Small bonus!' if multiplier > 0 else '💸 House wins!')}"
        elif won:
            result_text = f"🎉 {win_type} 🎉\n\n🎯 Number: **{number}** {color_emoji}\n🏆 {bet_type.upper()} bet won!\n\n💰 Nice payout!"
        else:
            result_text = f"😔 No win this time\n\n🎯 Number: **{number}** {color_emoji}\n💸 {bet_type.upper()} bet lost\n\n🍀 Better luck next spin!"

        result = {
            'number': number,
            'color': color,
            'color_emoji': color_emoji,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': won or multiplier > 0,
            'win_type': win_type,
            'special_effect': special_effect,
            'bet_amount': bet_amount,
            'result_text': result_text,
            'animation_frames': [
                "🎯 Placing your bet... 🎯",
                "🎯 🔄 Spinning the wheel... 🔄 🎯",
                "🎯 ⚡ Slowing down... ⚡ 🎯",
                f"🎯 {color_emoji} **{number}** {color_emoji} 🎯",
                result_text
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_blackjack(bet_amount: int, user_id: int = None) -> dict:
        """Enhanced Professional Blackjack with animations"""
        def card_value(cards):
            value = sum(min(card, 10) for card in cards)
            aces = sum(1 for card in cards if card == 1)
            while aces > 0 and value + 10 <= 21:
                value += 10
                aces -= 1
            return value
        
        def card_display(card):
            suits = ["♠️", "♥️", "♦️", "♣️"]
            if card == 1:
                return f"A{random.choice(suits)}"
            elif card == 11:
                return f"J{random.choice(suits)}"
            elif card == 12:
                return f"Q{random.choice(suits)}"
            elif card == 13:
                return f"K{random.choice(suits)}"
            else:
                return f"{card}{random.choice(suits)}"
        
        # Deal initial cards
        player_cards = [random.randint(1, 13), random.randint(1, 13)]
        dealer_cards = [random.randint(1, 13), random.randint(1, 13)]
        
        player_value = card_value(player_cards)
        dealer_value = card_value(dealer_cards)
        dealer_hit_cards = []
        
        # Check for natural blackjack
        player_blackjack = player_value == 21 and len(player_cards) == 2
        dealer_blackjack = dealer_value == 21 and len(dealer_cards) == 2
        
        # Dealer drawing logic
        if not player_blackjack:
            while dealer_value < 17:
                new_card = random.randint(1, 13)
                dealer_cards.append(new_card)
                dealer_hit_cards.append(new_card)
                dealer_value = card_value(dealer_cards)
        
        # Determine result with enhanced payouts
        if player_blackjack and dealer_blackjack:
            result = "both_blackjack"
            multiplier = 1.0  # Push
            result_text = "🏆 BOTH BLACKJACK - PUSH! 🏆"
        elif player_blackjack and not dealer_blackjack:
            result = "player_blackjack"
            multiplier = 2.2  # Reduced blackjack payout (was 2.5)
            result_text = "🎆✨ BLACKJACK! ✨🎆"
        elif player_value > 21:
            result = "bust"
            multiplier = 0
            result_text = "💥 BUST! 💥"
        elif dealer_value > 21:
            result = "dealer_bust"
            multiplier = 1.8  # Reduced payout (was 2.0)
            result_text = "🎉 DEALER BUST! 🎉"
        elif player_value > dealer_value:
            result = "win"
            multiplier = 1.8  # Reduced payout (was 2.0)
            result_text = "🏆 YOU WIN! 🏆"
        elif player_value == dealer_value:
            result = "push"
            multiplier = 1.0
            result_text = "🤝 PUSH - TIE! 🤝"
        else:
            result = "lose"
            multiplier = 0
            result_text = "😔 DEALER WINS 😔"
        
        win_amount = int(bet_amount * multiplier)
        
        # Create card display strings
        player_display = " | ".join([card_display(card) for card in player_cards])
        dealer_display = " | ".join([card_display(card) for card in dealer_cards])
        
        # Enhanced result display
        if player_blackjack and not dealer_blackjack:
            final_result = f"🎆✨ BLACKJACK! ✨🎆\n\n👤 **Your cards:** {player_display} = **{player_value}**\n🎲 **Dealer:** {dealer_display} = **{dealer_value}**\n\n💰 BLACKJACK PAYOUT!"
        elif result == "dealer_bust":
            final_result = f"🎉 DEALER BUST! 🎉\n\n👤 **Your cards:** {player_display} = **{player_value}**\n🎲 **Dealer:** {dealer_display} = **{dealer_value}** 💥\n\n💰 You win!"
        elif result == "win":
            final_result = f"🏆 YOU WIN! 🏆\n\n👤 **Your cards:** {player_display} = **{player_value}**\n🎲 **Dealer:** {dealer_display} = **{dealer_value}**\n\n💰 Great hand!"
        elif result == "push":
            final_result = f"🤝 PUSH - TIE! 🤝\n\n👤 **Your cards:** {player_display} = **{player_value}**\n🎲 **Dealer:** {dealer_display} = **{dealer_value}**\n\n💰 Bet returned!"
        elif result == "bust":
            final_result = f"💥 BUST! 💥\n\n👤 **Your cards:** {player_display} = **{player_value}**\n🎲 **Dealer:** {dealer_display} = **{dealer_value}**\n\n💸 Over 21!"
        else:
            final_result = f"😔 DEALER WINS 😔\n\n👤 **Your cards:** {player_display} = **{player_value}**\n🎲 **Dealer:** {dealer_display} = **{dealer_value}**\n\n💸 Better luck next time!"

        result = {
            'player_cards': player_cards,
            'dealer_cards': dealer_cards,
            'player_value': player_value,
            'dealer_value': dealer_value,
            'player_display': player_display,
            'dealer_display': dealer_display,
            'player_blackjack': player_blackjack,
            'dealer_blackjack': dealer_blackjack,
            'dealer_hit_cards': dealer_hit_cards,
            'result': result,
            'result_text': final_result,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': multiplier > 1,
            'bet_amount': bet_amount,
            'animation_frames': [
                "🃏 Shuffling deck... 🃏",
                "🃏 Dealing initial cards... 🃏",
                f"👤 **You:** {player_display} = {player_value}",
                f"🎲 **Dealer:** {card_display(dealer_cards[0])} | 🂠 = ??",
                f"🎲 **Dealer reveals:** {dealer_display} = {dealer_value}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_crash(bet_amount: int, cashout_multiplier: float = 2.0, user_id: int = None) -> dict:
        """Enhanced Crash game with advanced mechanics"""
        # More realistic crash distribution
        rand = random.random()
        if rand < 0.33:  # 33% chance of early crash
            crash_point = random.uniform(1.0, 2.0)
        elif rand < 0.66:  # 33% chance of medium crash
            crash_point = random.uniform(2.0, 5.0)
        elif rand < 0.90:  # 24% chance of high crash
            crash_point = random.uniform(5.0, 20.0)
        else:  # 10% chance of moon crash
            crash_point = random.uniform(20.0, 100.0)
        
        # Auto-cashout logic
        actual_multiplier = min(crash_point, cashout_multiplier)
        won = crash_point >= cashout_multiplier
        
        if won:
            multiplier = cashout_multiplier
            win_amount = int(bet_amount * multiplier)
            result_text = f"🚀 CASHED OUT AT {cashout_multiplier:.1f}x! 🚀"
        else:
            multiplier = 0
            win_amount = 0
            result_text = f"💥 CRASHED AT {crash_point:.1f}x! 💥"
        
        # Special effects
        special_effect = ""
        if crash_point >= 50:
            special_effect = "🌌🚀 MOON ROCKET! 🚀🌌"
        elif crash_point >= 20:
            special_effect = "💫✨ SPACE FLIGHT! ✨💫"
        elif crash_point >= 10:
            special_effect = "🎆🔥 HIGH FLIGHT! 🔥🎆"
        elif crash_point >= 5:
            special_effect = "🎈🐻 GOOD FLIGHT! 🐻🎈"
        
        # Enhanced crash result display
        if won:
            final_result = f"🚀💰 SUCCESSFUL CASHOUT! 💰🚀\n\n🎯 **Target:** {cashout_multiplier:.1f}x\n🚀 **Crashed at:** {crash_point:.1f}x\n\n{special_effect if special_effect else '💰 Safe landing!'}"
        else:
            final_result = f"💥💸 ROCKET CRASHED! 💸💥\n\n🎯 **Target:** {cashout_multiplier:.1f}x\n🚀 **Crashed at:** {crash_point:.1f}x\n\n😢 Too greedy this time!"

        result = {
            'crash_point': round(crash_point, 1),
            'cashout_multiplier': cashout_multiplier,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': won,
            'result_text': final_result,
            'special_effect': special_effect,
            'bet_amount': bet_amount,
            'animation_frames': [
                "🚀 Rocket preparing for launch... 🚀",
                "🚀 3... 2... 1... LIFTOFF! 🚀",
                "🚀 1.0x 🟢 FLYING... 🟢",
                f"🚀 {min(2.0, crash_point):.1f}x {'🟡' if crash_point > 2 else '🔴'} {'CLIMBING...' if crash_point > 2 else 'CRASHING!'}",
                f"🚀 {min(5.0, crash_point):.1f}x {'🟠' if crash_point > 5 else '🔴'} {'HIGH ALTITUDE!' if crash_point > 5 else 'GOING DOWN!'}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_mines(bet_amount: int, mines_count: int = 3, picks: int = 3, user_id: int = None) -> dict:
        """Enhanced Mines game with strategic gameplay"""
        grid_size = 25
        grid = [0] * grid_size
        mine_positions = set(random.sample(range(grid_size), mines_count))
        
        # Player picks positions
        picked_positions = set(random.sample(range(grid_size), picks))
        
        # Check for mine hits
        hit_mines = picked_positions & mine_positions
        hit_mine = len(hit_mines) > 0
        gems_found = len(picked_positions - mine_positions)
        
        # Enhanced multiplier calculation
        if hit_mine:
            multiplier = 0
            result_text = f"💣 HIT {len(hit_mines)} MINE(S)! 💣"
        else:
            # Balanced multiplier for fair gameplay
            base_multiplier = 0.8  # Reduced base (was 1.0)
            risk_bonus = mines_count * 0.2  # Reduced risk bonus (was 0.3)
            pick_bonus = picks * 0.25      # Reduced pick bonus (was 0.4)
            multiplier = base_multiplier + risk_bonus + pick_bonus
            result_text = f"💎 FOUND {gems_found} GEMS! 💎"
        
        win_amount = int(bet_amount * multiplier)
        
        # Create visual grid representation
        display_grid = []
        for i in range(grid_size):
            if i in hit_mines:
                display_grid.append("💣")  # Hit mine
            elif i in picked_positions:
                display_grid.append("💎")  # Found gem
            elif i in mine_positions:
                display_grid.append("❓")     # Hidden mine
            else:
                display_grid.append("⬜")     # Safe unknown
        
        # Format grid as 5x5
        grid_display = []
        for row in range(5):
            start = row * 5
            end = start + 5
            grid_display.append(" ".join(display_grid[start:end]))
        
        special_effect = ""
        if not hit_mine and gems_found >= 4:
            special_effect = "🎆✨ PERFECT PICKS! ✨🎆"
        elif not hit_mine and gems_found >= 2:
            special_effect = "🎉💎 GOOD MINING! 💎🎉"
        
        # Enhanced mines result display
        if hit_mine:
            final_result = f"💣💥 MINE EXPLOSION! 💥💣\n\n⛏️ **Mines hit:** {len(hit_mines)}/{mines_count}\n💎 **Gems found:** {gems_found}\n\n🔥 GAME OVER!"
        else:
            final_result = f"💎✨ SUCCESSFUL MINING! ✨💎\n\n⛏️ **Mines avoided:** {mines_count}\n💎 **Gems found:** {gems_found}\n\n{special_effect if special_effect else '💰 Safe mining!'}"

        # Grid display with enhanced formatting
        grid_text = "\n".join(grid_display)

        result = {
            'mines_count': mines_count,
            'picks': picks,
            'hit_mine': hit_mine,
            'hit_mines_count': len(hit_mines),
            'gems_found': gems_found,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': not hit_mine,
            'result_text': final_result,
            'special_effect': special_effect,
            'grid_display': grid_display,
            'grid_text': grid_text,
            'mine_positions': list(mine_positions),
            'picked_positions': list(picked_positions),
            'bet_amount': bet_amount,
            'animation_frames': [
                "⛏️ Setting up minefield... ⛏️",
                f"🔍 Placing {mines_count} mines in 25 positions...",
                f"💎 Starting excavation at {picks} locations...",
                f"\n{grid_text}\n",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_baccarat(bet_amount: int, bet_on: str = "player", user_id: int = None) -> dict:
        """Enhanced Professional Baccarat with proper rules"""
        def hand_value(hand):
            val = sum(min(card, 10) for card in hand) % 10
            return val
        
        def card_display(card):
            suits = ["♠️", "♥️", "♦️", "♣️"]
            if card == 1:
                return f"A{random.choice(suits)}"
            elif card == 11:
                return f"J{random.choice(suits)}"
            elif card == 12:
                return f"Q{random.choice(suits)}"
            elif card == 13:
                return f"K{random.choice(suits)}"
            else:
                return f"{card}{random.choice(suits)}"
        
        # Initial deal - 2 cards each
        player_hand = [random.randint(1, 13), random.randint(1, 13)]
        banker_hand = [random.randint(1, 13), random.randint(1, 13)]
        
        player_val = hand_value(player_hand)
        banker_val = hand_value(banker_hand)
        
        # Natural win check (8 or 9)
        player_natural = player_val >= 8
        banker_natural = banker_val >= 8
        
        # Third card rules (simplified)
        if not (player_natural or banker_natural):
            if player_val <= 5:
                player_hand.append(random.randint(1, 13))
                player_val = hand_value(player_hand)
            
            if banker_val <= 5 and len(player_hand) == 2:
                banker_hand.append(random.randint(1, 13))
                banker_val = hand_value(banker_hand)
        
        # Determine winner
        if player_val > banker_val:
            winner = 'player'
            winner_text = "👤 PLAYER WINS!"
        elif banker_val > player_val:
            winner = 'banker'
            winner_text = "🏦 BANKER WINS!"
        else:
            winner = 'tie'
            winner_text = "🤝 TIE GAME!"
        
        # Payout calculation
        if bet_on == winner:
            if winner == 'tie':
                multiplier = 6.0  # Reduced tie payout (was 9.0)
                result_text = "🎆🐻 TIE BET WINS! 🐻🎆"
            elif winner == 'banker':
                multiplier = 1.8   # Reduced banker payout (was 1.95)
                result_text = "🏦✨ BANKER BET WINS! ✨🏦"
            else:  # player
                multiplier = 1.8   # Reduced player payout (was 2.0)
                result_text = "👤🎉 PLAYER BET WINS! 🎉👤"
        else:
            multiplier = 0
            result_text = f"😔 {winner_text} - You bet {bet_on.upper()}"
        
        win_amount = int(bet_amount * multiplier)
        
        # Create display strings
        player_display = " | ".join([card_display(card) for card in player_hand])
        banker_display = " | ".join([card_display(card) for card in banker_hand])
        
        special_effect = ""
        if winner == 'tie':
            special_effect = "🌈✨ RARE TIE! ✨🌈"
        elif player_natural or banker_natural:
            special_effect = "🎆💫 NATURAL WIN! 💫🎆"
        
        # Enhanced baccarat result display
        if bet_on == winner:
            if winner == 'tie':
                final_result = f"🎆🤝 RARE TIE WIN! 🤝🎆\n\n👤 **Player:** {player_display} = {player_val}\n🏦 **Banker:** {banker_display} = {banker_val}\n🎯 **Your bet:** TIE\n\n💰 HUGE PAYOUT!"
            else:
                final_result = f"🎉 {winner_text} 🎉\n\n👤 **Player:** {player_display} = {player_val}\n🏦 **Banker:** {banker_display} = {banker_val}\n🎯 **Your bet:** {bet_on.upper()}\n\n💰 You win!"
        else:
            final_result = f"😔 {winner_text} 😔\n\n👤 **Player:** {player_display} = {player_val}\n🏦 **Banker:** {banker_display} = {banker_val}\n🎯 **Your bet:** {bet_on.upper()}\n\n💸 Wrong guess!"

        result = {
            'player_hand': player_hand,
            'banker_hand': banker_hand,
            'player_val': player_val,
            'banker_val': banker_val,
            'player_display': player_display,
            'banker_display': banker_display,
            'winner': winner,
            'winner_text': winner_text,
            'player_natural': player_natural,
            'banker_natural': banker_natural,
            'bet_on': bet_on,
            'result_text': final_result,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': multiplier > 0,
            'special_effect': special_effect,
            'bet_amount': bet_amount,
            'animation_frames': [
                "🃏 Shuffling baccarat cards... 🃏",
                "🃏 Dealing initial hands... 🃏",
                f"👤 **Player hand:** {player_display} = {player_val}",
                f"🏦 **Banker hand:** {banker_display} = {banker_val}",
                f"🎯 **Your bet:** {bet_on.upper()}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_keno(bet_amount: int, numbers_chosen: list = None, user_id: int = None) -> dict:
        """Enhanced Keno with realistic payouts"""
        if numbers_chosen is None:
            # Auto-pick 10 random numbers if none provided
            numbers_chosen = random.sample(range(1, 81), 10)
        
        # Limit to 10 numbers max for better gameplay
        if len(numbers_chosen) > 10:
            numbers_chosen = numbers_chosen[:10]
        
        # Draw 20 winning numbers
        drawn = random.sample(range(1, 81), 20)
        drawn_set = set(drawn)
        chosen_set = set(numbers_chosen)
        
        # Calculate hits
        hits = len(chosen_set & drawn_set)
        hit_numbers = list(chosen_set & drawn_set)
        
        # Enhanced payout table based on hits
        payout_table = {
            0: 0,    1: 0,    2: 0.5,  3: 1.0,   4: 2.0,
            5: 3.0,  6: 5.0,  7: 10.0, 8: 25.0,  9: 100.0,
            10: 1000.0  # Jackpot for hitting all 10!
        }
        
        multiplier = payout_table.get(hits, 0)
        win_amount = int(bet_amount * multiplier)
        
        # Result messages
        if hits == 10:
            result_text = "🎆💥 KENO JACKPOT! ALL 10 HITS! 💥🎆"
            special_effect = "🌟🎆 PERFECT GAME! 🎆🌟"
        elif hits >= 8:
            result_text = f"🎉✨ AMAZING! {hits} HITS! ✨🎉"
            special_effect = "💫🔥 INCREDIBLE LUCK! 🔥💫"
        elif hits >= 6:
            result_text = f"🎈🐻 GREAT! {hits} HITS! 🐻🎈"
            special_effect = "🎆👏 WELL DONE! 👏🎆"
        elif hits >= 4:
            result_text = f"😊🎯 NICE! {hits} HITS! 🎯😊"
            special_effect = "🍀✨ Lucky picks! ✨🍀"
        elif hits >= 2:
            result_text = f"🙂 Small win: {hits} hits"
            special_effect = "🌱 Something is better than nothing!"
        else:
            result_text = f"😔 No luck: {hits} hits"
            special_effect = "🍀 Better luck next time!"
        
        # Format numbers for display
        drawn_display = sorted(drawn)
        chosen_display = sorted(numbers_chosen)
        hit_display = sorted(hit_numbers)
        
        # Enhanced keno result display
        if hits == 10:
            final_result = f"🎆💥 KENO JACKPOT! 💥🎆\n\n🎯 **Your numbers:** {', '.join(map(str, chosen_display))}\n🎲 **Drawn numbers:** {', '.join(map(str, drawn_display[:10]))}...\n🏆 **Perfect match:** {hits}/10\n\n💰 INCREDIBLE PAYOUT!"
        elif hits >= 8:
            final_result = f"🎉✨ AMAZING! {hits} HITS! ✨🎉\n\n🎯 **Your numbers:** {', '.join(map(str, chosen_display[:5]))}...\n🎲 **Matches:** {', '.join(map(str, hit_display))}\n🏆 **Hit rate:** {hits}/10\n\n💰 Great win!"
        elif hits >= 4:
            final_result = f"🎈🐻 NICE! {hits} HITS! 🐻🎈\n\n🎯 **Your numbers:** {', '.join(map(str, chosen_display[:5]))}...\n🎲 **Matches:** {', '.join(map(str, hit_display))}\n🏆 **Hit rate:** {hits}/10\n\n💰 Good payout!"
        elif hits >= 2:
            final_result = f"🙂 Small win: {hits} hits\n\n🎯 **Your numbers:** {', '.join(map(str, chosen_display[:5]))}...\n🎲 **Matches:** {', '.join(map(str, hit_display))}\n🏆 **Hit rate:** {hits}/10\n\n🍀 Something is better than nothing!"
        else:
            final_result = f"😔 No luck this time\n\n🎯 **Your numbers:** {', '.join(map(str, chosen_display[:5]))}...\n🎲 **No matches** from drawn numbers\n🏆 **Hit rate:** {hits}/10\n\n🍀 Better luck next time!"

        result = {
            'numbers_chosen': chosen_display,
            'drawn': drawn_display,
            'hits': hits,
            'hit_numbers': hit_display,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': hits >= 2,  # Need at least 2 hits to win
            'result_text': final_result,
            'special_effect': special_effect,
            'bet_amount': bet_amount,
            'animation_frames': [
                "🎲 Keno machine starting... 🎲",
                f"🎯 **Your picks:** {', '.join(map(str, chosen_display))}",
                "💫 Drawing 20 winning numbers...",
                f"🎲 **Drawn:** {', '.join(map(str, drawn_display[:10]))}...",
                f"✨ **Matches found:** {', '.join(map(str, hit_display))}" if hit_numbers else "😔 No matches found...",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_rock_paper_scissors(bet_amount: int, player_choice: str = None, user_id: int = None) -> dict:
        """Taş-Kağıt-Makas oyunu"""
        choices = ["🗿", "📄", "✂️"]
        choice_names = {"🗿": "Taş", "📄": "Kağıt", "✂️": "Makas"}
        
        # Otomatik seçim yapılmazsa rastgele seç
        if not player_choice:
            player_choice = random.choice(choices)
        
        bot_choice = random.choice(choices)
        
        # Oyun mantığı
        if player_choice == bot_choice:
            result = "tie"
            multiplier = 1.0
            result_text = f"🤝 BERABERE! İkiniz de {choice_names[player_choice]} seçtiniz!"
        elif (player_choice == "🗿" and bot_choice == "✂️") or \
             (player_choice == "📄" and bot_choice == "🗿") or \
             (player_choice == "✂️" and bot_choice == "📄"):
            result = "win"
            multiplier = 2.0
            result_text = f"🎉 KAZANDINIZ! {choice_names[player_choice]} > {choice_names[bot_choice]}"
        else:
            result = "lose"
            multiplier = 0
            result_text = f"😔 KAYBETTİNİZ! {choice_names[bot_choice]} > {choice_names[player_choice]}"
        
        win_amount = int(bet_amount * multiplier)
        
        special_effect = ""
        if result == "win":
            special_effect = "🏆 Mükemmel seçim! 🏆"
        elif result == "tie":
            special_effect = "🧠 Aynı dalga boyundayız! 🧠"
        
        # Enhanced rock-paper-scissors result display
        if result == "win":
            final_result = f"🎉 KAZANDINIZ! 🎉\n\n👤 **Sizin:** {player_choice} {choice_names[player_choice]}\n🤖 **Bot:** {bot_choice} {choice_names[bot_choice]}\n\n🏆 {choice_names[player_choice]} beats {choice_names[bot_choice]}!\n\n💰 Perfect choice!"
        elif result == "tie":
            final_result = f"🤝 BERABERE! 🤝\n\n👤 **Sizin:** {player_choice} {choice_names[player_choice]}\n🤖 **Bot:** {bot_choice} {choice_names[bot_choice]}\n\n🧠 Great minds think alike!\n\n💰 Bet returned!"
        else:
            final_result = f"😔 KAYBETTİNİZ 😔\n\n👤 **Sizin:** {player_choice} {choice_names[player_choice]}\n🤖 **Bot:** {bot_choice} {choice_names[bot_choice]}\n\n💪 {choice_names[bot_choice]} beats {choice_names[player_choice]}\n\n🍀 Try a different strategy!"

        result = {
            'player_choice': player_choice,
            'bot_choice': bot_choice,
            'result': result,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': result in ['win', 'tie'],
            'bet_amount': bet_amount,
            'result_text': final_result,
            'special_effect': special_effect,
            'animation_frames': [
                "🎮 Rock-Paper-Scissors challenge! 🎮",
                "3... 2... 1... SHOOT! 💫",
                f"👤 **You chose:** {player_choice} {choice_names[player_choice]}",
                f"🤖 **Bot chose:** {bot_choice} {choice_names[bot_choice]}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_number_guess(bet_amount: int, player_guess: int = None, user_id: int = None) -> dict:
        """Sayı tahmin oyunu (1-100 arası)"""
        target_number = random.randint(1, 100)
        
        # Otomatik tahmin yapılmazsa rastgele seç
        if not player_guess:
            player_guess = random.randint(1, 100)
        
        # Yakınlık hesapla
        difference = abs(target_number - player_guess)
        
        # Ödül sistemi - yakınlığa göre
        if difference == 0:
            multiplier = 100.0  # Tam isabet - JACKPOT!
            result_text = "🎆💥 JACKPOT! TAM İSABET! 💥🎆"
            special_effect = "🌟🎉 İNANILMAZ ŞANS! 🎉🌟"
        elif difference <= 2:
            multiplier = 25.0  # Çok yakın
            result_text = f"🎯 ÇOK YAKLAŞTIN! Fark: {difference}"
            special_effect = "🔥 Neredeyse mükemmel! 🔥"
        elif difference <= 5:
            multiplier = 10.0  # Yakın
            result_text = f"👏 YAKLAŞTIN! Fark: {difference}"
            special_effect = "⭐ İyi tahmin! ⭐"
        elif difference <= 10:
            multiplier = 5.0  # Orta
            result_text = f"😊 Fena değil! Fark: {difference}"
            special_effect = "🍀 Şans var! 🍀"
        elif difference <= 20:
            multiplier = 2.0  # Uzak
            result_text = f"🙂 Biraz uzak. Fark: {difference}"
            special_effect = "💫 Denemeye devam! 💫"
        else:
            multiplier = 0.5  # Çok uzak - teselli ödülü
            result_text = f"😔 Çok uzak. Fark: {difference}"
            special_effect = "🌱 Bir dahaki sefere!"
        
        win_amount = int(bet_amount * multiplier)
        won = difference <= 20  # 20'den az farkla kazançlı sayılır
        
        # Enhanced number guess result display
        if difference == 0:
            final_result = f"🎆💥 JACKPOT! TAM İSABET! 💥🎆\n\n🎯 **Your guess:** {player_guess}\n🎲 **Target number:** {target_number}\n🏆 **Difference:** {difference}\n\n💰 INCREDIBLE PAYOUT!"
        elif difference <= 5:
            final_result = f"🎉 ÇOK YAKLAŞTIN! 🎉\n\n🎯 **Your guess:** {player_guess}\n🎲 **Target number:** {target_number}\n🏆 **Difference:** {difference}\n\n💰 Great payout!"
        elif difference <= 10:
            final_result = f"👏 YAKLAŞTIN! 👏\n\n🎯 **Your guess:** {player_guess}\n🎲 **Target number:** {target_number}\n🏆 **Difference:** {difference}\n\n💰 Nice payout!"
        elif difference <= 20:
            final_result = f"🙂 Fena değil! 🙂\n\n🎯 **Your guess:** {player_guess}\n🎲 **Target number:** {target_number}\n🏆 **Difference:** {difference}\n\n💰 Small win!"
        else:
            final_result = f"😔 Çok uzak 😔\n\n🎯 **Your guess:** {player_guess}\n🎲 **Target number:** {target_number}\n🏆 **Difference:** {difference}\n\n🍀 Try again!"

        result = {
            'target_number': target_number,
            'player_guess': player_guess,
            'difference': difference,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': won,
            'bet_amount': bet_amount,
            'result_text': final_result,
            'special_effect': special_effect,
            'animation_frames': [
                "🎯 Mystery number generator starting... 🎯",
                "🎲 Selecting random number from 1-100...",
                f"🤔 **Your guess:** {player_guess}",
                f"✨ **Target number:** {target_number}",
                f"📈 **Calculating difference:** {difference}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_lucky_wheel(bet_amount: int, user_id: int = None) -> dict:
        """Şans çarkı oyunu"""
        # Çark sektörleri (ödül ve olasılık)
        wheel_sectors = [
            {"prize": "MEGA JACKPOT", "multiplier": 50.0, "emoji": "🌟", "weight": 1},
            {"prize": "JACKPOT", "multiplier": 25.0, "emoji": "💎", "weight": 2},
            {"prize": "BIG WIN", "multiplier": 10.0, "emoji": "🎆", "weight": 5},
            {"prize": "SUPER WIN", "multiplier": 7.5, "emoji": "✨", "weight": 8},
            {"prize": "GREAT WIN", "multiplier": 5.0, "emoji": "🎉", "weight": 12},
            {"prize": "GOOD WIN", "multiplier": 3.0, "emoji": "🎊", "weight": 15},
            {"prize": "WIN", "multiplier": 2.0, "emoji": "🏆", "weight": 20},
            {"prize": "SMALL WIN", "multiplier": 1.5, "emoji": "🎈", "weight": 25},
            {"prize": "LUCKY", "multiplier": 1.0, "emoji": "🍀", "weight": 12}
        ]
        
        # Ağırlıklı seçim
        weights = [sector["weight"] for sector in wheel_sectors]
        selected_sector = random.choices(wheel_sectors, weights=weights)[0]
        
        multiplier = selected_sector["multiplier"]
        win_amount = int(bet_amount * multiplier)
        
        # Çark döndürme animasyonu için rastgele sektörler
        animation_sectors = random.choices(wheel_sectors, k=8)
        
        result_text = f"{selected_sector['emoji']} {selected_sector['prize']}! {selected_sector['emoji']}"
        
        special_effect = ""
        if multiplier >= 25:
            special_effect = "🎆🌟 INCREDIBLE LUCK! 🌟🎆"
        elif multiplier >= 10:
            special_effect = "💫🔥 AMAZING SPIN! 🔥💫"
        elif multiplier >= 5:
            special_effect = "🎉⭐ GREAT LUCK! ⭐🎉"
        
        # Enhanced lucky wheel result display
        if multiplier >= 25:
            final_result = f"🎆{selected_sector['emoji']} {selected_sector['prize']}! {selected_sector['emoji']}🎆\n\n🎪 **Wheel stopped at:** {selected_sector['prize']}\n💰 **Multiplier:** {multiplier:.1f}x\n\n{special_effect if special_effect else '🎉 Amazing luck!'}"
        elif multiplier >= 5:
            final_result = f"🎉{selected_sector['emoji']} {selected_sector['prize']}! {selected_sector['emoji']}🎉\n\n🎪 **Wheel stopped at:** {selected_sector['prize']}\n💰 **Multiplier:** {multiplier:.1f}x\n\n{special_effect if special_effect else '👏 Great spin!'}"
        else:
            final_result = f"🍀{selected_sector['emoji']} {selected_sector['prize']} {selected_sector['emoji']}🍀\n\n🎪 **Wheel stopped at:** {selected_sector['prize']}\n💰 **Multiplier:** {multiplier:.1f}x\n\n😊 Good result!"

        result = {
            'selected_sector': selected_sector,
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': multiplier >= 1.0,
            'bet_amount': bet_amount,
            'result_text': final_result,
            'special_effect': special_effect,
            'animation_frames': [
                "🎪 Fortune wheel preparing to spin... 🎪",
                "🎪 Wheel spinning faster... 🔄",
                f"🎪 Passing {animation_sectors[0]['emoji']} {animation_sectors[0]['prize']}...",
                f"🎪 Passing {animation_sectors[1]['emoji']} {animation_sectors[1]['prize']}...",
                f"🎪 Slowing down at {animation_sectors[2]['emoji']} {animation_sectors[2]['prize']}...",
                f"🎪 **STOPPED!** {selected_sector['emoji']} {selected_sector['prize']}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result
    
    @staticmethod
    def play_solo_dice(bet_amount: int, target: int = 4, user_id: int = None) -> dict:
        """Gelişmiş zar oyunu"""
        dice_result = random.randint(1, 6)
        dice_emojis = ["⚪", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        
        # Hedef belirleme sistemi
        if target < 1 or target > 6:
            target = 4  # Varsayılan hedef
        
        # Sonuç hesaplama
        if dice_result == target:
            multiplier = 6.0  # Tam isabet
            result_text = f"🎯 TAM İSABET! {dice_emojis[dice_result]} = {dice_result}"
            special_effect = "🎆🔥 PERFECT ROLL! 🔥🎆"
        elif abs(dice_result - target) == 1:
            multiplier = 2.5  # Yakın
            result_text = f"🎈 YAKLAŞTIN! {dice_emojis[dice_result]} = {dice_result}"
            special_effect = "⭐ Close enough! ⭐"
        elif dice_result == 6:
            multiplier = 2.0  # Altı gelirse bonus
            result_text = f"🎉 ALTI GELDİ! {dice_emojis[dice_result]} = {dice_result}"
            special_effect = "👑 Lucky six! 👑"
        else:
            multiplier = 0.2  # Teselli ödülü
            result_text = f"😔 {dice_emojis[dice_result]} = {dice_result}"
            special_effect = "🍀 Better luck next time!"
        
        win_amount = int(bet_amount * multiplier)
        
        # Enhanced dice result display
        if dice_result == target:
            final_result = f"🎯🔥 TAM İSABET! 🔥🎯\n\n🎲 **Rolled:** {dice_emojis[dice_result]} = {dice_result}\n🎯 **Target:** {target}\n🏆 **Perfect match!**\n\n💰 EXCELLENT PAYOUT!"
        elif abs(dice_result - target) == 1:
            final_result = f"🎈⭐ YAKLAŞTIN! ⭐🎈\n\n🎲 **Rolled:** {dice_emojis[dice_result]} = {dice_result}\n🎯 **Target:** {target}\n👏 **Close enough!**\n\n💰 Good payout!"
        elif dice_result == 6:
            final_result = f"🎉👑 ALTI GELDİ! 👑🎉\n\n🎲 **Rolled:** {dice_emojis[dice_result]} = {dice_result}\n🎯 **Target:** {target}\n🍀 **Lucky six bonus!**\n\n💰 Bonus payout!"
        else:
            final_result = f"😔 {dice_emojis[dice_result]} = {dice_result}\n\n🎲 **Rolled:** {dice_emojis[dice_result]} = {dice_result}\n🎯 **Target:** {target}\n💔 **Not close enough**\n\n🍀 Better luck next time!"

        result = {
            'dice_result': dice_result,
            'target': target,
            'dice_emoji': dice_emojis[dice_result],
            'multiplier': multiplier,
            'win_amount': win_amount,
            'won': multiplier > 0.5,
            'bet_amount': bet_amount,
            'result_text': final_result,
            'special_effect': special_effect,
            'animation_frames': [
                "🎲 Preparing dice roll...",
                f"🎯 **Target number:** {target}",
                "🎲 Rolling the dice... 🌪️",
                "🎲 Dice is spinning...",
                f"🎲 **Result:** {dice_emojis[dice_result]} = {dice_result}",
                final_result
            ]
        }
        
        # Admin bonus sistemi uygula
        if user_id:
            result = SoloGameEngine._apply_admin_bonus(result, user_id)
            
        return result