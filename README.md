# Robot Library (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Pera-Swarm/robot-library-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Pera-Swarm/robot-library-python/actions/workflows/ci.yml)
[![Documentation: Publish](https://github.com/Pera-Swarm/robot-library-python/actions/workflows/docs-cd.yml/badge.svg)](https://github.com/Pera-Swarm/robot-library-python/actions/workflows/docs-cd.yml)

A modular Python library for building robot applications. It provides components for motion control, sensors, communications, and indicators over MQTT.

Documentation: the full site is auto-built and deployed to GitHub Pages on pushes to the `dev` branch. Once enabled in the repo settings, it will be available at: `https://pera-swarm.github.io/robot-library-python/`.

## Installation

You can install in a few ways:

- Editable (development) install from a local checkout:

  ```bash
  pip install -e .
  ```

- From source via Git (replace org/repo as appropriate):

This library requires `paho-mqtt` (declared in `pyproject.toml`) and Python 3.8+.

## Quick Start

Create a virtual robot by subclassing `robot.VirtualRobot`, configure MQTT, and start the main loop:

```python
from robot import MQTTSettings, VirtualRobot
from robot.interfaces import RobotState


class MyRobot(VirtualRobot):
    def loop(self):
        if self.state == RobotState.RUN:
            print("running...")
            # do work
            self.delay(1000)


# Configure MQTT broker connection
MQTTSettings.server = "localhost"
MQTTSettings.port = 1883
MQTTSettings.user_name = ""
MQTTSettings.password = ""
MQTTSettings.channel = "v1"

r = MyRobot(1, 0, 0, 90)
r.start()
r.run()  # or run in a separate thread
```

See `examples/my_test_robot.py` for a complete runnable example.

## Core Concepts

- Robot: base lifecycle (`start/stop/reset/delay/loop`) and MQTT subscription handling. See `robot.Robot`.
- VirtualRobot: convenient virtual implementation; subclass and implement `loop`. See `robot.VirtualRobot`.
- Motion: differential drive style controller for movement and rotation. See `robot.MotionController`.
- Sensors: distance, color, and proximity, with non-blocking MQTT updates and blocking request/reply helpers.
- Communication: simple and directed messaging channels to other robots or a controller.
- Indicators: NeoPixel control via MQTT topics.

## Usage Examples

Motion control:

```python
from robot import MotionController

motion = MotionController()  # standalone stub coordinate for quick tests
motion.move(100, 100, duration=1000)   # forward 1s
motion.rotate_degree(120, 90)          # rotate 90 degrees at speed 120
```

Sensors (within a `Robot` subclass after `setup()` has run):

```python
dist = self.dist_sensor.get_distance()
rgb  = self.color_sensor.get_color()          # RGBColorType
prox = self.proximity_sensor.get_proximity()  # ProximityReadingType
```

Communications:

```python
self.simple_comm.send_message("hello swarm")
self.directed_comm.send_message_with_distance("to leader", distance=25)
```

Indicators:

```python
self.neo_pixel.change_color(255, 128, 0)
```

## Extending and Customizing

- New behavior: subclass `VirtualRobot` and implement `loop`. Optionally override `sensor_interrupt` or `communication_interrupt`.
- New sensors/indicators: follow the pattern in `robot.sensors.*` and `robot.indicators.*`, implementing `handle_subscription` and publishing/consuming your desired topics via `RobotMqttClient`.
- Motion tuning: adjust `robot.configs.robot_settings.RobotSettings` constants (speed bounds, robot geometry) to match your platform.
- MQTT setup: set fields on `robot.configs.mqtt_settings.MQTTSettings` before constructing robots.

## Documentation

Sphinx documentation lives in `docs/` and is auto-generated on pushes to `dev` via GitHub Actions, then deployed to GitHub Pages. To build locally:

```bash
pip install -r requirements.txt
sphinx-apidoc -o docs/api src/robot
python -m sphinx -b html docs docs/_build/html
open docs/_build/html/index.html
```

## Contributing

- Run lint and tests: `flake8 src tests` and `PYTHONPATH=src pytest`
- Example to run: `python examples/my_test_robot.py`
