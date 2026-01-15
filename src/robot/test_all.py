"""Lightweight integration smoke tests for the robot package.

This script is intended to be runnable directly and avoids network
dependencies by injecting a fake MQTT client and a minimal robot stub.

Run from the repository root with:

  python -m unittest robot.test_all -v

"""
from __future__ import annotations

import os
import sys
import unittest

# Ensure package root (src) is on sys.path when running the file directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from robot.types.rgb_color_type import RGBColorType
from robot.types.proximity_reading_type import ProximityReadingType
from robot.helpers.coordinate import Coordinate
from robot.helpers.motion_controller import MotionController
from robot.indicators.neopixel import NeoPixel
from robot.sensors.distance import DistanceSensor
from robot.sensors.color import ColorSensor
from robot.sensors.proximity import ProximitySensor
from robot.mqtt.mqtt_msg import MqttMsg


class FakeMqttClient:
    def __init__(self):
        self.publishes = []
        self.subscribes = []

    def publish(self, topic: str, body: str, qos: int = 0, retain: bool = False):
        self.publishes.append((topic, body, qos, retain))

    def subscribe(self, topic: str):
        self.subscribes.append(topic)


class FakeRobot:
    def __init__(self, _id: int = 1):
        self._id = _id

    def get_id(self) -> int:
        return self._id

    def delay(self, ms: int) -> None:
        # no-op for tests
        return

    def handle_subscribe_queue(self) -> None:
        # no-op for tests
        return

    def start(self) -> None:
        self._state = "started"

    def stop(self) -> None:
        self._state = "stopped"

    def reset(self) -> None:
        self._state = "reset"


class RobotPackageSmokeTests(unittest.TestCase):
    def test_rgb_color_type_basic(self):
        c = RGBColorType(10, 20, 30)
        self.assertEqual(c.get_color(), [10, 20, 30])

        c2 = RGBColorType("#0A141E")
        self.assertEqual(c2.get_color(), [10, 20, 30])

        c3 = RGBColorType("10 20 30")
        self.assertEqual(str(c3), "R:10, G:20, B:30")

        self.assertTrue(c.compare_to(c3))

        with self.assertRaises(Exception):
            RGBColorType("#BAD")

    def test_proximity_reading_type(self):
        angles = [0, 1]
        # distances: 5 and 10, colors: blue and red
        s = "5 10 #0000FF #FF0000"
        pr = ProximityReadingType(angles, s)
        self.assertEqual(pr.distances(), [5, 10])
        cols = pr.colors()
        self.assertEqual(cols[0].get_color(), [0, 0, 255])
        self.assertEqual(cols[1].get_color(), [255, 0, 0])

    def test_coordinate_publish_and_setters(self):
        fake = FakeMqttClient()
        coord = Coordinate(1, 1.5, 2.5, 90.0, fake)
        self.assertAlmostEqual(coord.get_x(), 1.5)
        coord.set_coordinate_heading(3.3, 4.4, -45)
        coord.publish_coordinate()
        self.assertTrue(any(p[0] == "localization/update" for p in fake.publishes))

    def test_motion_controller_stub_coord_and_moves(self):
        mc = MotionController(None)
        # Should not raise when moving with zeros
        mc.move(0, 0, 0)
        mc.rotate(0, 0)

    def test_neopixel_and_indicator_publish(self):
        fake = FakeMqttClient()
        robot = FakeRobot(2)
        np = NeoPixel(robot, fake)
        # initialization should have called change_color -> publish present
        self.assertTrue(any(p[0] == "output/neopixel" for p in fake.publishes))
        # change color explicitly
        fake.publishes.clear()
        np.change_color(1, 2, 3)
        self.assertTrue(any(p[0] == "output/neopixel" for p in fake.publishes))

    def test_sensors_handle_subscription(self):
        fake = FakeMqttClient()
        robot = FakeRobot(3)

        d = DistanceSensor(robot, fake)
        # Simulate incoming distance message
        topic = d._topics_sub.get("DISTANCE_IN")
        m = MqttMsg(topic, "42")
        d.handle_subscription(robot, m)
        self.assertEqual(d._dist_value, 42)

        c = ColorSensor(robot, fake)
        topic_c = c._topics_sub.get("COLOR_IN")
        mc = MqttMsg(topic_c, "12 34 56")
        c.handle_subscription(robot, mc)
        self.assertEqual(c.color.get_color(), [12, 34, 56])

        p = ProximitySensor(robot, fake, angles=[0])
        topic_p = p._topics_sub.get("PROXIMITY_IN")
        pm = MqttMsg(topic_p, "5 #00FF00")
        p.handle_subscription(robot, pm)
        # After handling, internal _proximity should be set (or printed on error)
        self.assertIsNotNone(p._proximity)


if __name__ == "__main__":
    unittest.main()
