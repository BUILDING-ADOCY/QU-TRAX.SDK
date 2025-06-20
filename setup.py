# setup.py

from setuptools import setup, find_packages

setup(
    name="qtrax_sdk",
    version="0.1.0",
    description="Quantum-Inspired Logistics Optimizer SDK — Q-TRAX",
    author="Suraj Mahapatra",
    author_email="contact@adocy.ai",
    packages=find_packages(exclude=["tests", "examples"]),
    install_requires=[
        "pydantic>=2.0",
        "typer[all]>=0.9",
        "rich>=13.0",
        "numpy>=1.24",
        "loguru>=0.7",
    ],
    entry_points={
        "console_scripts": [
            "qtrax = qtrax_sdk.main:app",
        ]
    },
    python_requires=">=3.9",
)
