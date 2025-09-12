---
title: Usage
---

# Usage Guide

This guide shows how to configure MQTT, build a `VirtualRobot`, use motion control, read sensors, send communications, and control indicators.

## Configure MQTT

```python
from robot import MQTTSettings

MQTTSettings.server = "localhost"
MQTTSettings.port = 1883
MQTTSettings.user_name = ""
MQTTSettings.password = ""
MQTTSettings.channel = "v1"
```

## Subclass `VirtualRobot`

```python
from robot import VirtualRobot
from robot.interfaces import RobotState

class MyRobot(VirtualRobot):
    def loop(self):
        if self.state == RobotState.RUN:
            # read sensors, move, and communicate here
            self.delay(1000)

robot = MyRobot(1, 0, 0, 90)
robot.start()
robot.run()
```

## Motion Control

Use `MotionController` directly or through a `Robot` via `self.motion`.

```python
from robot import MotionController

motion = MotionController()  # standalone with a stub coordinate
motion.move(150, 150, duration=1000)   # forward 1 second
motion.rotate_degree(120, 90)          # rotate 90 degrees
```

In a robot loop:

```python
self.motion.move(180, 180, duration=500)
self.motion.rotate_degree(160, -45)
```

Configure geometry and speeds via `robot.configs.robot_settings.RobotSettings`.

## Sensors

Sensors are initialized in `Robot.setup()` and available on the robot instance.

Distance:

```python
dist_cm = self.dist_sensor.get_distance()
```

Color:

```python
rgb = self.color_sensor.get_color()  # RGBColorType
print(rgb.get_r(), rgb.get_g(), rgb.get_b())
```

Proximity (multi-angle):

```python
# Optionally configure angles first
self.proximity_sensor.set_angles([0, 45, 90, 135, 180])
reading = self.proximity_sensor.get_proximity()
print(reading.distances())
for c in reading.colors():
    print(c.to_string_color())
```

## Communications

Simple broadcast-like messages:

```python
self.simple_comm.send_message("hello swarm")
self.simple_comm.send_message_with_distance("tag", distance=10)
```

Directed messages (to controller routing topic):

```python
self.directed_comm.send_message("to leader")
```

Override `communication_interrupt(self, msg: str)` in your robot to handle inbound messages.

## Indicators (NeoPixel)

```python
self.neo_pixel.change_color(0, 128, 255)
```

## Extensibility Guidelines

- Subclass `VirtualRobot` to add behaviors; implement `loop()` and optionally `sensor_interrupt`/`communication_interrupt`.
- New sensors/indicators: follow `robot.sensors.abstract_sensor` / `robot.indicators.abstract_indicator`. Subscribe to topics in `__init__`, implement `handle_subscription`, and publish using `RobotMqttClient`.
- MQTT is namespaced by `MQTTSettings.channel` (e.g., `v1/robot/create`), mirroring the original Java design.

