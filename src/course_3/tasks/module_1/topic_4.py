# Задача: Найти длину наибольшей возрастающей подпоследовательности.


def longest_increasing_subsequence(nums: list[int]) -> int:
    if not nums:
        return 0
    max_len = 0
    current_len = 1
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            current_len += 1
        else:
            if current_len > max_len:
                max_len = current_len
            current_len = 1
    return max_len


nums = [10, 9, 2, 5, 3, 7, 101, 18]
print(longest_increasing_subsequence(nums))
