"""
Rate-limiting utilities for throttling Gmail API calls.
"""

import asyncio
import time


async def rate_limit_sleep(seconds: int) -> None:
    """Sleep for *seconds* without blocking the event loop."""
    if seconds > 0:
        await asyncio.sleep(seconds)


class TokenBucket:
    """
    Simple token-bucket rate limiter for future extensibility.

    Parameters
    ----------
    rate : float
        Tokens added per second.
    capacity : int
        Maximum tokens the bucket can hold.
    """

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate = rate
        self.capacity = capacity
        self._tokens: float = float(capacity)
        self._last_refill: float = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume *tokens* from the bucket.

        Returns True if tokens were available, False otherwise.
        """
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    async def wait_and_consume(self, tokens: int = 1) -> None:
        """Block (async) until *tokens* are available, then consume them."""
        while not self.consume(tokens):
            await asyncio.sleep(0.1)
