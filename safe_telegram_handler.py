#!/usr/bin/env python3
"""
🛡️ Güvenli Telegram API Handler - 400 Bad Request Düzeltme Sistemi
"""

import asyncio
import logging
import time
import hashlib
from typing import Optional, Dict, Any
from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest, TimedOut, NetworkError, RetryAfter

try:
    from error_monitor import log_telegram_error
    ERROR_MONITORING = True
except ImportError:
    ERROR_MONITORING = False
    def log_telegram_error(error_type, error_message, context=""):
        pass

logger = logging.getLogger(__name__)

class SafeTelegramHandler:
    """Telegram API istekleri için güvenli işleyici"""
    
    def __init__(self):
        self.message_cache = {}  # Mesaj içerik cache'i
        self.last_edit_time = {}  # Son düzenleme zamanları
        self.rate_limit_tracker = {}  # Rate limit takibi
        self.MIN_EDIT_INTERVAL = 1.0  # Minimum düzenleme aralığı (saniye)
        self.MAX_MESSAGE_LENGTH = 4096  # Telegram max mesaj uzunluğu
        self.MAX_RETRIES = 5  # Increased retry attempts for better reliability
        
    def _get_message_hash(self, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None) -> str:
        """Mesaj içeriğinin hash'ini oluştur"""
        content = f"{text}_{str(reply_markup)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _should_skip_edit(self, query_id: str, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
        """Düzenlemeyi atlayıp atlamayacağını kontrol et"""
        current_hash = self._get_message_hash(text, reply_markup)
        
        # Aynı içerikse atla
        if query_id in self.message_cache and self.message_cache[query_id] == current_hash:
            return True
            
        # Rate limit kontrolü
        current_time = time.time()
        if query_id in self.last_edit_time:
            time_diff = current_time - self.last_edit_time[query_id]
            if time_diff < self.MIN_EDIT_INTERVAL:
                logger.debug(f"Rate limit: Waiting {self.MIN_EDIT_INTERVAL - time_diff:.2f}s")
                return True
                
        return False
    
    def _clean_message_text(self, text: str) -> str:
        """Mesaj metnini temizle ve doğrula"""
        if not text:
            return "⚠️ Boş mesaj"

        # Uzunluk kontrolü
        if len(text) > self.MAX_MESSAGE_LENGTH:
            text = text[:self.MAX_MESSAGE_LENGTH - 10] + "... [kesildi]"

        # Problemli karakterleri temizle
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\u2060', '')  # Word joiner

        # Markdown validation and fixing
        text = self._fix_markdown_entities(text)

        return text.strip()

    def _fix_markdown_entities(self, text: str) -> str:
        """Fix malformed Markdown entities"""
        # Fix triple backticks first (as they can contain single backticks)
        triple_backtick_count = text.count('```')
        if triple_backtick_count % 2 != 0:
            last_triple = text.rfind('```')
            if last_triple != -1:
                text = text[:last_triple] + text[last_triple + 3:]

        # Fix single backticks (`code`) - but don't count those inside triple backticks
        # Simple approach: count remaining single backticks after triple fix
        single_backtick_count = text.count('`') - text.count('```') * 3
        if single_backtick_count % 2 != 0:
            last_backtick = text.rfind('`')
            if last_backtick != -1:
                # Make sure it's not part of ```
                if not (last_backtick >= 2 and text[last_backtick-2:last_backtick+1] == '```'):
                    text = text[:last_backtick] + text[last_backtick + 1:]

        # Fix bold (*text*)
        asterisk_count = text.count('*')
        if asterisk_count % 2 != 0:
            # Odd number of asterisks - remove the last unpaired one
            last_asterisk = text.rfind('*')
            if last_asterisk != -1:
                text = text[:last_asterisk] + text[last_asterisk + 1:]

        # Fix italic (_text_)
        underscore_count = text.count('_')
        if underscore_count % 2 != 0:
            # Odd number of underscores - remove the last unpaired one
            last_underscore = text.rfind('_')
            if last_underscore != -1:
                text = text[:last_underscore] + text[last_underscore + 1:]

        return text

    def _strip_all_markdown(self, text: str) -> str:
        """Remove all markdown characters as a last resort"""
        # Remove all markdown formatting characters
        markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '~']
        for char in markdown_chars:
            text = text.replace(char, '')

        # Remove triple backticks
        text = text.replace('```', '')

        return text.strip()

    async def safe_answer_callback_query(self, query, text: str = "", show_alert: bool = False) -> bool:
        """Güvenli callback query cevaplama"""
        try:
            await query.answer(text[:200], show_alert=show_alert)  # Telegram limit: 200 karakter
            return True
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["too old", "invalid", "expired", "timeout"]):
                logger.debug(f"Callback query expired: {e}")
                log_telegram_error("callback_expired", str(e), "answer_callback")
                return False
            else:
                logger.error(f"Callback answer error: {e}")
                log_telegram_error("callback_error", str(e), "answer_callback")
                return False
    
    async def safe_edit_message_text(
        self, 
        query, 
        text: str, 
        reply_markup: Optional[InlineKeyboardMarkup] = None, 
        parse_mode: Optional[str] = 'Markdown'
    ) -> bool:
        """Güvenli mesaj düzenleme"""
        
        query_id = f"{query.message.chat_id}_{query.message.message_id}"
        
        # Önceden kontrol et
        if self._should_skip_edit(query_id, text, reply_markup):
            return True
            
        # Mesajı temizle
        clean_text = self._clean_message_text(text)
        
        # Retry mekanizması
        for attempt in range(self.MAX_RETRIES):
            try:
                await query.edit_message_text(
                    text=clean_text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                
                # Başarılı düzenleme
                self.message_cache[query_id] = self._get_message_hash(clean_text, reply_markup)
                self.last_edit_time[query_id] = time.time()
                return True
                
            except BadRequest as e:
                error_str = str(e).lower()
                
                if "message is not modified" in error_str:
                    # Mesaj değişmemiş - normal durum, cache'i güncelle
                    self.message_cache[query_id] = self._get_message_hash(clean_text, reply_markup)
                    self.last_edit_time[query_id] = time.time()
                    logger.debug(f"Message not modified for {query_id} - content unchanged")
                    return True
                    
                elif "query is too old" in error_str or "invalid query id" in error_str:
                    # Süresi dolmuş query
                    logger.debug(f"Query expired: {e}")
                    log_telegram_error("query_expired", str(e), "edit_message")
                    return False
                    
                elif "message to edit not found" in error_str:
                    # Mesaj bulunamadı
                    logger.warning(f"Message not found: {e}")
                    log_telegram_error("message_not_found", str(e), "edit_message")
                    return False
                    
                elif "message text is empty" in error_str:
                    # Boş mesaj
                    log_telegram_error("empty_message", str(e), "edit_message")
                    clean_text = "⚠️ İçerik yükleniyor..."
                    continue
                    
                elif "can't parse entities" in error_str:
                    # Markdown parse hatası - disable parse_mode and clean text more aggressively
                    log_telegram_error("parse_error", str(e), "edit_message")
                    parse_mode = None
                    # Remove all markdown characters as fallback
                    clean_text = self._strip_all_markdown(clean_text)
                    continue
                    
                elif "message is too long" in error_str:
                    # Çok uzun mesaj
                    log_telegram_error("message_too_long", str(e), "edit_message")
                    clean_text = clean_text[:3000] + "...\n\n📝 Mesaj kısaltıldı."
                    continue
                    
                else:
                    logger.error(f"BadRequest error (attempt {attempt + 1}): {e}")
                    log_telegram_error("bad_request", str(e), f"edit_message_attempt_{attempt + 1}")
                    if attempt == self.MAX_RETRIES - 1:
                        return False
                    await asyncio.sleep(min(1.5 * (attempt + 1), 8.0))  # Improved backoff with max 8s
                    
            except RetryAfter as e:
                # Rate limit
                retry_after = e.retry_after
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                
            except (TimedOut, NetworkError) as e:
                # Ağ hataları
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    return False
                await asyncio.sleep(min(3.0 * (attempt + 1), 15.0))  # Longer timeout handling with max 15s
                
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    return False
                await asyncio.sleep(0.5 * (attempt + 1))
        
        return False
    
    async def safe_reply_message(
        self, 
        message, 
        text: str, 
        reply_markup: Optional[InlineKeyboardMarkup] = None, 
        parse_mode: Optional[str] = 'Markdown'
    ) -> Optional[object]:
        """Güvenli mesaj cevaplama"""
        
        clean_text = self._clean_message_text(text)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return await message.reply_text(
                    text=clean_text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                
            except BadRequest as e:
                error_str = str(e).lower()
                
                if "can't parse entities" in error_str:
                    log_telegram_error("parse_error", str(e), "reply_message")
                    parse_mode = None
                    # Remove all markdown characters as fallback
                    clean_text = self._strip_all_markdown(clean_text)
                    continue
                    
                elif "message text is empty" in error_str:
                    clean_text = "⚠️ İçerik yükleniyor..."
                    continue
                    
                elif "message is too long" in error_str:
                    clean_text = clean_text[:3000] + "...\n\n📝 Mesaj kısaltıldı."
                    continue
                    
                else:
                    logger.error(f"Reply BadRequest (attempt {attempt + 1}): {e}")
                    if attempt == self.MAX_RETRIES - 1:
                        return None
                    await asyncio.sleep(min(1.5 * (attempt + 1), 8.0))  # Improved backoff with max 8s
                    
            except RetryAfter as e:
                retry_after = e.retry_after
                logger.warning(f"Reply rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                
            except (TimedOut, NetworkError) as e:
                logger.warning(f"Reply network error (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    return None
                await asyncio.sleep(min(3.0 * (attempt + 1), 15.0))  # Longer timeout handling with max 15s
                
            except Exception as e:
                logger.error(f"Reply unexpected error (attempt {attempt + 1}): {e}")
                if attempt == self.MAX_RETRIES - 1:
                    return None
                await asyncio.sleep(0.5 * (attempt + 1))
        
        return None
    
    def cleanup_old_cache(self, max_age: int = 3600):
        """Eski cache'leri temizle"""
        current_time = time.time()
        
        # Eski message cache'leri temizle
        old_keys = []
        for key, timestamp in self.last_edit_time.items():
            if current_time - timestamp > max_age:
                old_keys.append(key)
                
        for key in old_keys:
            self.message_cache.pop(key, None)
            self.last_edit_time.pop(key, None)
            
        if old_keys:
            logger.debug(f"Cleaned {len(old_keys)} old cache entries")

# Global instance
safe_handler = SafeTelegramHandler()

# Kolaylık fonksiyonları
async def safe_edit_message(query, text: str, reply_markup=None, parse_mode='Markdown') -> bool:
    """Kolay kullanım için wrapper fonksiyon"""
    return await safe_handler.safe_edit_message_text(query, text, reply_markup, parse_mode)

async def safe_answer_query(query, text: str = "", show_alert: bool = False) -> bool:
    """Kolay kullanım için wrapper fonksiyon"""
    return await safe_handler.safe_answer_callback_query(query, text, show_alert)

async def safe_reply(message, text: str, reply_markup=None, parse_mode='Markdown'):
    """Kolay kullanım için wrapper fonksiyon"""
    return await safe_handler.safe_reply_message(message, text, reply_markup, parse_mode)

def cleanup_telegram_cache():
    """Cache temizlik fonksiyonu"""
    safe_handler.cleanup_old_cache()