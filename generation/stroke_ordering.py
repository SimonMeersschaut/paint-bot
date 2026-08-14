
from datatypes.strokes import LoadBrush


def sort_strokes(strokes, batch_size=10):
    """Group strokes into similar-pigment batches and prefix each batch with a brush-load instruction."""
    if not strokes:
        return []

    ordered = sorted(strokes, key=lambda stroke: float(getattr(stroke, 'pigment', 0.0)))

    batched = []
    for index in range(0, len(ordered), batch_size):
        batch = ordered[index:index + batch_size]
        if not batch:
            continue

        mean_pigment = sum(float(getattr(stroke, 'pigment', 0.0)) for stroke in batch) / len(batch)
        batched.append(LoadBrush(color=(0, 0, 0), pigment=mean_pigment, deep_clean=False))
        batched.extend(batch)

    return batched