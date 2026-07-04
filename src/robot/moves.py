
import math

FEED_RATE_TRAVEL = 3000
FEED_RATE_WET = 1500
FEED_RATE_LOAD = 700
FEED_RATE_PAINT = 1200


def swirl(printer, center_x, center_y, z_top, z_down, radius, down_turns=3):
    transition_steps = 16
    loading_steps = 16
    # Move down while rotating
    for i in range(transition_steps + 1):
        angle = (2 * math.pi / transition_steps) * i
        circle_x = center_x + radius * math.cos(angle)
        circle_y = center_y + radius * math.sin(angle)
        z = z_top*(1 - i/transition_steps) + z_down*(i/transition_steps)
        printer.move_to(x=circle_x, y=circle_y, z=z,  feed_rate=FEED_RATE_WET)

    # rotate
    for _ in range(down_turns):
        for i in range(loading_steps + 1):
            angle = (2 * math.pi / loading_steps) * i
            circle_x = center_x + radius * math.cos(angle)
            circle_y = center_y + radius * math.sin(angle)
            printer.move_to(x=circle_x, y=circle_y, z=z_down,  feed_rate=FEED_RATE_WET)

    # Move up while rotating
    for i in range(transition_steps + 1):
        angle = (2 * math.pi / transition_steps) * i
        circle_x = center_x + radius * math.cos(angle)
        circle_y = center_y + radius * math.sin(angle)
        z = z_top*(i/transition_steps) + z_down*(1 - i/transition_steps)
        printer.move_to(x=circle_x, y=circle_y, z=z,  feed_rate=FEED_RATE_WET)


def water_brush(printer, my_robot_calibration, down_turns=3):
    print("Watering Brush")
    x_water, y_water, z_water = my_robot_calibration.water_reservoir
    safe_z_height = my_robot_calibration.safe_height

    # Lift to safe height, move to water cup, and dip down
    printer.move_to(z=safe_z_height, feed_rate=FEED_RATE_TRAVEL)
    printer.move_to(x=x_water, y=y_water, feed_rate=FEED_RATE_TRAVEL)

    # Perform a rapid mechanical "shake" to flex bristles and soak up water
    swirl(
        printer,
        center_x=x_water,
        center_y=y_water,
        z_top=safe_z_height,
        z_down=z_water,
        radius=18.0,
        down_turns=down_turns
    )
    
    # lift up
    printer.move_to(z=safe_z_height, feed_rate=FEED_RATE_TRAVEL)


def load_brush(printer, my_robot_calibration, color_index, down_turns=2):
    print("Loading brush")
    x_paint, y_paint, z_paint = my_robot_calibration.color_palette.color_positions[color_index]["position"]
    safe_z_height = my_robot_calibration.safe_height

    # Move over the target well, dip down to paint height
    printer.move_to(x=x_paint, y=y_paint, feed_rate=FEED_RATE_TRAVEL)

    swirl(
        printer,
        center_x=x_paint,
        center_y=y_paint,
        z_top=safe_z_height,
        z_down=z_paint,
        radius=8.0,
        down_turns=down_turns
    )

    # Move back up to clear the well completely before drawing or traveling
    printer.move_to(z=safe_z_height, feed_rate=FEED_RATE_TRAVEL)
    


def execute_stroke(printer, robot_calibration, stroke_sequence, index: int, up_height=None) -> None:
    """
    Fetches a specific stroke path by index from a StrokeSequence, lifts the brush,
    travels to the starting position, drops down, and traces the coordinates.
    
    :param printer: The connected Printer instance (e.g., SerialPrinter)
    :param stroke_sequence: The StrokeSequence object containing the stroke list
    :param index: Index of the stroke to execute
    """
    
    down_height = robot_calibration.bottom_left[2]

    if up_height is not None:
        up_height += down_height
    else:
        up_height = robot_calibration.safe_height
    
    # 1. Bounds check to ensure the index exists
    if index < 0 or index >= len(stroke_sequence.strokes):
        print(f"Error: Stroke index {index} out of bounds (0 to {len(stroke_sequence.strokes)-1}).")
        return

    # 2. Extract the specific stroke data
    stroke = stroke_sequence.strokes[index]
    
    # Safety check: ensure the stroke path actually has points
    if not stroke.path:
        print(f"Stroke at index {index} has an empty path. Skipping.")
        return

    # 3. Pull the starting coordinate
    start_x, start_y = stroke.path[0]
    start_x += robot_calibration.bottom_left[0]
    start_y += robot_calibration.bottom_left[1]

    # 4. Lift up to travel height first (prevent dragging across previous paint)
    # printer.move_to(z=up_height, feed_rate=FEED_RATE_TRAVEL)

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
    printer.move_to(z=up_height, feed_rate=FEED_RATE_TRAVEL)
