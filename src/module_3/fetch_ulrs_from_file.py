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


def parse_json_file(
    tmp_file: str,
    result_file: str,
    url,
) -> None:
    """
    Добавляет содержимое временного файла в
    файл с итоговым результатом.
    """

    async def merge_file(tmp_file, result_file):
        async with aiofiles.open(tmp_file, "r") as file:
            async with aiofiles.open(result_file, "a") as result:
                await result.write(
                    json.dumps({"url": url, "content": json.loads(await file.read())})
                    + "\n"
                )

    asyncio.run(merge_file(tmp_file, result_file))


async def handler(
    session: ClientSession,
    queue: Queue,
    file_lock: Lock,
):
    while True:
        try:
            url = await queue.get()
        except CancelledError:
            break

        try:
            async with session.get(url) as response:
                async with aiofiles.tempfile.NamedTemporaryFile(
                    "wb+",
                    delete_on_close=False,
                ) as tmp_file:
                    if response.status == 200:
                        async for chunk in response.content.iter_chunked(1024):
                            await tmp_file.write(chunk)
                            await tmp_file.flush()
                        async with file_lock:
                            await asyncio.to_thread(
                                parse_json_file,
                                str(tmp_file.name),
                                RESULT_FILE,
                                url,
                            )
        except (ClientConnectorDNSError, TimeoutError, JSONDecodeError) as exc:
            print(exc)
        finally:
            queue.task_done()


async def fetch_urls(urls_path: str, results_path: str) -> None:
    queue: Queue[str] = Queue(maxsize=QUEUE_MAXSIZE)
    lock: Lock = Lock()

    timeout: ClientTimeout = ClientTimeout(total=TIMEOUT)
    connector: TCPConnector = TCPConnector(limit=LIMIT)

    async with ClientSession(connector=connector, timeout=timeout) as session:
        workers = [
            asyncio.create_task(
                handler(session, queue, lock),
            )
            for _ in range(LIMIT)
        ]

        async with aiofiles.open(urls_path, "r", encoding="utf-8") as urls_file:
            async for line in urls_file:
                url = line.strip()
                await queue.put(url)

        await queue.join()

        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers)


if __name__ == "__main__":
    asyncio.run(fetch_urls(URLS_FILE, RESULT_FILE))
