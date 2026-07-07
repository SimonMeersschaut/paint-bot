import json
import numpy as np
import cv2
from datatypes import StrokePath
from .supervisor import Events
from .expand import expand_point
from .acceptance import accept_stroke, MIN_LEN

with open("data/my_robot_calibration.json", "r") as f:
    # Helper to convert a single hex string (e.g., "#FF5733") to [R, G, B]
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip("#")
        return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]

    # Extract and convert the entire palette
    COLOR_PALETTE = [
        hex_to_rgb(entry["color"]) for entry in json.load(f)["color_palette"]
        if not all(c == 255 for c in entry["color"]) # exclude white!
    ]


PALETTE_ARR = np.array(list(COLOR_PALETTE), dtype=np.float32)
PALETTE_LIST = list(COLOR_PALETTE)

# acceptance constants moved to acceptance.py

def generate_strokes_for_layer(stroke_sequence, resized_segments, label, image, grad, coverage_mask, padding_mask,
                                stroke_generation_supervisor: object):
    """
    Optimized stroke generation using minimized memory allocations and localized tracking.
    Evaluates color errors optimistically based on multi-pass opacity projections.
    Uses Perceptual RGB distance metrics to fix unrealistic color assignments.
    """
    image_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)

    H, W, _ = image.shape
    gy, gx = grad
    segment_mask = (resized_segments == label)
    total_sp_pixels = np.sum(segment_mask)
    
    if total_sp_pixels < 5:
        stroke_generation_supervisor.register_event(Events.superpixel_too_small)
        raise RuntimeError("Superpixel too small.")
        
    # Pre-convert the PALETTE_ARR to HSV for fast vectorized lookup
    # PALETTE_ARR shape: (N, 3). We reshape to (1, N, 3) for OpenCV compatibility
    palette_hsv = cv2.cvtColor(PALETTE_ARR.astype(np.uint8).reshape(1, -1, 3), cv2.COLOR_RGB2HSV).reshape(-1, 3).astype(np.float32)

    # Define HSV feature weights: Put massive emphasis on Hue (index 0) 
    # so blue pixels are strictly forced to blue palette colors.
    HSV_WEIGHTS = np.array([1.0, 0.1, 0], dtype=np.float32)

    attempts = 0
    while attempts < stroke_generation_supervisor.max_attempts:
        covered_sp_pixels = np.sum(segment_mask & coverage_mask)
        current_coverage = covered_sp_pixels / total_sp_pixels
        
        if current_coverage >= stroke_generation_supervisor.supercell_target_coverage:
            stroke_generation_supervisor.register_event(Events.coverage_reached)
            return 
            
        unpainted_indices = np.argwhere(segment_mask & ~coverage_mask)
        if len(unpainted_indices) == 0:
            stroke_generation_supervisor.register_event(Events.all_indices_painted)
            return
            
        if attempts == 0:
            cy, cx = np.mean(np.argwhere(segment_mask), axis=0)
        else:
            random_idx = np.random.choice(len(unpainted_indices))
            cy, cx = unpainted_indices[random_idx]
            
        start_x_idx = int(np.clip(cx, 0, W - 1))
        source_y_idx = int(np.clip(cy, 0, H - 1))
        
        pixel_hsv = image_hsv[source_y_idx, start_x_idx].astype(np.uint8)

        # Calculate cyclic hue difference (Hue loops at 180 in OpenCV)
        hue_diff = np.abs(palette_hsv[:, 0] - pixel_hsv[0])
        hue_diff = np.minimum(hue_diff, 180 - hue_diff)

        # Calculate standard differences for Saturation and Value
        sat_diff = palette_hsv[:, 1] - pixel_hsv[1]
        val_diff = palette_hsv[:, 2] - pixel_hsv[2]

        # Combine using the HSV weights
        dists = (HSV_WEIGHTS[0] * (hue_diff ** 2) + 
                HSV_WEIGHTS[1] * (sat_diff ** 2) + 
                HSV_WEIGHTS[2] * (val_diff ** 2))

        closest_idx = np.argmin(dists)
        palette_color = PALETTE_LIST[closest_idx]

        start_point = (start_x_idx, source_y_idx)
        path, stroke_length_pixels = expand_point(image, H, W, gx, gy, start_point, segment_mask, coverage_mask, start_x_idx, source_y_idx, palette_color, stroke_generation_supervisor)
        
        if stroke_length_pixels >= MIN_LEN:
            path_np = np.array(path, dtype=np.int32)
            accepted = accept_stroke(
                path=path,
                path_np=path_np,
                stroke_length_pixels=stroke_length_pixels,
                palette_color=palette_color,
                image=image,
                image_hsv=image_hsv,
                coverage_mask=coverage_mask,
                stroke_sequence=stroke_sequence,
                stroke_generation_supervisor=stroke_generation_supervisor,
                source_y_idx=source_y_idx,
                start_x_idx=start_x_idx,
            )

            if not accepted:
                attempts += 1
                continue
            
    stroke_generation_supervisor.register_event(Events.max_attempts_reached)
    return