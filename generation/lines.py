from dataclasses import dataclass, field


@dataclass
class Line:
    positions: list[tuple[float, float]]
    opacity: float = 0.0
    darkness: float = 0.0
    contour_strength: float = 0.0
    pigment: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_string(self, min_x, min_y, pad):
        return ",".join([
            str((p[0] - min_x + pad) * 0.5) + "," + str((p[1] - min_y + pad) * 0.5)
            for p in self.positions
        ])

    def to_dict(self):
        payload = {
            "points": [list(point) for point in self.positions],
            "opacity": self.opacity,
            "darkness": self.darkness,
            "contour_strength": self.contour_strength,
            "pigment": round(self.pigment, 3),
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    @classmethod
    def from_points(cls, points, **kwargs):
        return cls(positions=[tuple(point) for point in points], **kwargs)

    def copy_with_points(self, points):
        return Line(
            positions=[tuple(point) for point in points],
            opacity=self.opacity,
            darkness=self.darkness,
            contour_strength=self.contour_strength,
            pigment=self.pigment,
            metadata=dict(self.metadata),
        )