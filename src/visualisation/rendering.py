import cv2
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm #  progress bar

def get_stroke_frame(stroke_sequence, stroke_index, label="", do_annotate=True):
    """Create a frame showing strokes up to a specified index with dimension annotations.
    
    Args:
        stroke_sequence: A StrokeSequence instance containing StrokePath objects.
        stroke_index: Index of the last stroke to include in the frame (0-indexed).
                     If -1, no strokes are drawn (blank canvas with dimensions).
        opacity: Float between 0.0 and 1.0 specifying how opaque the paint strokes should look.
        label: Custom text string to burn into the top-center padding area of the frame.
    
    Returns:
        A numpy array representing the frame with dimensions from image_size and annotations.
    """

    opacity=0.5
    
    # Initialize the single-entry cache attribute if it doesn't exist
    if not hasattr(get_stroke_frame, "cache"):
        # Format: {"index": -1, "canvas": None}
        get_stroke_frame.cache = {"index": -1, "canvas": None}
    
    cached_idx = get_stroke_frame.cache["index"]
    cached_canvas = get_stroke_frame.cache["canvas"]
    
    canvas_width, canvas_height = stroke_sequence.image_size
    # Can we resume from the cache? 
    # Must have a valid cache, and the requested index must be forward-facing.
    if cached_canvas is not None and stroke_index >= cached_idx:
        canvas = cached_canvas.copy()
        start_index = cached_idx + 1
    else:
        # Cache miss or "rewind" scenario: Start from scratch
        base_canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
        canvas = base_canvas.copy()
        start_index = 0

    # Draw strokes from our start_index up to the requested stroke_index
    upper_bound = min(max(stroke_index + 1, 0), len(stroke_sequence.strokes))
    
    for i in range(start_index, upper_bound):
        command = stroke_sequence.strokes[i]

        if hasattr(command, 'path'): #  is StrokePath:
            stroke = command
        else:
            continue # skip LoadBrush
        
        # Guard against empty paths
        if not stroke.path or len(stroke.path) < 2:
            continue
            
        # Convert RGB to BGR for OpenCV
        pure_color = np.array([stroke.color[2], stroke.color[1], stroke.color[0]])
        color_bgr = (1 - stroke.pigment) * np.array([255, 255, 255]) + (stroke.pigment) * pure_color
        color_bgr = color_bgr.tolist()
        
        # Reshape path points into a compatible numpy matrix array
        pts = np.array(stroke.path, dtype=np.int32).reshape((-1, 1, 2))
        
        # Create a localized transparent overlay image layer for alpha blending
        overlay = canvas.copy()
        
        # Draw the continuous curve onto the overlay
        cv2.polylines(overlay, [pts], isClosed=False, color=color_bgr, 
                        thickness=round(stroke.brushWidth / 2), lineType=cv2.LINE_AA)
        
        # Perform alpha blending
        cv2.addWeighted(overlay, opacity, canvas, 1.0 - opacity, 0, canvas)


    # Update the single cache entry with the final state of this current run
    # (We save it before UI text/annotations are burned into it)
    get_stroke_frame.cache["index"] = stroke_index
    get_stroke_frame.cache["canvas"] = canvas.copy()


    if not do_annotate:
        return canvas
    
    canvas = np.flip(canvas, axis=0) # vertical flip

    # Add padding and annotations
    padding = 100
    annotated_height = canvas_height + 2 * padding
    annotated_width = canvas_width + 2 * padding
    
    annotated_frame = np.ones((annotated_height, annotated_width, 3), dtype=np.uint8) * 255
    
    # Place canvas in the center
    annotated_frame[padding:padding+canvas_height, padding:padding+canvas_width] = canvas
    
    # Draw border around canvas
    cv2.rectangle(annotated_frame, (padding, padding), 
                  (padding+canvas_width, padding+canvas_height), (0, 0, 0), 2)
    
    # Annotation styling
    arrow_color = (0, 0, 0)
    arrow_thickness = 2
    
    # Load a reliable TrueType font for PIL so sizes match perfectly
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 18)
        except IOError:
            font = ImageFont.load_default()
    
    # --- Horizontal dimension (width) ---
    arrow_y = padding + canvas_height + 40
    arrow_x_start = padding
    arrow_x_end = padding + canvas_width
    arrow_mid = (arrow_x_start + arrow_x_end) // 2
    
    # Left arrow
    cv2.arrowedLine(annotated_frame, (arrow_mid, arrow_y), 
                    (arrow_x_start, arrow_y), arrow_color, arrow_thickness, tipLength=0.1)
    # Right arrow
    cv2.arrowedLine(annotated_frame, (arrow_mid, arrow_y), 
                    (arrow_x_end, arrow_y), arrow_color, arrow_thickness, tipLength=0.1)
    
    # --- Vertical dimension (height) ---
    arrow_x = padding + canvas_width + 40
    arrow_y_start = padding
    arrow_y_end = padding + canvas_height
    arrow_mid_v = (arrow_y_start + arrow_y_end) // 2
    
    # Top arrow
    cv2.arrowedLine(annotated_frame, (arrow_x, arrow_mid_v), 
                    (arrow_x, arrow_y_start), arrow_color, arrow_thickness, tipLength=0.1)
    # Bottom arrow
    cv2.arrowedLine(annotated_frame, (arrow_x, arrow_mid_v), 
                    (arrow_x, arrow_y_end), arrow_color, arrow_thickness, tipLength=0.1)
    
    # --- Render Text using PIL ---
    pil_img = Image.fromarray(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    # 1. Draw Width Text
    width_text = f"{canvas_width} {stroke_sequence.unit}"
    w_bbox = draw.textbbox((0, 0), width_text, font=font)
    w_text_width = w_bbox[2] - w_bbox[0]
    
    text_x = (arrow_x_start + arrow_x_end - w_text_width) // 2
    text_y = arrow_y + 15
    draw.text((text_x, text_y), width_text, fill=(0, 0, 0), font=font)
    
    # 2. Draw Height Text (Rotated)
    height_text = f"{canvas_height} {stroke_sequence.unit}"
    h_bbox = draw.textbbox((0, 0), height_text, font=font)
    h_text_width = h_bbox[2] - h_bbox[0]
    h_text_height = h_bbox[3] - h_bbox[1]
    
    text_canvas_w = h_text_width + 20
    text_canvas_h = h_text_height + 20
    text_img = Image.new('RGBA', (text_canvas_w, text_canvas_h), (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((10, 10), height_text, fill=(0, 0, 0, 255), font=font)
    
    rotated_text_img = text_img.rotate(90, expand=True)
    
    v_text_x = arrow_x + 15
    v_text_y = (arrow_y_start + arrow_y_end - rotated_text_img.size[1]) // 2
    
    pil_img.paste(rotated_text_img, (v_text_x, v_text_y), rotated_text_img)
    
    # 3. Draw Custom User Label (Centered at the top)
    if label:
        label_text = str(label)
        label_bbox = draw.textbbox((0, 0), label_text, font=font)
        label_width = label_bbox[2] - label_bbox[0]
        
        # Horizontally center the text based on the total annotated canvas width
        label_x = (annotated_width - label_width) // 2
        # Position it vertically right in the middle of the top 100px padding zone
        label_y = (padding - (label_bbox[3] - label_bbox[1])) // 2
        
        draw.text((label_x, label_y), label_text, fill=(0, 0, 0), font=font)
    
    # Convert back to OpenCV BGR array format
    annotated_frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    return annotated_frame

def calculate_stroke_duration(stroke_sequence, i, length_per_seconds:float):
    if not hasattr(stroke_sequence.strokes[i], 'path'):
        return 0 # TODO calculate loading time
    points = np.array(stroke_sequence.strokes[i].path)

    # Calculate differences between consecutive points: (dx, dy)
    coefficients = np.diff(points, axis=0)
    
    # Segment length = sqrt(dx^2 + dy^2)
    segment_lengths = np.sqrt(np.sum(coefficients**2, axis=1))
    
    total_path_length = float(np.sum(segment_lengths))
    return total_path_length / length_per_seconds

def animate_stroke_sequence(stroke_sequence, filename = "tmp"):
    """Animate a StrokeSequence data structure as a video with alpha transparency rendering."""
    canvas_width, canvas_height = stroke_sequence.image_size
    padding = 100
    video_width = canvas_width + 2 * padding
    video_height = canvas_height + 2 * padding
    fps = 30
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    if not os.path.exists("tmp"):
        raise FileExistsError("tmp not found.")
    video_writer = cv2.VideoWriter(f'tmp/{filename}.mp4', fourcc, fps, (video_width, video_height))

    print("Start video rendering...")
    clock_time = 0
    for i in tqdm(range(len(stroke_sequence.strokes))):
        # Pass the opacity down into the frame generator loop
        clock_time += calculate_stroke_duration(stroke_sequence, i, length_per_seconds=50) # mm/seconds
        frame = get_stroke_frame(stroke_sequence, i, label=f"{clock_time//60} min.")
        video_writer.write(frame)
        clock_time += 5 # time to load brush etc.
    
    video_writer.release()


def visualize_stroke_sequence(stroke_sequence, max_count=None, do_annotate = True):
    """Visualize a StrokeSequence by returning the image of all strokes with alpha transparency rendering."""
    if len(stroke_sequence.strokes) == 0:
        raise ValueError("No strokes to visualize")
    
    if max_count is None:
        max_count = len(stroke_sequence.strokes) - 1
    frame = get_stroke_frame(stroke_sequence, max_count, do_annotate=do_annotate)
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    return pil_image