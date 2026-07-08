# Evaluate a StrokeSequence by comparing rendered strokes against the target image.
from visualisation import visualize_stroke_sequence
import numpy as np
import cv2
from stroke_generation.hyperparameters import HSV_WEIGHTS


def _to_uint8_rgb(arr):
    """Normalize numpy image to uint8 RGB format.

    Accepts float images in [0,1], or uint8 images in [0,255].
    Returns uint8 RGB array.
    """
    if isinstance(arr, np.ndarray):
        if arr.dtype == np.uint8:
            return arr
        if np.issubdtype(arr.dtype, np.floating):
            a = np.clip(arr, 0.0, 1.0)
            return (a * 255.0).astype(np.uint8)
        else:
            return arr.astype(np.uint8)
    else:
        raise TypeError("Expected numpy array for image")


def evaluate(np_resized_image, stroke_sequence) -> float:
    """Compute a weighted mean squared error between target image and rendered strokes.

    - np_resized_image: numpy array (H, W, 3) in RGB (uint8 or float [0,1]).
    - stroke_sequence: StrokeSequence; rendered using `visualize_stroke_sequence`.

    Returns a single float: the weighted MSE over HSV channels using `HSV_WEIGHTS`.
    """
    # Render strokes to an image (PIL) without annotations
    pil_render = visualize_stroke_sequence(stroke_sequence, do_annotate=False)
    render_np = np.array(pil_render)  # RGB uint8

    target = _to_uint8_rgb(np_resized_image)
    render = _to_uint8_rgb(render_np)

    if target.shape != render.shape:
        raise ValueError(f"Shape mismatch: target {target.shape} vs render {render.shape}")

    # Convert to HSV (OpenCV uses H:0-179, S:0-255, V:0-255)
    target_hsv = cv2.cvtColor(target, cv2.COLOR_RGB2HSV).astype(np.float32)
    render_hsv = cv2.cvtColor(render, cv2.COLOR_RGB2HSV).astype(np.float32)

    # Hue cyclic difference
    hue_diff = np.abs(target_hsv[:, :, 0] - render_hsv[:, :, 0])
    hue_diff = np.minimum(hue_diff, 180.0 - hue_diff)

    sat_diff = target_hsv[:, :, 1] - render_hsv[:, :, 1]
    val_diff = target_hsv[:, :, 2] - render_hsv[:, :, 2]

    # Weighted per-pixel squared error
    weights = np.asarray(HSV_WEIGHTS, dtype=np.float32)
    per_pixel = (weights[0] * (hue_diff ** 2) +
                 weights[1] * (sat_diff ** 2) +
                 weights[2] * (val_diff ** 2))

    mse = float(np.mean(per_pixel))
    return mse