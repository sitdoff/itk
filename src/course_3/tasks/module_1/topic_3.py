# Задача: Закодировать строку, заменяя последовательности одинаковых символов на сам символ + количество повторений.


def code_string(s: str) -> str:
    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(s[i - 1] + str(count))
            count = 1

    result.append(s[-1] + str(count))
    return "".join(result)


s = "AAAaaaDE"
print(code_string(s))
