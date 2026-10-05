# Arduino Sensor Monitoring System

A small, practical Arduino + Python project that reads temperature and humidity from a DHT11 sensor and turns the readings into a live analytics dashboard.

This repository is intentionally documented around what the project actually does, rather than making the system sound more complicated than it is.

## What this project does

The DHT11 measures:

- Temperature
- Relative humidity

The Arduino reads those two values and sends them to the laptop over USB serial.

The Python application receives the readings and builds the live dashboard. It also calculates additional analytics such as heat index, a project-specific comfort score, threshold alerts, trends, distributions, regression, statistics, and a simple short-horizon forecast.

### Overall flow

```text
DHT11 sensor
     │
     │ temperature + humidity
     ▼
Arduino
     │
     │ USB serial @ 9600 baud
     │ "28.4,65.2"
     ▼
Laptop
     │
     ▼
sensor_dashboard.py
     │
     ├── Parse and validate readings
     ├── Calculate heat index
     ├── Calculate comfort score
     ├── Check thresholds
     ├── Store recent readings
     ├── Save CSV log
     └── Update dashboard
              │
              ├── Temperature
              ├── Humidity
              ├── Heat Index
              ├── Trends
              ├── KDE distributions
              ├── Scatter + regression
              ├── Recent readings
              ├── Comfort gauge
              ├── Statistics
              └── Next-10-reading forecast
```

## Hardware

The demonstrated hardware is deliberately simple:

- Arduino board
- DHT11 temperature/humidity sensor module
- USB cable to the laptop

### Documented connection

| DHT11 | Arduino |
|---|---|
| VCC | 5V |
| DATA | D2 |
| GND | GND |

See:

- `docs/HARDWARE_CONNECTION.md`
- `docs/ARDUINO_PYTHON_INTEGRATION.md`

**Accuracy note:** D2 is the documented circuit/firmware choice. The original demonstration video did not clearly expose the Arduino pin labels, so the original physical pin number was not visually verified from the footage.

## Repository structure

```text
arduino-sensor-monitoring-system/
├── sensor_dashboard.py
├── arduino_dht11.ino
├── requirements.txt
├── .gitignore
├── README.md
├── data/
│   └── sample_sensor_data.csv
└── docs/
    ├── HARDWARE_CONNECTION.md
    └── ARDUINO_PYTHON_INTEGRATION.md
```

## 1. Arduino code

The Arduino firmware is in:

`arduino_dht11.ino`

Its job is only to read the DHT11 and send clean serial data.

The Arduino sends:

```text
28.4,65.2
```

The first value is temperature in °C.

The second value is relative humidity in %.

The serial speed is **9600 baud**.

The Python dashboard is written around this exact format.

## 2. Arduino library setup

Open `arduino_dht11.ino` in Arduino IDE.

Install **DHT sensor library by Adafruit** using:

**Sketch → Include Library → Manage Libraries...**

Search for **DHT sensor library** and install it. Recent versions also require the Adafruit Unified Sensor library.

Then:

1. Select the actual Arduino board.
2. Select the Arduino COM port.
3. Upload `arduino_dht11.ino`.
4. If you open Serial Monitor for testing, use **9600 baud**.
5. Confirm that readings look like `28.4,65.2`.

## 3. Python setup

Install Python 3.9 or newer.

From the project folder:

```bash
pip install -r requirements.txt
```

Run with the real Arduino:

```bash
python sensor_dashboard.py
```

The application lists the available serial ports and asks you to select the Arduino port.

## 4. Demo mode

You do not need the Arduino to test the dashboard.

Run:

```bash
python sensor_dashboard.py --demo
```

Demo mode generates simulated temperature and humidity readings locally.

This is useful for testing the dashboard, screenshots, or demonstrations when the physical sensor is not connected.

## 5. What happens to one real reading

Suppose the Arduino sends:

```text
28.4,65.2
```

Python:

1. Reads the serial line.
2. Splits the two values.
3. Converts them to numbers.
4. Validates them.
5. Calculates heat index.
6. Calculates the project-specific comfort score.
7. Checks temperature and humidity thresholds.
8. Adds the reading to the live data buffers.
9. Appends it to `sensor_log.csv`.
10. Refreshes the dashboard.

This is the main connection between the Arduino code and the Python code.

## 6. Dashboard analytics

The dashboard currently provides:

- Real-time temperature monitoring
- Real-time humidity monitoring
- Heat-index calculation
- Project-specific comfort score
- High/low threshold alerts
- CSV logging
- Smoothed time-series curves
- Heat-index moving average
- Temperature and humidity KDE distributions
- Temperature vs. humidity scatter analysis
- Linear regression and R²
- Recent-reading bar chart
- Comfort gauge
- Mean, minimum, maximum, and standard deviation
- Next-10-reading forecast

## 7. Important limitation: the forecast

The forecast is a **simple linear-regression projection** over recent readings.

It is not a trained machine-learning model.

It is included as a lightweight analytics feature and should be described honestly in demonstrations and presentations.

## 8. Important limitation: comfort score

The comfort score is a project-specific heuristic calculated from temperature and humidity.

It is not an official medical measurement or environmental safety standard.

## 9. Data logging

Live readings are written to:

`sensor_log.csv`

The columns are:

```text
timestamp,temperature,humidity,heat_index,comfort
```

The runtime log is excluded from Git.

The repository also contains:

`data/sample_sensor_data.csv`

That file is example/sample data for the project.

## Do's

- Keep the Arduino and Python baud rate at **9600**.
- Keep the Arduino output as `temperature,humidity`.
- Use the DHT11 sensor type in the Arduino sketch.
- Select the correct COM port.
- Install the required DHT library before compiling.
- Use demo mode when hardware is unavailable.
- Describe the forecast as linear regression, not AI.
- Describe the comfort score as a project-specific heuristic.
- Keep the hardware description limited to hardware actually used.

## Don'ts

- Do not send labelled serial text unless the Python parser is changed too.
- Do not change the baud rate on only one side.
- Do not say Python reads the DHT11 directly.
- Do not call the forecast a trained AI model.
- Do not call the comfort score an official medical/environmental standard.
- Do not add hardware to the project description that was not actually used.
- Do not assume a bare 4-pin DHT11 has the same wiring as a 3-pin module.
- Do not claim D2 was visually verified from the original video.

## Troubleshooting

### No COM port appears

Check the USB cable, Arduino connection, board selection, and the operating-system COM port.

### Arduino is connected but Python shows no readings

Check the Arduino serial output. It should look like:

```text
28.4,65.2
```

If the Arduino sends labels or other text, the current parser will ignore those lines.

### Arduino prints ERROR

Check the DHT11 wiring, sensor type, library installation, and physical sensor connection.

### Forecast is not shown

The dashboard waits until enough readings are available before drawing the next-10-reading forecast.

## What this project is—and is not

This is an educational/portfolio IoT analytics system.

It demonstrates the complete path from a physical sensor to a desktop analytics dashboard:

**sensor → microcontroller → serial communication → Python data processing → visualization**

It is not presented as an industrial environmental monitoring product or a trained predictive-AI system.

## Author

**Faqeeha Fathima**
**Mushfiya**
