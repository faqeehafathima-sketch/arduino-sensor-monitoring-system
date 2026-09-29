# Arduino Sensor Monitoring System

Real-time IoT sensor monitoring and analytics dashboard built with Python, Arduino serial communication, Matplotlib, Seaborn, Pandas, NumPy, and SciPy.

## Overview

This project reads temperature and humidity data from an Arduino-based DHT11 sensor through serial communication and presents the data in a live analytics dashboard.

It also includes a demo mode, so the dashboard can be tested without connecting an Arduino.

## Features

- Real-time temperature monitoring
- Real-time humidity monitoring
- Heat-index calculation
- Comfort score calculation
- Configurable high/low threshold alerts
- CSV data logging
- Smoothed time-series visualization
- Trend analysis using linear regression
- Temperature/humidity distribution analysis with KDE
- Temperature vs humidity scatter analysis
- Recent-readings bar chart
- Comfort-score gauge
- Live statistics including mean, min, max, and standard deviation
- Short-horizon forecast of the next 10 readings
- Arduino serial mode and standalone demo mode

## Tech Stack

- Python
- NumPy
- Pandas
- Matplotlib
- Seaborn
- SciPy
- PySerial
- Arduino
- DHT11

## Project Structure

```text
arduino-sensor-monitoring-system/
├── sensor_dashboard.py
├── sample_sensor_log.csv
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

Clone the repository and install the dependencies:

```bash
pip install -r requirements.txt
```

## Run in Demo Mode

You can run the dashboard without an Arduino:

```bash
python sensor_dashboard.py --demo
```

The demo generator produces simulated temperature and humidity readings every 2 seconds.

## Run with Arduino

1. Upload an Arduino sketch that reads the DHT11 sensor.
2. Send readings over serial in this format:

```text
temperature,humidity
```

Example:

```text
28.2,67.1
```

3. Use a serial connection at **9600 baud**.
4. Start the dashboard:

```bash
python sensor_dashboard.py
```

5. Select the available COM port when prompted.

## Analytics

The dashboard calculates and visualizes:

- Temperature and humidity trends
- Heat index
- Comfort score
- Threshold-based alerts
- Moving averages
- Linear-regression trends
- Distribution estimates
- Temperature/humidity relationship
- Basic next-10-reading linear forecast
- Descriptive statistics

The forecast is a simple linear-regression projection for demonstration and analytics purposes; it should not be treated as a production forecasting model.

## Data Logging

Live readings are appended to:

```text
sensor_log.csv
```

The repository includes `sample_sensor_log.csv` as example data. The generated `sensor_log.csv` is ignored by Git so local runtime logs do not continuously change the repository.

## Configuration

Thresholds and dashboard settings can be adjusted near the top of `sensor_dashboard.py`, including:

- Serial baud rate
- Maximum chart points
- Dashboard refresh interval
- Temperature thresholds
- Humidity thresholds

## Notes

- The project is designed as an educational/portfolio IoT analytics system.
- Arduino hardware is required only for live sensor mode; demo mode works independently.
- The repository does not include an Arduino firmware sketch because the uploaded project source contains the Python dashboard/serial consumer rather than the Arduino-side firmware.

## Authors

**FAQEEHA FATHIMA**  \
**MUSHFIYA**

B.Tech AI & Data Science
