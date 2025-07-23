import asyncio
import json
import threading
from asyncio import CancelledError, Queue, TimeoutError
from json import JSONDecodeError

import aiofiles
from aiohttp import ClientConnectorDNSError, ClientSession, ClientTimeout, TCPConnector
from aiologic import Lock

URLS_FILE = "urls.txt"
RESULT_FILE = "results.jsonl"
QUEUE_MAXSIZE = 100
TIMEOUT = 60
LIMIT = 5


async def merge_file(tmp_files: dict[str, str], result_file: str):
    """
    Перебирает временные файлы и записывает данные из них
    в файл с общими результатами
    """
    async with aiofiles.open(result_file, "a") as result:
        for url, tmp_file_path in tmp_files.items():
            async with aiofiles.open(tmp_file_path, "r", encoding="utf-8") as file:
                try:
                    await result.write(
                        json.dumps(
                            {
                                "url": url,
                                "content": json.loads(await file.read()),
                            }
                        )
                        + "\n"
                    )
                except JSONDecodeError as exc:
                    print(f"File {tmp_file_path} has a trouble: {exc}")


def merge_files(
    tmp_files: dict[str, str],
    result_file: str,
) -> None:
    """
        Добавляет содержимое временных файлов в
        файл с итоговым результатом.
    r"""

    print("Current thread:", threading.current_thread().name)
    asyncio.run(merge_file(tmp_files, result_file))


async def handler(
    session: ClientSession,
    queue: Queue,
    file_lock: Lock,
):
    tmp_files = {}
    while True:
        try:
            url = await queue.get()
        except CancelledError:
            # Если на первом await поймали CancelledError,
            # то мерджим готовые файлы этого воркера
            # в общий результат
            if tmp_files:
                async with file_lock:
                    await asyncio.to_thread(
                        merge_files,
                        tmp_files,
                        RESULT_FILE,
                    )
            break

        try:
            async with session.get(url) as response:
                async with aiofiles.tempfile.NamedTemporaryFile(
                    "wb+",
                    delete=False,
                ) as tmp_file:
                    if response.status == 200:
                        async for chunk in response.content.iter_chunked(1024):
                            await tmp_file.write(chunk)
                        else:
                            await tmp_file.flush()
                            tmp_files[url] = str(tmp_file.name)
        except (ClientConnectorDNSError, TimeoutError) as exc:
            print(exc)
        finally:
            queue.task_done()


async def fetch_urls(urls_path: str) -> None:
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
    asyncio.run(fetch_urls(URLS_FILE))
