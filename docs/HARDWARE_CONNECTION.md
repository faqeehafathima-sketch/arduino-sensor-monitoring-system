# Arduino Sensor Monitoring System — Hardware Connection

## Hardware actually used

- Arduino board
- DHT11 temperature/humidity sensor module
- USB cable to the laptop

No additional sensor, display, LED, buzzer, or other hardware is part of the demonstrated setup.

## Wiring

| DHT11 pin | Arduino |
|---|---|
| VCC | 5V |
| DATA | D2 |
| GND | GND |

## How the hardware reaches the software

```text
DHT11
  ↓
Arduino D2
  ↓
Arduino reads temperature + humidity
  ↓
USB serial connection
  ↓
Python sensor_dashboard.py
```

## Serial contract

**Baud rate:** 9600

**Format:**

```text
temperature,humidity
```

Example:

```text
28.4,65.2
```

The first value is temperature in °C and the second is relative humidity in %.

## Important package note

This documentation assumes the **3-pin DHT11 module** used for the project documentation. A bare 4-pin DHT11 sensor can require different wiring and a pull-up resistor.

## Pin-number accuracy note

D2 is the documented connection used by the Arduino firmware and circuit documentation. The original supplied demonstration footage did not clearly expose the Arduino pin labels, so D2 was not visually verified from that video.

## Software boundary

The Arduino reads the sensor.

The Python application receives the serial values and performs the analytics and visualization.

The laptop/USB cable is the communication path; it is not an additional sensing component.
