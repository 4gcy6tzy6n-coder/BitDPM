"""BitDPM v15 router-validation benchmark.

v14 showed that sparse correction opportunities exist at 300-sample scale, but
deployable routing must satisfy a stricter safety requirement. This benchmark is
not a broad capability benchmark; it is a validation slice for router admission.
It keeps the current safe arithmetic router features, adds risky arithmetic
controls, and expands factual/commonsense candidate regions.
"""

from __future__ import annotations

import math


def _multiplication() -> tuple[list[str], list[str]]:
    pairs = [
        (9, 8), (12, 11), (21, 6), (25, 4), (14, 13),
        (16, 15), (18, 7), (22, 5), (17, 9), (13, 12),
    ]
    variants = [
        "What is {a} times {b}?",
        "Compute {a} times {b}.",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for a, b in pairs:
        for variant in variants:
            prompts.append(variant.format(a=a, b=b))
            answers.append(str(a * b))
    return prompts, answers


def _core_mixed() -> tuple[list[str], list[str]]:
    prompts: list[str] = []
    answers: list[str] = []

    for x, y in [(3, 4), (5, 12), (8, 15), (7, 24), (9, 12), (20, 21), (12, 16), (15, 20)]:
        prompts.append(f"What is the distance from (0,0) to ({x},{y})?")
        answers.append(str(int(math.sqrt(x * x + y * y))))

    for value, answer in [(1000, 3), (100000, 5), (100, 2), (1000000, 6)]:
        prompts.append(f"What is log base 10 of {value}?")
        answers.append(str(answer))

    means = [
        ([4, 8, 12, 16], 10),
        ([5, 10, 15, 20], 12.5),
        ([3, 6, 9, 12], 7.5),
        ([2, 4, 6, 8], 5),
        ([10, 20, 30, 40], 25),
        ([1, 3, 5, 7], 4),
        ([6, 12, 18, 24], 15),
        ([8, 16, 24, 32], 20),
    ]
    for values, answer in means:
        joined = ", ".join(str(v) for v in values[:-1]) + f", and {values[-1]}"
        prompts.append(f"What is the mean of {joined}?")
        answers.append(str(answer))

    return prompts, answers


def _risky_arithmetic_controls() -> tuple[list[str], list[str]]:
    prompts: list[str] = []
    answers: list[str] = []

    for a, b in [(37, 45), (56, 29), (123, 77), (208, 315), (91, 64), (72, 38), (145, 255), (333, 444), (88, 67), (19, 27)]:
        prompts.append(f"What is {a} + {b}?")
        answers.append(str(a + b))

    for n in [144, 169, 196, 225, 256, 81, 121, 400, 625, 900]:
        prompts.append(f"What is the square root of {n}?")
        answers.append(str(int(math.sqrt(n))))

    return prompts, answers


def _factual_constants() -> tuple[list[str], list[str]]:
    facts = [
        ("What is the approximate acceleration due to gravity on Earth in m/s^2?", "9.8"),
        ("What is the speed of light in vacuum in meters per second?", "299"),
        ("What is Avogadro's number approximately?", "6.02"),
        ("What is the boiling point of water in Celsius?", "100"),
        ("What is the freezing point of water in Celsius?", "0"),
    ]
    variants = [
        "{}",
        "Answer briefly: {}",
        "Give the standard value: {}",
        "In one short answer, {}",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for prompt, answer in facts:
        for variant in variants:
            prompts.append(variant.format(prompt))
            answers.append(answer)
    return prompts, answers


def _commonsense_repairs() -> tuple[list[str], list[str]]:
    facts = [
        ("How many continents are commonly counted on Earth?", "7"),
        ("Which animal is often called the king of the jungle?", "lion"),
        ("What do you call money borrowed that must be repaid?", "loan"),
        ("Which star is closest to Earth?", "sun"),
        ("What fruit is typically yellow and curved?", "banana"),
    ]
    variants = [
        "{}",
        "Answer briefly: {}",
        "Give the common answer: {}",
        "In one short answer, {}",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for prompt, answer in facts:
        for variant in variants:
            prompts.append(variant.format(prompt))
            answers.append(answer)
    return prompts, answers


def _commonsense_controls() -> tuple[list[str], list[str]]:
    facts = [
        ("What is the capital of France?", "paris"),
        ("Which planet is known as the Red Planet?", "mars"),
        ("Which organ pumps blood through the body?", "heart"),
        ("What do bees produce?", "honey"),
        ("What is the natural satellite of Earth?", "moon"),
        ("What is the opposite of hot?", "cold"),
        ("What do we call frozen water?", "ice"),
        ("What vehicle runs on rails?", "train"),
        ("What is used to unlock a door?", "key"),
        ("What is the opposite of empty?", "full"),
    ]
    prompts = [prompt for prompt, _ in facts]
    answers = [answer for _, answer in facts]
    prompts.extend(f"Answer briefly: {prompt}" for prompt, _ in facts)
    answers.extend(answer for _, answer in facts)
    return prompts, answers


_MULT_PROMPTS, _MULT_ANSWERS = _multiplication()
_CORE_PROMPTS, _CORE_ANSWERS = _core_mixed()
_RISKY_PROMPTS, _RISKY_ANSWERS = _risky_arithmetic_controls()
_FACT_PROMPTS, _FACT_ANSWERS = _factual_constants()
_COMMON_REPAIR_PROMPTS, _COMMON_REPAIR_ANSWERS = _commonsense_repairs()
_COMMON_CONTROL_PROMPTS, _COMMON_CONTROL_ANSWERS = _commonsense_controls()

V15_EVAL_PROMPTS: dict[str, list[str]] = {
    "router_multiplication": _MULT_PROMPTS,
    "router_core_mixed": _CORE_PROMPTS,
    "router_risky_arithmetic": _RISKY_PROMPTS,
    "router_factual_constants": _FACT_PROMPTS,
    "router_commonsense_repairs": _COMMON_REPAIR_PROMPTS,
    "router_commonsense_controls": _COMMON_CONTROL_PROMPTS,
}

V15_EXPECTED_ANSWERS: dict[str, list[str]] = {
    "router_multiplication": _MULT_ANSWERS,
    "router_core_mixed": _CORE_ANSWERS,
    "router_risky_arithmetic": _RISKY_ANSWERS,
    "router_factual_constants": _FACT_ANSWERS,
    "router_commonsense_repairs": _COMMON_REPAIR_ANSWERS,
    "router_commonsense_controls": _COMMON_CONTROL_ANSWERS,
}


assert sum(len(v) for v in V15_EVAL_PROMPTS.values()) == 120
assert all(
    len(V15_EXPECTED_ANSWERS[category]) == len(prompts)
    for category, prompts in V15_EVAL_PROMPTS.items()
)

