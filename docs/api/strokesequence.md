# StrokeSequence

A collection of paint strokes that can be visualized, animated, and serialized to JSON.

## Overview

`StrokeSequence` manages a sequence of strokes to be painted on a canvas. It handles:

- Storing and managing multiple `StrokePath` objects
- Canvas size and unit tracking
- Visualization and animation of strokes
- JSON serialization for persistence

## Constructor

```python
from paintbot.datatypes.strokes import StrokeSequence

sequence = StrokeSequence(image_size=(width, height))
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_size` | `tuple[int, int]` | Canvas dimensions as (width, height) in pixels |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `strokes` | `list[StrokePath]` | List of strokes in the sequence |
| `image_size` | `tuple[int, int]` | Canvas dimensions (width, height) |
| `unit` | `str` | Unit of measurement (default: "mm") |

## Methods

### `visualize()`

Display the rendered result of the stroke sequence.

```python
result = sequence.visualize()
```

**Returns:**
- Final rendered image with all strokes painted

**Example:**
```python
sequence = StrokeSequence((800, 600))
# ... add strokes ...
image = sequence.visualize()
```

### `animate()`

Create an animation video showing strokes being painted in sequence.

```python
sequence.animate()
```

**Behavior:**
- Creates a video file at `tmp/animation.mp4`
- Automatically plays on Windows (via `os.startfile`)
- Shows strokes being applied in order

**Example:**
```python
sequence.animate()  # Creates and plays animation.mp4
```

### `save_to_json(filepath)`

Serialize the stroke sequence to a JSON file.

Streams data to prevent high memory usage with large sequences.

```python
sequence.save_to_json("output/strokes.json")
```

**Parameters:**
- `filepath` (str): Path to save the JSON file

**JSON Structure:**
```json
{
  "image_size": [800, 600],
  "dimension_name": "mm",
  "strokes": [
    {
      "color": [255, 0, 0],
      "brushWidth": 2,
      "path": [[0, 0], [100, 100], [200, 50]]
    }
  ]
}
```

### `load_from_json(filepath)` (classmethod)

Load a stroke sequence from a JSON file.

```python
sequence = StrokeSequence.load_from_json("output/strokes.json")
```

**Parameters:**
- `filepath` (str): Path to the JSON file

**Returns:**
- `StrokeSequence` instance reconstructed from the file

**Example:**
```python
loaded = StrokeSequence.load_from_json("saved_strokes.json")
print(f"Loaded {len(loaded.strokes)} strokes")
print(f"Canvas size: {loaded.image_size}")
```

### `resize_to(dimensions)`

Resize the canvas and scale all strokes proportionally.

```python
sequence.resize_to((1920, 1440))
```

**Parameters:**
- `dimensions` (tuple[int, int]): New canvas size as (width, height)

**Behavior:**
- Scales all stroke coordinates proportionally
- Adjusts brush widths based on scale factors
- Ensures brush width never drops below 1 pixel
- Updates `image_size` attribute

**Example:**
```python
# Original canvas: 800x600
sequence = StrokeSequence((800, 600))
# ... add strokes ...

# Upscale to 4K
sequence.resize_to((1920, 1440))
```

## Usage Example

```python
from paintbot.datatypes.strokes import StrokeSequence, StrokePath

# Create sequence
sequence = StrokeSequence(image_size=(800, 600))

# Add strokes
red_stroke = StrokePath(
    color=(255, 0, 0),
    path=[(50, 50), (150, 50), (150, 150), (50, 150)],
    brushWidth=3
)
blue_stroke = StrokePath(
    color=(0, 0, 255),
    path=[(200, 200), (300, 300)],
    brushWidth=2
)

sequence.strokes.append(red_stroke)
sequence.strokes.append(blue_stroke)

# Visualize
image = sequence.visualize()

# Save for later
sequence.save_to_json("my_painting.json")

# Load and modify
loaded = StrokeSequence.load_from_json("my_painting.json")
loaded.resize_to((1600, 1200))
loaded.save_to_json("my_painting_4x.json")

# Create animation
loaded.animate()
```

## Notes

- Canvas dimensions are always in **pixels**
- Color values are RGB tuples: `(red, green, blue)` with values 0-255
- Paths are lists of coordinate tuples: `[(x1, y1), (x2, y2), ...]`
- Brush width is always in pixels, minimum 1
- Unit field is informational and doesn't affect calculations

## See Also

- [StrokePath](strokepath.md) - Individual stroke structure
- [RobotCalibration](calibration.md) - Robot calibration
