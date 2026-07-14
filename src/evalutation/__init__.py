"""Feature-based evaluation for rendered paint-bot images."""

from functools import lru_cache

import numpy as np
from PIL import Image

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


def _to_pil_rgb(image):
    if isinstance(image, Image.Image):
        return image.convert("RGB")

    array = np.asarray(image)

    if array.ndim == 2:
        array = np.repeat(array[:, :, None], 3, axis=2)
    elif array.ndim == 3 and array.shape[2] == 1:
        array = np.repeat(array, 3, axis=2)
    elif array.ndim != 3 or array.shape[2] < 3:
        raise ValueError(f"Expected a grayscale or RGB image, got shape {array.shape}")

    return Image.fromarray(_to_uint8_rgb(array[:, :, :3]), mode="RGB")


def _apply_attention_mask(image: Image.Image, attention_mask) -> Image.Image:
    image_array = np.asarray(image.convert("RGB"), dtype=np.uint8)
    mask = np.asarray(attention_mask)

    if mask.ndim > 2:
        mask = np.any(mask, axis=tuple(range(2, mask.ndim)))

    mask = mask.astype(bool)

    if mask.shape != image_array.shape[:2]:
        raise ValueError(
            f"Attention mask shape {mask.shape} does not match image shape {image_array.shape[:2]}"
        )

    if not np.any(mask):
        raise ValueError("Attention mask is empty")

    masked_array = image_array.copy()
    masked_array[~mask] = 0

    rows, cols = np.where(mask)
    top, bottom = rows.min(), rows.max() + 1
    left, right = cols.min(), cols.max() + 1

    return Image.fromarray(masked_array[top:bottom, left:right], mode="RGB")


@lru_cache(maxsize=1)
def _load_dinov2_model():
    try:
        import torch
        from transformers import AutoImageProcessor, AutoModel
    except ImportError as exc:
        raise RuntimeError(
            "Feature evaluation requires 'torch' and 'transformers' to be installed."
        ) from exc

    model_name = "facebook/dinov2-small"
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    return processor, model, device, torch


def _extract_features(images):
    processor, model, device, torch = _load_dinov2_model()
    inputs = processor(images=images, return_tensors="pt")
    pixel_values = inputs["pixel_values"].to(device)

    with torch.no_grad():
        outputs = model(pixel_values=pixel_values)
        hidden_states = outputs.last_hidden_state
        cls_token = hidden_states[:, 0, :]
        pooled_tokens = hidden_states[:, 1:, :].mean(dim=1)
        features = torch.cat([cls_token, pooled_tokens], dim=-1)
        features = torch.nn.functional.normalize(features, dim=-1)

    return features.cpu().numpy().astype(np.float32)


def evaluate(np_target_image, np_current_image, attention_mask=None) -> float:
    """Return a feature-space error between two images using DINOv2.

    The images are converted to RGB, resized by the DINOv2 processor, encoded,
    and compared with mean squared error in the normalized feature space.
    Lower values indicate closer images.
    """
    target_image = _to_pil_rgb(np_target_image)
    current_image = _to_pil_rgb(np_current_image)

    if attention_mask is not None:
        target_image = _apply_attention_mask(target_image, attention_mask)
        current_image = _apply_attention_mask(current_image, attention_mask)

    target_features, current_features = _extract_features([target_image, current_image])
    difference = target_features - current_features
    return float(np.mean(difference ** 2))
