#!/usr/bin/env python3

"""
-------------------------------------------------------------------------------
Author        : Florian Hild
Created       : yyyy-mm-dd
Python version: 3.x
Description   :
  Tested with DS18B20 1Wire Temp Sensor
-------------------------------------------------------------------------------
"""

__VERSION__ = '1.0.0'

import sys
import os
import time

def getTemp(id):
  file = open('/sys/bus/w1/devices/' + id + '/w1_slave', 'r')
  filecontent = file.read()
  file.close()

  # Temperaturwerte auslesen und konvertieren
  stringvalue = filecontent.split("\n")[1].split(" ")[9]
  temperature = float(stringvalue[2:]) / 1000
  return('%6.2f'%temperature )

def main():
  sensor_id = '28-01193cda254a'
  count = 0
  rotations = 20
  interupt = 1

  try:
    while count <= rotations:
      print("Aktuelle Temperatur: " + getTemp(sensor_id) + "°C")
      time.sleep(interupt)
      count += 1

    print("Temperaturabfrage beendet")
  except KeyboardInterrupt:
    print("Exit")
    sys.exit(0)

if __name__ == '__main__':
  main()

