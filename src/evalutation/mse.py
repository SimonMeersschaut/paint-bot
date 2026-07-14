# TODO imports

def evaluate(pil_resized_image, stroke_sequence, np_padded_mask_resized, show_debug=False) -> float:
    """Compute a weighted mean squared error between target image and rendered strokes.

    - np_resized_image: numpy array (H, W, 3) in RGB (uint8 or float [0,1]).
    - stroke_sequence: StrokeSequence; rendered using `visualize_stroke_sequence`.

    Returns a single float: the weighted MSE over HSV channels using `HSV_WEIGHTS`.
    """
    mask = np.asarray(np_padded_mask_resized)        # convert if it's PIL or similar
    mask_bool = mask.astype(bool) 

    # Render strokes to an image (PIL) without annotations
    pil_render = visualize_stroke_sequence(stroke_sequence, do_annotate=False)
    render_np = np.array(pil_render)  # RGB uint8

    pil_blurred_image = pil_resized_image.filter(ImageFilter.GaussianBlur(radius=3))
    np_resized_blurred_image = np.array(pil_blurred_image)

    target = _to_uint8_rgb(np_resized_blurred_image)
    render = _to_uint8_rgb(render_np)

    if target.shape != render.shape:
        raise ValueError(f"Shape mismatch: target {target.shape} vs render {render.shape} vs mask {mask_bool.shape}")

    # Convert to HSV (OpenCV uses H:0-179, S:0-255, V:0-255)
    target_hsv = cv2.cvtColor(target, cv2.COLOR_RGB2HSV).astype(np.float32)
    render_hsv = cv2.cvtColor(render, cv2.COLOR_RGB2HSV).astype(np.float32)

    # Hue cyclic difference
    hue_diff = np.abs(target_hsv[:, :, 0] - render_hsv[:, :, 0])
    hue_diff = np.minimum(hue_diff, 180.0 - hue_diff)

    sat_diff = target_hsv[:, :, 1] - render_hsv[:, :, 1]
    val_diff = target_hsv[:, :, 2] - render_hsv[:, :, 2]

    if show_debug:
        show_np_image(np.where(mask_bool, sat_diff, 0.0))

    # Weighted per-pixel squared error
    weights = np.asarray(Hyperparameters.HSV_WEIGHTS, dtype=np.float32)
    per_pixel = (weights[0] * (hue_diff ** 2) +
                 weights[1] * (sat_diff ** 2) +
                 weights[2] * (val_diff ** 2))
    
    mse = float(np.mean(per_pixel))
    return mse