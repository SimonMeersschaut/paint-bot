from dataclasses import dataclass


@dataclass
class Line:
    positions: list[tuple[float, float]]
    pigment: float = 0.0
    darkness: float = 0.0
    contour_strength: float = 0.0
    background: bool = False
    brushDiameter: int = 2

    def to_string(self, min_x, min_y, pad):
        return ",".join([
            str((p[0] - min_x + pad) * 0.5) + "," + str((p[1] - min_y + pad) * 0.5)
            for p in self.positions
        ])

    def to_dict(self):
        payload = {
            "type": "StrokePath",
            "points": [list(point) for point in self.positions],
            "path": [list(point) for point in self.positions],
            "pigment": round(self.pigment, 3),
            "darkness": round(float(self.darkness), 3),
            "contour_strength": round(float(self.contour_strength), 3),
            "background": bool(self.background),
            "brushDiameter": int(self.brushDiameter),
        }
        return payload

    @classmethod
    def from_points(cls, points, **kwargs):
        return cls(positions=[tuple(point) for point in points], **kwargs)

    def copy_with_points(self, points):
        return Line(
            positions=[tuple(point) for point in points],
            pigment=self.pigment,
            darkness=self.darkness,
            contour_strength=self.contour_strength,
            background=self.background,
            brushDiameter=self.brushDiameter,
        )