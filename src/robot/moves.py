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


import math

def execute_stroke(printer: Printer, robot_calibration: RobotCalibration, stroke_sequence: StrokeSequence, index: int) -> None:
    """
    Fetches a specific stroke path by index from a StrokeSequence, lifts the brush,
    travels to a calculated lead-in position, smoothly swoops down into the stroke,
    paints, and gracefully swoops up and away to prevent robotic artifacts.
    
    :param printer: The connected Printer instance (e.g., SerialPrinter)
    :param robot_calibration: Calibration data for coordinate offsets and heights
    :param stroke_sequence: The StrokeSequence object containing the stroke list
    :param index: Index of the stroke to execute
    """
    up_height = robot_calibration.safe_height
    down_height = robot_calibration.bottom_left[2]
    
    # Configurable extension distance for the fluid motion (in mm)
    LEAD_DISTANCE = 5.0 
    
    # 1. Bounds check to ensure the index exists
    if index < 0 or index >= len(stroke_sequence.strokes):
        print(f"Error: Stroke index {index} out of bounds (0 to {len(stroke_sequence.strokes)-1}).")
        return

    # 2. Extract the specific stroke data
    stroke: StrokePath = stroke_sequence.strokes[index]
    
    # Safety check: ensure the stroke path actually has points
    if not stroke.path or len(stroke.path) < 2:
        print(f"Stroke at index {index} requires at least 2 points for natural planning. Skipping.")
        return

    print(f"--- Executing Natural Stroke {index} | Color: {stroke.color} | Width: {stroke.brushWidth} ---")
    
    # 3. Convert all path points to absolute world coordinates first
    abs_path = []
    for pt in stroke.path:
        abs_x = pt[0] + robot_calibration.bottom_left[0]
        abs_y = pt[1] + robot_calibration.bottom_left[1]
        abs_path.append((abs_x, abs_y))
        
    start_x, start_y = abs_path[0]
    end_x, end_y = abs_path[-1]

    # 4. Calculate beginning direction vector for the lead-in
    dx_start = abs_path[1][0] - start_x
    dy_start = abs_path[1][1] - start_y
    dist_start = math.sqrt(dx_start**2 + dy_start**2)
    
    if dist_start > 0:
        ux_start = dx_start / dist_start
        uy_start = dy_start / dist_start
        # Back up away from the direction of the stroke
        leadin_x = start_x - (ux_start * LEAD_DISTANCE)
        leadin_y = start_y - (uy_start * LEAD_DISTANCE)
    else:
        leadin_x, leadin_y = start_x, start_y

    # 5. Calculate ending direction vector for the lead-out
    dx_end = end_x - abs_path[-2][0]
    dy_end = end_y - abs_path[-2][1]
    dist_end = math.sqrt(dx_end**2 + dy_end**2)
    
    if dist_end > 0:
        ux_end = dx_end / dist_end
        uy_end = dy_end / dist_end
        # Follow through past the final stroke coordinate
        leadout_x = end_x + (ux_end * LEAD_DISTANCE)
        leadout_y = end_y + (uy_end * LEAD_DISTANCE)
    else:
        leadout_x, leadout_y = end_x, end_y

    # ================= ACTION SEQUENCE =================

    # Step A: Ensure brush is safely raised up before traveling
    printer.move_to(z=up_height, feed_rate=FEED_RATE_TRAVEL)

    # Step B: Travel to the extended airborne start point (Lead-in position)
    printer.move_to(x=leadin_x, y=leadin_y, feed_rate=FEED_RATE_TRAVEL)

    # Step C: Swoop down! Move to the true start point and down_height simultaneously
    printer.move_to(x=start_x, y=start_y, z=down_height, feed_rate=FEED_RATE_PAINT)

    # Step D: Trace out the core points on the canvas at painting speed
    for next_x, next_y in abs_path[1:]:
        printer.move_to(x=next_x, y=next_y, feed_rate=FEED_RATE_PAINT)

    # Step E: Swoop up! Fluidly exit the canvas by moving to leadout and up_height simultaneously
    printer.move_to(x=leadout_x, y=leadout_y, z=up_height, feed_rate=FEED_RATE_PAINT)

    print(f"--- Stroke {index} execution complete ---")