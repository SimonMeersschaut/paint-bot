# StrokePath

Represents a single paint stroke with color, path, and brush width.

## Overview

`StrokePath` is a dataclass that defines an individual stroke to be painted. Each stroke consists of:

- A color (RGB tuple)
- A path (list of x,y coordinates)
- A brush width (thickness)

## Definition

```python
from dataclasses import dataclass

@dataclass
class StrokePath:
    color: tuple[int, int, int]  # (r, g, b)
    path: list[tuple[int, int]]   # [(x, y), ...]
    brushWidth: int = 2
```

## Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `color` | `tuple[int, int, int]` | Required | RGB color values (0-255 each) |
| `path` | `list[tuple[int, int]]` | Required | List of coordinate points in pixels |
| `brushWidth` | `int` | 2 | Stroke thickness in pixels |

## Creating a Stroke

### Basic Stroke

```python
from paintbot.datatypes.strokes import StrokePath

# Simple red line
stroke = StrokePath(
    color=(255, 0, 0),
    path=[(0, 0), (100, 0)]
)
```

### With Custom Brush Width

```python
# Thick blue line
stroke = StrokePath(
    color=(0, 0, 255),
    path=[(10, 10), (50, 50), (100, 10)],
    brushWidth=5
)
```

### Complex Path

```python
# Green wavy path
stroke = StrokePath(
    color=(0, 255, 0),
    path=[
        (0, 100), (25, 80), (50, 100),
        (75, 80), (100, 100), (125, 80),
        (150, 100)
    ],
    brushWidth=3
)
```

## Color Reference

### Common Colors

| Color | RGB | Hex |
|-------|-----|-----|
| Red | `(255, 0, 0)` | `#FF0000` |
| Green | `(0, 255, 0)` | `#00FF00` |
| Blue | `(0, 0, 255)` | `#0000FF` |
| Black | `(0, 0, 0)` | `#000000` |
| White | `(255, 255, 255)` | `#FFFFFF` |
| Yellow | `(255, 255, 0)` | `#FFFF00` |
| Cyan | `(0, 255, 255)` | `#00FFFF` |
| Magenta | `(255, 0, 255)` | `#FF00FF` |

### Grayscale

```python
light_gray = (200, 200, 200)
dark_gray = (50, 50, 50)
```

## Path Design

### Straight Line

```python
stroke = StrokePath(
    color=(0, 0, 0),
    path=[(0, 0), (100, 100)]  # Diagonal line from (0,0) to (100,100)
)
```

### Curved Path (Multiple Points)

```python
# Approximates a curve with line segments
stroke = StrokePath(
    color=(100, 150, 200),
    path=[
        (0, 50),
        (25, 20),
        (50, 15),
        (75, 25),
        (100, 50)
    ]
)
```

### Closed Shape

```python
# Square
stroke = StrokePath(
    color=(255, 0, 0),
    path=[
        (0, 0),
        (100, 0),
        (100, 100),
        (0, 100),
        (0, 0)  # Close the shape
    ],
    brushWidth=2
)
```

## Usage in StrokeSequence

```python
from paintbot.datatypes.strokes import StrokeSequence, StrokePath

# Create sequence
sequence = StrokeSequence(image_size=(800, 600))

# Create and add strokes
for i in range(5):
    stroke = StrokePath(
        color=(i * 50, 100, 200 - i * 40),
        path=[(0, i * 100), (800, i * 100)],
        brushWidth=2
    )
    sequence.strokes.append(stroke)

# Visualize
sequence.visualize()
```

## Brush Width Guidelines

| Width | Use Case |
|-------|----------|
| 1-2 | Fine details, thin lines |
| 2-4 | Normal brush strokes |
| 5-10 | Bold lines, thick strokes |
| 10+ | Large fills, broad strokes |

## Coordinate System

- **Origin (0, 0)**: Top-left corner
- **X-axis**: Increases left to right
- **Y-axis**: Increases top to bottom
- **Units**: Pixels

```
(0,0)          (width, 0)
  +----------------+
  |                |
  |                | height
  |                |
  +----------------+
(0,height)  (width, height)
```

## Accessing Stroke Data

```python
stroke = StrokePath(
    color=(255, 0, 0),
    path=[(0, 0), (100, 100)],
    brushWidth=3
)

# Access attributes
red, green, blue = stroke.color
print(f"Color: R={red}, G={green}, B={blue}")

start_x, start_y = stroke.path[0]
print(f"Start: ({start_x}, {start_y})")

print(f"Thickness: {stroke.brushWidth} pixels")
print(f"Path length: {len(stroke.path)} points")
```

## Notes

- All coordinates are in **pixels**
- Color values must be integers 0-255
- Path must contain at least 2 points for a valid stroke
- Brush width must be at least 1 pixel
- Paths are modified in-place (no immutability)

## See Also

- [StrokeSequence](strokesequence.md) - Collection of strokes
- [Guides: Stroke Generation](../guides/stroke-generation.md) - How strokes are generated
