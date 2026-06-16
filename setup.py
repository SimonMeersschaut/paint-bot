"""
Setup configuration for Paint Robot package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="paintbot",
    version="0.1.0",
    author="Simon",
    author_email="",
    description="A Python package for controlling and optimizing paint robot operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/paint-bot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "matplotlib>=3.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.9",
            "isort>=5.9",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
