"""
Paint Robot Package

A Python package for controlling and optimizing paint robot operations.
"""

from paintbot.datatypes import StrokeSequence, Stroke
from paintbot.stroke_generation import generate_strokes

__version__ = "0.1.0"
__author__ = "Simon Meersschaut"
__all__ = ["StrokeSequence", "Stroke", "generate_strokes"]
