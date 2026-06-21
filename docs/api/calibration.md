# RobotCalibration

Stores and manages robot hardware calibration parameters.

## Overview

`RobotCalibration` is a dataclass that stores calibration points for mapping pixel coordinates to physical robot positions. It includes:

- Canvas corner positions in robot coordinates
- Water reservoir position
- Color palette management
- Canvas size calculation

## Definition

```python
from dataclasses import dataclass

@dataclass
class RobotCalibration:
    top_left: tuple[int, int, int]
    top_right: tuple[int, int, int]
    bottom_left: tuple[int, int, int]
    bottom_right: tuple[int, int, int]
    water_reservoir: tuple[int, int, int]
    color_palette: ColorPalette = None
```

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `top_left` | `tuple[int, int, int]` | Calibration point at canvas top-left corner (x, y, z) |
| `top_right` | `tuple[int, int, int]` | Calibration point at canvas top-right corner (x, y, z) |
| `bottom_left` | `tuple[int, int, int]` | Calibration point at canvas bottom-left corner (x, y, z) |
| `bottom_right` | `tuple[int, int, int]` | Calibration point at canvas bottom-right corner (x, y, z) |
| `water_reservoir` | `tuple[int, int, int]` | Position of water reservoir for brush cleaning (x, y, z) |
| `color_palette` | `ColorPalette` | Attached color palette for painting |

## Creating Calibration

### Basic Calibration

```python
from paintbot.datatypes.robot import RobotCalibration

calibration = RobotCalibration(
    top_left=(100, 100, 0),
    top_right=(900, 100, 0),
    bottom_left=(100, 600, 0),
    bottom_right=(900, 600, 0),
    water_reservoir=(1000, 700, 50)
)
```

### Understanding Calibration Points

Calibration points are the physical robot coordinates where the brush touches the canvas corners:

```
top_left (100,100)         top_right (900,100)
         +------------------------+
         |                        |
         |    Canvas Area         |
         |   (800 x 500 pixels)   |
         |                        |
         +------------------------+
bottom_left (100,600)  bottom_right (900,600)

Water Reservoir: (1000, 700)
```

## Methods

### `get_canvas_size()`

Calculate the physical canvas dimensions in robot coordinates.

```python
width, height = calibration.get_canvas_size()
```

**Returns:**
- `tuple[int, int]`: Canvas size as (width, height) in robot units

**Example:**
```python
calibration = RobotCalibration(
    top_left=(0, 0, 0),
    top_right=(100, 0, 0),
    bottom_left=(0, 80, 0),
    bottom_right=(100, 80, 0),
    water_reservoir=(110, 90, 50)
)

width, height = calibration.get_canvas_size()
print(f"Canvas size: {width}mm x {height}mm")  # 100mm x 80mm
```

### `dump(filepath)`

Save calibration data to a JSON file.

```python
calibration.dump("calibration.json")
```

**Parameters:**
- `filepath` (str): Path to save the JSON file

**JSON Format:**
```json
{
    "top_left": [100, 100, 0],
    "top_right": [900, 100, 0],
    "bottom_left": [100, 600, 0],
    "bottom_right": [900, 600, 0],
    "water_reservoir": [1000, 700, 50],
    "color_palette": [
        {"position": 0, "color": [255, 0, 0]},
        {"position": 1, "color": [0, 255, 0]}
    ]
}
```

### `load(filepath)` (classmethod)

Load calibration data from a JSON file.

```python
calibration = RobotCalibration.load("calibration.json")
```

**Parameters:**
- `filepath` (str): Path to the JSON file

**Returns:**
- `RobotCalibration` instance reconstructed from file

**Example:**
```python
calibration = RobotCalibration.load("my_robot.json")
width, height = calibration.get_canvas_size()
print(f"Loaded calibration for {width}x{height} canvas")
```

## ColorPalette Management

### Accessing the Color Palette

```python
palette = calibration.color_palette
```

### Adding Colors

```python
palette.add_color(position=0, color=(255, 0, 0))      # Red
palette.add_color(position=1, color=(0, 255, 0))      # Green
palette.add_color(position=2, color=(0, 0, 255))      # Blue
```

### Saving with Palette

```python
# Colors are automatically included when saving
calibration.dump("calibration_with_colors.json")

# Load includes palette
loaded = RobotCalibration.load("calibration_with_colors.json")
print(loaded.color_palette.dump())
```

## Usage Example

```python
from paintbot.datatypes.robot import RobotCalibration

# Create calibration for a 200x200mm canvas
calibration = RobotCalibration(
    top_left=(0, 0, 0),
    top_right=(200, 0, 0),
    bottom_left=(0, 200, 0),
    bottom_right=(200, 200, 0),
    water_reservoir=(250, 250, 50)
)

# Check canvas size
canvas_w, canvas_h = calibration.get_canvas_size()
print(f"Canvas: {canvas_w}x{canvas_h}mm")  # 200x200mm

# Add colors to palette
calibration.color_palette.add_color(0, (255, 0, 0))
calibration.color_palette.add_color(1, (0, 255, 0))
calibration.color_palette.add_color(2, (0, 0, 255))

# Save for robot
calibration.dump("robot_calibration.json")

# Later, load the same calibration
loaded = RobotCalibration.load("robot_calibration.json")
```

## Coordinate System

Calibration uses a **3D coordinate system** (X, Y, Z):

- **X-axis**: Horizontal movement (left-right)
- **Y-axis**: Vertical movement (up-down)
- **Z-axis**: Height/depth (brush up-down, typically 0 for canvas surface)

### Common Z Values

| Z Value | Meaning |
|---------|---------|
| 0 | Brush on canvas (painting) |
| 50+ | Brush raised (moving without painting) |

## Calibration Workflow

```python
# 1. Create initial calibration
cal = RobotCalibration(
    top_left=(0, 0, 0),
    top_right=(500, 0, 0),
    bottom_left=(0, 500, 0),
    bottom_right=(500, 500, 0),
    water_reservoir=(600, 600, 50)
)

# 2. Set up color palette
cal.color_palette.add_color(0, (0, 0, 0))      # Black
cal.color_palette.add_color(1, (128, 128, 128)) # Gray
cal.color_palette.add_color(2, (255, 255, 255)) # White

# 3. Save to file
cal.dump("robot_setup.json")

# 4. Use in robot operations
loaded = RobotCalibration.load("robot_setup.json")
print(f"Ready to paint on {loaded.get_canvas_size()} canvas")
```

## Notes

- Coordinates are typically in **millimeters** for physical robots
- Z-axis usually represents brush height or nozzle position
- Canvas size is calculated from corner positions (not independent input)
- Color palette is automatically initialized on instantiation
- Use JSON files for persistence across sessions

## Related Datatypes

- [ColorPalette](#colorpalette) - Color management
- [StrokeSequence](strokesequence.md) - Strokes to be painted
- [Guides: Calibration](../guides/calibration.md) - How to calibrate

## ColorPalette Reference

### Class: ColorPalette

Manages a collection of painting colors.

```python
from paintbot.datatypes.robot import ColorPalette

palette = ColorPalette()
palette.add_color(0, (255, 0, 0))
colors = palette.dump()
```

### Methods

#### `add_color(position, color)`

Add a color to the palette at a specific position.

```python
palette.add_color(position=0, color=(255, 0, 0))  # Red at position 0
```

#### `dump()`

Get all colors as a list of dicts.

```python
colors = palette.dump()
# Returns: [{"position": 0, "color": [255, 0, 0]}, ...]
```

#### `load(data)`

Populate palette from a list of position/color dicts.

```python
data = [{"position": 0, "color": [255, 0, 0]}]
palette.load(data)
```

