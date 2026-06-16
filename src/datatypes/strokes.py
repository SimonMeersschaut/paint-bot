from dataclasses import dataclass
import os
import json


class StrokeSequence:
    def __init__(self, image_size:tuple[int, int]):
        self.strokes = []
        self.image_size = image_size
        self.unit = "mm"
    
    def visualize(self):
        """Display the visualization of the stroke sequence.
        
        Returns the final rendered image with all strokes painted.
        """
        from paintbot.visualisation import visualize_stroke_sequence
        return visualize_stroke_sequence(self)
    
    def animate(self):
        """Create an animation video of the stroke sequence.
        
        Creates a video file showing strokes being painted in sequence.
        """
        from paintbot.visualisation import animate_stroke_sequence
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        os.remove("tmp/animation.mp4")
        animate_stroke_sequence(self)
        try:
            os.startfile("tmp/animation.mp4")
        except (AttributeError, FileNotFoundError):
            pass  # os.startfile is Windows-specific
    
    def save_to_json(self, filepath: str):
        """Streams the StrokeSequence to a JSON file to prevent high memory usage."""
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write opening structure and metadata
            f.write("{\n")
            f.write(f'  "image_size": [{self.image_size[0]}, {self.image_size[1]}],\n')
            f.write(f'  "dimension_name": "{self.unit}",\n')
            f.write('  "strokes": [\n')
            
            # Stream out individual strokes
            num_strokes = len(self.strokes)
            for idx, stroke in enumerate(self.strokes):
                stroke_dict = {
                    "color": stroke.color,
                    "brushWidth": stroke.brushWidth,
                    "path": stroke.path
                }
                
                # Manual formatting/indentation to keep the file structure valid
                stroke_json = json.dumps(stroke_dict)
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
        
        for s_data in data.get("strokes", []):
            stroke = StrokePath(
                color=tuple(s_data["color"]),
                path=[tuple(pt) for pt in s_data["path"]],
                brushWidth=s_data.get("brushWidth", 2)
            )
            sequence.strokes.append(stroke)
            
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
        for stroke in self.strokes:
            # 1. Scale coordinates (x, y)
            scaled_path = []
            for x, y in stroke.path:
                # Keeping as float or round() depending on precision needs. 
                # Since coordinates default to pixels, round() is generally safest.
                scaled_x = round(x * scale_x)
                scaled_y = round(y * scale_y)
                scaled_path.append((scaled_x, scaled_y))
            
            stroke.path = scaled_path

            # 2. Scale the brush stroke thickness (ensuring it never drops below 1 pixel)
            stroke.brushWidth = max(1, round(stroke.brushWidth * scale_brush))

        # Update the canvas bounds to complete the resize operation
        self.image_size = dimensions

@dataclass
class StrokePath:
    color: tuple[int, int, int] # (r, g, b)
    path: list[tuple[int, int]]  # (x, y)
    brushWidth: int = 2
    # all dimensions (if not specified otherwise) are pixels
