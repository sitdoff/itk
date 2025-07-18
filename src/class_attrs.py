from datetime import datetime


class TimeStampMeta(type):
    def __new__(cls, *args, **kwargs):
        new_cls = super().__new__(cls, *args, **kwargs)
        setattr(new_cls, "created_at", datetime.now())
        return new_cls


class MyClass(metaclass=TimeStampMeta):
    pass


class MySubClass(MyClass):
    pass


a = MyClass()
b = MySubClass()
assert isinstance(MyClass.created_at, datetime)
assert isinstance(MySubClass.created_at, datetime)
assert isinstance(a.created_at, datetime)
assert isinstance(b.created_at, datetime)
