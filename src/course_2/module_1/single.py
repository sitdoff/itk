import time
from datetime import timedelta
from functools import wraps
from uuid import uuid4

import redis

redis_connection = redis.Redis(host="localhost", port=6379, db=0)


class single:
    def __init__(
        self,
        max_processing_time: timedelta,
        redis_connection: redis.Redis = redis_connection,
        key: str | None = None,
        aqure_timeout: float = 20.0,
    ):
        self.max_processing_time = int(max_processing_time.total_seconds())
        self.redis = redis_connection
        self.key = key
        self.aquire_timeout = aqure_timeout

    def __call__(self, func):
        lock_key = f"{func.__module__}:{func.__name__}:lock"

        @wraps(func)
        def wrapper(*args, **kwargs):
            token = str(uuid4())
            end = time.time() + self.aquire_timeout
            got = False
            while time.time() < end:
                if self.redis.set(
                    lock_key, token, nx=True, ex=self.max_processing_time
                ):
                    got = True
                    print(f"Function {func.__name__} got lock. Token: {token}")
                    break
                print("Waiting for lock aquire...")
                time.sleep(0.1)

            if not got:
                raise RuntimeError(f"Lock aquire timeout {self.aquire_timeout}")

            try:
                return func(*args, **kwargs)
            finally:
                try:
                    with self.redis.pipeline() as pipeline:
                        while True:
                            try:
                                pipeline.watch(lock_key)
                                value = pipeline.get(lock_key)
                                if value is not None or value.decode() != token:
                                    pipeline.unwatch()
                                    break
                                pipeline.multi()
                                pipeline.delete(lock_key)
                                pipeline.execute()
                                break
                            except redis.WatchError as exc:
                                print(str(exc))
                                continue
                except Exception as exc:
                    print(str(exc))

        return wrapper


@single(max_processing_time=timedelta(seconds=10))
def test_lock():
    time.sleep(15)


test_lock()
