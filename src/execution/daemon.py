from datatypes import RobotCalibration, StrokeSequence, StrokePath, LoadBrush
from robot import load_brush, execute_stroke, water_brush
from robot import Camera
from visualisation import get_stroke_frame
import cv2
from pathlib import Path
import os
from .log import Log
from webserver import WebApp, FeedType


class ExecutionDaemon:
    @classmethod
    def run_thread(cls, printer, project_name):
        # Load Data
        input_file = Path("data/stroke_renders") / Path(project_name + ".json")
        my_stroke_sequence = StrokeSequence.load_from_json(input_file)
        my_calibration = RobotCalibration.load("data/my_robot_calibration.json")

        try:
            os.mkdir(Path("timelapse") / Path(project_name))
        except FileExistsError:
            pass # ok

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

        START_INDEX = Log.get_progress(WebApp._project)

        expected_frame = get_stroke_frame(my_stroke_sequence, START_INDEX, do_annotate=False)
        WebApp.set_feed_image(FeedType.expected_feed, cv2.flip(expected_frame, 0))

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
                color_index = [
                    index
                    for index, entry in enumerate(my_calibration.color_palette.color_positions)
                    if list(hex_to_rgb(entry["color"])) == list(command.color)
                ][0]
                # re-water the brush
                water_brush(printer, my_calibration)
                # Take picture
                pil_picture = Camera.take_picture_and_return()
                # re-load brush
                load_brush(printer, my_calibration, color_index)

                WebApp.set_feed_image(FeedType.camera_feed, pil_picture)
                expected_frame = get_stroke_frame(my_stroke_sequence, index, do_annotate=False)
                WebApp.set_feed_image(FeedType.expected_feed, cv2.flip(expected_frame, 0))
            else:
                raise ValueError("Type not found.")
            

            
            Log.set_progress(index, WebApp._project)


        water_brush(printer, my_calibration)

        # Close camera and create timelapse
        Camera.close()
        Camera.create_timelapse()