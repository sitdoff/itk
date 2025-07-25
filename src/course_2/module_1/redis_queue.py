import json
from typing import Any

import redis

redis_connection = redis.Redis(host="localhost", port=6379, db=0)


class RedisQueue:
    def __init__(
        self, queue_name: str, redis_connection: redis.Redis = redis_connection
    ):
        self.queue_name = queue_name
        self.redis = redis_connection

    def publish(self, message: dict[str, Any]) -> None:
        data = json.dumps(message, ensure_ascii=False)
        self.redis.lpush(self.queue_name, data)

    def consume(self) -> dict[str, Any] | None:
        data = self.redis.brpop([self.queue_name], timeout=5)
        if data is None:
            return None
        try:
            return json.loads(data[1].decode("utf-8"))
        except json.JSONDecodeError:
            return None


if __name__ == "__main__":
    queue = RedisQueue("test")
    queue.publish({"a": 1})
    queue.publish({"b": 2})
    queue.publish({"c": 3})

    assert queue.consume() == {"a": 1}
    assert queue.consume() == {"b": 2}
    assert queue.consume() == {"c": 3}
    assert queue.consume() is None

    print("OK")
