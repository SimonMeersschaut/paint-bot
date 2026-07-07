from .supervisor import Events

import numpy as np
import math

ATTRACTION_WEIGHT: float = 0.3
ATTRACTION_RADIUS: int = 15
STEP_SIZE = 1
COLOR_WEIGHTS = np.array([0.30, 0.59, 0.11], dtype=np.float32)

MIN_LEN = 20
MAX_LEN = 20

def expand_point(image, H, W, gx, gy, start_point, segment_mask, coverage_mask, start_x_idx, source_y_idx, palette_color, stroke_generation_supervisor):
    path = [start_point]
    stroke_length_pixels = 0

    curr_x, curr_y = float(start_x_idx), float(source_y_idx)
    last_dx, last_dy = 0.0, 0.0
    for _ in range(MAX_LEN):
        map_y, map_x = int(np.clip(curr_y, 0, H - 1)), int(np.clip(curr_x, 0, W - 1))

        gx_val = gx[map_y, map_x]
        gy_val = gy[map_y, map_x]

        dx, dy = -gy_val, gx_val
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

        if ATTRACTION_WEIGHT > 0:
            y_min, y_max = max(0, map_y - ATTRACTION_RADIUS), min(H, map_y + ATTRACTION_RADIUS + 1)
            x_min, x_max = max(0, map_x - ATTRACTION_RADIUS), min(W, map_x + ATTRACTION_RADIUS + 1)

            local_unpainted = (segment_mask[y_min:y_max, x_min:x_max] & ~coverage_mask[y_min:y_max, x_min:x_max])
            
            if np.any(local_unpainted):
                local_indices = np.argwhere(local_unpainted)
                rel_y = local_indices[:, 0] + y_min - map_y
                rel_x = local_indices[:, 1] + x_min - map_x
                
                dist_sq = rel_x**2 + rel_y**2
                dist_sq[dist_sq == 0] = 1.0  
                weights = 1.0 / dist_sq
                
                pull_x = np.sum(rel_x * weights)
                pull_y = np.sum(rel_y * weights)
                
                pull_mag = np.sqrt(pull_x**2 + pull_y**2)
                if pull_mag > 0:
                    dx += ATTRACTION_WEIGHT * (pull_x / pull_mag)
                    dy += ATTRACTION_WEIGHT * (pull_y / pull_mag)
                    
                    final_mag = np.sqrt(dx**2 + dy**2)
                    if final_mag > 0:
                        dx, dy = dx / final_mag, dy / final_mag
            
        next_x = curr_x + dx * STEP_SIZE
        next_y = curr_y + dy * STEP_SIZE

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
        color_diff = np.sqrt(np.sum(COLOR_WEIGHTS * ((image[next_y_idx, next_x_idx] - palette_color) ** 2)))
        if color_diff > 75 and stroke_length_pixels >= MIN_LEN: 
            stroke_generation_supervisor.register_event(Events.stroke_too_short)
            break

        path.append((next_x_idx, next_y_idx))
        curr_x, curr_y = next_x, next_y
        last_dx, last_dy = dx, dy
        stroke_length_pixels += math.sqrt((last_dx)**2 + (last_dy)**2)
    
    return path, stroke_length_pixels