from dataclasses import dataclass
import json

class ColorPalette:
    def __init__(self):
        self.color_positions = []

    def add_color(self, position, color):
        self.color_positions.append(
            {"position": position, "color": color}
        )
    
    def dump(self) -> list:
        return self.color_positions

    def load(self, data: list) -> None:
        """Populates the palette from a list of position/color dicts."""
        self.color_positions = data


@dataclass
class RobotCalibration:
    top_left: tuple[int, int, int]
    top_right: tuple[int, int, int]
    bottom_left: tuple[int, int, int]
    bottom_right: tuple[int, int, int]
    water_reservoir: tuple[int, int, int]
    safe_height: int
    canvas_up_height: int
    color_palette = None

    def __post_init__(self):
        self.color_palette = ColorPalette()
    
    def get_canvas_size(self) -> tuple[int, int]:
        return (
            int(self.bottom_right[0] - self.bottom_left[0]),
            int(self.top_right[1] - self.bottom_right[1])
            # round down for pixels in a PIL image
        )
    
    def dump(self, path: str) -> None:
        """Saves the calibration data to a JSON file."""
        with open(path, 'w') as f:
            data = {
                "top_left": self.top_left,
                "top_right": self.top_right,
                "bottom_left": self.bottom_left,
                "bottom_right": self.bottom_right,
                "water_reservoir": self.water_reservoir,
                "color_palette": self.color_palette.dump(),
                "safe_height": self.safe_height,
                "canvas_up_height": self.canvas_up_height,
            }
            json.dump(data, f, indent=4)

    @classmethod
    def load(cls, path: str) -> "RobotCalibration":
        """Loads a JSON file and returns a new RobotCalibration instance."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        instance = cls(
            top_left=tuple(data["top_left"]),
            top_right=tuple(data["top_right"]),
            bottom_left=tuple(data["bottom_left"]),
            bottom_right=tuple(data["bottom_right"]),
            water_reservoir=tuple(data["water_reservoir"]),
            safe_height=data["safe_height"],
            canvas_up_height=data["canvas_up_height"],
        )
        
        if "color_palette" in data:
            instance.color_palette.load(data["color_palette"])
            
        return instance