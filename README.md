# Robot Library Python

A modular Python library for building robot applications. It provides components for motion control, sensor access, communication, and indicators.

## Installation

```bash
pip install -e .
```

## Usage

```python
from robot import MQTTSettings, VirtualRobot
from robot.interfaces import RobotState


class MyRobot(VirtualRobot):
    def loop(self):
        if self.state == RobotState.RUN:
            print("running...")
            self.delay(1000)


MQTTSettings.server = "localhost"
MQTTSettings.port = 1883
MQTTSettings.user_name = ""
MQTTSettings.password = ""
MQTTSettings.channel = "v1"

r = MyRobot(1, 0, 0, 90)
r.start()
r.run()  # or run via a thread
```

See `examples/my_test_robot.py` for a complete example mirroring the Java demo.
