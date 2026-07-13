# Datatypes API

Core data structures for representing painting operations and robot calibration.

## Overview

The datatypes module provides the fundamental structures for working with paint robot operations:

- **StrokeSequence** - Collection of strokes to be painted
- **StrokePath** - Individual paint stroke definition
- **RobotCalibration** - Robot hardware calibration parameters
- **ColorPalette** - Color management and palette

## Quick Reference

| Class | Purpose |
|-------|---------|
| `StrokeSequence` | Manages a collection of strokes with serialization |
| `StrokePath` | Represents a single paint stroke |
| `RobotCalibration` | Stores calibration points and canvas dimensions |
| `ColorPalette` | Manages painting colors |

## Common Usage Pattern

```python
from paintbot.datatypes.strokes import StrokeSequence, StrokePath

# Create a sequence
sequence = StrokeSequence(image_size=(800, 600))

# Add strokes
stroke = StrokePath(
    color=(255, 0, 0),  # Red
    path=[(0, 0), (100, 100), (200, 50)],
    brushDiameter=2
)
sequence.strokes.append(stroke)

# Save and load
sequence.save_to_json("output.json")
loaded = StrokeSequence.load_from_json("output.json")

# Visualize
sequence.visualize()
```

## See Also

- [StrokeSequence](strokesequence.md) - Detailed documentation
- [StrokePath](strokepath.md) - Detailed documentation
- [RobotCalibration](calibration.md) - Detailed documentation
