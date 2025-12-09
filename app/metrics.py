"""
Performance monitoring and metrics tracking for the medical bot
Tracks response times, user activity, and system performance
"""

import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)

# Thread-safe metrics storage
metrics_lock = Lock()

# Metrics data structures
class BotMetrics:
    def __init__(self):
        self.total_requests = 0
        self.total_users = set()
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        self.requests_per_user = defaultdict(int)
        self.requests_per_hour = defaultdict(int)
        self.language_usage = defaultdict(int)
        self.error_count = 0
        self.translation_times = deque(maxlen=100)
        self.ai_generation_times = deque(maxlen=100)
        self.start_time = datetime.now()

    def record_request(self, user_id: str, response_time: float, language: str = 'en',
                      translation_time: float = 0, ai_time: float = 0, error: bool = False):
        """Record a request with all timing details"""
        with metrics_lock:
            self.total_requests += 1
            self.total_users.add(user_id)
            self.response_times.append(response_time)
            self.requests_per_user[user_id] += 1

            # Track requests per hour
            current_hour = datetime.now().strftime('%Y-%m-%d %H:00')
            self.requests_per_hour[current_hour] += 1

            # Track language usage
            self.language_usage[language] += 1

            # Track component timings
            if translation_time > 0:
                self.translation_times.append(translation_time)
            if ai_time > 0:
                self.ai_generation_times.append(ai_time)

            if error:
                self.error_count += 1

    def get_average_response_time(self):
        """Get average response time from recent requests"""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)

    def get_average_translation_time(self):
        """Get average translation time"""
        if not self.translation_times:
            return 0
        return sum(self.translation_times) / len(self.translation_times)

    def get_average_ai_time(self):
        """Get average AI generation time"""
        if not self.ai_generation_times:
            return 0
        return sum(self.ai_generation_times) / len(self.ai_generation_times)

    def get_requests_last_hour(self):
        """Get number of requests in the last hour"""
        current_hour = datetime.now().strftime('%Y-%m-%d %H:00')
        return self.requests_per_hour.get(current_hour, 0)

    def get_top_users(self, limit=10):
        """Get top users by request count"""
        sorted_users = sorted(self.requests_per_user.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]

    def get_uptime(self):
        """Get bot uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()

    def get_stats(self):
        """Get all statistics as a dictionary"""
        with metrics_lock:
            uptime_seconds = self.get_uptime()
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))

            return {
                'total_requests': self.total_requests,
                'unique_users': len(self.total_users),
                'average_response_time': round(self.get_average_response_time(), 2),
                'average_translation_time': round(self.get_average_translation_time(), 2),
                'average_ai_time': round(self.get_average_ai_time(), 2),
                'requests_last_hour': self.get_requests_last_hour(),
                'error_count': self.error_count,
                'error_rate': round((self.error_count / self.total_requests * 100) if self.total_requests > 0 else 0, 2),
                'language_usage': dict(self.language_usage),
                'top_users': self.get_top_users(5),
                'uptime': uptime_str,
                'uptime_seconds': int(uptime_seconds),
                'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'recent_response_times': list(self.response_times)[-10:],  # Last 10
            }

# Global metrics instance
bot_metrics = BotMetrics()

# Context manager for timing requests
class RequestTimer:
    def __init__(self, user_id: str, language: str = 'en'):
        self.user_id = user_id
        self.language = language
        self.start_time = None
        self.translation_time = 0
        self.ai_time = 0
        self.error = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        total_time = time.time() - self.start_time

        if exc_type is not None:
            self.error = True

        bot_metrics.record_request(
            user_id=self.user_id,
            response_time=total_time,
            language=self.language,
            translation_time=self.translation_time,
            ai_time=self.ai_time,
            error=self.error
        )

        logger.info(f"Request completed in {total_time:.2f}s (AI: {self.ai_time:.2f}s, Translation: {self.translation_time:.2f}s)")

    def set_translation_time(self, duration: float):
        """Set translation time"""
        self.translation_time = duration

    def set_ai_time(self, duration: float):
        """Set AI generation time"""
        self.ai_time = duration

def get_metrics():
    """Get current metrics"""
    return bot_metrics.get_stats()

def reset_metrics():
    """Reset all metrics (useful for testing)"""
    global bot_metrics
    with metrics_lock:
        bot_metrics = BotMetrics()
        logger.info("Metrics reset")
