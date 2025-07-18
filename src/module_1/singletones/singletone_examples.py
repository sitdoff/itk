from functools import wraps
from typing import Self

from modules import singletone

# Реализация паттерна Singletone через импорт
a = singletone
b = singletone
assert a is b


class SingletoneMeta(type):
    """
    Реализация паттерна Singletone через метакласс
    """

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class MySingletone(metaclass=SingletoneMeta):
    pass


a = MySingletone()
b = MySingletone()
assert a is b


class MySingletoneNew:
    """
    Реализация паттерна Singletone через метод __new__
    """

    _instance: Self | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance


a = MySingletoneNew()
b = MySingletoneNew()
assert a is b


def singletone(cls):
    """
    Реализация паттерна Singletone через декоратор
    """
    instance = None

    @wraps(cls)
    def wrapper(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return wrapper


@singletone
class DecoratedSingletone:
    pass


a = DecoratedSingletone()
b = DecoratedSingletone()
assert a is b
