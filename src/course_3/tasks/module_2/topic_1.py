import asyncio
from functools import wraps
from typing import Type


def async_retry(
    retries: int = 3,
    exceptions: tuple[Type[BaseException]] = (Exception,),
):
    """
    Декоратор для повторного выполнения асинхронной функции при ошибках.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    print(f"Retrying {func.__name__} ({attempt}/{retries})")
                    last_exc = exc
                    if attempt < retries:
                        continue
            raise last_exc or Exception("BaseException raised")

        return wrapper

    return decorator


@async_retry(retries=3, exceptions=(ValueError,))
async def unstable_task():
    print("Running task...")
    raise ValueError("Something went wrong")


async def main():
    try:
        await unstable_task()
    except Exception as e:
        print(f"Final failure: {e}")


asyncio.run(main())
