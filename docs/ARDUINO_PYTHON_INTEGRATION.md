# Arduino ↔ Python Integration Guide

This document explains what is physically connected, what runs on the Arduino, what runs on the laptop, and exactly how the data moves from the DHT11 to the dashboard.

## 1. The complete system in one line

**DHT11 → Arduino → USB serial → Python `sensor_dashboard.py` → analytics → live dashboard + CSV log**

There is no direct Python-to-DHT11 connection. The Arduino is the bridge between the physical sensor and the Python application.

## 2. Hardware actually used

For the demonstrated setup, keep the hardware list simple:

- Arduino board
- DHT11 temperature/humidity sensor module
- USB cable connecting the Arduino to the laptop

Do not add hardware to the project description that was not actually used in the demonstration.

### Documented wiring

| DHT11 | Arduino |
|---|---|
| VCC | 5V |
| DATA | D2 |
| GND | GND |

The repository documents a **3-pin DHT11 module**. A bare 4-pin DHT11 sensor is different: its wiring may require a pull-up resistor, so do not assume the 3-pin module wiring applies to every DHT11 package.

## 3. Arduino side

The file `arduino_dht11.ino` is the Arduino firmware.

Its job is intentionally small:

1. Start serial communication at 9600 baud.
2. Start the DHT11 sensor.
3. Read temperature in °C.
4. Read relative humidity in %.
5. Reject invalid sensor readings.
6. Send the two valid values to the laptop.

The Arduino does **not** calculate the heat index, comfort score, regression, KDE, forecast, or charts. Those are handled by Python.

## 4. Arduino library setup

Open `arduino_dht11.ino` in Arduino IDE.

Install **DHT sensor library by Adafruit** through:

**Sketch → Include Library → Manage Libraries...**

Search for **DHT sensor library** and install it. Current Adafruit guidance also notes that the Adafruit Unified Sensor library is required by recent versions of the DHT library.

Then select the actual Arduino board and its COM port and upload the sketch.

## 5. What the Arduino sends

The Arduino sends one reading approximately every 2 seconds:

```text
28.4,65.2
28.5,65.0
28.7,64.8
```

Meaning:

- `28.4` = temperature in °C
- `65.2` = relative humidity in %
- `9600` = serial baud rate

The format is deliberately simple because the Python program is written to parse exactly two comma-separated numbers.

## 6. Physical connection to the laptop

The USB cable connects the Arduino to the laptop.

The same USB connection provides the serial communication used by Python.

```text
DHT11
  │
  │ sensor signal
  ▼
Arduino
  │
  │ USB / Serial @ 9600
  ▼
Laptop
  │
  ▼
sensor_dashboard.py
```

## 7. Python side

Install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Then start the dashboard:

```bash
python sensor_dashboard.py
```

The program lists available serial ports. Select the port belonging to the Arduino.

If the Arduino is not connected, use:

```bash
python sensor_dashboard.py --demo
```

## 8. What happens to one reading

Suppose Arduino sends:

```text
28.4,65.2
```

Python's `serial_reader()` then:

1. Reads the serial line.
2. Checks that a comma is present.
3. Splits the line into two values.
4. Converts both values to floating-point numbers.
5. Rejects non-finite or malformed values.
6. Calculates the heat index.
7. Calculates the project-specific comfort score.
8. Checks the configured temperature/humidity thresholds.
9. Stores the reading in the live data buffers.
10. Writes the reading to `sensor_log.csv`.
11. The Matplotlib animation refreshes the dashboard.

## 9. What the dashboard shows

The current dashboard contains:

- Temperature time series
- Humidity time series
- Heat index
- Smoothed curves
- High/low threshold lines
- Linear trend line
- Temperature distribution (KDE)
- Humidity distribution (KDE)
- Temperature vs. humidity scatter plot
- Regression relationship and R²
- Recent-reading bar chart
- Comfort gauge
- Current/mean/min/max/std-dev statistics
- Alert messages
- Next-10-reading forecast

## 10. Important: what the forecast actually is

The "Next 10 Readings Forecast" is **not a trained AI/ML model**.

It uses a simple linear regression over recent readings and extends that trend forward.

That is useful for demonstrating analytics, but it should not be described as a production forecasting system or machine-learning model.

## 11. Data logging

Live readings are appended to:

`sensor_log.csv`

The columns are:

```text
timestamp,temperature,humidity,heat_index,comfort
```

The runtime log is excluded from Git through `.gitignore`.

The repository's `data/sample_sensor_data.csv` is example data, not a claim that those values came from the live hardware session.

## 12. Do's

- Use the DHT11 sensor type in the Arduino code.
- Keep the Arduino serial speed at 9600 baud.
- Keep the serial output in the format `temperature,humidity`.
- Select the correct Arduino COM port in the Python program.
- Close Arduino Serial Monitor before starting Python if the port is already in use.
- Install the required DHT library before compiling the Arduino sketch.
- Use `--demo` when you want to demonstrate the Python dashboard without hardware.
- Treat the comfort score as a project-specific indicator.
- Treat the forecast as a simple statistical projection.

## 13. Don'ts

- Do not send labels such as `Temperature: 28.4 C` from Arduino unless the Python parser is changed too.
- Do not change the baud rate on only one side.
- Do not claim that Python reads the DHT11 directly.
- Do not describe the forecast as a trained AI model.
- Do not call the comfort score an official medical or environmental standard.
- Do not add LEDs, buzzers, displays, extra sensors, breadboards, or other hardware to the project description unless they were actually used.
- Do not assume a bare 4-pin DHT11 has the same wiring as a 3-pin DHT11 module.
- Do not treat the supplied demonstration video as proof of a pin number when the pin labels are not clearly visible.

## 14. Troubleshooting

### No serial ports appear

Check the USB cable, Arduino connection, board selection, and operating-system COM port.

### Arduino is connected but the dashboard stays empty

Check the Arduino serial output. It should look like:

```text
28.4,65.2
```

If it contains labels or unrelated text, the current Python parser will ignore those lines.

### Arduino prints ERROR

Check:

- DHT11 VCC
- DHT11 DATA
- DHT11 GND
- `DHTTYPE DHT11`
- DHT sensor library installation
- sensor connection

### Forecast is not visible yet

The dashboard waits until at least 10 readings are available.

## 15. Accuracy note about the documented pin

The repository uses **D2** as the documented DATA connection because it is the connection represented in the project circuit documentation and firmware.

The original demonstration footage did not clearly expose the Arduino pin labels. Therefore, this repository does **not** claim that D2 was visually verified from the original video.

## 16. The clean mental model

Think of the project as two programs working together:

**Arduino = sensor reader**

**Python = data processor + visualizer**

Arduino collects the physical measurement and sends it.

Python receives it, analyzes it, logs it, and turns it into the dashboard.
