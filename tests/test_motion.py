"""Tests for the MotionController."""

from robot.motion import MotionController


def test_motion_controller_instantiation():
    """Instantiate MotionController."""
    controller = MotionController()
    assert isinstance(controller, MotionController)
