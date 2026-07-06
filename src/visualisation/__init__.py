"""Visualization module for paint-bot data structures."""

from .rendering import get_stroke_frame, calculate_stroke_duration, animate_stroke_sequence, visualize_stroke_sequence


import matplotlib.pyplot as plt

def show_np_image(np_image, *args, **kwargs):
    """Put the origin in the bottom left corner."""

    plt.imshow(np_image, origin="lower", *args, **kwargs)
    plt.show()