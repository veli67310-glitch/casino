#!/usr/bin/env python3
"""
🎮 Casino Bot Oyun Motoru
"""

import random
import time

class GameEngine:
    """Eğlence odaklı oyun motoru"""
    
    @staticmethod
    def generate_game_id() -> str:
        return f"GAME_{int(time.time())}_{random.randint(1000, 9999)}"
    
    @staticmethod
    def play_duel_coinflip(player1_choice: str, player2_choice: str) -> dict:
        """İki oyuncu coin flip düellosu"""
        result = random.choice(['heads', 'tails'])
        
        p1_wins = (player1_choice == result)
        p2_wins = (player2_choice == result)
        
        if p1_wins and not p2_wins:
            winner = 1
        elif p2_wins and not p1_wins:
            winner = 2
        else:
            winner = 0  # Berabere
        
        return {
            'result': result,
            'winner': winner,
            'player1_correct': p1_wins,
            'player2_correct': p2_wins
        }
    
    @staticmethod
    def play_duel_dice() -> dict:
        """İki oyuncu zar savaşı"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        if dice1 > dice2:
            winner = 1
        elif dice2 > dice1:
            winner = 2
        else:
            winner = 0
        
        return {
            'dice1': dice1,
            'dice2': dice2,
            'winner': winner
        }
    
    @staticmethod
    def play_duel_dice_with_type(dice_type: str) -> dict:
        """Belirli zar türü ile düello"""
        # Dice type to emoji mapping
        dice_emojis = {
            'standard': '🎲',
            'basketball': '🏀', 
            'football': '⚽',
            'slot_machine': '🎰',
            'bowling': '🎳',
            'darts': '🎯'
        }
        
        # Get dice values (1-6 for all types except slot which is 1-64)
        if dice_type == 'slot_machine':
            dice1 = random.randint(1, 64)
            dice2 = random.randint(1, 64)
        else:
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
        
        if dice1 > dice2:
            winner = 1
        elif dice2 > dice1:
            winner = 2
        else:
            winner = 0
        
        return {
            'dice1': dice1,
            'dice2': dice2,
            'winner': winner,
            'dice_type': dice_type,
            'emoji': dice_emojis.get(dice_type, '🎲')
        }

    @staticmethod
    def play_duel_rockpaper(p1_choice: str, p2_choice: str) -> dict:
        """Rock-Paper-Scissors düellosu"""
        rules = {'rock': 'scissors', 'scissors': 'paper', 'paper': 'rock'}
        if p1_choice == p2_choice:
            return {'winner': 0}
        elif rules[p1_choice] == p2_choice:
            return {'winner': 1}
        else:
            return {'winner': 2}
    
    @staticmethod
    def calculate_xp_reward(bet_amount: int, won: bool) -> int:
        """XP ödül hesaplama"""
        base_xp = bet_amount // 10
        if won:
            return base_xp * 2
        return base_xp

    @staticmethod
    def play_tournament_round(players: list, game_type: str) -> list:
        """Turnuva round simülasyonu"""
        scores = {p: random.randint(1, 100) for p in players}
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winners = [p[0] for p in sorted_scores[:len(players)//2]]
        return winners