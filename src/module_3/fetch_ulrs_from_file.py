import asyncio
import json
from asyncio import CancelledError, Lock, Queue, TimeoutError
from json import JSONDecodeError

import aiofiles
from aiohttp import ClientConnectorDNSError, ClientSession, ClientTimeout, TCPConnector

URLS_FILE = "urls.txt"
RESULT_FILE = "results.jsonl"
QUEUE_MAXSIZE = 100
TIMEOUT = 60
LIMIT = 5


async def handler(
    session: ClientSession,
    queue: Queue,
    file,
    file_lock: Lock,
):
    while True:
        try:
            url = await queue.get()
        except CancelledError:
            break

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.json(content_type=None)
                    line = json.dumps(
                        {"url": url, "content": content}, ensure_ascii=False
                    )
                    async with file_lock:
                        await file.write(line + "\n")
        except (ClientConnectorDNSError, TimeoutError, JSONDecodeError) as exc:
            print(exc)
        finally:
            queue.task_done()


async def fetch_uls(urls_path: str, results_path: str) -> None:
    queue: Queue[str] = Queue(maxsize=QUEUE_MAXSIZE)
    lock: Lock = Lock()

    timeout: ClientTimeout = ClientTimeout(total=TIMEOUT)
    connector: TCPConnector = TCPConnector(limit=LIMIT)

    async with ClientSession(connector=connector, timeout=timeout) as session:
        async with aiofiles.open(urls_path, "w", encoding="utf-8") as result_file:
            workers = [
                asyncio.create_task(
                    handler(session, queue, result_file, lock),
                )
                for _ in range(LIMIT)
            ]

            async with aiofiles.open(results_path, "r", encoding="utf-8") as urls_file:
                async for line in urls_file:
                    url = line.strip()
                    await queue.put(url)

            await queue.join()

            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers)


if __name__ == "__main__":
    asyncio.run(fetch_uls(URLS_FILE, RESULT_FILE))
