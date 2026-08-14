import random


def clip(value: float, min_value=0):
    return max(min_value, min(1.0, float(value)))


def normalize_stroke_distribution(strokes):
    """Rescale darkness and contour values to the 0..1 range across a stroke set."""
    if not strokes:
        return []

    darkness_values = [float(getattr(stroke, 'darkness', 0.0)) for stroke in strokes]
    contour_values = [float(getattr(stroke, 'contour_strength', 0.0)) for stroke in strokes]

    def normalize(values):
        minimum = min(values)
        maximum = max(values)
        if maximum == minimum:
            return [0.0 for _ in values]
        return [(value - minimum) / (maximum - minimum) for value in values]

    darkness_norm = normalize(darkness_values)
    contour_norm = normalize(contour_values)

    for stroke, darkness_value, contour_value in zip(strokes, darkness_norm, contour_norm):
        stroke.darkness = darkness_value
        stroke.contour_strength = contour_value

    return strokes


def calculate_pigment(stroke, average_darkness, contour_strength, image=None, **kwargs):
    """Populate stroke pigment metadata based on image-derived stroke statistics."""

    stroke.darkness = clip(float(average_darkness))
    stroke.contour_strength = clip(float(contour_strength))

    factors = [
        (.7, stroke.contour_strength),
        (.1, random.random()*2-1),
        (.2, stroke.darkness),
    ]

    lin_comb = sum(weight * value for weight, value in factors)
    stroke.pigment = clip(lin_comb, min_value=.1)

    return stroke
