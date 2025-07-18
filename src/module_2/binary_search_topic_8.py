import bisect

numbers = [1, 2, 3, 45, 356, 569, 600, 705, 923]


# binary search "le classic"
def search(value: int) -> bool:
    minimum, maximum = 0, len(numbers) - 1
    while minimum <= maximum:
        mid = (minimum + maximum) // 2
        if numbers[mid] == value:
            return True
        elif numbers[mid] < value:
            minimum = mid + 1
        else:
            maximum = mid - 1
    return False


assert search(1)
assert search(4) == False
assert search(400000000000) == False


# binary search bisect
def search_bisect(value: int) -> bool:
    i = bisect.bisect_left(numbers, value)
    print("index:", i, "value:", value)
    return i != len(numbers) and numbers[i] == value


assert search_bisect(1)
assert search_bisect(4) == False
assert search_bisect(400000000000) == False
