# Задача: Удалить дубликаты из отсортированного массива без использования дополнительной памяти (in-place) и вернуть новую длину массива.


def delete_duplicates(nums: list[int]) -> tuple[int, list[int]]:
    if not nums:
        return 0, []

    unique_index = 1
    for i in range(1, len(nums)):
        if nums[i] != nums[unique_index - 1]:
            nums[unique_index] = nums[i]
            unique_index += 1
    return unique_index, nums[:unique_index]


nums = [1, 1, 2, 2, 3, 4, 4, 5]
print(delete_duplicates(nums))
