from datatypes import RobotCalibration, StrokeSequence, StrokePath
from robot import SerialPrinter, Printer
import math

FEED_RATE_TRAVEL = 3000
FEED_RATE_WET = 1500
FEED_RATE_LOAD = 700
FEED_RATE_PAINT = 1200

def scrub(printer, center_x, center_y, z_top, z_down, radius=10, cycles=2, steps_per_cycle=32):
    """
    Moves back and forth in the X direction while dipping down.
    The lowest point (z_down) occurs exactly in the center of the palette.
    """
    # Total steps across all back-and-forth strokes
    total_steps = cycles * steps_per_cycle
    
    for i in range(total_steps + 1):
        # Normalize the progress through the entire movement (0.0 to 1.0)
        progress = i / total_steps
        
        # 1. Calculate X: Oscillates back and forth using a cosine wave
        # Multiplying by cycles * 2 * pi ensures it completes the requested number of full laps
        angle_x = progress * cycles * 2 * math.pi
        x = center_x + radius * math.cos(angle_x)
        
        # 2. Calculate Y: Stays fixed at the center line
        y = center_y
        
        # 3. Calculate Z: Must be lowest (z_down) when X is at center_x.
        # X is at the center when cos(angle_x) is 0, which means sin(angle_x) is at 1 or -1.
        # By taking the absolute value of sin, we get a wave that hits 1 at every center crossing.
        z_interpolation = abs(math.sin(angle_x))
        
        # Interpolate between z_top (when at the edges) and z_down (when at the center)
        z = z_top * (1 - z_interpolation) + z_down * z_interpolation
        
        # Move the printer
        printer.move_to(x=x, y=y, z=z, feed_rate=FEED_RATE_WET)

def water_brush(printer, my_robot_calibration):
    x_water, y_water, z_water = my_robot_calibration.water_reservoir
    safe_z_height = my_robot_calibration.safe_height
    print("--- Starting Full Brush Prep Sequence ---")

    print(f"Moving to water reservoir at ({x_water}, {y_water})...")
    # Lift to safe height, move to water cup, and dip down
    printer.move_to(z=safe_z_height, feed_rate=FEED_RATE_TRAVEL)
    printer.move_to(x=x_water, y=y_water, feed_rate=FEED_RATE_TRAVEL)

    print("Agitating brush in water...")
    # Perform a rapid mechanical "shake" to flex bristles and soak up water
    scrub(
        printer,
        center_x=x_water,
        center_y=y_water,
        z_top=z_water+4,
        z_down=z_water,
    )
    
    # lift up
    printer.move_to(z=safe_z_height, feed_rate=FEED_RATE_TRAVEL)


def load_brush(printer, my_robot_calibration, color_index):
    x_paint, y_paint, z_paint = my_robot_calibration.color_palette.color_positions[color_index]["position"]
    safe_z_height = my_robot_calibration.safe_height
    print(f"Moving to paint palette at ({x_paint}, {y_paint})...")
    # Move over the target well, dip down to paint height
    printer.move_to(x=x_paint, y=y_paint, feed_rate=FEED_RATE_TRAVEL)

    print("Swirling brush to load paint...")
    scrub(
        printer,
        center_x=x_paint,
        center_y=y_paint,
        z_top=z_paint+4,
        z_down=z_paint,
        radius=5
    )

    # Move back up to clear the well completely before drawing or traveling
    printer.move_to(z=safe_z_height, feed_rate=FEED_RATE_TRAVEL)
    
    print("--- Brush prep complete and ready to paint! ---")

def execute_stroke(printer: Printer, robot_calibration:RobotCalibration, stroke_sequence: StrokeSequence, index: int) -> None:
    """
    Fetches a specific stroke path by index from a StrokeSequence, lifts the brush,
    travels to the starting position, drops down, and traces the coordinates.
    
    :param printer: The connected Printer instance (e.g., SerialPrinter)
    :param stroke_sequence: The StrokeSequence object containing the stroke list
    :param index: Index of the stroke to execute
    """
    up_heigth = robot_calibration.safe_height
    down_height = robot_calibration.bottom_left[2]
    
    # 1. Bounds check to ensure the index exists
    if index < 0 or index >= len(stroke_sequence.strokes):
        print(f"Error: Stroke index {index} out of bounds (0 to {len(stroke_sequence.strokes)-1}).")
        return

    # 2. Extract the specific stroke data
    stroke: StrokePath = stroke_sequence.strokes[index]
    
    # Safety check: ensure the stroke path actually has points
    if not stroke.path:
        print(f"Stroke at index {index} has an empty path. Skipping.")
        return

    print(f"--- Executing Stroke {index} | Color: {stroke.color} | Width: {stroke.brushWidth} ---")
    print(f"Path {stroke.path}")
    
    # 3. Pull the starting coordinate
    start_x, start_y = stroke.path[0]
    start_x += robot_calibration.bottom_left[0]
    start_y += robot_calibration.bottom_left[1]

    # 4. Lift up to travel height first (prevent dragging across previous paint)
    printer.move_to(z=up_heigth, feed_rate=FEED_RATE_TRAVEL)

    # 5. Travel horizontally to the start position of the stroke
    printer.move_to(x=start_x, y=start_y, feed_rate=FEED_RATE_TRAVEL)

    # 6. Lower the brush onto the canvas
    printer.move_to(z=down_height, feed_rate=FEED_RATE_TRAVEL)

    # 7. Trace out the rest of the points on the canvas at painting speed
    # (Starting from index 1 because we are already at point 0)
    for next_point in stroke.path[1:]:
        next_x, next_y = next_point
        next_x += robot_calibration.bottom_left[0]
        next_y += robot_calibration.bottom_left[1] 
        printer.move_to(x=next_x, y=next_y, feed_rate=FEED_RATE_PAINT)

    # 8. Lift the brush up immediately when the stroke is finished to prevent a paint blob
    printer.move_to(z=up_heigth, feed_rate=FEED_RATE_TRAVEL)

    print(f"--- Stroke {index} execution complete ---")