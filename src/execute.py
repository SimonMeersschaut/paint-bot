from datatypes import RobotCalibration, StrokeSequence, StrokePath, LoadBrush
from robot import SerialPrinter, Printer
from robot import load_brush, execute_stroke, water_brush
from robot import start, close, take_picture, create_timelapse
from execution.database import init_db, log_progress, close_db


def main(start_index: int = 36):
    printer: Printer = SerialPrinter()
    printer.connect()

    # initialize progress DB
    conn = init_db()

    start()  # camera

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
        """#AABBCC"""
        hex_str = hex_str.lstrip("#")
        return [int(hex_str[i : i + 2], 16) for i in (0, 2, 4)]

    printer.move_to(z=my_calibration.safe_height)

    for index in range(start_index, len(my_stroke_sequence.strokes)):
        print(f"Executing index: {index}")
        command = my_stroke_sequence.strokes[index]
        if type(command) == StrokePath:
            execute_stroke(
                printer=printer,
                robot_calibration=my_calibration,
                stroke_sequence=my_stroke_sequence,
                index=index,
                up_height=7,
            )
        elif type(command) == LoadBrush:
            # Gets the index of the current color in the color palette
            color_index = [
                idx
                for idx, entry in enumerate(my_calibration.color_palette.color_positions)
                if list(hex_to_rgb(entry["color"])) == list(command.color)
            ][0]
            # re-water the brush
            water_brush(printer, my_calibration, down_turns=5)
            printer.move_and_wait(
                x=my_calibration.water_reservoir[0],
                y=my_calibration.water_reservoir[1],
                z=my_calibration.safe_height,
            )
            # Take picture
            take_picture()
            # re-load brush
            load_brush(printer, my_calibration, color_index, down_turns=3)
        else:
            raise ValueError("Type not found.")

        # Log progress to sqlite
        log_progress(conn, index)

    water_brush(printer, my_calibration)

    # close DB
    close_db(conn)

    # Close camera and create timelapse
    close()
    create_timelapse()


if __name__ == '__main__':
    main()
