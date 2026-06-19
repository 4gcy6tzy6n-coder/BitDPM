"""BitDPM v1k held-out mixed benchmark.

This benchmark extends the v14/v15 evidence path to a 1,000-prompt validation
surface. It is intentionally deterministic and self-contained so paper runs can
cite the exact prompt set from source control.

Categories:
- arithmetic: exact short-answer numeric tasks
- factual_constants: short factual/numeric constants
- commonsense: short factual commonsense
- code: qualitative programming prompts
- chinese: qualitative Chinese prompts
- reasoning: qualitative short reasoning prompts
"""

from __future__ import annotations

import math


def _arithmetic() -> tuple[list[str], list[str]]:
    prompts: list[str] = []
    answers: list[str] = []

    # 50 additions
    for i in range(50):
        a = 17 + i * 7
        b = 23 + i * 5
        prompts.append(f"What is {a} + {b}?")
        answers.append(str(a + b))

    # 40 multiplications
    for i in range(40):
        a = 6 + (i % 20)
        b = 7 + ((i * 3) % 18)
        prompts.append(f"What is {a} times {b}?")
        answers.append(str(a * b))

    # 40 percentages with integer answers
    pct_values = [5, 10, 12, 15, 20, 25, 30, 40]
    bases = [40, 50, 80, 100, 120, 160, 200, 240, 300, 400]
    for i in range(40):
        pct = pct_values[i % len(pct_values)]
        value = bases[(i * 3) % len(bases)]
        prompts.append(f"What is {pct}% of {value}?")
        answers.append(str((pct * value) // 100))

    # 35 square roots
    for n in range(6, 41):
        prompts.append(f"What is the square root of {n * n}?")
        answers.append(str(n))

    # 30 powers
    power_pairs = [(2, e) for e in range(3, 13)] + [(3, e) for e in range(2, 8)] + [(4, e) for e in range(2, 6)] + [(5, e) for e in range(2, 6)] + [(6, 2), (7, 2), (8, 2), (9, 2), (10, 2), (11, 2)]
    for base, exp in power_pairs[:30]:
        prompts.append(f"What is {base}^{exp}?")
        answers.append(str(base**exp))

    # 25 distance/geometry prompts using Pythagorean triples.
    triples = [
        (3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29),
        (12, 16, 20), (9, 12, 15), (15, 20, 25), (10, 24, 26), (16, 30, 34),
        (18, 24, 30), (21, 28, 35), (24, 32, 40), (27, 36, 45), (30, 40, 50),
        (33, 44, 55), (36, 48, 60), (39, 52, 65), (42, 56, 70), (45, 60, 75),
        (48, 64, 80), (51, 68, 85), (54, 72, 90), (57, 76, 95), (60, 80, 100),
    ]
    for x, y, d in triples:
        prompts.append(f"What is the distance from (0,0) to ({x},{y})?")
        answers.append(str(d))

    # 20 means
    for i in range(20):
        start = 2 + i
        values = [start, start + 4, start + 8, start + 12]
        mean_value = sum(values) / len(values)
        joined = ", ".join(str(v) for v in values[:-1]) + f", and {values[-1]}"
        prompts.append(f"What is the mean of {joined}?")
        answers.append(str(int(mean_value) if mean_value.is_integer() else mean_value))

    # 10 gcd/lcm mixed prompts
    pairs = [(24, 36), (12, 18), (21, 28), (30, 45), (16, 40)]
    for a, b in pairs:
        prompts.append(f"What is the GCD of {a} and {b}?")
        answers.append(str(math.gcd(a, b)))
        prompts.append(f"What is the LCM of {a} and {b}?")
        answers.append(str(abs(a * b) // math.gcd(a, b)))

    return prompts, answers


def _factual_constants() -> tuple[list[str], list[str]]:
    facts = [
        ("What is the speed of light in vacuum in meters per second?", "299"),
        ("What is the approximate acceleration due to gravity on Earth in m/s^2?", "9.8"),
        ("What is Avogadro's number approximately?", "6.02"),
        ("What is the boiling point of water in Celsius?", "100"),
        ("What is the freezing point of water in Celsius?", "0"),
        ("How many centimeters are in one meter?", "100"),
        ("How many millimeters are in one centimeter?", "10"),
        ("How many bytes are in one kilobyte in binary computing?", "1024"),
        ("What is the chemical symbol for gold?", "au"),
        ("What is the chemical symbol for sodium?", "na"),
        ("What is the chemical symbol for oxygen?", "o"),
        ("What is the chemical symbol for carbon?", "c"),
        ("How many minutes are in one hour?", "60"),
        ("How many seconds are in one minute?", "60"),
        ("How many hours are in one day?", "24"),
    ]
    variants = [
        "{}",
        "Answer briefly: {}",
        "Give the standard value: {}",
        "In one short answer, {}",
        "State the commonly used answer: {}",
        "Use only the answer: {}",
        "Give a concise answer: {}",
        "Reply with the standard answer: {}",
        "What is the expected short answer? {}",
        "Provide the usual value: {}",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for prompt, answer in facts:
        for variant in variants:
            prompts.append(variant.format(prompt))
            answers.append(answer)
    return prompts, answers


def _commonsense() -> tuple[list[str], list[str]]:
    facts = [
        ("What is the capital of France?", "paris"),
        ("Which planet is known as the Red Planet?", "mars"),
        ("What color is the sky on a clear day?", "blue"),
        ("Which ocean is the largest on Earth?", "pacific"),
        ("How many continents are commonly counted on Earth?", "7"),
        ("Which organ pumps blood through the body?", "heart"),
        ("What do bees produce?", "honey"),
        ("Which gas do plants absorb from the atmosphere?", "carbon dioxide"),
        ("What is the tallest mountain in the world?", "everest"),
        ("Which country is famous for the Eiffel Tower?", "france"),
        ("What is the main language spoken in Spain?", "spanish"),
        ("How many days are in a leap year?", "366"),
        ("What does a thermometer measure?", "temperature"),
        ("What do we call frozen water?", "ice"),
        ("Which star is closest to Earth?", "sun"),
        ("What is the natural satellite of Earth?", "moon"),
        ("What liquid do humans drink to stay hydrated?", "water"),
        ("What do you call a person who teaches students?", "teacher"),
        ("Which sense uses the ears?", "hearing"),
        ("What fruit is typically yellow and curved?", "banana"),
        ("What do you call the place where books are kept for borrowing?", "library"),
        ("What do you call the meal eaten in the morning?", "breakfast"),
        ("Which part of the body is used for seeing?", "eye"),
        ("What is the common name for H2O?", "water"),
        ("What do you call a shape with three sides?", "triangle"),
        ("What color are most healthy leaves?", "green"),
        ("What is used to unlock a door?", "key"),
        ("What do you call a person who treats sick people?", "doctor"),
        ("What machine is used to take photographs?", "camera"),
        ("What do fish use to breathe underwater?", "gills"),
        ("What do you call money borrowed that must be repaid?", "loan"),
        ("Which room is usually used for cooking?", "kitchen"),
        ("What is the common name for a young cat?", "kitten"),
        ("What object protects you from rain?", "umbrella"),
        ("What is the opposite of empty?", "full"),
        ("What is the opposite of hot?", "cold"),
        ("What is the opposite of up?", "down"),
        ("What is the opposite of left?", "right"),
        ("What vehicle runs on rails?", "train"),
        ("What tool is used to cut paper?", "scissors"),
    ]
    variants = [
        "{}",
        "Answer briefly: {}",
        "Give the common answer: {}",
        "In one short answer, {}",
        "Use a concise answer: {}",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for prompt, answer in facts:
        for variant in variants:
            prompts.append(variant.format(prompt))
            answers.append(answer)
    return prompts, answers


def _code() -> list[str]:
    templates = [
        "Write a Python function that returns the sum of a list of integers.",
        "Write Python code to reverse a string.",
        "Explain what a hash map is in one paragraph.",
        "Write a SQL query to select all rows from a users table.",
        "What is the time complexity of binary search?",
        "Write a regex that roughly validates an email address.",
        "Explain the difference between GET and POST.",
        "Write Python code to count words in a string.",
        "What is a unit test?",
        "Explain recursion with a short example.",
    ]
    prompts = []
    for round_idx in range(15):
        for prompt in templates:
            prompts.append(f"{prompt} Use concise wording. Variant {round_idx + 1}.")
    return prompts


def _chinese() -> list[str]:
    base = [
        "中国的首都是哪个城市？",
        "请用中文解释什么是人工智能。",
        "一年有多少个月？",
        "请写一句关于学习的中文句子。",
        "水的化学式是什么？",
        "太阳从哪个方向升起？",
        "什么是自然语言处理？",
        "中秋节通常会吃什么？",
        "请列举三种水果。",
        "长城位于哪个国家？",
    ]
    prompts = []
    for round_idx in range(15):
        for prompt in base:
            prompts.append(f"{prompt} 请简短回答。版本{round_idx + 1}。")
    return prompts


def _reasoning() -> list[str]:
    templates = [
        "If a book costs $20 after a 20% discount, what was the original price?",
        "A farmer has chickens and cows. There are 10 heads and 28 legs. How many chickens are there?",
        "If today is Monday, what day will it be in 10 days?",
        "Two people start at the same point and walk in opposite directions for 3 km. How far apart are they?",
        "You flip a fair coin twice. What is the probability of two heads?",
        "A car travels 30 km in 30 minutes. What is its average speed in km/h?",
        "If one box holds 6 bottles, how many boxes are needed for 26 bottles?",
        "What is heavier: one kilogram of iron or one kilogram of cotton?",
        "If all roses are flowers and some flowers fade quickly, must all roses fade quickly?",
        "A doctor gives you 3 pills and says take one every half hour. How long will the pills last?",
    ]
    prompts = []
    for round_idx in range(10):
        for prompt in templates:
            prompts.append(f"{prompt} Explain briefly. Variant {round_idx + 1}.")
    return prompts


_ARITHMETIC_PROMPTS, _ARITHMETIC_ANSWERS = _arithmetic()
_FACTUAL_PROMPTS, _FACTUAL_ANSWERS = _factual_constants()
_COMMONSENSE_PROMPTS, _COMMONSENSE_ANSWERS = _commonsense()

V1K_EVAL_PROMPTS: dict[str, list[str]] = {
    "arithmetic": _ARITHMETIC_PROMPTS,
    "factual_constants": _FACTUAL_PROMPTS,
    "commonsense": _COMMONSENSE_PROMPTS,
    "code": _code(),
    "chinese": _chinese(),
    "reasoning": _reasoning(),
}

V1K_EXPECTED_ANSWERS: dict[str, list[str]] = {
    "arithmetic": _ARITHMETIC_ANSWERS,
    "factual_constants": _FACTUAL_ANSWERS,
    "commonsense": _COMMONSENSE_ANSWERS,
    "code": [],
    "chinese": [],
    "reasoning": [],
}


assert sum(len(v) for v in V1K_EVAL_PROMPTS.values()) == 1000
assert all(
    len(V1K_EXPECTED_ANSWERS.get(category, [])) in (0, len(prompts))
    for category, prompts in V1K_EVAL_PROMPTS.items()
)
