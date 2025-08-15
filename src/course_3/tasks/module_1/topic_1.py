# Задача: Найти два индекса, сумма элементов которых равна target


def get_indexes(nums, target):
    seen: dict[int, int] = {}
    for index, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return seen[complement], index
        seen[num] = index


nums = [2, 7, 11, 15]
target = 9
print(get_indexes(nums, target))
