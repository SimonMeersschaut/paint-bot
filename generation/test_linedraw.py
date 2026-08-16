import json
import os
import sys

import pytest
from PIL import Image
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "execution"))

from lines import Line
from datatypes.strokes import StrokeSequence, StrokePath
from robot import execute_stroke
from linedraw import makesvg, measure_stroke_contour_strength
from pigment import normalize_stroke_distribution
from stroke_ordering import sort_strokes
from datatypes.strokes import LoadBrush


def test_makesvg_uses_explicit_svg_viewport():
    lines = [
        [(0, 0), (100, 0), (100, 80)],
        [(0, 80), (50, 80)],
    ]

    svg = makesvg(lines)

    assert 'viewBox=' in svg
    assert 'width=' in svg
    assert 'height=' in svg


def test_line_tracks_pigment_metadata_and_json_serializes_it():
    stroke = Line(
        positions=[(0, 0), (10, 10)],
        darkness=0.75,
        contour_strength=0.6,
        pigment=0.68,
    )

    payload = stroke.to_dict()

    assert payload['points'] == [[0, 0], [10, 10]]
    assert payload['darkness'] == 0.75
    assert payload['contour_strength'] == 0.6
    assert payload['pigment'] == 0.68

    assert json.loads(json.dumps(payload)) == payload


def test_distribution_spreads_darkness_and_contour_values_across_zero_to_one():
    strokes = [
        Line(positions=[(0, 0), (1, 0)], darkness=0.05, contour_strength=0.10),
        Line(positions=[(0, 1), (1, 1)], darkness=0.25, contour_strength=0.30),
        Line(positions=[(0, 2), (1, 2)], darkness=0.55, contour_strength=0.60),
        Line(positions=[(0, 3), (1, 3)], darkness=0.85, contour_strength=0.90),
    ]

    normalize_stroke_distribution(strokes)

    darkness_values = [stroke.darkness for stroke in strokes]
    contour_values = [stroke.contour_strength for stroke in strokes]

    assert min(darkness_values) == pytest.approx(0.0, abs=1e-9)
    assert max(darkness_values) == pytest.approx(1.0, abs=1e-9)
    assert min(contour_values) == pytest.approx(0.0, abs=1e-9)
    assert max(contour_values) == pytest.approx(1.0, abs=1e-9)
    assert all(0.0 <= value <= 1.0 for value in darkness_values + contour_values)


def test_measure_stroke_contour_strength_uses_sobel_edge_energy():
    image = Image.new('L', (100, 100), 255)
    for y in range(100):
        image.putpixel((50, y), 0)

    stroke = Line(positions=[(49, 30), (49, 31), (49, 69)])
    value = measure_stroke_contour_strength(image, stroke)

    assert 0.0 <= value <= 1.0
    assert value > 0.5


def test_execute_stroke_mirrors_canvas_coordinates_only_just_before_moving():
    sequence = StrokeSequence(image_size=(10, 20))
    sequence.strokes = [
        StrokePath(path=[(0, 0), (1, 0), (9, 0)], pigment=1.0, brushDiameter=2)
    ]

    class FakePrinter:
        def __init__(self):
            self.moves = []

        def move_to(self, **kwargs):
            self.moves.append(kwargs.copy())

    robot_calibration = SimpleNamespace(
        bottom_left=(100, 200, 50),
        canvas_up_height=90,
        get_canvas_size=lambda: (10, 20),
    )
    printer = FakePrinter()

    execute_stroke(printer, robot_calibration, sequence, 0)

    assert sequence.strokes[0].path == [(0, 0), (1, 0), (9, 0)]
    assert printer.moves[3]["x"] == pytest.approx(109.0)
    assert printer.moves[3]["y"] == pytest.approx(200.0)
    assert printer.moves[5]["x"] == pytest.approx(100.0)


def test_sort_strokes_batches_by_pigment_and_inserts_load_brush_commands():
    strokes = [
        Line(positions=[(0, 0), (1, 0)], pigment=0.05),
        Line(positions=[(0, 1), (1, 1)], pigment=0.12),
        Line(positions=[(0, 2), (1, 2)], pigment=0.19),
        Line(positions=[(0, 3), (1, 3)], pigment=0.25),
        Line(positions=[(0, 4), (1, 4)], pigment=0.31),
        Line(positions=[(0, 5), (1, 5)], pigment=0.38),
        Line(positions=[(0, 6), (1, 6)], pigment=0.46),
        Line(positions=[(0, 7), (1, 7)], pigment=0.57),
        Line(positions=[(0, 8), (1, 8)], pigment=0.64),
        Line(positions=[(0, 9), (1, 9)], pigment=0.72),
        Line(positions=[(0, 10), (1, 10)], pigment=0.80),
        Line(positions=[(0, 11), (1, 11)], pigment=0.89),
    ]

    ordered = sort_strokes(strokes)

    load_indices = [i for i, command in enumerate(ordered) if isinstance(command, LoadBrush)]
    assert load_indices == [0, 11]

    first_batch = ordered[1:11]
    second_batch = ordered[12:]
    assert len(first_batch) == 10
    assert len(second_batch) == 2
    assert all(getattr(stroke, 'pigment', 0.0) <= max(getattr(s, 'pigment', 0.0) for s in first_batch) for stroke in first_batch)
    assert ordered[0].pigment == pytest.approx(sum(stroke.pigment for stroke in first_batch) / len(first_batch))
    assert ordered[11].pigment == pytest.approx(sum(stroke.pigment for stroke in second_batch) / len(second_batch))
