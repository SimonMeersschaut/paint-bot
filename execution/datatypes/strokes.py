from dataclasses import dataclass
import json
from abc import ABC, abstractclassmethod
from datetime import datetime


class StrokeSequence:
    def __init__(self, image_size:tuple[int, int]):
        self.strokes = []
        self.image_size = image_size
        self.unit = "mm"
    
    def save_to_json(self, filepath: str):
        """Streams the StrokeSequence to a JSON file to prevent high memory usage."""
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write opening structure and metadata
            f.write("{\n")
            timestamp = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            f.write(f'  "date": "{timestamp}",\n')
            f.write(f'  "image_size": [{self.image_size[0]}, {self.image_size[1]}],\n')
            f.write(f'  "dimension_name": "{self.unit}",\n')
            f.write('  "strokes": [\n')
            
            # Stream out individual strokes
            num_strokes = len(self.strokes)
            for idx, command in enumerate(self.strokes):
                stroke_json = command.to_json()
                comma = "," if idx < num_strokes - 1 else ""
                f.write(f"    {stroke_json}{comma}\n")
                
            # Close json blocks
            f.write("  ]\n")
            f.write("}\n")
    
    @classmethod
    def load_from_json(cls, filepath: str) -> "StrokeSequence":
        """Loads a saved JSON file and reconstructs the StrokeSequence object."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        sequence = cls(image_size=tuple(data["image_size"]))
        sequence.unit = data.get("dimension_name", "mm")
        
        for data in data.get("strokes", []):
            command = Command.load_from_json(data)
            sequence.strokes.append(command)
            
        return sequence

    def resize_to(self, dimensions: tuple[int, int]) -> None:
        """Resizes the entire canvas, scale-adjusts all stroke paths, 

        and proportionally rescales brush widths to the new dimensions.
        """
        old_w, old_h = self.image_size
        new_w, new_h = dimensions
        if old_w == new_w and old_h == new_h:
            print("No resizing done.")
            return

        # Prevent DivisionByZero if handling empty or uninitialized classes
        scale_x = new_w / old_w if old_w > 0 else 1.0
        scale_y = new_h / old_h if old_h > 0 else 1.0
        
        # Use an average scale factor to dynamically adjust brush thickness
        scale_brush = (scale_x + scale_y) / 2.0

        # Update each stroke inline
        for command in self.strokes:
            if type(command) == StrokePath:
                # 1. Scale coordinates (x, y)
                scaled_path = []
                for x, y in command.path:
                    # Keeping as float or round() depending on precision needs. 
                    # Since coordinates default to pixels, round() is generally safest.
                    scaled_x = round(x * scale_x)
                    scaled_y = round(y * scale_y)
                    scaled_path.append((scaled_x, scaled_y))
                
                command.path = scaled_path

                # 2. Scale the brush stroke thickness (ensuring it never drops below 1 pixel)
                command.brushDiameter = max(1, round(command.brushDiameter * scale_brush))

        # Update the canvas bounds to complete the resize operation
        self.image_size = dimensions

class Command(ABC):
    
    @abstractclassmethod
    def to_json(self) -> dict:
        ...
    
    def load_from_json(data: dict) -> object:
        if data["type"] == StrokePath.__name__:
            return StrokePath.load_from_json(data)
        elif data["type"] == LoadBrush.__name__:
            return LoadBrush.load_from_json(data)
        else:
            raise ValueError("Type not found.")
    
    def get_type(self):
        return type(self).__name__

@dataclass
class StrokePath(Command):
    # color: tuple[int, int, int] # (r, g, b)
    path: list[tuple[int, int]]  # (x, y)
    pigment: float # 1 = pure color, 0 = white
    brushDiameter: int = 2
    background: bool = False
    # all dimensions (if not specified otherwise) are pixels

    def to_json(self):
        return json.dumps({
            "type": self.get_type(),
            "pigment": round(float(self.pigment), 4),
            "path": self.path,
            "brushDiameter": int(self.brushDiameter),
            "background": bool(self.background),
        })

    def load_from_json(data: dict) -> object:
        pigment = data.get("pigment", 1)
        return StrokePath(
            path = data["path"],
            pigment = pigment,
            brushDiameter=int(data.get("brushDiameter", 2)),
            background=bool(data.get("background", False)),
        )

@dataclass
class LoadBrush(Command):
    color: tuple[int, int, int]
    pigment: float
    deep_clean: bool

    def to_json(self):
        return json.dumps({
            "type": self.get_type(),
            "color": self.color,
            "pigment": round(float(self.pigment), 4),
            "deep_clean": self.deep_clean,
        })

    def load_from_json(data: dict) -> object:
        return LoadBrush(
            color = data["color"],
            pigment = data["pigment"],
            deep_clean = data["deep_clean"],
            # brushDiameter=
        )