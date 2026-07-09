import numpy as np

def k_nearest(np_image, k: int = 5):
    """
    Reduces the image palette to the top 'k' most dominant colors,
    mapping every pixel to its nearest neighbor among those 'k' colors.
    
    Parameters:
    - np_image: NumPy array of shape (H, W, C) representing the image.
    - k: The number of nearest colors to retain.
    
    Returns:
    - A new NumPy array of the same shape with only 'k' distinct colors.
    """
    # 1. Flatten the image to an array of pixels (N, C)
    original_shape = np_image.shape
    pixels = np_image.reshape(-1, original_shape[-1])
    
    # 2. Find all unique colors and their respective counts
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    
    # 3. Get the top 'k' most frequent (dominant) colors
    # If the image has fewer unique colors than k, adjust k to avoid indexing errors
    k = min(k, len(unique_colors))
    top_k_indices = np.argsort(counts)[::-1][:k]
    dominant_colors = unique_colors[top_k_indices]  # Shape: (k, C)
    
    # 4. Compute Euclidean distances from every pixel to the top 'k' colors
    # Using broadcasting: (N, 1, C) - (1, k, C) -> (N, k, C)
    # We omit the square root since squared distance preserves the order
    distances = np.sum((pixels[:, np.newaxis, :] - dominant_colors[np.newaxis, :, :]) ** 2, axis=2)
    
    # 5. Find the index of the closest dominant color for each pixel
    closest_color_indices = np.argmin(distances, axis=1)
    
    # 6. Map the pixels to their nearest dominant color and restore original shape
    quantized_pixels = dominant_colors[closest_color_indices]
    return quantized_pixels.reshape(original_shape)