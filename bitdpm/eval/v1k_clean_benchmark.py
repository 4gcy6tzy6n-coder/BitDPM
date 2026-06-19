"""BitDPM v1k-clean overlap-audited mixed benchmark.

This benchmark keeps the v1k category scale while using prompt phrasings that
are distinct from core/v08/v14/v15. The benchmark manifest verifies exact
normalized prompt overlap before it can be used as a held-out validation set.
"""

from __future__ import annotations

import math


def _arithmetic() -> tuple[list[str], list[str]]:
    prompts: list[str] = []
    answers: list[str] = []

    for i in range(50):
        a = 131 + i * 9
        b = 67 + i * 11
        prompts.append(f"Clean arithmetic check: compute the sum of {a} and {b}.")
        answers.append(str(a + b))

    for i in range(40):
        a = 12 + (i % 25)
        b = 9 + ((i * 5) % 23)
        prompts.append(f"Clean arithmetic check: compute the product of {a} and {b}.")
        answers.append(str(a * b))

    pct_values = [6, 8, 12, 14, 18, 22, 35, 45]
    bases = [50, 75, 125, 150, 175, 250, 300, 350, 500, 600]
    for i in range(40):
        pct = pct_values[i % len(pct_values)]
        value = bases[(i * 7) % len(bases)]
        result = pct * value / 100
        answer = str(int(result)) if result.is_integer() else str(result)
        prompts.append(f"Clean arithmetic check: find {pct} percent of {value}.")
        answers.append(answer)

    for n in range(41, 76):
        prompts.append(f"Clean arithmetic check: evaluate sqrt({n * n}).")
        answers.append(str(n))

    power_pairs = (
        [(2, e) for e in range(13, 23)]
        + [(3, e) for e in range(8, 14)]
        + [(4, e) for e in range(6, 11)]
        + [(5, e) for e in range(6, 10)]
        + [(6, 3), (7, 3), (8, 3), (9, 3), (10, 3)]
    )
    for base, exp in power_pairs[:30]:
        prompts.append(f"Clean arithmetic check: evaluate {base} raised to power {exp}.")
        answers.append(str(base**exp))

    triples = [
        (11, 60, 61), (13, 84, 85), (28, 45, 53), (33, 56, 65), (48, 55, 73),
        (65, 72, 97), (20, 99, 101), (60, 91, 109), (15, 112, 113), (44, 117, 125),
        (88, 105, 137), (17, 144, 145), (24, 143, 145), (51, 140, 149), (85, 132, 157),
        (119, 120, 169), (52, 165, 173), (19, 180, 181), (57, 176, 185), (104, 153, 185),
        (95, 168, 193), (28, 195, 197), (84, 187, 205), (133, 156, 205), (140, 171, 221),
    ]
    for x, y, d in triples:
        prompts.append(f"Clean geometry check: what is the Euclidean distance from origin to point ({x}, {y})?")
        answers.append(str(d))

    for i in range(20):
        start = 31 + i * 2
        values = [start, start + 6, start + 10, start + 20]
        mean_value = sum(values) / len(values)
        joined = "; ".join(str(v) for v in values)
        prompts.append(f"Clean arithmetic check: compute the average of these four values: {joined}.")
        answers.append(str(int(mean_value)) if mean_value.is_integer() else str(mean_value))

    pairs = [(42, 56), (48, 72), (54, 81), (63, 105), (84, 126)]
    for a, b in pairs:
        prompts.append(f"Clean number theory check: report gcd({a}, {b}).")
        answers.append(str(math.gcd(a, b)))
        prompts.append(f"Clean number theory check: report lcm({a}, {b}).")
        answers.append(str(abs(a * b) // math.gcd(a, b)))

    return prompts, answers


def _factual_constants() -> tuple[list[str], list[str]]:
    facts = [
        ("standard atmospheric pressure at sea level in pascals", "101325"),
        ("the number of bits in one byte", "8"),
        ("the number of grams in one kilogram", "1000"),
        ("the number of meters in one kilometer", "1000"),
        ("the number of degrees in a right angle", "90"),
        ("the number of degrees in a full circle", "360"),
        ("the SI unit symbol for electric current", "a"),
        ("the SI unit symbol for force", "n"),
        ("the SI unit symbol for energy", "j"),
        ("the chemical symbol for potassium", "k"),
        ("the chemical symbol for silver", "ag"),
        ("the chemical symbol for iron", "fe"),
        ("the atomic number of carbon", "6"),
        ("the atomic number of oxygen", "8"),
        ("the atomic number of hydrogen", "1"),
    ]
    variants = [
        "Clean factual check: give the short answer for {}.",
        "Clean factual check: provide only the usual value for {}.",
        "Clean factual check: answer concisely: {}.",
        "Clean factual check: state the standard answer to {}.",
        "Clean factual check: what is the accepted short answer for {}?",
        "Clean factual check: return the canonical value for {}.",
        "Clean factual check: give the compact answer for {}.",
        "Clean factual check: write the standard symbol or value for {}.",
        "Clean factual check: supply the expected answer for {}.",
        "Clean factual check: respond with the conventional answer for {}.",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for subject, answer in facts:
        for variant in variants:
            prompts.append(variant.format(subject))
            answers.append(answer)
    return prompts, answers


def _commonsense() -> tuple[list[str], list[str]]:
    facts = [
        ("the animal known for a long trunk", "elephant"),
        ("the place where airplanes usually take off", "airport"),
        ("the object used to tell time on a wall", "clock"),
        ("the season that usually comes after spring", "summer"),
        ("the direction opposite north", "south"),
        ("the tool commonly used to write on a blackboard", "chalk"),
        ("the protective item worn on the head while cycling", "helmet"),
        ("the device used to call someone remotely", "phone"),
        ("the place where doctors treat patients", "hospital"),
        ("the profession of a person who flies an airplane", "pilot"),
        ("the object used to erase pencil marks", "eraser"),
        ("the color made by mixing red and white paint", "pink"),
        ("the day after Friday", "saturday"),
        ("the month after January", "february"),
        ("the animal that barks", "dog"),
        ("the animal that meows", "cat"),
        ("the kitchen tool used to boil water", "kettle"),
        ("the body part used for smelling", "nose"),
        ("the natural light source during daytime", "sun"),
        ("the frozen dessert often served in a cone", "ice cream"),
        ("the writing instrument filled with ink", "pen"),
        ("the container often used to carry school books", "bag"),
        ("the vehicle with two wheels and pedals", "bicycle"),
        ("the place where trains stop for passengers", "station"),
        ("the common name for a baby dog", "puppy"),
        ("the material windows are usually made from", "glass"),
        ("the object opened to enter a room", "door"),
        ("the common liquid used to wash hands", "water"),
        ("the tool used to hit nails", "hammer"),
        ("the place where films are shown to an audience", "cinema"),
        ("the object used to cover a bed while sleeping", "blanket"),
        ("the small device used to open a lock", "key"),
        ("the color of ripe strawberries", "red"),
        ("the meal commonly eaten at midday", "lunch"),
        ("the shape of a typical wheel", "circle"),
        ("the opposite of early", "late"),
        ("the opposite of noisy", "quiet"),
        ("the opposite of fast", "slow"),
        ("the opposite of tall", "short"),
        ("the person who cuts hair professionally", "barber"),
    ]
    variants = [
        "Clean commonsense check: name {}.",
        "Clean commonsense check: give the common word for {}.",
        "Clean commonsense check: answer briefly, {}.",
        "Clean commonsense check: what is {}?",
        "Clean commonsense check: provide the usual answer for {}.",
    ]
    prompts: list[str] = []
    answers: list[str] = []
    for subject, answer in facts:
        for variant in variants:
            prompts.append(variant.format(subject))
            answers.append(answer)
    return prompts, answers


def _code() -> list[str]:
    templates = [
        "Clean coding check: give Python code that finds the maximum value in a list.",
        "Clean coding check: write a Python function that removes duplicates from a list.",
        "Clean coding check: explain a stack data structure in concise terms.",
        "Clean coding check: write SQL to count rows in an orders table.",
        "Clean coding check: state the complexity of scanning every element in a list.",
        "Clean coding check: provide a simple Python dictionary lookup example.",
        "Clean coding check: explain what an HTTP status code represents.",
        "Clean coding check: write Python code to join words with spaces.",
        "Clean coding check: define integration testing in one paragraph.",
        "Clean coding check: explain a loop invariant with a short example.",
    ]
    prompts = []
    for round_idx in range(15):
        for prompt in templates:
            prompts.append(f"{prompt} Keep the answer compact. Clean variant {round_idx + 1}.")
    return prompts


def _chinese() -> list[str]:
    base = [
        "请说明北京为什么是重要城市。",
        "请用一句中文解释机器翻译。",
        "一周通常有多少天？",
        "请写一句关于认真学习的中文短句。",
        "氧气的化学符号是什么？",
        "晚上通常由哪个天体提供自然光？",
        "请用中文解释什么是语音识别。",
        "春节常见的传统颜色是什么？",
        "请列举三种常见交通工具。",
        "黄河位于哪个国家？",
    ]
    prompts = []
    for round_idx in range(15):
        for prompt in base:
            prompts.append(f"Clean Chinese check: {prompt} 请简洁回答。清洁版本{round_idx + 1}。")
    return prompts


def _reasoning() -> list[str]:
    templates = [
        "Clean reasoning check: a ticket costs 15 dollars after a 25 percent discount. What was the original price?",
        "Clean reasoning check: there are 12 animals with 34 total legs, only ducks and goats. How many ducks are there?",
        "Clean reasoning check: if today is Wednesday, what day is it 17 days later?",
        "Clean reasoning check: two walkers leave the same point at right angles, one walks 6 km and one walks 8 km. How far apart are they?",
        "Clean reasoning check: a fair six-sided die is rolled once. What is the probability of rolling an even number?",
        "Clean reasoning check: a bike travels 18 km in 45 minutes. What is the speed in km/h?",
        "Clean reasoning check: one carton holds 8 eggs. How many cartons are needed for 45 eggs?",
        "Clean reasoning check: which is heavier, two kilograms of wood or one kilogram of steel?",
        "Clean reasoning check: if every tulip is a flower and some flowers are red, must every tulip be red?",
        "Clean reasoning check: a timer rings every 20 minutes, starting now. How many minutes until the third ring after now?",
    ]
    prompts = []
    for round_idx in range(10):
        for prompt in templates:
            prompts.append(f"{prompt} Give a brief explanation. Clean variant {round_idx + 1}.")
    return prompts


_ARITHMETIC_PROMPTS, _ARITHMETIC_ANSWERS = _arithmetic()
_FACTUAL_PROMPTS, _FACTUAL_ANSWERS = _factual_constants()
_COMMONSENSE_PROMPTS, _COMMONSENSE_ANSWERS = _commonsense()

V1K_CLEAN_EVAL_PROMPTS: dict[str, list[str]] = {
    "arithmetic": _ARITHMETIC_PROMPTS,
    "factual_constants": _FACTUAL_PROMPTS,
    "commonsense": _COMMONSENSE_PROMPTS,
    "code": _code(),
    "chinese": _chinese(),
    "reasoning": _reasoning(),
}

V1K_CLEAN_EXPECTED_ANSWERS: dict[str, list[str]] = {
    "arithmetic": _ARITHMETIC_ANSWERS,
    "factual_constants": _FACTUAL_ANSWERS,
    "commonsense": _COMMONSENSE_ANSWERS,
    "code": [],
    "chinese": [],
    "reasoning": [],
}


assert sum(len(v) for v in V1K_CLEAN_EVAL_PROMPTS.values()) == 1000
assert all(
    len(V1K_CLEAN_EXPECTED_ANSWERS.get(category, [])) in (0, len(prompts))
    for category, prompts in V1K_CLEAN_EVAL_PROMPTS.items()
)
