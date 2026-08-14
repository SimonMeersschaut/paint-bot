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
print(my_calibration.get_canvas_size())
print(my_stroke_sequence.image_size)

## Execute Stroke
def hex_to_rgb(hex_str):
    """#AABBCC"""
    hex_str = hex_str.lstrip("#")
    return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]


printer.move_to(z=my_calibration.safe_height)

START_INDEX = 0

# expected_frame = get_stroke_frame(my_stroke_sequence, START_INDEX, do_annotate=False)
# WebApp.set_feed_image(FeedType.expected_feed, cv2.flip(expected_frame, 0))

if START_INDEX != 0:
    input("Start index != 0, do you want to continue? [y]")

for index in range(START_INDEX, len(my_stroke_sequence.strokes)):   # continue where ended
    WebApp.set_progress(index/len(my_stroke_sequence.strokes))
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


water_brush(printer, my_calibration)

# Close camera and create timelapse
Camera.close()
Camera.create_timelapse()