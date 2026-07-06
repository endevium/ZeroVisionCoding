from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class TestCase:
    prompt: str
    expected: str


def _make_cases(n: int, seed: int = 1234) -> list[TestCase]:
    """
    Generates deterministic test cases.
    You can customize these to match what your braille input system should produce.
    """
    rng = random.Random(seed)

    base_tokens = [
        "a", "b", "c", "z",
        "cat", "dog", "python", "variable", "function",
        "print", "hello", "world",
        "(", ")", "[", "]", "{", "}",
        '"', "'", ",", ".", ":", ";",
        "=", "==", "!=", "<", ">", "<=", ">=",
        "_", "-", "+", "*", "/", "\\",
        "space", "tab", "new line",
        "if", "else", "for", "while", "try", "except",
    ]

    cases: list[TestCase] = []

    def add(prompt: str, expected: str) -> None:
        cases.append(TestCase(prompt=prompt, expected=expected))

    add("Type the word 'hello'", "hello")
    add("Type: print(\"hi\")", 'print("hi")')
    add("Type: ( )", "()")
    add("Type: a_b", "a_b")
    add("Type: x == 3", "x == 3")

    while len(cases) < n:
        token = rng.choice(base_tokens)

        if token == "space":
            expected = " "
            prompt = "Enter a single space"
        else:
            expected = token
            prompt = f"Type exactly: {repr(token)}"

        add(prompt, expected)

    return cases[:n]


def run_accuracy_test(total_tests: int = 50, seed: int = 1234) -> None:
    cases = _make_cases(total_tests, seed=seed)

    correct = 0
    per_test_times_s: list[float] = []

    for i, tc in enumerate(cases, start=1):
        print()
        print(f"Test {i}/{total_tests}")
        print(tc.prompt)

        t0 = time.perf_counter()
        got = input("> ")
        t1 = time.perf_counter()
        per_test_times_s.append(t1 - t0)

        # Normalize common user inputs for convenience:
        # allow typing "\t" to mean tab, "\n" to mean newline, "\s" to mean space
        if got == r"\t":
            got_norm = "\t"
        elif got == r"\n":
            got_norm = "\n"
        elif got == r"\s":
            got_norm = " "
        else:
            got_norm = got

        if got_norm == tc.expected:
            correct += 1
            print("OK")
        else:
            exp_show = tc.expected
            if tc.expected == " ":
                exp_show = "' ' (space)"
            print(f"WRONG (expected {exp_show!r}, got {got_norm!r})")

    acc = (correct / total_tests) * 100.0 if total_tests else 0.0
    avg_time_s = (sum(per_test_times_s) / len(per_test_times_s)) if per_test_times_s else 0.0

    print("\nBraille Input Accuracy Test\n")
    print(f"Total Tests: {total_tests}")
    print(f"Correct Outputs: {correct}")
    print(f"Accuracy: {acc:.0f}%" if acc.is_integer() else f"Accuracy: {acc:.1f}%")


def main() -> None:
    run_accuracy_test(total_tests=50, seed=1234)


if __name__ == "__main__":
    main()