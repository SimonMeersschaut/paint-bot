import numpy as np
# import matplotlib.pyplot as plt
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb
from scipy.cluster.vq import kmeans2
from .hyperparameters import Hyperparameters

def k_nearest(np_image, k: int = 5, m_buckets: int = 32, boldness_boost: float = 3.0):
    """
    Reduces the image palette using a weighted perceptual HSV distance metric,
    with an adjustable boost favoring bold, highly-saturated colors over neutrals.
    
    Parameters:
    - np_image: NumPy array of shape (H, W, C) representing an RGB image (0-255 or 0-1).
    - k: The number of final nearest colors to retain.
    - m_buckets: The number of initial color buckets for grouping similar tints.
    - boldness_boost: Multiplier strength for bold colors. Higher values force 
                      vibrant colors to be picked over grays/whites/blacks.
    """
    original_shape = np_image.shape
    is_uint8 = np_image.dtype == np.uint8
    
    # 1. Normalize image to [0, 1] range and convert to HSV
    rgb_normalized = np_image.astype(np.float32) / 255.0 if is_uint8 else np_image.astype(np.float32)
    hsv_pixels = rgb_to_hsv(rgb_normalized.reshape(-1, 3))
    
    # Per-channel color weights (H, S, V)
    COLOR_WEIGHTS = Hyperparameters.COLOR_WEIGHTS
    
    # 2. Cluster in HSV space using K-Means
    centroids_hsv, pixel_labels = kmeans2(hsv_pixels, m_buckets, minit='points', missing='warn')
    
    # 3. Count bucket populations
    bucket_indices, counts = np.unique(pixel_labels, return_counts=True)
    full_counts = np.zeros(m_buckets, dtype=float)  # Changed to float for multiplication
    full_counts[bucket_indices] = counts
    
    # --- BOLDNESS BOOST LOGIC ---
    # Extract Saturation (S) and Value (V) for each centroid
    # Grays/Whites have low S. Blacks have low V. Bold colors have high S and high V.
    S = centroids_hsv[:, 1]
    V = centroids_hsv[:, 2]
    
    # Define a boldness metric (0.0 to 1.0). 
    # High saturation and high brightness = bold.
    boldness_metric = S * V 
    
    # Create a weight vector: 1.0 for completely neutral, up to (1.0 + boldness_boost) for pure bold
    boost_weights = 1.0 + (boldness_metric * boldness_boost)
    
    # Multiply the true pixel counts by the boost weights to get an "effective" rank score
    boosted_scores = full_counts * boost_weights
    
    # Sort buckets by their boosted scores instead of raw population
    sorted_indices = np.argsort(boosted_scores)[::-1]
    sorted_counts = full_counts[sorted_indices]
    sorted_centroids_hsv = centroids_hsv[sorted_indices]
    # ----------------------------
    
    # --- PLOTTING BLOCK ---
    # Convert HSV centroids back to RGB for the bar colors
    sorted_centroids_rgb = hsv_to_rgb(sorted_centroids_hsv)
    bar_colors = np.clip(sorted_centroids_rgb, 0, 1)

    # plt.clf()
    # plt.bar(range(m_buckets), sorted_counts, color=bar_colors, edgecolor='black', linewidth=0.5)
    # plt.title(f'Weighted HSV Color Buckets ({m_buckets} total)')
    # plt.xlabel('Bucket Rank')
    # plt.ylabel('Pixel Count')
    # plt.tight_layout()
    # plt.show()
    # ----------------------
    
    # 4. Extract the top 'k' dominant HSV centroids (now biased towards bold colors)
    k = min(k, m_buckets)
    top_k_indices = sorted_indices[:k]
    dominant_colors_hsv = centroids_hsv[top_k_indices]
    
    # 5. Compute WEIGHTED Euclidean distances from every pixel to the top 'k' centroids
    # Shape analysis: (N, 1, 3) - (1, k, 3) -> (N, k, 3)
    diff_squared = (hsv_pixels[:, np.newaxis, :] - dominant_colors_hsv[np.newaxis, :, :]) ** 2
    weighted_distances = np.sum(COLOR_WEIGHTS * diff_squared, axis=2)
    
    # 6. Map pixels to the closest dominant centroid index
    closest_color_indices = np.argmin(weighted_distances, axis=1)
    quantized_pixels_hsv = dominant_colors_hsv[closest_color_indices]
    
    # 7. Convert back to RGB and original data shape/type
    quantized_pixels_rgb = hsv_to_rgb(quantized_pixels_hsv)
    
    if is_uint8:
        quantized_pixels_rgb = np.clip(quantized_pixels_rgb * 255.0, 0, 255).astype(np.uint8)
        
    return quantized_pixels_rgb.reshape(original_shape)