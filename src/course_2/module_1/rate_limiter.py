import random
import time
from datetime import timedelta

import redis

redis_connection = redis.Redis(host="localhost", port=6379, db=0)


class RateLimitExceed(Exception):
    pass


class RateLimiter:
    def __init__(
        self,
        redis_connection: redis.Redis,
        window: timedelta,
        limit: int = 5,
        sub: int = 1,
    ):
        self.redis = redis_connection
        self.window = int(window.total_seconds())
        self.prefix = "rate_limiter:"
        self.limit = limit
        self.sub = sub

    def test(self, identifier="identifier") -> bool:
        now = int(time.time())
        window_start = now - self.window
        key = f"{self.prefix}:{identifier}"

        old_fields = [
            field for field in self.redis.hkeys(key) if int(field) < window_start
        ]
        if old_fields:
            self.redis.hdel(key, *old_fields)

        values = self.redis.hvals(key)
        total = sum(int(value) for value in values) if values else 0

        if total >= self.limit:
            return False

        current_field = now - (now % self.sub)
        self.redis.hincrby(key, current_field, 1)
        self.redis.expire(key, self.window + self.sub)
        return True


def make_api_request(rate_limiter: RateLimiter):
    if not rate_limiter.test():
        raise RateLimitExceed
    else:
        print("Какая-то бизнес логика")


if __name__ == "__main__":
    rate_limiter = RateLimiter(
        redis_connection=redis_connection, window=timedelta(seconds=3), limit=5
    )

    for _ in range(50):
        time.sleep(random.randint(0, 2))

        try:
            make_api_request(rate_limiter)
        except RateLimitExceed:
            print("Rate limit exceed!")
        else:
            print("All good")
