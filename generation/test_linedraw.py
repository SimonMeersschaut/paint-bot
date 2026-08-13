import json
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))

from lines import Line
from linedraw import makesvg, measure_stroke_contour_strength
from pigment import normalize_stroke_distribution


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
