from datatypes import RobotCalibration, StrokeSequence
from robot import SerialPrinter, Printer
from robot import load_brush, execute_stroke, water_brush
from robot import start, close, take_picture, create_timelapse


printer: Printer = SerialPrinter()
printer.connect()

start() # camera

## Load Data
my_stroke_sequence = StrokeSequence.load_from_json("data/my_stroke_sequence.json")
my_calibration = RobotCalibration.load("data/my_robot_calibration.json")

## Resize to the canvas
my_stroke_sequence.resize_to(my_calibration.get_canvas_size())
print(my_calibration.get_canvas_size())
print(my_stroke_sequence.image_size)
my_stroke_sequence.save_to_json("data/resized_stroke_sequence.json")

## Execute Stroke
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]

current_color = None
current_color_repetition = 0
for index in range(0, len(my_stroke_sequence.strokes)):   # continue where ended
    print(f"Executing index: {index}")
    cleaning_needed: bool = current_color != my_stroke_sequence.strokes[index].color
    color_change_needed: bool = current_color_repetition >= 30
    if cleaning_needed or color_change_needed:
        current_color = my_stroke_sequence.strokes[index].color
        current_color_repetition = 0
        # Gets the index of the current color in the color palette
        color_index = [
            index
            for index, entry in enumerate(my_calibration.color_palette.color_positions)
            if list(hex_to_rgb(entry["color"])) == list(current_color)
        ][0]

        # re-water the brush
        water_brush(printer, my_calibration, down_turns=5)
        printer.wait_for_arrival(
            x=my_calibration.water_reservoir[0],
            y=my_calibration.water_reservoir[1],
            z=my_calibration.safe_height,
        )
        # Take picture
        take_picture()
        # re-load brush
        load_brush(printer, my_calibration, color_index, down_turns=3)

    execute_stroke(
        printer=printer,
        robot_calibration=my_calibration,
        stroke_sequence=my_stroke_sequence,
        index=index,
        up_height = 4
    )

    current_color_repetition += 1


water_brush(printer, my_calibration)

# Close camera and create timelapse
close()
create_timelapse()