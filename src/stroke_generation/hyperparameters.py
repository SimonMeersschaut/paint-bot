"""Centralized hyperparameters for stroke generation.

Move tunable constants here so they can be adjusted in one place.
"""
import numpy as np
from abc import ABC
from dataclasses import dataclass

class ColorMethod(ABC):
    ...

class PaletteColorsOnly(ColorMethod):
    ...

@dataclass
class KNearest():
    k:int = 5


class Hyperparameters:
    # Per-channel color weights for perceptual RGB distance (R, G, B)
    COLOR_WEIGHTS = np.array([0.30, 0.59, 0.11], dtype=np.float32)

    # Stroke length limits (in pixels or steps depending on context)
    MIN_LEN = 20
    MAX_LEN = 20

    # Expand/step behaviour
    STEP_SIZE = 1

    KALMAN_Z_VALUE = -2.5

    # HSV feature weights used when matching palette colors (Hue, Saturation, Value)
    HSV_WEIGHTS = np.array([1.0, 0.1, 0], dtype=np.float32)

    # Thresholds
    COLOR_DIFF_THRESHOLD = 75

    COLOR_METHOD: object = PaletteColorsOnly()
