#!/usr/bin/env python3
"""
Group Performance Optimizer - High-performance group system for 100+ concurrent users
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class GroupStats:
    """Group performance statistics"""
    group_id: int
    member_count: int
    last_activity: float
    message_count: int
    active_users: int
    response_time_avg: float
    load_factor: float

class GroupPerformanceManager:
    """High-performance group management system"""

    def __init__(self):
        self.group_stats: Dict[int, GroupStats] = {}
        self.cached_members: Dict[int, Dict] = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.last_cleanup = time.time()
        self.cleanup_interval = 600  # 10 minutes

        # Performance optimizations
        self.batch_operations = defaultdict(list)
        self.batch_size = 50
        self.batch_timeout = 5.0

        # Rate limiting
        self.rate_limits: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        self.rate_limit_window = 60  # seconds

        logger.info("Group Performance Manager initialized")

    async def get_cached_member_count(self, bot, group_id: int) -> int:
        """Get cached member count or fetch if needed"""
        try:
            current_time = time.time()

            # Check if we have cached data
            if group_id in self.cached_members:
                cache_data = self.cached_members[group_id]
                if current_time - cache_data.get('timestamp', 0) < self.cache_ttl:
                    return cache_data.get('count', 0)

            # Fetch new data
            count = await bot.get_chat_member_count(group_id)
            self.cached_members[group_id] = {
                'count': count,
                'timestamp': current_time
            }

            # Update group stats
            if group_id not in self.group_stats:
                self.group_stats[group_id] = GroupStats(
                    group_id=group_id,
                    member_count=count,
                    last_activity=current_time,
                    message_count=0,
                    active_users=0,
                    response_time_avg=0.0,
                    load_factor=0.0
                )
            else:
                self.group_stats[group_id].member_count = count
                self.group_stats[group_id].last_activity = current_time

            return count

        except Exception as e:
            logger.error(f"Error getting cached member count for group {group_id}: {e}")
            return 0

    def is_rate_limited(self, user_id: int, group_id: int) -> bool:
        """Check if user is rate limited"""
        current_time = time.time()
        key = f"{user_id}:{group_id}"

        # Clean old entries
        rate_queue = self.rate_limits[key]
        while rate_queue and current_time - rate_queue[0] > self.rate_limit_window:
            rate_queue.popleft()

        # Check rate limit
        if len(rate_queue) >= 10:  # Max 10 actions per minute
            return True

        # Add current action
        rate_queue.append(current_time)
        return False

    def update_group_activity(self, group_id: int, user_id: int):
        """Update group activity statistics"""
        current_time = time.time()

        if group_id in self.group_stats:
            stats = self.group_stats[group_id]
            stats.last_activity = current_time
            stats.message_count += 1

            # Calculate load factor based on recent activity
            stats.load_factor = min(1.0, stats.message_count / 1000.0)

        # Cleanup old data periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_data()
            self.last_cleanup = current_time

    def _cleanup_old_data(self):
        """Clean up old cached data"""
        current_time = time.time()
        expired_groups = []

        for group_id, cache_data in self.cached_members.items():
            if current_time - cache_data.get('timestamp', 0) > self.cache_ttl * 2:
                expired_groups.append(group_id)

        for group_id in expired_groups:
            del self.cached_members[group_id]
            if group_id in self.group_stats:
                del self.group_stats[group_id]

        if expired_groups:
            logger.info(f"Cleaned up {len(expired_groups)} expired group caches")

    async def batch_operation(self, operation: str, data: Dict) -> Any:
        """Queue operations for batch processing"""
        self.batch_operations[operation].append(data)

        if len(self.batch_operations[operation]) >= self.batch_size:
            return await self._process_batch(operation)

        return None

    async def _process_batch(self, operation: str) -> List[Any]:
        """Process a batch of operations"""
        batch = self.batch_operations[operation][:self.batch_size]
        self.batch_operations[operation] = self.batch_operations[operation][self.batch_size:]

        results = []
        for item in batch:
            try:
                # Process each item in the batch
                result = await self._process_single_operation(operation, item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch item {item}: {e}")
                results.append(None)

        return results

    async def _process_single_operation(self, operation: str, data: Dict) -> Any:
        """Process a single operation"""
        if operation == "member_check":
            bot = data.get('bot')
            group_id = data.get('group_id')
            user_id = data.get('user_id')

            if bot and group_id and user_id:
                try:
                    member = await bot.get_chat_member(group_id, user_id)
                    return member.status in ['member', 'administrator', 'creator']
                except Exception as e:
                    logger.error(f"Error checking member {user_id} in group {group_id}: {e}")
                    return False

        return None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        current_time = time.time()
        total_groups = len(self.group_stats)
        active_groups = sum(1 for stats in self.group_stats.values()
                          if current_time - stats.last_activity < 300)

        return {
            "total_groups": total_groups,
            "active_groups": active_groups,
            "cached_groups": len(self.cached_members),
            "batch_queue_sizes": {op: len(queue) for op, queue in self.batch_operations.items()},
            "rate_limited_users": len([q for q in self.rate_limits.values() if len(q) >= 10]),
            "uptime": current_time - self.last_cleanup,
            "cache_hit_rate": self._calculate_cache_hit_rate()
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # Simple estimation based on cache utilization
        if not self.cached_members:
            return 0.0

        current_time = time.time()
        fresh_caches = sum(1 for cache in self.cached_members.values()
                          if current_time - cache.get('timestamp', 0) < self.cache_ttl)

        return fresh_caches / len(self.cached_members) if self.cached_members else 0.0

class OptimizedGroupHandler:
    """Optimized handler for group operations"""

    def __init__(self, performance_manager: GroupPerformanceManager):
        self.perf_manager = performance_manager
        self.logger = logger

    async def handle_group_message(self, update, context, handler_func: Callable):
        """Handle group messages with performance optimizations"""
        try:
            group_id = update.effective_chat.id
            user_id = update.effective_user.id

            # Check rate limiting
            if self.perf_manager.is_rate_limited(user_id, group_id):
                logger.warning(f"Rate limited user {user_id} in group {group_id}")
                return

            # Update activity
            self.perf_manager.update_group_activity(group_id, user_id)

            # Execute handler with performance monitoring
            start_time = time.time()
            result = await handler_func(update, context)
            end_time = time.time()

            # Update performance stats
            if group_id in self.perf_manager.group_stats:
                stats = self.perf_manager.group_stats[group_id]
                response_time = end_time - start_time
                stats.response_time_avg = (stats.response_time_avg + response_time) / 2

            return result

        except Exception as e:
            logger.error(f"Error in optimized group handler: {e}")
            return None

    async def check_member_optimized(self, bot, group_id: int, user_id: int) -> bool:
        """Optimized member check with caching and batching"""
        try:
            # Use batch operation for member checks
            result = await self.perf_manager.batch_operation("member_check", {
                'bot': bot,
                'group_id': group_id,
                'user_id': user_id
            })

            if result is not None:
                return result

            # Fallback to direct check
            member = await bot.get_chat_member(group_id, user_id)
            return member.status in ['member', 'administrator', 'creator']

        except Exception as e:
            logger.error(f"Optimized member check failed for {user_id} in {group_id}: {e}")
            return False

# Global instances
_performance_manager = None
_optimized_handler = None

def initialize_group_performance():
    """Initialize the group performance system"""
    global _performance_manager, _optimized_handler

    if _performance_manager is None:
        _performance_manager = GroupPerformanceManager()

    if _optimized_handler is None:
        _optimized_handler = OptimizedGroupHandler(_performance_manager)

    logger.info("Group performance optimization system initialized")
    return _performance_manager, _optimized_handler

def group_performance_manager():
    """Get the global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = GroupPerformanceManager()
    return _performance_manager

def optimized_group_handler():
    """Get the global optimized handler instance"""
    global _optimized_handler
    if _optimized_handler is None:
        _optimized_handler = OptimizedGroupHandler(group_performance_manager())
    return _optimized_handler

if __name__ == "__main__":
    # Test the performance system
    async def test_performance_system():
        manager, handler = initialize_group_performance()

        # Test performance stats
        stats = manager.get_performance_stats()
        print(f"Performance stats: {stats}")

        # Test rate limiting
        is_limited = manager.is_rate_limited(12345, -100123456789)
        print(f"Rate limited: {is_limited}")

        # Test activity update
        manager.update_group_activity(-100123456789, 12345)
        print("Activity updated")

    asyncio.run(test_performance_system())