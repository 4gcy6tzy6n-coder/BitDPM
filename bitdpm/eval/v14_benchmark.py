"""BitDPM v14 stratified 300-sample benchmark.

v08 established that BitDPM utility is sparse on a 100-sample benchmark. This
module expands the evaluation surface to 300 prompts so coverage estimates are
less dominated by a few hand-picked arithmetic items.
"""

from __future__ import annotations

import math


def _arithmetic() -> tuple[list[str], list[str]]:
    prompts: list[str] = []
    answers: list[str] = []

    for a, b in [(18, 24), (37, 45), (56, 29), (123, 77), (208, 315), (91, 64), (72, 38), (145, 255)]:
        prompts.append(f"What is {a} + {b}?")
        answers.append(str(a + b))

    for a, b in [(9, 8), (12, 11), (14, 13), (16, 15), (21, 6), (25, 4), (32, 3), (18, 7)]:
        prompts.append(f"What is {a} times {b}?")
        answers.append(str(a * b))

    for pct, value in [(15, 80), (25, 200), (12, 50), (30, 90), (5, 240), (40, 75), (60, 45), (20, 125)]:
        prompts.append(f"What is {pct}% of {value}?")
        answers.append(str(pct * value // 100 if pct * value % 100 == 0 else pct * value / 100))

    for n in [144, 169, 196, 225, 256, 81, 121, 400]:
        prompts.append(f"What is the square root of {n}?")
        answers.append(str(int(math.sqrt(n))))

    for base, exp in [(2, 10), (3, 4), (5, 3), (10, 3), (4, 3), (6, 2), (7, 2), (2, 8)]:
        prompts.append(f"What is {base}^{exp}?")
        answers.append(str(base**exp))

    for x, y in [(3, 4), (5, 12), (8, 15), (7, 24), (6, 8)]:
        prompts.append(f"What is the distance from (0,0) to ({x},{y})?")
        answers.append(str(int(math.sqrt(x * x + y * y))))

    prompts.extend([
        "What is log base 10 of 1000?",
        "What is log base 10 of 100000?",
        "What is the mean of 4, 8, 12, and 16?",
        "What is the GCD of 24 and 36?",
        "What is the LCM of 12 and 18?",
    ])
    answers.extend(["3", "5", "10", "12", "36"])

    return prompts, answers


def _factual_constants() -> tuple[list[str], list[str]]:
    facts = [
        ("What is the speed of light in vacuum in meters per second?", "299"),
        ("What is the approximate acceleration due to gravity on Earth in m/s^2?", "9.8"),
        ("What is Avogadro's number approximately?", "6.02"),
        ("What is the chemical symbol for gold?", "au"),
        ("What is the chemical symbol for sodium?", "na"),
        ("What is the boiling point of water in Celsius?", "100"),
        ("What is the freezing point of water in Celsius?", "0"),
        ("How many bytes are in one kilobyte in binary computing?", "1024"),
        ("How many centimeters are in one meter?", "100"),
        ("How many millimeters are in one centimeter?", "10"),
    ]
    variants = [
        "{}",
        "Answer briefly: {}",
        "Give the standard value: {}",
        "In one short answer, {}",
        "State the commonly used answer: {}",
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
        ("Which animal is often called the king of the jungle?", "lion"),
        ("How many days are in a leap year?", "366"),
        ("What is the largest mammal?", "blue whale"),
        ("Who wrote Romeo and Juliet?", "shakespeare"),
        ("What does a thermometer measure?", "temperature"),
        ("What do we call frozen water?", "ice"),
        ("Which star is closest to Earth?", "sun"),
        ("What is the main ingredient in bread?", "flour"),
        ("Which direction does the sun rise from?", "east"),
        ("What do plants need from sunlight to make food?", "light"),
        ("What tool is used to cut paper?", "scissors"),
        ("What vehicle runs on rails?", "train"),
        ("What is a baby dog called?", "puppy"),
        ("What is the opposite of hot?", "cold"),
        ("What do you use to tell time on your wrist?", "watch"),
        ("Which season comes after winter?", "spring"),
        ("What is the natural satellite of Earth?", "moon"),
        ("What liquid do humans drink to stay hydrated?", "water"),
        ("What do you call a person who teaches students?", "teacher"),
        ("Which sense uses the ears?", "hearing"),
        ("What is the opposite of day?", "night"),
        ("What fruit is typically yellow and curved?", "banana"),
        ("What do you call the place where books are kept for borrowing?", "library"),
        ("What do you call the meal eaten in the morning?", "breakfast"),
        ("What is the opposite of up?", "down"),
        ("Which part of the body is used for seeing?", "eye"),
        ("What is the common name for H2O?", "water"),
        ("What do you call a shape with three sides?", "triangle"),
        ("What color are most healthy leaves?", "green"),
        ("What is used to unlock a door?", "key"),
        ("What do you call a person who treats sick people?", "doctor"),
        ("What machine is used to take photographs?", "camera"),
        ("What do fish use to breathe underwater?", "gills"),
        ("What is the opposite of left?", "right"),
        ("What do you call money borrowed that must be repaid?", "loan"),
        ("Which room is usually used for cooking?", "kitchen"),
        ("What is the common name for a young cat?", "kitten"),
        ("What object protects you from rain?", "umbrella"),
        ("What is the opposite of empty?", "full"),
    ]
    return [p for p, _ in facts], [a for _, a in facts]


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
    for round_idx in range(5):
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
    for round_idx in range(5):
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
    for round_idx in range(5):
        for prompt in templates:
            prompts.append(f"{prompt} Explain briefly. Variant {round_idx + 1}.")
    return prompts


_ARITHMETIC_PROMPTS, _ARITHMETIC_ANSWERS = _arithmetic()
_FACTUAL_PROMPTS, _FACTUAL_ANSWERS = _factual_constants()
_COMMONSENSE_PROMPTS, _COMMONSENSE_ANSWERS = _commonsense()

V14_EVAL_PROMPTS: dict[str, list[str]] = {
    "arithmetic": _ARITHMETIC_PROMPTS,
    "factual_constants": _FACTUAL_PROMPTS,
    "commonsense": _COMMONSENSE_PROMPTS,
    "code": _code(),
    "chinese": _chinese(),
    "reasoning": _reasoning(),
}

V14_EXPECTED_ANSWERS: dict[str, list[str]] = {
    "arithmetic": _ARITHMETIC_ANSWERS,
    "factual_constants": _FACTUAL_ANSWERS,
    "commonsense": _COMMONSENSE_ANSWERS,
    "code": [],
    "chinese": [],
    "reasoning": [],
}


assert sum(len(v) for v in V14_EVAL_PROMPTS.values()) == 300
assert all(
    len(V14_EXPECTED_ANSWERS.get(category, [])) in (0, len(prompts))
    for category, prompts in V14_EVAL_PROMPTS.items()
)
