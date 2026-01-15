# Robot Library Python — Testing Guide

## Overview

The robot library includes comprehensive unit and integration tests to validate functionality without requiring a physical robot or external MQTT broker.

- **Unit Tests** (`test_all.py`): Fast, isolated tests using mocks
- **Integration Tests** (`test_integration.py`): Real MQTT client behavior with in-process broker or live broker

## Quick Start

### Run All Tests

From the repository root:

```bash
cd src
python -m unittest discover -s robot -p "test_*.py" -v
```

Or run specific test suites:

```bash
# Unit tests only
python -m unittest robot.test_all -v

# Integration tests only
python -m unittest robot.test_integration -v

# Both
python -m unittest robot.test_all robot.test_integration -v
```

### Expected Output

```
test_coordinate_publish_and_setters (robot.test_all.RobotPackageSmokeTests...) ... ok
test_motion_controller_stub_coord_and_moves (robot.test_all.RobotPackageSmokeTests...) ... ok
test_neopixel_and_indicator_publish (robot.test_all.RobotPackageSmokeTests...) ... ok
test_proximity_reading_type (robot.test_all.RobotPackageSmokeTests...) ... ok
test_rgb_color_type_basic (robot.test_all.RobotPackageSmokeTests...) ... ok
test_sensors_handle_subscription (robot.test_all.RobotPackageSmokeTests...) ... ok
test_client_initialization (robot.test_integration.IntegrationTestRobotMqttClient...) ... ok
test_mqtt_msg_queueing (robot.test_integration.IntegrationTestRobotMqttClient...) ... ok
test_multiple_subscribers (robot.test_integration.IntegrationTestRobotMqttClient...) ... ok
test_publish_and_receive (robot.test_integration.IntegrationTestRobotMqttClient...) ... ok
test_client_queue_operations (robot.test_integration.RobotMqttClientMockTests...) ... ok
test_in_queue_append (robot.test_integration.RobotMqttClientMockTests...) ... ok

Ran 12 tests in 0.024s

OK
```

## Test Structure

### Unit Tests (`src/robot/test_all.py`)

Fast smoke tests using lightweight mocks, no external dependencies.

**Coverage:**
- `RGBColorType`: Color initialization, hex code parsing, string parsing, comparison
- `ProximityReadingType`: Distance/color parsing, list operations
- `Coordinate`: Getters, setters, publish operations
- `MotionController`: Movement calculations, zero-speed handling
- `NeoPixel`: Initialization, color changes, publish
- `Sensors` (Distance, Color, Proximity): Subscription handling, state updates

**Run:**
```bash
python -m unittest robot.test_all -v
```

**Execution Time:** < 0.01s

### Integration Tests (`src/robot/test_integration.py`)

Tests for `RobotMqttClient` behavior with real or simulated MQTT broker.

**Coverage:**
- Client initialization and connection
- Publish/subscribe with in-process broker
- Multi-client message routing
- Message queue operations
- Connection lifecycle

**Run:**
```bash
python -m unittest robot.test_integration -v
```

**Execution Time:** < 0.05s

## MQTT Broker Setup (Optional)

### For Development/Integration Testing

The integration tests work with or without a real MQTT broker:

- **Without broker**: Uses in-process `InMemoryMQTTBroker` stub (tests skip gracefully)
- **With broker**: Tests connect to real `localhost:1883`

#### Install Mosquitto (Windows via Chocolatey)

```powershell
choco install mosquitto
```

#### Start Mosquitto

```bash
mosquitto -p 1883
```

Or use Windows Service:
```powershell
net start mosquitto
```

#### Verify Connection

```bash
python -c "from paho import mqtt; print('MQTT available')"
```

## Development Workflow

### Before Committing

1. **Run all tests:**
   ```bash
   cd src
   python -m unittest robot.test_all robot.test_integration -v
   ```

2. **Check for syntax errors (optional):**
   ```bash
   python -m py_compile robot/**/*.py
   ```

3. **Run specific test file:**
   ```bash
   python -m unittest robot.test_all.RobotPackageSmokeTests.test_rgb_color_type_basic -v
   ```

### Adding New Tests

1. Add test method to existing test class or create new `TestCase`:
   ```python
   def test_new_feature(self):
       # Arrange
       obj = MyClass()
       
       # Act
       result = obj.do_something()
       
       # Assert
       self.assertEqual(result, expected_value)
   ```

2. Run tests to verify:
   ```bash
   python -m unittest robot.test_all -v
   ```

## Dependencies

### Required
- Python 3.10+
- (No external packages for unit tests)

### Optional
- `paho-mqtt`: For real MQTT broker integration (auto-stubbed if missing)
- Mosquitto: Real MQTT broker for development (optional)

## Troubleshooting

### Import Errors in IDE

If VS Code shows `Import "robot.x.y" could not be resolved`:

1. Ensure `src/` is the Python source root
2. VS Code settings (`.vscode/settings.json`):
   ```json
   {
     "python.analysis.extraPaths": ["${workspaceFolder}/src"]
   }
   ```

### Tests Won't Run

**Error: `No module named robot`**
```bash
cd src
python -m unittest robot.test_all -v  # Must run from src/
```

**Error: `ModuleNotFoundError: No module named 'paho'`**
- This is expected and graceful. Tests skip MQTT connection tests.
- To fix: `pip install paho-mqtt`

### MQTT Connection Refused

If tests show `MQTT connection error`:
1. Ensure Mosquitto is running: `mosquitto -p 1883`
2. Check if port 1883 is in use: `netstat -ano | findstr :1883`
3. Tests will skip gracefully if broker unavailable

## Test Coverage

| Module | Status | Notes |
|--------|--------|-------|
| `types/` | ✅ Full | RGBColorType, ProximityReadingType |
| `sensors/` | ✅ Full | Distance, Color, Proximity |
| `helpers/` | ✅ Partial | Coordinate, MotionController (logic tested) |
| `indicators/` | ✅ Full | NeoPixel |
| `mqtt/` | ✅ Partial | RobotMqttClient (connection + queue ops) |
| `communication/` | ⚠️ Mock only | Requires full robot context |
| `robot_base/` | ⚠️ Mock only | Requires MQTT server + robot setup |

## CI/CD Integration

For GitHub Actions or similar:

```yaml
- name: Run Tests
  run: |
    cd src
    python -m unittest discover -s robot -p "test_*.py" -v
```

## Performance Benchmarks

| Test Suite | Count | Duration | Notes |
|-----------|-------|----------|-------|
| Unit Tests | 6 | < 0.01s | No I/O, no network |
| Integration Tests | 6 | < 0.05s | In-process broker or real MQTT |
| **Total** | **12** | **< 0.1s** | Fast feedback loop |

## Further Reading

- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [MQTT Protocol](https://mqtt.org/)
- [Mosquitto Docs](https://mosquitto.org/documentation/)

---

**Last Updated:** January 12, 2026
