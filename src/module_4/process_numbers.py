import json
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import wraps
from multiprocessing import Process, Queue
from random import randint
from time import monotonic

from tabulate import tabulate


def time_it(title: str):
    """
    Замеряет время выполнения функции и возвращает результат
    измерения вместо результата работы функции
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = monotonic()
            result = func(*args, **kwargs)
            end = monotonic()
            diff = end - start
            return title, f"{diff:.6f}"

        return wrapper

    return decorator


def generate_data(n: int, limit: int = 1000) -> list[int]:
    """
    Генерирует список из n случайных целых чисел в диапазоне от 1 до limit
    """
    return [randint(1, limit) for _ in range(n)]


def is_prime(num: int) -> bool:
    """
    Самым отвратительным способом проверяет, является ли число простым
    """
    if num < 2:
        return False
    divisors = []
    for i in range(1, num + 1):
        if num % i == 0:
            divisors.append(i)
    return len(divisors) == 2


def get_factorial(num: int) -> int:
    """
    Вычисляет факториал числа
    """
    result = 1
    for i in range(2, num + 1):
        result *= i
    return result


def process_number(number: int) -> tuple:
    """
    Обрабатывает число
    """
    prime_check = is_prime(number)
    factorial_result = get_factorial(number)
    return prime_check, factorial_result


def worker(input_queue, output_queue, worker_id: int):
    """
    Обрабатывает данные из очереди
    """
    while True:
        try:
            item = input_queue.get()
            if item is None:
                break
            output_queue.put(process_number(item))
        except:
            break
    return None


@time_it("sequence")
def sequence_processing(numbers: list[int]) -> None:
    """
    Последовательная обработка чисел
    """
    tuple(map(process_number, numbers))
    return None


@time_it("thread_pool")
def thread_poo_processing(numbers: list[int], max_workers: int | None) -> None:
    """
    Обработка чисел с использованием пула потоков
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_number, numbers)
    return None


@time_it("process_pool")
def process_pool_processing(numbers: list[int], max_workers: int | None) -> None:
    """
    Обработка чисел с использованием пула процессов
    """
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_number, numbers)
    return None


@time_it("maual_processing")
def maual_processing(numbers: list[int], process_count: int) -> None:
    """
    Обработка чисел с использованием отдельных процессов и очередей
    """
    input_queue: Queue = Queue()
    output_queue: Queue = Queue()

    for number in numbers:
        input_queue.put(number)

    for _ in range(process_count):
        input_queue.put(None)

    processes = []
    for i in range(process_count):
        process = Process(target=worker, args=(input_queue, output_queue, i))
        process.start()
        processes.append(process)

    results = []
    for _ in range(len(numbers)):
        results.append(output_queue.get())

    for process in processes:
        process.join()

    return None


def print_data(data: list | tuple) -> None:
    """
    Выводит даныне в виде таблицы
    """
    headers = ["Функция", "Время выполнения"]
    print(
        tabulate(
            data,
            headers=headers,
            tablefmt="psql",
            colalign=["left", "right"],
        )
    )


def frite_data(data: list | tuple, file_path: str) -> None:
    """
    Записывает данные в файл
    """
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def main() -> None:
    numbers = generate_data(1000)
    count = os.cpu_count() or 1
    data = (
        sequence_processing(numbers),
        thread_poo_processing(numbers, count),
        process_pool_processing(numbers, count),
        maual_processing(numbers, count),
    )
    frite_data(data, "results.jsonl")
    print_data(data)


if __name__ == "__main__":
    main()
