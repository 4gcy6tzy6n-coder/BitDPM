"""Block training infrastructure for BitDPM.

Provides category-specific datasets and training loops for
training independent ParameterBlocks on different task types.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from bitdpm.models.backbone import BackboneModel
from bitdpm.models.patch_lora import BlockInjector
from bitdpm.params.parameter_block import ParameterBlock, ParameterBlockConfig


# ---------------------------------------------------------------------------
# Data augmentation: generate diverse prompts from templates
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, list[str]] = {
    "general": [
        "What is {}?",
        "Tell me about {}.",
        "Describe {}.",
        "How does {} work?",
        "Explain {} in simple terms.",
        "What do you know about {}?",
        "Can you explain {}?",
        "Define {}.",
        "What are the key facts about {}?",
        "Give me information about {}.",
    ],
    "math": [
        "Calculate {}.",
        "Solve: {}",
        "What is {}?",
        "If {}, find the answer.",
        "Compute {}.",
        "Evaluate {}.",
        "Find {}.",
        "Determine {}.",
        "Solve the equation: {}",
        "What is the value of {}?",
    ],
    "code": [
        "Write a Python function to {}.",
        "Explain {}.",
        "How do you {} in programming?",
        "What is {} in computer science?",
        "Write code to {}.",
        "Describe the concept of {}.",
        "Implement a function that {}.",
        "What's the difference between {}?",
        "Explain how to {} in Python.",
        "What is the purpose of {}?",
    ],
    "chinese": [
        "请解释{}。",
        "什么是{}？",
        "请介绍{}。",
        "请描述一下{}。",
        "关于{}你知道什么？",
        "请用中文说明{}。",
        "请讲解{}。",
        "请用一段话描述{}。",
        "{}是什么？请用中文回答。",
        "请详细说明{}。",
    ],
    "reasoning": [
        "Here's a puzzle: {}. Think step by step.",
        "Solve this logic problem: {}",
        "Reason through this: {}",
        "Consider the following: {}. What's the answer?",
        "Let's think about this problem: {}",
        "Work through this step by step: {}",
        "Problem: {}. Explain your reasoning.",
        "If {}, what follows?",
        "Think carefully about: {}",
        "Given that {}, determine the solution.",
    ],
}

TOPICS: dict[str, list[str]] = {
    "general": [
        "photosynthesis", "gravity", "the water cycle", "electricity",
        "the solar system", "evolution", "the human heart", "DNA",
        "the atmosphere", "global warming", "the internet", "Einstein's theory of relativity",
        "the food chain", "earthquakes", "volcanoes", "the human brain",
        "biodiversity", "the Industrial Revolution", "World War II", "the Renaissance",
        "the French Revolution", "democracy", "capitalism", "socialism",
        "the United Nations", "the World Bank", "Napoleon Bonaparte", "Shakespeare",
        "the Amazon rainforest", "the Great Wall of China", "the pyramids of Egypt",
        "the Silk Road", "the Titanic", "the Moon landing", "the Big Bang theory",
        "black holes", "the periodic table", "the microscope", "vaccines", "penicillin",
    ],
    "math": [
        "15 + 27", "144 / 12", "x + 5 = 12, what is x",
        "25% of 200", "the area of a circle with radius 3",
        "the square root of 144", "2^10",
        "3x - 7 = 14", "the sum of angles in a triangle",
        "the GCD of 24 and 36", "7 factorial",
        "the probability of rolling a 6 on a die",
        "15% of 80", "the derivative of x^3",
        "the integral of 2x dx", "log base 10 of 1000",
        "the volume of a sphere with radius 2",
        "the hypotenuse of a 3-4-5 triangle",
        "the mean of 4, 8, 12, 16", "sin(30 degrees)",
        "cos(60 degrees)", "the solution to 2x + 3 = 11",
        "the distance from (0,0) to (3,4)",
        "the LCM of 12 and 18", "the value of e^0",
        "the slope of y = 3x + 2", "the median of 3, 7, 9, 12, 15",
    ],
    "code": [
        "check if a string is a palindrome",
        "sort a list of integers using quicksort",
        "a hash map works",
        "the difference between a list and a tuple in Python",
        "validate an email address using regex",
        "find duplicate entries in a SQL database",
        "what recursion is with an example",
        "what the time complexity of binary search is",
        "create a BankAccount class with deposit and withdraw methods",
        "the difference between HTTP GET and POST",
        "what a unit test is and why it's important",
        "find the nth Fibonacci number using dynamic programming",
        "what git merge does",
        "the MVC architecture pattern",
        "the difference between an array and a linked list",
        "count word frequency in a string",
        "implement a binary search tree",
        "reverse a linked list",
        "what a RESTful API is",
        "implement a simple cache with LRU eviction",
        "what the difference between TCP and UDP is",
        "implement a stack using arrays",
        "what an HTTP status code 404 means",
        "create a simple HTML form with validation",
        "what CSS flexbox is",
        "implement a basic neural network in PyTorch",
        "what the difference between supervised and unsupervised learning is",
        "parse a JSON string in Python",
        "implement a producer-consumer pattern",
        "what an ORM is in web development",
    ],
    "chinese": [
        "人工智能", "大数据", "云计算", "区块链",
        "量子计算", "虚拟现实", "物联网",
        "中国的四大发明", "中秋节的传统", "春节的习俗",
        "兵马俑", "长城的历史", "丝绸之路",
        "中国书法", "中国茶文化", "中医理论",
        "太极", "孔子思想", "中国园林艺术",
        "中国戏曲", "美食文化", "中国画",
        "汉字的演变", "中国古代建筑", "中国近代史",
        "中国的经济改革", "中国的教育体系", "中国的环境保护政策",
        "垃圾分类", "可再生能源", "高速铁路",
        "电子商务", "移动支付", "社交媒体的影响",
        "远程教育的优缺点", "城市化进程",
    ],
    "reasoning": [
        "Alice is twice as old as Bob. In 5 years, Alice will be 1.5 times as old as Bob. How old is Alice now?",
        "Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?",
        "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
        "You have a 3-gallon jug and a 5-gallon jug. How can you measure exactly 4 gallons?",
        "A doctor gives you three pills and tells you to take one every half hour. How long will they last?",
        "You have a 3x3x3 cube made of smaller cubes. If you dip the whole cube in paint, how many small cubes have exactly 2 sides painted?",
        "There are 10 birds on a fence. A hunter shoots one. How many are left?",
        "A man pushes his car to a hotel and tells the owner he's bankrupt. What's happening?",
        "If a doctor gives you 3 pills and says take one every half hour, how long will they last?",
        "A plane crashes on the border of the US and Canada. Where do they bury the survivors?",
        "What comes next in the sequence: 2, 3, 5, 7, 11, ___?",
        "If you have me you want to share me. If you share me you haven't got me. What am I?",
        "What gets wetter the more it dries?",
        "How many months have 28 days?",
        "If you rearrange the letters 'CIFAIPC' you get the name of what ocean?",
        "What building has the most stories?",
    ],
}


class CategoryDataset(Dataset):
    """Dataset for training a block on a specific category.

    Uses causal language modeling: predict the next token.
    """

    def __init__(
        self,
        texts: list[str],
        tokenizer,
        max_length: int = 128,
    ):
        self.tokens: list[torch.Tensor] = []
        self.attention_masks: list[torch.Tensor] = []

        for text in texts:
            enc = tokenizer(
                text,
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt",
            )
            self.tokens.append(enc["input_ids"][0])
            self.attention_masks.append(enc["attention_mask"][0])

    def __len__(self):
        return len(self.tokens)

    def __getitem__(self, idx):
        input_ids = self.tokens[idx]
        labels = input_ids.clone()
        return {
            "input_ids": input_ids,
            "attention_mask": self.attention_masks[idx],
            "labels": labels,
        }


def get_category_data(category: str, num_augmented: int = 5) -> list[str]:
    """Get training prompts for a category, with data augmentation.

    Each base topic is combined with multiple prompt templates,
    generating a diverse set of training examples that prevents overfitting.
    """
    topics = TOPICS.get(category, TOPICS["general"])
    templates = TEMPLATES.get(category, TEMPLATES["general"])

    augmented: list[str] = []

    for topic in topics:
        count = 0
        for tmpl in templates:
            if count >= num_augmented:
                break
            prompt = tmpl.format(topic)
            if prompt not in augmented:
                augmented.append(prompt)
                count += 1

    # Include the original curated data as well (ensures quality)
    original = CATEGORY_DATA.get(category, [])
    for p in original:
        if p not in augmented:
            augmented.append(p)

    return augmented


# ---------------------------------------------------------------------------
# Original curated data (kept for quality)
# ---------------------------------------------------------------------------

CATEGORY_DATA: dict[str, list[str]] = {
    "general": [
        "What is the capital of France?",
        "How many days are in a leap year?",
        "What color is the sky on a clear day?",
        "Which planet is known as the Red Planet?",
        "What is the boiling point of water in Celsius?",
        "Who wrote Romeo and Juliet?",
        "What is the largest ocean on Earth?",
        "How many continents are there?",
        "What is the speed of light in vacuum?",
        "Which gas do plants absorb from the atmosphere?",
        "What is the tallest mountain in the world?",
        "Which country has the largest population?",
        "What is the smallest country in the world?",
        "How many bones are in the human body?",
        "What is the chemical symbol for gold?",
        "Which animal is known as the king of the jungle?",
        "What is the longest river in the world?",
        "Which language has the most native speakers?",
        "What is the largest desert in the world?",
        "How many teeth does an adult human have?",
    ],
    "math": [
        "Calculate 15 + 27 =",
        "What is 144 divided by 12?",
        "If x + 5 = 12, what is x?",
        "What is 25 percent of 200?",
        "Calculate the area of a circle with radius 3.",
        "What is the square root of 144?",
        "How many seconds are in 2 hours?",
        "Solve: 3x - 7 = 14",
        "What is 2 to the power of 10?",
        "If a train travels at 60 km/h for 2.5 hours, how far does it go?",
    ],
    "code": [
        "Write a Python function to check if a string is a palindrome.",
        "Create a JSON object representing a person with name, age, and city.",
        "Explain what a hash map is in one paragraph.",
        "Write a simple function to sort a list of integers.",
        "What is the difference between a list and a tuple in Python?",
        "Write a regex to validate an email address.",
        "What is an API endpoint?",
        "Write a SQL query to find duplicate entries in a table.",
        "Explain recursion with an example.",
        "What is the time complexity of binary search?",
    ],
    "chinese": [
        "中国的首都是哪个城市？",
        "请用中文解释什么是人工智能。",
        "一年有多少个月？",
        "请写一段关于春天的短文。",
        "什么是机器学习？请用中文回答。",
        "水的化学式是什么？",
        "请列举三种水果。",
        "太阳从哪个方向升起？",
        "请用中文写一句问候语。",
        "什么是自然语言处理？",
    ],
    "reasoning": [
        "If all squares are rectangles, and some rectangles are not squares, can a shape be a rectangle but not a square? Explain.",
        "Alice is twice as old as Bob. In 5 years, Alice will be 1.5 times as old as Bob. How old is Alice now?",
        "Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?",
        "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        "A bat and a ball cost 1.10 dollars in total. The bat costs 1.00 dollars more than the ball. How much does the ball cost?",
    ],
}


@dataclass
class TrainingMetrics:
    """Training progress metrics."""
    category: str
    block_id: str
    layer_id: int
    module_name: str
    rank: int
    epochs: int
    final_loss: float
    best_loss: float
    total_steps: int
    training_time_s: float
    loss_history: list[float] = field(default_factory=list)


def create_block_for_layer(
    backbone: BackboneModel,
    layer_id: int,
    module_name: str,
    block_id: str,
    block_type: str,
    rank: int = 8,
    scale: float = 1.0,
    device: str = "cpu",
) -> ParameterBlock:
    """Create a ParameterBlock for a specific layer, matching backbone dims."""
    lin = backbone.get_linear_layer(layer_id, module_name)
    if lin is None:
        raise ValueError(f"Layer {layer_id}/{module_name} not found in backbone")

    backbone_dtype = next(backbone.model.parameters()).dtype

    config = ParameterBlockConfig(
        block_id=block_id,
        layer_id=layer_id,
        module_name=module_name,
        rank=rank,
        scale=scale,
        block_type=block_type,
        hidden_size=backbone.hidden_size,
        in_features=lin.in_features,
        out_features=lin.out_features,
    )
    block = ParameterBlock(config)
    block = block.to(device=device, dtype=backbone_dtype)

    print(f"  Created block {block_id}: {lin.in_features}->{lin.out_features}, "
          f"rank={rank}, dtype={backbone_dtype}, ΔW params={sum(p.numel() for p in block.parameters()):,}")

    return block


def train_block(
    backbone: BackboneModel,
    block: ParameterBlock,
    category: str = "general",
    texts: Optional[list[str]] = None,
    epochs: int = 5,
    batch_size: int = 2,
    lr: float = 5e-4,
    max_length: int = 128,
    device: str = "cpu",
    log_interval: int = 5,
    num_augmented: int = 3,
) -> TrainingMetrics:
    """Train a single parameter block on category-specific data.

    The backbone is frozen; only the block's A/B matrices are trained.

    Args:
        backbone: The frozen backbone model.
        block: The parameter block to train.
        category: Training data category.
        texts: Optional explicit training texts. When provided, these replace
            the built-in category data.
        epochs: Number of training epochs.
        batch_size: Batch size.
        lr: Learning rate for block parameters.
        max_length: Max sequence length for tokenization.
        device: Device to train on.
        log_interval: Log every N steps.

    Returns:
        TrainingMetrics with loss history.
    """
    # 1. Inject block into backbone
    injector = BlockInjector(backbone)
    injector.inject_block(block, block.layer_id, block.module_name)

    # 2. Prepare dataset
    train_texts = texts if texts is not None else get_category_data(category, num_augmented=num_augmented)
    dataset = CategoryDataset(train_texts, backbone.tokenizer, max_length=max_length)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 3. Setup optimizer (only block params)
    optimizer = torch.optim.AdamW(block.parameters(), lr=lr)

    # 4. Training loop
    block.train()
    backbone.model.eval()  # backbone is frozen

    total_steps = 0
    loss_history: list[float] = []
    best_loss = float("inf")
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"Training block [{block.block_id}] on category [{category}]")
    print(f"  Samples: {len(dataset)}, Epochs: {epochs}, Batch: {batch_size}, LR: {lr}")
    print(f"  Block params: {sum(p.numel() for p in block.parameters()):,}")
    print(f"{'='*60}")

    for epoch in range(epochs):
        epoch_loss = 0.0
        num_batches = 0

        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False)
        for batch in pbar:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()

            outputs = backbone.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            num_batches += 1
            total_steps += 1

            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

            if total_steps % log_interval == 0:
                loss_history.append(loss.item())
                if loss.item() < best_loss:
                    best_loss = loss.item()

        avg_epoch_loss = epoch_loss / max(num_batches, 1)
        print(f"  Epoch {epoch+1}/{epochs}: avg_loss = {avg_epoch_loss:.4f}")

    training_time = time.time() - start_time
    final_loss = loss_history[-1] if loss_history else 0.0

    # Remove injection
    injector.remove_all_patches()

    metrics = TrainingMetrics(
        category=category,
        block_id=block.block_id,
        layer_id=block.layer_id,
        module_name=block.module_name,
        rank=block.rank,
        epochs=epochs,
        final_loss=final_loss,
        best_loss=best_loss,
        total_steps=total_steps,
        training_time_s=training_time,
        loss_history=loss_history,
    )

    print(f"  ✓ Training complete: {training_time:.1f}s, "
          f"final_loss={final_loss:.4f}, best_loss={best_loss:.4f}")

    return metrics


def save_block_with_metadata(
    block: ParameterBlock,
    metrics: TrainingMetrics,
    save_dir: str,
):
    """Save a trained block along with training metadata."""
    os.makedirs(save_dir, exist_ok=True)

    # Save block parameters
    block_path = os.path.join(save_dir, f"{block.block_id}.pt")
    block.save(block_path)

    # Save training metadata as JSON
    meta_path = os.path.join(save_dir, f"{block.block_id}_meta.json")
    meta = {
        "block_id": block.block_id,
        "block_type": block.block_type,
        "category": metrics.category,
        "layer_id": block.layer_id,
        "module_name": block.module_name,
        "rank": block.rank,
        "scale": block.scale,
        "final_loss": metrics.final_loss,
        "best_loss": metrics.best_loss,
        "epochs": metrics.epochs,
        "total_steps": metrics.total_steps,
        "training_time_s": metrics.training_time_s,
        "in_features": block.A.shape[0],
        "out_features": block.B.shape[1],
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved: {block_path}")
    print(f"  ✓ Metadata: {meta_path}")
