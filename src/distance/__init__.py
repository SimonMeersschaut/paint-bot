import os
# import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from transformers import pipeline

# 1. Initialize the depth estimation pipeline
depth_estimator = pipeline(
    "depth-estimation",
    model="Intel/dpt-hybrid-midas",
    token=os.environ.get("HF_TOKEN"),  # 'token' is the standard argument name in current transformers versions
)


def get_distance_heatmap(pil_image: Image.Image) -> Image.Image:
    """Predicts depth for an input PIL image and returns a colored distance heatmap.

    Note: Depth models output *depth* (higher values = closer).
    For a *distance* heatmap (higher values = further away), we invert the map.
    """
    # 2. Run inference
    predictions = depth_estimator(pil_image)

    # The pipeline returns a dictionary containing a 'predicted_depth' tensor
    # and a pre-rendered PIL 'depth' image. We will use the raw predicted depth
    # tensor for custom heatmap formatting.
    raw_depth = predictions["predicted_depth"].numpy()

    # 3. Invert depth to represent distance (closer objects become dark, far objects become bright)
    # First, normalize to 0-1 range
    raw_depth_min = raw_depth.min()
    raw_depth_max = raw_depth.max()

    if raw_depth_max - raw_depth_min > 0:
        normalized_depth = (raw_depth - raw_depth_min) / (
            raw_depth_max - raw_depth_min
        )
    else:
        normalized_depth = np.zeros_like(raw_depth)

    return normalized_depth


# if __name__ == "__main__":
#     # Load a sample image (replace with your image path)
#     # input_image = Image.open("path_to_your_image.jpg")

#     # For demonstration, creating a dummy random image
#     input_image = Image.fromarray(
#         np.random.randint(0, 255, (384, 384, 3), dtype=np.uint8)
#     )

#     # Generate heatmap
#     try:
#         heatmap = get_distance_heatmap(input_image)
#         heatmap.save("distance_heatmap.png")
#         print("Distance heatmap generated and saved successfully!")
#     except Exception as e:
#         print(f"An error occurred: {e}")