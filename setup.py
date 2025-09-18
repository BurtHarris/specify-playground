#!/usr/bin/env python3
"""Setup configuration for Video Duplicate Scanner CLI."""

from setuptools import setup, find_packages

setup(
    name="video-duplicate-scanner",
    version="1.0.0",
    description="CLI tool for detecting duplicate video files",
    author="Video Duplicate Scanner Team",
    python_requires=">=3.12",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.1.0",
        "PyYAML>=6.0",
        "fuzzywuzzy>=0.18.0",
        "python-Levenshtein>=0.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "video-dedup=src.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)