#!/usr/bin/env python3
"""
Group Performance Monitor - Real-time monitoring for group performance optimization
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
import gc
import psutil
import os

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Container for performance metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)
        self.memory_usage = deque(maxlen=100)
        self.cpu_usage = deque(maxlen=100)
        self.active_connections = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def add_response_time(self, response_time: float):
        """Add a response time measurement"""
        self.response_times.append(response_time)

    def add_memory_usage(self, usage: float):
        """Add memory usage measurement"""
        self.memory_usage.append(usage)

    def add_cpu_usage(self, usage: float):
        """Add CPU usage measurement"""
        self.cpu_usage.append(usage)

    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_average_memory_usage(self) -> float:
        """Get average memory usage"""
        if not self.memory_usage:
            return 0.0
        return sum(self.memory_usage) / len(self.memory_usage)

    def get_average_cpu_usage(self) -> float:
        """Get average CPU usage"""
        if not self.cpu_usage:
            return 0.0
        return sum(self.cpu_usage) / len(self.cpu_usage)

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.start_time

class GroupPerformanceMonitor:
    """Real-time performance monitoring for group operations"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.group_metrics: Dict[int, PerformanceMetrics] = {}
        self.alerts_enabled = True
        self.monitoring_active = False
        self.monitor_thread = None
        self.alert_thresholds = {
            'response_time_max': 2.0,  # seconds
            'memory_usage_max': 80.0,  # percentage
            'cpu_usage_max': 80.0,     # percentage
            'error_rate_max': 5.0,     # percentage
            'cache_hit_rate_min': 70.0  # percentage
        }

        # Performance history
        self.performance_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data

        logger.info("Group Performance Monitor initialized")

    def start_monitoring(self):
        """Start the performance monitoring thread"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop the performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_alerts()
                self._cleanup_old_metrics()
                time.sleep(60)  # Monitor every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # Memory usage
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            self.metrics.add_memory_usage(memory_percent)

            # CPU usage
            cpu_percent = process.cpu_percent()
            self.metrics.add_cpu_usage(cpu_percent)

            # Store historical data
            self.performance_history.append({
                'timestamp': time.time(),
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'active_connections': self.metrics.active_connections,
                'message_count': self.metrics.message_count,
                'error_count': self.metrics.error_count,
                'avg_response_time': self.metrics.get_average_response_time(),
                'cache_hit_rate': self.metrics.get_cache_hit_rate()
            })

            # Trigger garbage collection periodically
            if len(self.performance_history) % 60 == 0:  # Every hour
                gc.collect()

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _check_alerts(self):
        """Check for performance alerts"""
        if not self.alerts_enabled:
            return

        try:
            current_metrics = {
                'response_time': self.metrics.get_average_response_time(),
                'memory_usage': self.metrics.get_average_memory_usage(),
                'cpu_usage': self.metrics.get_average_cpu_usage(),
                'cache_hit_rate': self.metrics.get_cache_hit_rate(),
                'error_rate': self._calculate_error_rate()
            }

            # Check thresholds
            alerts = []

            if current_metrics['response_time'] > self.alert_thresholds['response_time_max']:
                alerts.append(f"High response time: {current_metrics['response_time']:.2f}s")

            if current_metrics['memory_usage'] > self.alert_thresholds['memory_usage_max']:
                alerts.append(f"High memory usage: {current_metrics['memory_usage']:.1f}%")

            if current_metrics['cpu_usage'] > self.alert_thresholds['cpu_usage_max']:
                alerts.append(f"High CPU usage: {current_metrics['cpu_usage']:.1f}%")

            if current_metrics['error_rate'] > self.alert_thresholds['error_rate_max']:
                alerts.append(f"High error rate: {current_metrics['error_rate']:.1f}%")

            if current_metrics['cache_hit_rate'] < self.alert_thresholds['cache_hit_rate_min']:
                alerts.append(f"Low cache hit rate: {current_metrics['cache_hit_rate']:.1f}%")

            # Log alerts
            for alert in alerts:
                logger.warning(f"Performance Alert: {alert}")

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        total_operations = self.metrics.message_count + self.metrics.error_count
        if total_operations == 0:
            return 0.0
        return (self.metrics.error_count / total_operations) * 100

    def _cleanup_old_metrics(self):
        """Clean up old group-specific metrics"""
        current_time = time.time()
        groups_to_remove = []

        for group_id, metrics in self.group_metrics.items():
            # Remove metrics for groups inactive for more than 24 hours
            if current_time - metrics.start_time > 86400:  # 24 hours
                groups_to_remove.append(group_id)

        for group_id in groups_to_remove:
            del self.group_metrics[group_id]

        if groups_to_remove:
            logger.info(f"Cleaned up metrics for {len(groups_to_remove)} inactive groups")

    def record_message(self, group_id: Optional[int] = None):
        """Record a message processed"""
        self.metrics.message_count += 1

        if group_id:
            if group_id not in self.group_metrics:
                self.group_metrics[group_id] = PerformanceMetrics()
            self.group_metrics[group_id].message_count += 1

    def record_error(self, group_id: Optional[int] = None):
        """Record an error occurrence"""
        self.metrics.error_count += 1

        if group_id:
            if group_id not in self.group_metrics:
                self.group_metrics[group_id] = PerformanceMetrics()
            self.group_metrics[group_id].error_count += 1

    def record_response_time(self, response_time: float, group_id: Optional[int] = None):
        """Record a response time"""
        self.metrics.add_response_time(response_time)

        if group_id:
            if group_id not in self.group_metrics:
                self.group_metrics[group_id] = PerformanceMetrics()
            self.group_metrics[group_id].add_response_time(response_time)

    def record_cache_hit(self):
        """Record a cache hit"""
        self.metrics.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss"""
        self.metrics.cache_misses += 1

    def set_active_connections(self, count: int):
        """Set the current number of active connections"""
        self.metrics.active_connections = count

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        current_time = time.time()

        return {
            'global_metrics': {
                'uptime_seconds': self.metrics.get_uptime(),
                'total_messages': self.metrics.message_count,
                'total_errors': self.metrics.error_count,
                'error_rate_percent': self._calculate_error_rate(),
                'average_response_time': self.metrics.get_average_response_time(),
                'current_memory_usage': self.metrics.get_average_memory_usage(),
                'current_cpu_usage': self.metrics.get_average_cpu_usage(),
                'active_connections': self.metrics.active_connections,
                'cache_hit_rate_percent': self.metrics.get_cache_hit_rate() * 100
            },
            'group_count': len(self.group_metrics),
            'monitoring_active': self.monitoring_active,
            'alerts_enabled': self.alerts_enabled,
            'alert_thresholds': self.alert_thresholds.copy(),
            'system_info': {
                'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
                'process_id': os.getpid(),
                'available_memory_mb': psutil.virtual_memory().available // (1024 * 1024),
                'cpu_count': psutil.cpu_count()
            },
            'performance_trend': self._get_performance_trend()
        }

    def _get_performance_trend(self) -> Dict[str, str]:
        """Get performance trend indicators"""
        if len(self.performance_history) < 2:
            return {'trend': 'insufficient_data'}

        recent = list(self.performance_history)[-10:]  # Last 10 minutes
        older = list(self.performance_history)[-20:-10]  # Previous 10 minutes

        if not older:
            return {'trend': 'insufficient_data'}

        try:
            # Calculate trends
            recent_response_time = sum(h['avg_response_time'] for h in recent) / len(recent)
            older_response_time = sum(h['avg_response_time'] for h in older) / len(older)

            recent_memory = sum(h['memory_percent'] for h in recent) / len(recent)
            older_memory = sum(h['memory_percent'] for h in older) / len(older)

            trends = {}

            # Response time trend
            if recent_response_time > older_response_time * 1.1:
                trends['response_time'] = 'deteriorating'
            elif recent_response_time < older_response_time * 0.9:
                trends['response_time'] = 'improving'
            else:
                trends['response_time'] = 'stable'

            # Memory usage trend
            if recent_memory > older_memory * 1.1:
                trends['memory'] = 'increasing'
            elif recent_memory < older_memory * 0.9:
                trends['memory'] = 'decreasing'
            else:
                trends['memory'] = 'stable'

            return trends

        except Exception as e:
            logger.error(f"Error calculating performance trend: {e}")
            return {'trend': 'error'}

    def get_group_metrics(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific group"""
        if group_id not in self.group_metrics:
            return None

        metrics = self.group_metrics[group_id]
        return {
            'group_id': group_id,
            'uptime_seconds': metrics.get_uptime(),
            'message_count': metrics.message_count,
            'error_count': metrics.error_count,
            'error_rate_percent': (metrics.error_count / max(metrics.message_count, 1)) * 100,
            'average_response_time': metrics.get_average_response_time(),
            'cache_hit_rate_percent': metrics.get_cache_hit_rate() * 100
        }

# Global instance
_performance_monitor = None

def get_performance_monitor() -> GroupPerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = GroupPerformanceMonitor()
    return _performance_monitor

# Decorator for monitoring function performance
def monitor_performance(group_id: Optional[int] = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                monitor.record_message(group_id)
                return result
            except Exception as e:
                monitor.record_error(group_id)
                raise
            finally:
                end_time = time.time()
                monitor.record_response_time(end_time - start_time, group_id)

        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the monitoring system
    def test_performance_monitor():
        monitor = get_performance_monitor()
        monitor.start_monitoring()

        # Simulate some activity
        for i in range(10):
            monitor.record_message()
            monitor.record_response_time(0.1 + i * 0.01)
            time.sleep(0.1)

        # Get performance report
        report = monitor.get_performance_report()
        print(f"Performance Report: {report}")

        monitor.stop_monitoring()

    test_performance_monitor()