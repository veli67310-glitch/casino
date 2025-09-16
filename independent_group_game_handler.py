#!/usr/bin/env python3
"""
🎮 Independent Group Game Handler
Her kullanıcı kendi istediği oyunu bağımsız oynayabilir - grup kilidi yok
"""

import asyncio
import time
import random
import logging
from typing import Dict, Set, Optional
from collections import defaultdict
from safe_telegram_handler import safe_edit_message
from game_error_handler import safe_game_edit, safe_animation, robust_game_operation

logger = logging.getLogger(__name__)

class IndependentGroupGameManager:
    """Her kullanıcının bağımsız oyun oynayabilmesi için yönetici"""
    
    def __init__(self):
        # Active user sessions - kullanıcı başına aktif oyunları takip et
        self.active_user_sessions = {}  # user_id: {'game_type', 'start_time', 'chat_id', 'query_message_id'}
        
        # Group activity tracking
        self.group_activities = defaultdict(list)  # chat_id: [recent_activities]
        
        # Rate limiting per user (not per group!)
        self.user_rate_limits = defaultdict(list)  # user_id: [timestamps]
        self.RATE_LIMIT_WINDOW = 5  # 5 saniye
        self.MAX_GAMES_PER_WINDOW = 2  # 5 saniyede max 2 oyun
        
        # Performance tracking
        self.stats = {
            'total_independent_games': 0,
            'concurrent_users_peak': 0,
            'games_per_minute': defaultdict(int)
        }
    
    def can_user_start_game(self, user_id: int, chat_id: int) -> tuple[bool, str]:
        """Kullanıcı oyun başlatabilir mi?"""
        current_time = time.time()
        
        # Rate limiting kontrolü
        user_history = self.user_rate_limits[user_id]
        # Eski kayıtları temizle
        user_history[:] = [ts for ts in user_history if current_time - ts < self.RATE_LIMIT_WINDOW]
        
        if len(user_history) >= self.MAX_GAMES_PER_WINDOW:
            return False, f"⏱️ Çok hızlı oynuyorsun! {self.RATE_LIMIT_WINDOW} saniye bekle."
        
        # Kullanıcının aktif oyunu var mı?
        if user_id in self.active_user_sessions:
            session = self.active_user_sessions[user_id]
            game_duration = current_time - session['start_time']
            if game_duration < 1.0:  # 1 saniyeden az süre geçtiyse
                return False, "🎮 Önceki oyunun bitmesini bekle!"
        
        return True, ""
    
    def start_user_game(self, user_id: int, chat_id: int, game_type: str, query_message_id: int):
        """Kullanıcı oyununu başlat"""
        current_time = time.time()
        
        # Rate limit kaydını ekle
        self.user_rate_limits[user_id].append(current_time)
        
        # Session kaydını oluştur
        self.active_user_sessions[user_id] = {
            'game_type': game_type,
            'start_time': current_time,
            'chat_id': chat_id,
            'query_message_id': query_message_id
        }
        
        # Group activity ekle
        activity = {
            'user_id': user_id,
            'game_type': game_type,
            'timestamp': current_time
        }
        self.group_activities[chat_id].append(activity)
        
        # Son 10 aktiviteyi sakla
        if len(self.group_activities[chat_id]) > 10:
            self.group_activities[chat_id] = self.group_activities[chat_id][-10:]
        
        # Stats güncelle
        self.stats['total_independent_games'] += 1
        current_minute = int(current_time / 60)
        self.stats['games_per_minute'][current_minute] += 1
        
        # Peak concurrent users
        concurrent_users = len(self.active_user_sessions)
        self.stats['concurrent_users_peak'] = max(
            self.stats['concurrent_users_peak'], 
            concurrent_users
        )
        
        logger.info(f"User {user_id} started {game_type} in group {chat_id}")
    
    def end_user_game(self, user_id: int):
        """Kullanıcı oyununu bitir"""
        if user_id in self.active_user_sessions:
            session = self.active_user_sessions[user_id]
            duration = time.time() - session['start_time']
            del self.active_user_sessions[user_id]
            
            logger.info(f"User {user_id} finished {session['game_type']} (duration: {duration:.2f}s)")
    
    def get_group_status(self, chat_id: int) -> dict:
        """Grup durumunu getir"""
        current_players = [
            session for session in self.active_user_sessions.values()
            if session['chat_id'] == chat_id
        ]
        
        recent_activities = self.group_activities[chat_id]
        
        return {
            'active_players': len(current_players),
            'current_games': [p['game_type'] for p in current_players],
            'recent_activities': len(recent_activities),
            'last_activity': max([a['timestamp'] for a in recent_activities]) if recent_activities else 0
        }
    
    def get_global_stats(self) -> dict:
        """Global istatistikleri getir"""
        current_time = time.time()
        
        # Aktif session'ları temizle (5 dakikadan eski)
        expired_users = [
            user_id for user_id, session in self.active_user_sessions.items()
            if current_time - session['start_time'] > 300
        ]
        for user_id in expired_users:
            del self.active_user_sessions[user_id]
        
        return {
            'total_games': self.stats['total_independent_games'],
            'concurrent_users': len(self.active_user_sessions),
            'peak_concurrent': self.stats['concurrent_users_peak'],
            'active_groups': len(set(s['chat_id'] for s in self.active_user_sessions.values())),
            'games_last_minute': self.stats['games_per_minute'][int(current_time / 60)]
        }

# Global manager instance
independent_game_manager = IndependentGroupGameManager()

@robust_game_operation("Grup oyunu tamamlandı!")
async def handle_independent_group_game(query, user, casino_bot, game_type: str, bet_amount: int):
    """Bağımsız grup oyunu handler - kilit sistemi YOK"""
    try:
        user_id = user['user_id']
        chat_id = query.message.chat.id
        message_id = query.message.message_id
        
        # Kullanıcı oyun başlatabilir mi kontrol et
        can_play, reason = independent_game_manager.can_user_start_game(user_id, chat_id)
        if not can_play:
            await safe_game_edit(query, 
                f"⚠️ **Oyun Başlatılamadı**\n\n{reason}",
                reply_markup=casino_bot.create_keyboard([
                    [("🔄 Tekrar Dene", f"group_{game_type}_{bet_amount}")],
                    [("🎮 Oyun Menüsü", "games")]
                ])
            )
            return
        
        # Bakiye kontrolü
        if user['fun_coins'] < bet_amount:
            await safe_game_edit(query,
                f"💸 **Yetersiz Bakiye!**\n\n"
                f"💰 Mevcut: {user['fun_coins']:,} FC\n"
                f"🎯 Gerekli: {bet_amount:,} FC\n\n"
                f"🎁 Günlük bonus alarak bakiye artırabilirsin!",
                reply_markup=casino_bot.create_keyboard([
                    [("🎁 Günlük Bonus", "daily_bonus"), ("💳 Yatır", "payment")],
                    [("🔙 Geri", "games")]
                ]),
                parse_mode='Markdown'
            )
            return
        
        # Oyunu başlat
        independent_game_manager.start_user_game(user_id, chat_id, game_type, message_id)
        
        # Bahisi düş
        with casino_bot.db.get_connection() as conn:
            conn.execute(
                "UPDATE users SET fun_coins = fun_coins - ? WHERE user_id = ?",
                (bet_amount, user_id)
            )
            conn.commit()
        
        # Oyun oyna
        result = await play_independent_game(query, user, casino_bot, game_type, bet_amount)
        
        if result:
            # Kazancı ekle
            if result['won'] and result['win_amount'] > 0:
                with casino_bot.db.get_connection() as conn:
                    conn.execute(
                        "UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?",
                        (result['win_amount'], user_id)
                    )
                    conn.commit()
            
            # İstatistikleri güncelle
            casino_bot.update_user_stats(user_id, bet_amount, result['win_amount'], result['won'])
        
        # Oyunu bitir
        independent_game_manager.end_user_game(user_id)
        
        logger.info(f"Independent game completed: user={user_id}, game={game_type}, won={result['won'] if result else False}")
        
    except Exception as e:
        logger.error(f"Independent group game error: {e}")
        # Oyunu bitir (hata durumunda)
        independent_game_manager.end_user_game(user['user_id'])
        raise

async def play_independent_game(query, user, casino_bot, game_type: str, bet_amount: int) -> Optional[dict]:
    """Bağımsız oyunu oyna"""
    try:
        # Solo game engine'i al
        from solo_games import SoloGameEngine
        if not hasattr(casino_bot, 'solo_engine'):
            casino_bot.solo_engine = SoloGameEngine()
        
        engine = casino_bot.solo_engine
        
        # Oyun türüne göre oyna
        result = None
        game_display_name = ""
        
        if game_type == "solo_slots":
            # Slots animasyonu
            await safe_game_edit(query, 
                "🎰 **SLOT MAKİNESİ** 🎰\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n\n"
                "🎰 Makaralar döndürülüyor...\n"
                "🔄 ▓▓▓ ▓▓▓ ▓▓▓ 🔄\n\n"
                "⏳ Lütfen bekleyin...",
                parse_mode='Markdown'
            )
            await asyncio.sleep(4.5)

            result = engine.play_solo_slots(bet_amount)
            game_display_name = "🎰 Slot Makinesi"
            
        elif game_type == "solo_roulette":
            await safe_game_edit(query, 
                "🎡 **RULET** 🎡\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n"
                f"🔴 Renk: Kırmızı\n\n"
                "🎡 Çark döndürülüyor...\n"
                "⚪ ⚫ 🔴 ⚫ ⚪ 🔴 ⚫\n\n"
                "⏳ Top durmak üzere...",
                parse_mode='Markdown'
            )
            await asyncio.sleep(5.0)

            result = engine.play_solo_roulette(bet_amount, "color", "red")
            game_display_name = "🎡 Rulet"
            
        elif game_type == "solo_blackjack":
            await safe_game_edit(query, 
                "🃏 **BLACKJACK** 🃏\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n\n"
                "🃏 Kartlar dağıtılıyor...\n"
                "📚 [?] [?] | [?] [?]\n\n"
                "⏳ Krupye oynuyor...",
                parse_mode='Markdown'
            )
            await asyncio.sleep(4.2)

            result = engine.play_solo_blackjack(bet_amount)
            game_display_name = "🃏 Blackjack"
            
        elif game_type == "solo_crash":
            await safe_game_edit(query, 
                "🚀 **CRASH** 🚀\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n"
                f"🎯 Hedef Çarpan: x2.00\n\n"
                "🚀 Roket fırlatılıyor...\n"
                "📈 1.00x... 1.50x... 1.75x...\n\n"
                "⚠️ Ne zaman patlar?",
                parse_mode='Markdown'
            )
            await asyncio.sleep(4.8)

            result = engine.play_solo_crash(bet_amount, 2.0)
            game_display_name = "🚀 Crash"
            
        elif game_type == "solo_dice" or game_type.startswith("solo_dice_"):
            # Determine dice type
            if "_" in game_type and len(game_type.split("_")) > 2:
                dice_subtype = game_type.split("_")[-1]  # e.g., "classic" from "solo_dice_classic"
            else:
                dice_subtype = "classic"
            
            # Dice configurations
            dice_config = {
                'classic': {'emoji': '🎲', 'name': 'Klasik Zar', 'min': 1, 'max': 6},
                'darts': {'emoji': '🎯', 'name': 'Dart', 'min': 1, 'max': 6},
                'basketball': {'emoji': '🏀', 'name': 'Basketbol', 'min': 1, 'max': 5},
                'football': {'emoji': '⚽', 'name': 'Futbol', 'min': 1, 'max': 5},
                'bowling': {'emoji': '🎳', 'name': 'Bowling', 'min': 1, 'max': 6},
                'slot_machine': {'emoji': '🎰', 'name': 'Slot Dice', 'min': 1, 'max': 64}
            }
            
            config = dice_config.get(dice_subtype, dice_config['classic'])
            dice_emoji = config['emoji']
            dice_name = config['name']
            
            # Show animation
            await safe_game_edit(query, 
                f"{dice_emoji} **{dice_name}** {dice_emoji}\n\n"
                f"🐻 **Bahis:** {bet_amount:,} 🐻\n"
                f"🎯 **{dice_name} atılıyor...**\n\n"
                f"⏳ Lütfen bekleyin...",
                parse_mode='Markdown'
            )
            
            # Send actual Telegram dice with animation
            try:
                dice_message = await query.message.reply_dice(emoji=dice_emoji)
                dice_value = dice_message.dice.value
                
                # Wait for dice animation to complete - UZATILDI
                await asyncio.sleep(6)

                # Delete dice message after animation
                try:
                    await dice_message.delete()
                except:
                    pass
                    
            except Exception as e:
                logger.warning(f"Failed to send Telegram dice: {e}")
                # Fallback to random value
                dice_value = random.randint(config['min'], config['max'])
                await asyncio.sleep(4)  # Still show some delay - UZATILDI
            
            # Calculate payout based on dice type and value
            win_amount = 0
            
            if dice_subtype == 'classic':
                if dice_value == 6:
                    win_amount = bet_amount * 6
                elif dice_value >= 4:
                    win_amount = bet_amount * 2
                elif dice_value == 3:
                    win_amount = bet_amount
                    
            elif dice_subtype == 'darts':
                if dice_value == 6:
                    win_amount = bet_amount * 10
                elif dice_value >= 4:
                    win_amount = bet_amount * 3
                elif dice_value >= 2:
                    win_amount = bet_amount
                    
            elif dice_subtype in ['basketball', 'football']:
                if dice_value >= 4:
                    win_amount = bet_amount * 5
                elif dice_value >= 2:
                    win_amount = bet_amount * 2
                    
            elif dice_subtype == 'bowling':
                if dice_value == 6:
                    win_amount = bet_amount * 6
                elif dice_value >= 4:
                    win_amount = bet_amount * 3
                elif dice_value >= 2:
                    win_amount = bet_amount
                    
            elif dice_subtype == 'slot_machine':
                if dice_value >= 50:
                    win_amount = bet_amount * 10
                elif dice_value >= 30:
                    win_amount = bet_amount * 5
                elif dice_value >= 15:
                    win_amount = bet_amount * 2
            
            won = win_amount > 0
            
            result = {
                'won': won,
                'win_amount': win_amount,
                'dice_value': dice_value,
                'dice_type': dice_subtype,
                'multiplier': win_amount / bet_amount if bet_amount > 0 and won else 0
            }
            
            game_display_name = dice_name
            
        elif game_type == "solo_baccarat":
            await safe_game_edit(query, 
                "🃏 **BACCARAT** 🃏\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n"
                f"👤 Bahis: Player\n\n"
                "🃏 Kartlar dağıtılıyor...\n"
                "👤 [?] [?] vs 🏦 [?] [?]\n\n"
                "⏳ Kim 9'a yakın?",
                parse_mode='Markdown'
            )
            await asyncio.sleep(4.0)
            
            result = engine.play_solo_baccarat(bet_amount, "player")
            game_display_name = "🃏 Baccarat"
            
        elif game_type == "solo_mines":
            await safe_game_edit(query, 
                "⛏️ **MINES** ⛏️\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n"
                f"💣 Mayın Sayısı: 3\n\n"
                "⛏️ Alan tarıyor...\n"
                "🟩 🟩 🟩\n🟩 ❓ 🟩\n🟩 🟩 🟩\n\n"
                "⚠️ Mayına çarpmadan kaç tane?",
                parse_mode='Markdown'
            )
            await asyncio.sleep(4.5)
            
            result = engine.play_solo_mines(bet_amount, 3, 3)
            game_display_name = "⛏️ Mines"
            
        elif game_type == "solo_keno":
            await safe_game_edit(query, 
                "🎯 **KENO** 🎯\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n\n"
                "🎯 Sayılar seçiliyor...\n"
                "🔢 [?] [?] [?] [?] [?]\n\n"
                "⏳ Çekiliş yapılıyor...",
                parse_mode='Markdown'
            )
            await asyncio.sleep(4.3)
            
            result = engine.play_solo_keno(bet_amount, None)
            game_display_name = "🎯 Keno"
            
        elif game_type == "rock_paper_scissors":
            await safe_game_edit(query, 
                "✂️ **TAŞ-KAĞIT-MAKAS** ✂️\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n\n"
                "✂️ Seçim yapılıyor...\n"
                "🪨 📄 ✂️\n\n"
                "⏳ Rakiple karşılaşıyor...",
                parse_mode='Markdown'
            )
            await asyncio.sleep(3.8)
            
            result = engine.play_rock_paper_scissors(bet_amount, None)
            game_display_name = "✂️ Taş-Kağıt-Makas"
            
        elif game_type == "number_guess":
            await safe_game_edit(query, 
                "🔢 **SAYI TAHMİN** 🔢\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n\n"
                "🔢 Sayı tahmin ediliyor...\n"
                "❓ (1-100 arası)\n\n"
                "⏳ Şansına güven!",
                parse_mode='Markdown'
            )
            await asyncio.sleep(3.5)
            
            result = engine.play_number_guess(bet_amount, None)
            game_display_name = "🔢 Sayı Tahmin"
            
        elif game_type == "lucky_wheel":
            await safe_game_edit(query, 
                "🎪 **ŞANS ÇARKI** 🎪\n\n"
                f"💰 Bahis: {bet_amount:,} 🐻\n\n"
                "🎪 Çark döndürülüyor...\n"
                "🔄 💰 🎁 💎 🍀 💰 🎁 💎 🔄\n\n"
                "⏳ Çark yavaşlıyor...",
                parse_mode='Markdown'
            )
            await asyncio.sleep(5.2)
            
            result = engine.play_lucky_wheel(bet_amount)
            game_display_name = "🎪 Şans Çarkı"
            
        else:
            # Varsayılan oyun
            await safe_game_edit(query, f"🎮 **{game_type.upper()}**\n\n🎮 Oyun başlatılıyor...", parse_mode='Markdown')
            await asyncio.sleep(3.0)
            
            result = {'won': False, 'win_amount': 0, 'message': 'Oyun tamamlandı'}
            game_display_name = game_type.replace('_', ' ').title()
        
        if not result:
            await safe_game_edit(query, "❌ Oyun hatası oluştu!")
            return None
        
        # Sonuç mesajı hazırla
        username = user['username'] if 'username' in user else 'Oyuncu'
        
        if result['won']:
            net_profit = result['win_amount'] - bet_amount
            result_text = f"🎉 **{username} Kazandı!** 🎉\n\n"
            result_text += f"🎮 Oyun: {game_display_name}\n"
            
            # Dice oyunları için sonucu göster
            if 'dice_value' in result:
                dice_emoji = {'classic': '🎲', 'darts': '🎯', 'basketball': '🏀', 'football': '⚽', 'bowling': '🎳', 'slot_machine': '🎰'}.get(result.get('dice_type', 'classic'), '🎲')
                result_text += f"{dice_emoji} **Sonuç:** {result['dice_value']}\n"
            
            result_text += f"💰 Bahis: {bet_amount:,} 🐻\n"
            result_text += f"🏆 Kazanç: {result['win_amount']:,} 🐻\n"
            result_text += f"📈 Net Kar: +{net_profit:,} 🐻"
            
            if result.get('multiplier', 1) > 1:
                result_text += f"\n⚡ Çarpan: x{result['multiplier']:.1f}"
        else:
            result_text = f"💔 **{username} Kaybetti** 💔\n\n"
            result_text += f"🎮 Oyun: {game_display_name}\n"
            
            # Dice oyunları için sonucu göster
            if 'dice_value' in result:
                dice_emoji = {'classic': '🎲', 'darts': '🎯', 'basketball': '🏀', 'football': '⚽', 'bowling': '🎳', 'slot_machine': '🎰'}.get(result.get('dice_type', 'classic'), '🎲')
                result_text += f"{dice_emoji} **Sonuç:** {result['dice_value']}\n"
            
            result_text += f"💸 Kayıp: {bet_amount:,} 🐻\n"
            result_text += f"🍀 Bir sonraki sefer şansın yaver gider!"
        
        # Oyun sonucu butonları
        buttons = [
            [("🔄 Tekrar Oyna", f"group_{game_type}_{bet_amount}"), ("🎮 Başka Oyun", "games")],
            [("📊 Profil", "profile")]
        ]
        keyboard = casino_bot.create_keyboard(buttons)
        
        await safe_game_edit(query, result_text, reply_markup=keyboard, parse_mode='Markdown')
        
        return result
        
    except Exception as e:
        logger.error(f"Play independent game error: {e}")
        await safe_game_edit(query, 
            f"⚠️ **Oyun Hatası**\n\nBir hata oluştu, bahisin iade edildi.",
            reply_markup=casino_bot.create_keyboard([
                [("🔄 Tekrar Dene", f"group_{game_type}_{bet_amount}")],
                [("🎮 Oyunlar", "games")]
            ])
        )
        
        # Bahisi iade et
        try:
            with casino_bot.db.get_connection() as conn:
                conn.execute(
                    "UPDATE users SET fun_coins = fun_coins + ? WHERE user_id = ?",
                    (bet_amount, user['user_id'])
                )
                conn.commit()
        except:
            pass
        
        return None

def get_group_activity_summary(chat_id: int) -> str:
    """Grup aktivite özetini getir"""
    status = independent_game_manager.get_group_status(chat_id)
    
    if status['active_players'] == 0:
        return "📭 Şu anda kimse oyun oynamıyor"
    
    summary = f"🎮 **Aktif Oyuncular:** {status['active_players']}\n"
    
    # Oyun türlerini say
    game_counts = {}
    for game in status['current_games']:
        game_counts[game] = game_counts.get(game, 0) + 1
    
    for game, count in game_counts.items():
        game_emoji = {
            'solo_slots': '🎰',
            'solo_roulette': '🎡', 
            'solo_blackjack': '🃏',
            'solo_crash': '🚀',
            'solo_dice': '🎲'
        }.get(game, '🎮')
        summary += f"{game_emoji} {game.replace('solo_', '').title()}: {count}\n"
    
    return summary

def get_independent_game_manager():
    """Global manager instance'ını getir"""
    return independent_game_manager