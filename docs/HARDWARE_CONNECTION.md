# Arduino Sensor Monitoring System — Hardware & Circuit Documentation

## Hardware Used

The project demonstration used only:

- Arduino board
- DHT11 temperature/humidity sensor module
- USB connection to the laptop for serial communication

No additional display, LED, buzzer, breadboard, or other sensor is documented as part of the demonstrated hardware.

## Connection

| Arduino | DHT11 |
|---|---|
| 5V | VCC |
| D2 | DATA |
| GND | GND |

See the rendered circuit diagram: [Arduino DHT11 Circuit Diagram](./Arduino_DHT11_Circuit_Diagram.svg)

## Working Principle

1. The DHT11 measures temperature and humidity.
2. The Arduino reads the sensor values.
3. The readings are transmitted to the computer through serial communication.
4. The Python dashboard receives the values and performs analytics.
5. The dashboard displays temperature, humidity, heat index, comfort score, trends, distributions, regression/scatter analysis, recent readings, statistics, and threshold alerts.

## Serial Format

The Python dashboard expects:

```text
temperature,humidity
```

Example:

```text
28.2,67.1
```

Default serial speed: **9600 baud**.

## Demonstration

The supplied demonstration video shows the DHT11 being exposed to a heat source and the laptop dashboard responding with environmental readings and analytics.

## Accuracy Note

The original supplied video is 832×464 and does not clearly expose the Arduino board's pin labels. Therefore, the **D2 DATA connection is presented as the documented circuit choice for this diagram, not as a claim that D2 was visually verified from the original footage**.

The project source also identifies the system as an Arduino + DHT11 serial dashboard but does not contain the original Arduino firmware sketch.

## Media

The cleaned/enhanced HD demonstration video was produced separately from the original footage with audio removed and visual sharpening/upscaling applied. The source footage itself limits how much fine text detail can be recovered.
