"""Tests for the MotionController."""

from robot.helpers.coordinate import Coordinate
from robot.helpers.robot_mqtt import RobotMQTT
from robot.motion import MotionController


class DummyMqttClient:
    def publish(self, *a, **kw):
        # This method is intentionally left empty as it is a dummy
        # implementation for testing purposes and does not require any
        # functionality.
        pass

    def subscribe(self, *a, **kw):
        # This method is intentionally left empty as it is a dummy
        # implementation for testing purposes and does not require any
        # functionality.
        pass


def test_motion_controller_instantiation():
    """Instantiate MotionController."""
    coordinate = Coordinate()
    robot_mqtt = RobotMQTT(
        robot_id=1, mqtt_client=DummyMqttClient(), coordinate=coordinate
    )
    controller = MotionController(coordinate=coordinate, robot_mqtt=robot_mqtt)
    assert isinstance(controller, MotionController)


def test_robot_base_run_and_shutdown():
    """Test Robot base class run and shutdown."""
    import threading
    from unittest.mock import patch

    from robot.robot_base import Robot

    class TestRobot(Robot):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.loop_called = 0

        def setup(self):
            self.setup_called = True

        def loop(self):
            self.loop_called += 1
            # Stop after first loop for test
            self._stop_event.set()

    robot = TestRobot(robot_id="testbot", loop_hz=100)
    with patch.object(robot.mqtt_client, "connect", return_value=None):
        t = threading.Thread(target=robot.run)
        t.start()
        t.join(timeout=2)
    assert hasattr(robot, "setup_called")
    assert robot.loop_called >= 1
