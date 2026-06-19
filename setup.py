"""Minimal setup.py for BitDPM development installation."""

from setuptools import find_packages, setup

setup(
    name="bitdpm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "datasets>=2.0.0",
    ],
    extras_require={
        "modelscope": ["modelscope>=1.9.0"],
        "bnb": ["bitsandbytes>=0.41.0"],
        "peft": ["peft>=0.11.0"],
        "all": ["modelscope>=1.9.0", "bitsandbytes>=0.41.0", "psutil>=5.8.0", "peft>=0.11.0"],
    },
)
