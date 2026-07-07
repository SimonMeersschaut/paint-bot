import numpy as np
import cv2
from datatypes import StrokePath
from .supervisor import Events
from .hyperparameters import COLOR_WEIGHTS, MIN_LEN

def accept_stroke(path, path_np, stroke_length_pixels, palette_color, image, image_hsv,
                  coverage_mask, stroke_sequence, stroke_generation_supervisor,
                  source_y_idx, start_x_idx):
    """Evaluate a candidate stroke for acceptance and update image/coverage/sequence.

    Returns True when the stroke was accepted and added to `stroke_sequence`.
    Returns False when the stroke was rejected (caller should increment attempts).
    Side-effects: may update `coverage_mask`, `stroke_sequence`, and register events.
    """
    H, W = image.shape[:2]

    if stroke_length_pixels < MIN_LEN:
        return False

    # extract coordinates and sampled colors
    path_x, path_y = path_np[:, 0], path_np[:, 1]
    actual_colors = image[path_y, path_x]

    # color error (per-channel weighted euclidean)
    error = np.sqrt(np.sum(COLOR_WEIGHTS * ((actual_colors - palette_color) ** 2), axis=1))
    mean_error = np.mean(error)
    if not stroke_generation_supervisor.accept_error(mean_error):
        stroke_generation_supervisor.register_event(Events.too_much_color_error)
        coverage_mask[source_y_idx, start_x_idx] = True
        return False

    # compute ROI for localized updates
    x_start, y_start = np.min(path_np, axis=0)
    x_end, y_end = np.max(path_np, axis=0)

    pad = stroke_generation_supervisor.brush_size + 1
    x_min_roi, y_min_roi = max(0, x_start - pad), max(0, y_start - pad)
    x_max_roi, y_max_roi = min(W, x_end + pad), min(H, y_end + pad)

    roi_w = x_max_roi - x_min_roi
    roi_h = y_max_roi - y_min_roi

    stroke_buffer_roi = np.zeros((roi_h, roi_w), dtype=np.uint8)
    pts_roi = path_np.copy()
    pts_roi[:, 0] -= x_min_roi
    pts_roi[:, 1] -= y_min_roi

    cv2.polylines(stroke_buffer_roi, [pts_roi.reshape((-1, 1, 2))], isClosed=False,
                  color=255, thickness=stroke_generation_supervisor.brush_size)

    current_stroke_mask_roi = (stroke_buffer_roi > 0)
    coverage_mask_roi = coverage_mask[y_min_roi:y_max_roi, x_min_roi:x_max_roi]

    over_painted_mask_roi = current_stroke_mask_roi & coverage_mask_roi
    newly_painted_mask_roi = current_stroke_mask_roi & ~coverage_mask_roi

    newly_painted_area = np.sum(newly_painted_mask_roi)
    over_painted_area = np.sum(over_painted_mask_roi)
    total_painted_area = newly_painted_area + over_painted_area

    if total_painted_area == 0:
        coverage_mask[source_y_idx, start_x_idx] = True
        stroke_generation_supervisor.register_event(Events.no_painted_area)
        return False

    if (newly_painted_area / total_painted_area) <= stroke_generation_supervisor.min_stroke_coverage_score:
        coverage_mask[source_y_idx, start_x_idx] = True
        stroke_generation_supervisor.register_event(Events.coverage_score_too_low)
        return False

    # apply color to image ROI and update coverage
    image_roi = image[y_min_roi:y_max_roi, x_min_roi:x_max_roi]
    image_roi[newly_painted_mask_roi] = palette_color

    coverage_mask_roi |= current_stroke_mask_roi

    boolean_stroke_mask = (current_stroke_mask_roi > 0)
    image_hsv_roi = image_hsv[y_min_roi:y_max_roi, x_min_roi:x_max_roi]

    average_hsv = np.mean(image_hsv_roi[boolean_stroke_mask], axis=0)
    pigment = average_hsv[1] / 255 * .6 + average_hsv[1] / 255 * .4

    stroke_sequence.strokes.append(
        StrokePath(
            color=tuple(int(c) for c in palette_color),
            pigment=pigment,
            path=path,
            brushWidth=stroke_generation_supervisor.brush_size,
        )
    )

    stroke_generation_supervisor.register_event(Events.stroke_accepted)
    return True
