import random


def clip(value: float):
    return max(0.0, min(1.0, float(value)))


def normalize_stroke_distribution(strokes):
    """Rescale darkness and contour strengths so all values span the full [0, 1] range."""
    if not strokes:
        return []

    darkness_values = [float(stroke.darkness) for stroke in strokes]
    contour_values = [float(stroke.contour_strength) for stroke in strokes]

    def _normalize(values):
        if not values:
            return []
        min_value = min(values)
        max_value = max(values)
        if max_value == min_value:
            return [0.0 for _ in values]
        return [
            (value - min_value) / (max_value - min_value)
            for value in values
        ]

    normalized_darkness = _normalize(darkness_values)
    normalized_contours = _normalize(contour_values)

    for stroke, darkness, contour in zip(strokes, normalized_darkness, normalized_contours):
        stroke.darkness = clip(darkness)
        stroke.contour_strength = clip(contour)
        stroke.pigment = clip(0.5 * stroke.darkness + 0.5 * stroke.contour_strength)

    return strokes


def calculate_pigment(stroke, average_darkness, contour_strength, image=None, **kwargs):
    """Populate stroke pigment metadata based on image-derived stroke statistics."""

    stroke.darkness = clip(float(average_darkness))
    stroke.contour_strength = clip(float(contour_strength))

    factors = [
        (0.3, stroke.darkness),
        (0.9, stroke.contour_strength),
        # (.5, random.random()*2-1)
    ]

    lin_comb = sum(weight * value for weight, value in factors)
    stroke.pigment = clip(lin_comb)

    stroke.metadata.setdefault("image_size", None if image is None else image.size)
    stroke.metadata.setdefault("source", "calculate_pigment")
    return stroke
