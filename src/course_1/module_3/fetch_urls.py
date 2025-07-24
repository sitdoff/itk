import asyncio
import json
from asyncio import Lock, Semaphore, TimeoutError

import aiofiles
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectorDNSError

urls = [
    "https://example.com",
    "https://httpbin.org/status/302",
    "https://httpbin.org/status/400",
    "https://httpbin.org/status/404",
    "https://httpbin.org/status/500",
    "https://nonexistent.url",
]


async def fetch_and_write(
    url: str,
    session: ClientSession,
    semaphore: Semaphore,
    file,
    file_lock: Lock,
    timeout: ClientTimeout = ClientTimeout(5),
) -> None:
    """
    Выполняет запрос и пишет линию с файл
    """
    error = None
    async with semaphore:
        try:
            async with session.get(url, timeout=timeout) as response:
                status = response.status
        except (ClientConnectorDNSError, TimeoutError) as exc:
            status = 0
            error = (f"{exc.__class__.__name__} {exc}").strip()

        result = {
            "url": url,
            "status_code": status,
        }

        if error is not None:
            result["error"] = error

        async with file_lock:
            await file.write(json.dumps(result) + "\n")


async def fetch_urls(urls: list[str], file_path: str, limit: int = 5) -> None:
    """
    Задаёт ограничения и создаёт таски
    """
    semaphore = Semaphore(limit)
    file_lock = Lock()
    timeout = ClientTimeout(5)

    async with ClientSession() as session:
        async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
            tasks = [
                fetch_and_write(
                    url,
                    session,
                    semaphore,
                    file,
                    file_lock,
                    timeout,
                )
                for url in urls
            ]
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(fetch_urls(urls, "./results.jsonl"))
