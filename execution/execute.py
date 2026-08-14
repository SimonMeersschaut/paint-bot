from datatypes import RobotCalibration, StrokeSequence, StrokePath, LoadBrush
from robot import SerialPrinter, Printer
from robot import load_brush, execute_stroke, water_brush
from robot import Camera
from webserver import WebApp, FeedType
# from visualisation import get_stroke_frame
from PIL import Image
import cv2

printer: Printer = SerialPrinter()
WebApp.init(on_fan_change=printer.set_fan)
WebApp.start()
printer.connect()
Camera.start() # camera

# Load Data
my_stroke_sequence = StrokeSequence.load_from_json("data/output.json")
my_calibration = RobotCalibration.load("data/my_robot_calibration.json")

## Resize to the canvas
my_stroke_sequence.resize_to(my_calibration.get_canvas_size())
my_stroke_sequence.mirror_y_axis()
print(my_calibration.get_canvas_size())
print(my_stroke_sequence.image_size)

## Execute Stroke
def hex_to_rgb(hex_str):
    """#AABBCC"""
    hex_str = hex_str.lstrip("#")
    return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]


def stroke_sequence_to_expected_svg(stroke_sequence: StrokeSequence) -> str:
    width, height = stroke_sequence.image_size
    width = max(1, int(width))
    height = max(1, int(height))

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">',
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
    ]

    for command_index, command in enumerate(stroke_sequence.strokes):
        if type(command) != StrokePath or not command.path:
            continue

        points = []
        for point_index, (x, y) in enumerate(command.path):
            prefix = "M" if point_index == 0 else "L"
            points.append(f"{prefix}{float(x):.2f} {float(y):.2f}")

        path_data = " ".join(points)
        stroke_width = max(1, int(getattr(command, "brushDiameter", 1)))
        svg_parts.append(
            f'<path data-command-index="{command_index}" d="{path_data}" fill="none" stroke="#a7adb4" stroke-opacity="0.35" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round"/>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)


expected_svg = stroke_sequence_to_expected_svg(my_stroke_sequence)
WebApp.set_expected_svg(expected_svg, total_strokes=len(my_stroke_sequence.strokes))


printer.move_to(z=my_calibration.safe_height)

START_INDEX = 123

# expected_frame = get_stroke_frame(my_stroke_sequence, START_INDEX, do_annotate=False)
# WebApp.set_feed_image(FeedType.expected_feed, cv2.flip(expected_frame, 0))

if START_INDEX != 0:
    input("Start index != 0, do you want to continue? [y]")

for index in range(START_INDEX, len(my_stroke_sequence.strokes)):   # continue where ended
    WebApp.set_progress(index/len(my_stroke_sequence.strokes))
    WebApp.set_current_stroke_index(index)
    print(f"Executing index: {index}")
    command = my_stroke_sequence.strokes[index]
    if type(command) == StrokePath:
        execute_stroke(
            printer=printer,
            robot_calibration=my_calibration,
            stroke_sequence=my_stroke_sequence,
            index=index,
        )
    elif type(command) == LoadBrush:
        # Gets the index of the current color in the color palette
        color_index = 0 # monochrome
        # [
        #     index
        #     for index, entry in enumerate(my_calibration.color_palette.color_positions)
        #     if list(hex_to_rgb(entry["color"])) == list(command.color)
        # ][0]
        # re-water the brush
        water_brush(printer, my_calibration)
        # Take picture
        pil_picture = Camera.take_picture_and_return()
        # re-load brush
        load_brush(printer, my_calibration, color_index)

        WebApp.set_feed_image(FeedType.camera_feed, pil_picture)
        # expected_frame = get_stroke_frame(my_stroke_sequence, index, do_annotate=False)
        # WebApp.set_feed_image(FeedType.expected_feed, cv2.flip(expected_frame, 0))
    else:
        raise ValueError("Type not found.")
    
    with open("log", 'a') as f:
        f.write(f"{index}\n")


WebApp.set_current_stroke_index(len(my_stroke_sequence.strokes))
WebApp.set_progress(1.0)


water_brush(printer, my_calibration)

# Close camera and create timelapse
Camera.close()
Camera.create_timelapse()