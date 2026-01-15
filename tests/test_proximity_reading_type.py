from __future__ import annotations

import pytest

from robot.exception import ProximityException
from robot.types.proximity_reading_type import ProximityReadingType


def test_parses_distances_and_colors():
    reading = ProximityReadingType([0, 30], "10 20 #FF0000 #00FF00")

    assert reading.distances() == [10, 20]
    colors = reading.colors()
    assert colors[0].get_color() == [255, 0, 0]
    assert colors[1].get_color() == [0, 255, 0]


def test_infinity_maps_to_negative_one():
    reading = ProximityReadingType([0], "Infinity #010203")

    assert reading.distances() == [-1]
    assert reading.colors()[0].get_color() == [1, 2, 3]


def test_length_mismatch_raises():
    with pytest.raises(ProximityException):
        ProximityReadingType([0, 30], "10 #FF0000")
