# Arduino Sensor Monitoring System

A real-time temperature and humidity monitoring project using an Arduino, DHT11 sensor, and a Python dashboard.

The Arduino reads the sensor values and sends them over the serial connection. The Python program displays the readings, calculates a few useful values, stores the readings in a CSV file, and shows charts.

## Features

- Read temperature and humidity from a DHT11
- Display live readings
- Calculate heat index
- Calculate a comfort score
- Show temperature and humidity trends
- Show distributions and recent readings
- Display simple alerts when values cross the set limits
- Save readings to `sensor_log.csv`
- Run in demo mode without the Arduino

## Hardware

- Arduino
- DHT11 temperature and humidity sensor
- USB connection

### DHT11 wiring

```text
DHT11 VCC   → Arduino 5V
DHT11 DATA  → Arduino D2
DHT11 GND   → Arduino GND
```

## Software

- Arduino C++
- Python
- NumPy
- Pandas
- Matplotlib
- Seaborn
- SciPy
- PySerial

## Files

```text
arduino-sensor-monitoring-system/
├── arduino_dht11.ino
├── sensor_dashboard.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Running the project

Install the Python packages:

```bash
pip install -r requirements.txt
```

Upload `arduino_dht11.ino` to the Arduino and connect it to the computer.

Then run:

```bash
python sensor_dashboard.py
```

If an Arduino is not connected, the dashboard can be tested with:

```bash
python sensor_dashboard.py --demo
```

The program will ask you to select the available serial port when running with the Arduino.

## Data format

The Arduino sends two values separated by a comma:

```text
temperature,humidity
```

For example:

```text
28.4,65.2
```

## Notes

The temperature and humidity limits used for alerts can be changed in `sensor_dashboard.py`.

The forecast shown by the dashboard is a simple linear-regression estimate based on recent readings. It is intended for demonstration and experimentation rather than accurate long-term prediction.

## Possible Improvements

- Add more sensors
- Store data in a database
- Add better forecasting
- Add a small web interface
- Add calibration and sensor-health checks

## Author

**Faqeeha Fathima**

B.Tech AI & Data Science
