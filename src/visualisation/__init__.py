"""Visualization module for paint-bot data structures."""

from .rendering import get_stroke_frame, calculate_stroke_duration, animate_stroke_sequence, visualize_stroke_sequence


import matplotlib.pyplot as plt
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import numpy as np

from PIL import Image


def rotate_if_vertical(img):
    """Accepts a PIL Image object and rotates it if it's portrait."""
    width, height = img.size

    if height > width:
        print(f"Image is vertical ({width}x{height}). Rotating 90 degrees...")
        # Rotate 90 degrees clockwise
        return img.transpose(Image.ROTATE_90)
    else:
        print(
            f"Image is already horizontal ({width}x{height}). No rotation needed."
        )
        return img

def show_np_image(np_image, *args, **kwargs):
    """Put the origin in the bottom left corner."""

    plt.imshow(np_image, origin="lower", *args, **kwargs)
    plt.show()

def show_pil_image(pil):
    # slower than `show_np_image`
    show_np_image(np.array(pil))

def resize_image(img: object, CANVAS_SIZE):
    """
    Unified entry point that pads and resizes either a PIL Image 
    or a NumPy ndarray to CANVAS_SIZE while preserving aspect ratio.
    """
    if isinstance(img, np.ndarray):
        # Route to the ndarray processor
        return resize_image_ndarray(img)
    else:
        # Original PIL logic
        if len(img.getbands()) == 1:
            PADDING_COLOR = 0  # Single integer for grayscale/depth maps
        else:
            PADDING_COLOR = (0, 0, 0)  # Tuple for RGB images
        return ImageOps.pad(img, CANVAS_SIZE, color=PADDING_COLOR)

def resize_image_ndarray(image_array: np.ndarray) -> np.ndarray:
    """
    Pads and resizes a NumPy ndarray to CANVAS_SIZE while maintaining aspect ratio.
    Automatically handles arbitrary channels (Grayscale, RGB, BGR, or multi-band masks).
    """
    # 1. Determine padding color based on array shape
    if image_array.ndim == 2:
        # Grayscale / Single-channel mask
        PADDING_COLOR = 0
    else:
        # Multi-channel image (RGB, BGR, etc.)
        channels = image_array.shape[2]
        PADDING_COLOR = (0,) * channels

    # 2. Convert NumPy array to PIL Image
    if image_array.dtype == bool:
        pil_img = Image.fromarray(image_array.astype(np.uint8) * 255)
    elif np.issubdtype(image_array.dtype, np.floating):
        # Scale float [0, 1] up to integer [0, 255]
        pil_img = Image.fromarray((image_array * 255).astype(np.uint8))
    else:
        pil_img = Image.fromarray(image_array)

    # 3. Use ImageOps.pad to handle aspect ratio centering and padding
    padded_pil = ImageOps.pad(pil_img, CANVAS_SIZE, color=PADDING_COLOR)

    # 4. Convert back to a NumPy array
    output_array = np.array(padded_pil)
    
    # Restore boolean type if the input was a mask
    if image_array.dtype == bool:
        return output_array > 127
        
    return output_array
