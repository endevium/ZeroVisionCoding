import json
from pathlib import Path

def setup_test_cases():
    PROJECT_ROOT = Path(__file__).resolve().parent
    base_dir = PROJECT_ROOT / "tests" / "ai_test_cases"
    
    fixer_dir = base_dir / "fixer"
    reviewer_dir = base_dir / "reviewer"
    analyze_dir = base_dir / "analyze"
    explain_dir = base_dir / "explain"
    
    for d in [fixer_dir, reviewer_dir, analyze_dir, explain_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════
    # CODE FIXER TEST CASES (25 cases)
    # ═══════════════════════════════════════════════════════════════

    fixer_cases = [
        {
            "file": "zero_division.json",
            "code": "a = 5\nb = 0\nprint(a / b)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 3, in <module>\n    print(a / b)\nZeroDivisionError: division by zero"
        },
        {
            "file": "index_error.json",
            "code": "numbers = [1, 2, 3]\nprint(numbers[5])\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    print(numbers[5])\nIndexError: list index out of range"
        },
        {
            "file": "name_error.json",
            "code": "print(c)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 1, in <module>\n    print(c)\nNameError: name 'c' is not defined"
        },
        {
            "file": "key_error.json",
            "code": "person = {}\nperson['age'] = 30\nprint(person['name'])\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 3, in <module>\n    print(person['name'])\nKeyError: 'name'"
        },
        {
            "file": "attribute_error.json",
            "code": "x = 5\nx.append(3)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    x.append(3)\nAttributeError: 'int' object has no attribute 'append'"
        },
        {
            "file": "type_error_concat.json",
            "code": "x = 5\ny = 'hello'\nprint(x + y)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 3, in <module>\n    print(x + y)\nTypeError: unsupported operand type(s) for +: 'int' and 'str'"
        },
        {
            "file": "value_error.json",
            "code": "num = int('abc')\nprint(num)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 1, in <module>\n    num = int('abc')\nValueError: invalid literal for int() with base 10: 'abc'"
        },
        {
            "file": "syntax_error.json",
            "code": "def greet(name)\n    print('Hello ' + name)\n\ngreet('World')\n",
            "error": "  File \"temp.py\", line 1\n    def greet(name)\n                  ^\nSyntaxError: expected ':'"
        },
        {
            "file": "indentation_error.json",
            "code": "def add(a, b):\nreturn a + b\n\nprint(add(2, 3))\n",
            "error": "  File \"temp.py\", line 2\n    return a + b\n    ^\nIndentationError: expected an indented block after function definition on line 1"
        },
        {
            "file": "unbound_local.json",
            "code": "count = 10\ndef increment():\n    count = count + 1\n    return count\nprint(increment())\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 5, in <module>\n    print(increment())\n  File \"temp.py\", line 3, in increment\n    count = count + 1\nUnboundLocalError: cannot access local variable 'count' where it is not associated with a value"
        },
        {
            "file": "module_not_found.json",
            "code": "import tenserflow\nprint(tenserflow.__version__)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 1, in <module>\n    import tenserflow\nModuleNotFoundError: No module named 'tenserflow'"
        },
        {
            "file": "type_error_args.json",
            "code": "def add(a, b):\n    return a + b\n\nresult = add(1, 2, 3)\nprint(result)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 4, in <module>\n    result = add(1, 2, 3)\nTypeError: add() takes 2 positional arguments but 3 were given"
        },
        {
            "file": "file_not_found.json",
            "code": "with open('nonexistent_file.txt', 'r') as f:\n    content = f.read()\nprint(content)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 1, in <module>\n    with open('nonexistent_file.txt', 'r') as f:\nFileNotFoundError: [Errno 2] No such file or directory: 'nonexistent_file.txt'"
        },
        {
            "file": "recursion_error.json",
            "code": "def countdown(n):\n    print(n)\n    countdown(n - 1)\n\ncountdown(5)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 5, in <module>\n    countdown(5)\n  File \"temp.py\", line 3, in countdown\n    countdown(n - 1)\n  File \"temp.py\", line 3, in countdown\n    countdown(n - 1)\n  [Previous line repeated 996 more times]\nRecursionError: maximum recursion depth exceeded"
        },
        {
            "file": "wrong_function_usage.json",
            "code": "numbers = [3, 1, 2]\nsorted_nums = numbers.sort()\nprint(sorted_nums[0])\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 3, in <module>\n    print(sorted_nums[0])\nTypeError: 'NoneType' object is not subscriptable"
        },
        {
            "file": "float_division_zero.json",
            "code": "numerator = 1.0\ndenominator = 0.0\nprint(numerator / denominator)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 3, in <module>\n    print(numerator / denominator)\nZeroDivisionError: float division by zero"
        },
        {
            "file": "empty_pop.json",
            "code": "items = []\nprint(items.pop())\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    print(items.pop())\nIndexError: pop from empty list"
        },
        {
            "file": "none_append.json",
            "code": "value = None\nvalue.append(1)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    value.append(1)\nAttributeError: 'NoneType' object has no attribute 'append'"
        },
        {
            "file": "int_subscript.json",
            "code": "x = 42\nprint(x[0])\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    print(x[0])\nTypeError: 'int' object is not subscriptable"
        },
        {
            "file": "unpack_error.json",
            "code": "first, second = [1]\nprint(first, second)\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 1, in <module>\n    first, second = [1]\nValueError: not enough values to unpack (expected 2, got 1)"
        },
        {
            "file": "assertion_error.json",
            "code": "assert False, 'something went wrong'\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 1, in <module>\n    assert False, 'something went wrong'\nAssertionError: something went wrong"
        },
        {
            "file": "nested_key_error.json",
            "code": "payload = {'user': {'name': 'Ada'}}\nprint(payload['user']['age'])\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    print(payload['user']['age'])\nKeyError: 'age'"
        },
        {
            "file": "list_index_negative.json",
            "code": "values = []\nprint(values[-1])\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    print(values[-1])\nIndexError: list index out of range"
        },
        {
            "file": "call_none.json",
            "code": "handler = None\nhandler()\n",
            "error": "Traceback (most recent call last):\n  File \"temp.py\", line 2, in <module>\n    handler()\nTypeError: 'NoneType' object is not callable"
        },
    ]

    for case in fixer_cases:
        data = {"code": case["code"], "error": case["error"], "expected_resolution": True}
        with open(fixer_dir / case["file"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════
    # CODE REVIEWER TEST CASES (25 cases)
    # ═══════════════════════════════════════════════════════════════

    reviewer_cases = [
        {
            "file": "infinite_loop.json",
            "code": "def process():\n    while True:\n        print('hello')\n\nprocess()",
            "expected_bugs": ["infinite loop", "no break condition"]
        },
        {
            "file": "recursion_no_base.json",
            "code": "def factorial(n):\n    return n * factorial(n - 1)\n\nprint(factorial(5))",
            "expected_bugs": ["no base case", "recursion", "infinite recursion"]
        },
        {
            "file": "clean_code.json",
            "code": "def add(a, b):\n    return a + b\n\nresult = add(3, 5)\nprint(result)",
            "expected_bugs": []
        },
        {
            "file": "division_no_check.json",
            "code": "def divide(a, b):\n    return a / b\n\nresult = divide(10, 0)\nprint(result)",
            "expected_bugs": ["division by zero", "no error handling"]
        },
        {
            "file": "unused_variable.json",
            "code": "def compute():\n    x = 10\n    y = 20\n    z = 30\n    return x + y\n\nprint(compute())",
            "expected_bugs": ["unused variable"]
        },
        {
            "file": "mutable_default.json",
            "code": "def add_item(item, items=[]):\n    items.append(item)\n    return items\n\nprint(add_item('a'))\nprint(add_item('b'))",
            "expected_bugs": ["mutable default argument"]
        },
        {
            "file": "bare_except.json",
            "code": "try:\n    result = 10 / 0\nexcept:\n    pass\n\nprint('Done')",
            "expected_bugs": ["bare except", "silently swallowing exceptions"]
        },
        {
            "file": "debug_prints.json",
            "code": "def calculate_total(items):\n    print(items)\n    return sum(items)\n\nprint(calculate_total([1, 2, 3]))",
            "expected_bugs": ["debug print", "noisy output"]
        },
        {
            "file": "unreachable_return.json",
            "code": "def is_even(n):\n    return True\n    if n % 2 == 0:\n        return True\n    return False",
            "expected_bugs": ["unreachable code", "dead code", "logic bug"]
        },
        {
            "file": "list_concat_loop.json",
            "code": "result = []\nfor i in range(100):\n    result = result + [i]\nprint(result)",
            "expected_bugs": ["inefficient list concatenation", "performance"]
        },
        {
            "file": "missing_validation.json",
            "code": "def set_age(age):\n    return age + 1\n\nprint(set_age(-5))",
            "expected_bugs": ["missing input validation", "invalid data"]
        },
        {
            "file": "shadow_builtin.json",
            "code": "list = [1, 2, 3]\nprint(list)\nprint(len(list))",
            "expected_bugs": ["shadowing built-in", "list"]
        },
        {
            "file": "missing_return.json",
            "code": "def greet(name):\n    message = f'Hello {name}'\n\nprint(greet('Ada'))",
            "expected_bugs": ["missing return", "function returns None"]
        },
        {
            "file": "comparison_is_string.json",
            "code": "status = 'ready'\nif status is 'ready':\n    print('go')",
            "expected_bugs": ["incorrect identity comparison", "is vs =="]
        },
        {
            "file": "magic_number.json",
            "code": "def discount(price):\n    return price * 0.87\n\nprint(discount(100))",
            "expected_bugs": ["magic number", "maintainability"]
        },
        {
            "file": "broad_exception.json",
            "code": "try:\n    value = int('abc')\nexcept Exception:\n    value = 0\n\nprint(value)",
            "expected_bugs": ["broad exception handling", "hidden errors"]
        },
        {
            "file": "no_docs.json",
            "code": "def transform(data):\n    return [item.strip() for item in data if item]\n\nprint(transform([' a ', '', 'b']))",
            "expected_bugs": ["missing documentation", "unclear intent"]
        },
        {
            "file": "global_mutation.json",
            "code": "settings = {'mode': 'dev'}\ndef update():\n    settings['mode'] = 'prod'\n\nupdate()\nprint(settings)",
            "expected_bugs": ["global mutation", "shared state"]
        },
        {
            "file": "off_by_one.json",
            "code": "values = [1, 2, 3]\nfor i in range(len(values) + 1):\n    print(values[i])",
            "expected_bugs": ["off by one", "index error"]
        },
    ]

    for case in reviewer_cases:
        data = {"code": case["code"], "expected_bugs": case["expected_bugs"]}
        with open(reviewer_dir / case["file"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════
    # ANALYZE CODE TEST CASES (25 cases)
    # ═══════════════════════════════════════════════════════════════

    analyze_cases = [
        {
            "file": "bubble_sort.json",
            "code": "def sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr"
        },
        {
            "file": "fibonacci.json",
            "code": "def fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)\n\nfor i in range(10):\n    print(fibonacci(i))"
        },
        {
            "file": "binary_search.json",
            "code": "def binary_search(arr, target):\n    low = 0\n    high = len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1"
        },
        {
            "file": "read_csv.json",
            "code": "import csv\n\ndef read_data(filename):\n    results = []\n    with open(filename, 'r') as f:\n        reader = csv.DictReader(f)\n        for row in reader:\n            results.append(row)\n    return results\n\ndata = read_data('students.csv')\nfor student in data:\n    print(student['name'], student['grade'])"
        },
        {
            "file": "calculator.json",
            "code": "def calculate(a, b, op):\n    if op == '+':\n        return a + b\n    elif op == '-':\n        return a - b\n    elif op == '*':\n        return a * b\n    elif op == '/':\n        if b == 0:\n            return 'Error: Division by zero'\n        return a / b\n    else:\n        return 'Unknown operator'"
        },
        {
            "file": "list_comprehension.json",
            "code": "numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\nevens = [x for x in numbers if x % 2 == 0]\nsquares = [x**2 for x in evens]\nprint(squares)"
        },
        {
            "file": "class_student.json",
            "code": "class Student:\n    def __init__(self, name, grades):\n        self.name = name\n        self.grades = grades\n\n    def average(self):\n        return sum(self.grades) / len(self.grades)\n\n    def is_passing(self):\n        return self.average() >= 60\n\ns = Student('Alice', [85, 90, 78])\nprint(f'{s.name}: {s.average():.1f}')"
        },
        {
            "file": "file_counter.json",
            "code": "def count_words(filename):\n    with open(filename, 'r') as f:\n        text = f.read()\n    words = text.split()\n    word_count = {}\n    for word in words:\n        word = word.lower()\n        word_count[word] = word_count.get(word, 0) + 1\n    return word_count"
        },
        {
            "file": "prime_check.json",
            "code": "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n\nprimes = [x for x in range(100) if is_prime(x)]\nprint(primes)"
        },
        {
            "file": "stack_implementation.json",
            "code": "class Stack:\n    def __init__(self):\n        self.items = []\n\n    def push(self, item):\n        self.items.append(item)\n\n    def pop(self):\n        if self.is_empty():\n            return None\n        return self.items.pop()\n\n    def peek(self):\n        if self.is_empty():\n            return None\n        return self.items[-1]\n\n    def is_empty(self):\n        return len(self.items) == 0\n\n    def size(self):\n        return len(self.items)"
        },
        {
            "file": "average_grade.json",
            "code": "def average_grade(grades):\n    if not grades:\n        return 0\n    total = sum(grades)\n    return total / len(grades)"
        },
        {
            "file": "linear_search.json",
            "code": "def linear_search(items, target):\n    for index, value in enumerate(items):\n        if value == target:\n            return index\n    return -1"
        },
        {
            "file": "palindrome_check.json",
            "code": "def is_palindrome(text):\n    cleaned = ''.join(ch.lower() for ch in text if ch.isalnum())\n    return cleaned == cleaned[::-1]\n\nprint(is_palindrome('Never odd or even'))"
        },
        {
            "file": "factorial_iterative.json",
            "code": "def factorial(n):\n    result = 1\n    for value in range(2, n + 1):\n        result *= value\n    return result\n\nprint(factorial(5))"
        },
        {
            "file": "sum_digits.json",
            "code": "def sum_digits(number):\n    total = 0\n    for digit in str(abs(number)):\n        total += int(digit)\n    return total"
        },
        {
            "file": "matrix_transpose.json",
            "code": "def transpose(matrix):\n    return [[row[column] for row in matrix] for column in range(len(matrix[0]))]\n\nprint(transpose([[1, 2, 3], [4, 5, 6]]))"
        },
        {
            "file": "word_frequency.json",
            "code": "def word_frequency(text):\n    counts = {}\n    for word in text.lower().split():\n        counts[word] = counts.get(word, 0) + 1\n    return counts\n\nprint(word_frequency('hello world hello'))"
        },
        {
            "file": "celsius_to_fahrenheit.json",
            "code": "def celsius_to_fahrenheit(celsius):\n    return (celsius * 9 / 5) + 32\n\nfor temp in [0, 20, 100]:\n    print(celsius_to_fahrenheit(temp))"
        },
        {
            "file": "remove_duplicates.json",
            "code": "def remove_duplicates(items):\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result"
        },
        {
            "file": "fizzbuzz.json",
            "code": "def fizzbuzz(limit):\n    result = []\n    for value in range(1, limit + 1):\n        if value % 15 == 0:\n            result.append('FizzBuzz')\n        elif value % 3 == 0:\n            result.append('Fizz')\n        elif value % 5 == 0:\n            result.append('Buzz')\n        else:\n            result.append(str(value))\n    return result"
        },
        {
            "file": "anagram_check.json",
            "code": "def is_anagram(left, right):\n    return sorted(left.replace(' ', '').lower()) == sorted(right.replace(' ', '').lower())\n\nprint(is_anagram('listen', 'silent'))"
        },
        {
            "file": "merge_dicts.json",
            "code": "def merge_dicts(primary, secondary):\n    merged = primary.copy()\n    merged.update(secondary)\n    return merged"
        },
        {
            "file": "running_average.json",
            "code": "def running_average(values):\n    total = 0\n    averages = []\n    for index, value in enumerate(values, start=1):\n        total += value\n        averages.append(total / index)\n    return averages"
        },
        {
            "file": "find_largest.json",
            "code": "def find_largest(numbers):\n    largest = numbers[0]\n    for number in numbers[1:]:\n        if number > largest:\n            largest = number\n    return largest"
        },
        {
            "file": "json_parse.json",
            "code": "import json\n\ndef parse_payload(payload):\n    data = json.loads(payload)\n    return data.get('items', [])\n\nprint(parse_payload('{\"items\": [1, 2, 3]}'))"
        },
    ]

    for case in analyze_cases:
        data = {"code": case["code"]}
        with open(analyze_dir / case["file"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ═══════════════════════════════════════════════════════════════
    # EXPLAIN CODE TEST CASES (25 cases)
    # ═══════════════════════════════════════════════════════════════

    explain_cases = [
        {
            "file": "get_age.json",
            "code": "user = {'name': 'Alice', 'age': 30}\ndef get_age(u):\n    return u.get('age', 0)",
            "target": "get_age",
            "kind": "function"
        },
        {
            "file": "for_loop_sum.json",
            "code": "total = 0\nfor i in range(1, 11):\n    total += i\nprint(total)",
            "target": "for loop",
            "kind": "for"
        },
        {
            "file": "list_comprehension.json",
            "code": "numbers = [1, 2, 3, 4, 5]\nsquared = [x**2 for x in numbers if x > 2]\nprint(squared)",
            "target": "squared",
            "kind": "variable"
        },
        {
            "file": "class_animal.json",
            "code": "class Animal:\n    def __init__(self, name, sound):\n        self.name = name\n        self.sound = sound\n\n    def speak(self):\n        return f'{self.name} says {self.sound}'\n\ndog = Animal('Dog', 'Woof')\nprint(dog.speak())",
            "target": "Animal",
            "kind": "class"
        },
        {
            "file": "lambda_sort.json",
            "code": "students = [('Alice', 85), ('Bob', 92), ('Charlie', 78)]\nstudents.sort(key=lambda x: x[1], reverse=True)\nfor name, grade in students:\n    print(f'{name}: {grade}')",
            "target": "lambda",
            "kind": ""
        },
        {
            "file": "try_except.json",
            "code": "def safe_divide(a, b):\n    try:\n        result = a / b\n    except ZeroDivisionError:\n        result = 0\n    return result\n\nprint(safe_divide(10, 0))",
            "target": "try except",
            "kind": ""
        },
        {
            "file": "decorator.json",
            "code": "def timer(func):\n    import time\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        end = time.time()\n        print(f'{func.__name__} took {end-start:.4f}s')\n        return result\n    return wrapper\n\n@timer\ndef slow_add(a, b):\n    import time\n    time.sleep(0.1)\n    return a + b",
            "target": "timer",
            "kind": "function"
        },
        {
            "file": "while_loop.json",
            "code": "n = 10\nwhile n > 0:\n    if n % 2 == 0:\n        print(n)\n    n -= 1",
            "target": "while loop",
            "kind": "while"
        },
        {
            "file": "dict_comprehension.json",
            "code": "words = ['hello', 'world', 'python', 'code']\nword_lengths = {w: len(w) for w in words}\nprint(word_lengths)",
            "target": "word_lengths",
            "kind": "variable"
        },
        {
            "file": "generator.json",
            "code": "def even_numbers(limit):\n    n = 0\n    while n < limit:\n        if n % 2 == 0:\n            yield n\n        n += 1\n\nfor num in even_numbers(20):\n    print(num)",
            "target": "even_numbers",
            "kind": "function"
        },
        {
            "file": "normalize_name.json",
            "code": "def normalize_name(name):\n    return name.strip().title()\n\nprint(normalize_name('  ada lovelace  '))",
            "target": "normalize_name",
            "kind": "function"
        },
        {
            "file": "total_variable.json",
            "code": "total = 0\nfor number in [1, 2, 3, 4]:\n    total += number\nprint(total)",
            "target": "total",
            "kind": "variable"
        },
        {
            "file": "safe_counter.json",
            "code": "class SafeCounter:\n    def __init__(self, initial=0):\n        self.value = initial\n\n    def increment(self):\n        self.value += 1\n        return self.value\n\ncounter = SafeCounter()\nprint(counter.increment())",
            "target": "SafeCounter",
            "kind": "class"
        },
        {
            "file": "safe_counter_init.json",
            "code": "class SafeCounter:\n    def __init__(self, initial=0):\n        self.value = initial\n\n    def increment(self):\n        self.value += 1\n        return self.value",
            "target": "__init__",
            "kind": "method"
        },
        {
            "file": "reverse_words.json",
            "code": "def reverse_words(sentence):\n    words = sentence.split()\n    return ' '.join(reversed(words))\n\nprint(reverse_words('zero vision coding'))",
            "target": "reverse_words",
            "kind": "function"
        },
        {
            "file": "sorted_students.json",
            "code": "students = [('Alice', 85), ('Bob', 92), ('Charlie', 78)]\nsorted_students = sorted(students, key=lambda item: item[1], reverse=True)\nprint(sorted_students)",
            "target": "sorted_students",
            "kind": "variable"
        },
        {
            "file": "retry.json",
            "code": "def retry(operation, attempts=3):\n    for _ in range(attempts):\n        result = operation()\n        if result is not None:\n            return result\n    return None",
            "target": "retry",
            "kind": "function"
        },
        {
            "file": "main_function.json",
            "code": "def main():\n    print('start')\n    print('done')\n\nmain()",
            "target": "main",
            "kind": "function"
        },
        {
            "file": "decimal_format.json",
            "code": "price = 12.3456\nprint(f'{price:.2f}')",
            "target": "price",
            "kind": "variable"
        },
        {
            "file": "filter_even.json",
            "code": "numbers = [1, 2, 3, 4, 5, 6]\neven_numbers = [value for value in numbers if value % 2 == 0]\nprint(even_numbers)",
            "target": "even_numbers",
            "kind": "variable"
        },
        {
            "file": "context_manager.json",
            "code": "def read_first_line(path):\n    with open(path, 'r') as handle:\n        return handle.readline().strip()",
            "target": "read_first_line",
            "kind": "function"
        },
        {
            "file": "class_method.json",
            "code": "class Greeter:\n    def greet(self, name):\n        return f'Hello {name}'",
            "target": "greet",
            "kind": "method"
        },
        {
            "file": "map_lambda.json",
            "code": "numbers = [1, 2, 3]\ndoubled = list(map(lambda value: value * 2, numbers))\nprint(doubled)",
            "target": "doubled",
            "kind": "variable"
        },
        {
            "file": "count_vowels.json",
            "code": "def count_vowels(text):\n    vowels = 'aeiou'\n    return sum(1 for char in text.lower() if char in vowels)",
            "target": "count_vowels",
            "kind": "function"
        },
    ]

    for case in explain_cases:
        data = {"code": case["code"], "target": case["target"], "kind": case["kind"]}
        with open(explain_dir / case["file"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # Print summary
    print(f"Scaffolded test cases:")
    print(f"  Fixer:    {len(fixer_cases)} cases")
    print(f"  Reviewer: {len(reviewer_cases)} cases")
    print(f"  Analyze:  {len(analyze_cases)} cases")
    print(f"  Explain:  {len(explain_cases)} cases")
    print(f"  Total:    {len(fixer_cases) + len(reviewer_cases) + len(analyze_cases) + len(explain_cases)} cases")

if __name__ == "__main__":
    setup_test_cases()
