from .supervisor import Events

import numpy as np
import math
from .hyperparameters import Hyperparameters

def expand_point(image, H, W, vector_field, start_point, segment_mask, coverage_mask, start_x_idx, source_y_idx, palette_color, stroke_generation_supervisor):
    path = [start_point]
    stroke_length_pixels = 0
    
    vector_field_x, vector_field_y = vector_field

    curr_x, curr_y = float(start_x_idx), float(source_y_idx)
    last_dx, last_dy = 0.0, 0.0
    for _ in range(Hyperparameters.MAX_LEN):
        map_y, map_x = int(np.clip(curr_y, 0, H - 1)), int(np.clip(curr_x, 0, W - 1))

        dx = vector_field_x[map_y, map_x]
        dy = vector_field_y[map_y, map_x]

        mag = np.sqrt(dx**2 + dy**2)

        if mag == 0:
            if last_dx == 0 and last_dy == 0: 
                random_angle = np.random.uniform(0, 2 * np.pi)
                dx, dy = np.cos(random_angle), np.sin(random_angle)
            else:
                dx, dy = last_dx, last_dy
        else:
            dx, dy = dx / mag, dy / mag
            
        if len(path) > 1 and (dx * last_dx + dy * last_dy) < 0:
            dx, dy = -dx, -dy

        next_x = curr_x + dx * Hyperparameters.STEP_SIZE
        next_y = curr_y + dy * Hyperparameters.STEP_SIZE

        next_x_idx = int(np.clip(next_x, 0, W - 1))
        next_y_idx = int(np.clip(next_y, 0, H - 1))

        if next_x_idx == map_x and next_y_idx == map_y:
            fallback_dx = np.sign(dx) if dx != 0 else 0
            fallback_dy = np.sign(dy) if dy != 0 else 0
            if fallback_dx == 0 and fallback_dy == 0:
                fallback_dx, fallback_dy = np.random.choice([-1, 1]), np.random.choice([-1, 1])
                
            next_x_idx = int(np.clip(map_x + fallback_dx, 0, W - 1))
            next_y_idx = int(np.clip(map_y + fallback_dy, 0, H - 1))
            
            if next_x_idx == map_x and next_y_idx == map_y:
                stroke_generation_supervisor.register_event(Events.flat_gradient)
                break
        
        # Perceptual color boundary rejection check
        color_diff = np.sqrt(np.sum(Hyperparameters.COLOR_WEIGHTS * ((image[next_y_idx, next_x_idx] - palette_color) ** 2)))
        if color_diff > Hyperparameters.COLOR_DIFF_THRESHOLD and stroke_length_pixels >= Hyperparameters.MIN_LEN:
            stroke_generation_supervisor.register_event(Events.stroke_too_short)
            break

        path.append((next_x_idx, next_y_idx))
        curr_x, curr_y = next_x, next_y
        last_dx, last_dy = dx, dy
        stroke_length_pixels += math.sqrt((last_dx)**2 + (last_dy)**2)
    
    return path, stroke_length_pixels