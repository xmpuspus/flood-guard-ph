"""Rate limiting middleware for API protection"""
import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket

        Returns:
            True if tokens available, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_wait_time(self) -> float:
        """Get seconds to wait before retry"""
        if self.tokens >= 1:
            return 0.0

        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """
    Rate limiter with multiple strategies

    Enhancement #15: Add Rate Limiting to API endpoints
    """

    def __init__(self):
        # Session-based rate limits (for WebSocket chat)
        # 10 requests per minute (refill at 10/60 = 0.167 tokens/sec)
        self.session_buckets: Dict[str, TokenBucket] = {}
        self.session_capacity = 10
        self.session_refill_rate = 10 / 60  # 10 per minute

        # IP-based rate limits (for REST endpoints)
        # 100 requests per minute
        self.ip_buckets: Dict[str, TokenBucket] = {}
        self.ip_capacity = 100
        self.ip_refill_rate = 100 / 60  # 100 per minute

        # Cleanup old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def check_session_limit(self, session_id: str) -> tuple[bool, Optional[float]]:
        """
        Check if session is within rate limit

        Returns:
            (allowed, wait_time): If allowed, wait_time is None. Otherwise wait_time in seconds.
        """
        self._cleanup_if_needed()

        if session_id not in self.session_buckets:
            self.session_buckets[session_id] = TokenBucket(
                self.session_capacity,
                self.session_refill_rate
            )

        bucket = self.session_buckets[session_id]

        if bucket.consume():
            return True, None
        else:
            wait_time = bucket.get_wait_time()
            return False, wait_time

    def check_ip_limit(self, ip_address: str) -> tuple[bool, Optional[float]]:
        """
        Check if IP is within rate limit

        Returns:
            (allowed, wait_time)
        """
        self._cleanup_if_needed()

        if ip_address not in self.ip_buckets:
            self.ip_buckets[ip_address] = TokenBucket(
                self.ip_capacity,
                self.ip_refill_rate
            )

        bucket = self.ip_buckets[ip_address]

        if bucket.consume():
            return True, None
        else:
            wait_time = bucket.get_wait_time()
            return False, wait_time

    def get_remaining_quota(self, session_id: str) -> int:
        """Get remaining requests for session"""
        if session_id not in self.session_buckets:
            return self.session_capacity

        bucket = self.session_buckets[session_id]
        bucket._refill()  # Update tokens first
        return int(bucket.tokens)

    def _cleanup_if_needed(self):
        """Remove old unused buckets to prevent memory leaks"""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove session buckets that are full and haven't been used in 10 minutes
        sessions_to_remove = []
        for session_id, bucket in self.session_buckets.items():
            bucket._refill()
            if bucket.tokens >= bucket.capacity and now - bucket.last_refill > 600:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.session_buckets[session_id]

        # Remove IP buckets that are full and haven't been used in 10 minutes
        ips_to_remove = []
        for ip, bucket in self.ip_buckets.items():
            bucket._refill()
            if bucket.tokens >= bucket.capacity and now - bucket.last_refill > 600:
                ips_to_remove.append(ip)

        for ip in ips_to_remove:
            del self.ip_buckets[ip]

        self.last_cleanup = now

        if sessions_to_remove or ips_to_remove:
            logger.info(f"Rate limiter cleanup: removed {len(sessions_to_remove)} sessions, {len(ips_to_remove)} IPs")


# Global rate limiter instance
rate_limiter = RateLimiter()
