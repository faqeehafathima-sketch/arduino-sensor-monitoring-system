/*
  Arduino Sensor Monitoring System
  DHT11 -> Arduino -> USB Serial -> Python Dashboard

  Hardware:
    DHT11 VCC  -> Arduino 5V
    DHT11 DATA -> Arduino D2
    DHT11 GND  -> Arduino GND

  Serial protocol expected by sensor_dashboard.py:
    temperature,humidity
  Example:
    28.4,65.2

  Baud rate: 9600
  Reading interval: approximately 2 seconds

  Library required:
    Adafruit DHT sensor library
*/

#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
  delay(2000);
}

void loop() {
  // DHT11 should not be polled too quickly.
  delay(2000);

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();  // Celsius

  // Do not send malformed data to the Python dashboard.
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("ERROR");
    return;
  }

  // Python expects exactly two comma-separated numbers.
  Serial.print(temperature, 1);
  Serial.print(",");
  Serial.println(humidity, 1);
}
