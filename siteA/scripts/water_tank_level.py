#!/usr/bin/env python3

"""
-------------------------------------------------------------------------------
Author        : Florian Hild
Created       : 2024-05-29
Python version: 3.x
Description   : Distance messure with RPi.GPIO library and JSN-SR04T-2.0 sensor
-------------------------------------------------------------------------------
"""

__VERSION__ = '1.0.0'

import sys
import time
import logging as log
import argparse
import statistics
import RPi.GPIO as GPIO

water_tank_heigh_max_cm = 100
sensor_offset_cm = 10 # Distance from sensor to water_tank_heigh_max_cm
pin_trigger = 11
pin_echo = 13
trigger_pulse_us = 0.00002 # 20 microsec
values = []
failed_attempts = 5


def getDistance():
  log.debug('Set trigger pin (%i) to high', pin_trigger)
  GPIO.output(pin_trigger, GPIO.HIGH)
  log.debug('Trigger pulse width: %f microseconds', trigger_pulse_us)
  time.sleep(trigger_pulse_us)
  log.debug('Set trigger pin (%i) to low', pin_trigger)
  GPIO.output(pin_trigger, GPIO.LOW)

  log.debug('Waiting for start (high) pulse from echo pin ...')
  pulse_start = time.time()
  while GPIO.input(pin_echo) == 0:
    pass
  log.debug("Current echo pin (%i) state: %i", pin_echo, GPIO.input(pin_echo))
  pulse_start = round(time.time() * 1000000)
  log.debug("Set start pulse to %s", pulse_start)

  log.debug('Waiting for end (low) pulse from echo pin ...')
  while GPIO.input(pin_echo) == 1:
    pass
  log.debug("Current echo pin (%i) state: %i", pin_echo, GPIO.input(pin_echo))
  pulse_end = round(time.time() * 1000000) # time in microsec
  log.debug("Set end pulse to %s", pulse_end)


  # Calculate the time it took the wave to travel there and back
  pulse_duration = pulse_end - pulse_start
  log.debug("Duartion: %i microseconds", pulse_duration)

  # Schallgeschwindigkeit in Luft: 343m/S (bei 20°C)
  # 343,2 m/S --> 34,32cm / ms --> 0,03432cm / µs
  # durch 2 wegen Echo hin und zurück
  distance = (pulse_duration * 0.03432)/2
  # CorrectedCmDistance = duration *(0.03315 + 0.00006 * temperature)/2;

  if distance == 0:
    log.error('No pulse from sensor')
    return None
  elif distance > 20 and distance < 600:
    log.info("Distance: %.1f cm", distance)
    return distance
  else:
    # Range 20cm - 600cm
    log.error("Distance %.1f cm out of range. (Range: 20cm - 600cm)", distance)

    return 20
    # return None

def round_down_to_nearest_ten(value):
  # Calculate the nearest lower multiple of 10
  return (value // 10) * 10


def main():
  log.basicConfig(
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
  )

  # Parameter configuration
  parser = argparse.ArgumentParser(
    description='Distance messure with RPi.GPIO library and JSN-SR04T-2.0 sensor',
    prog='water_tank_level',
        usage='%(prog)s [options]',
        add_help=False,
    )

  parser.add_argument(
    '-V', '--version',
    help="Print version number and exit.",
    action='version',
    version=f"%(prog)s version {__VERSION__}",
  )

  parser.add_argument(
    '-h', '--help',
    help='Print a short help page describing the options available and exit.',
    action='help',
  )

  parser.add_argument(
    '-v', '--verbose',
    help="""Verbose mode. Multiple -v options increase the verbosity.
         The maximum is 3.""",
    action='count',
    default=0,
  )

  args = parser.parse_args()

  if args.verbose == 0:
    log.getLogger().setLevel(log.WARN)
  elif args.verbose == 1:
    log.getLogger().setLevel(log.INFO)
  else:
    log.getLogger().setLevel(log.DEBUG)

  # Initialise GPIOs
  # GPIP.BOARD = Use pin-numbering scheme
  # GPIO.BCM = Use gpio-numbering scheme
  GPIO.setmode(GPIO.BOARD)

  # Disable msg port already in use
  GPIO.setwarnings(False)

  # Set trigger pin to output mode
  GPIO.setup(pin_trigger, GPIO.OUT)
  # Set echo pin to input mode
  GPIO.setup(pin_echo, GPIO.IN)

  # Set trigger pin to low
  GPIO.output(pin_trigger, GPIO.LOW)

  # Let the sensor settle for a while
  time.sleep(0.5)

  try:
    count = 0
    log.info('Reading data from sensor')
    while len(values) <= 4: # 5 Messungen
      distance = getDistance()

      if distance is not None:
        count = 0
        values.append(distance)
      else:
        count +=1

      if count == failed_attempts:
        GPIO.cleanup()
        sys.exit(0)

      time.sleep(0.5)

    GPIO.cleanup()

    log.debug("Average distance: %.0f cm" %statistics.mean(values))
    average_result_cm = statistics.mean(values)

    # Calculate how many percent is full of water tank
    water_depth_cm = water_tank_heigh_max_cm + sensor_offset_cm - average_result_cm
    log.info("Water tank %s cm of %s cm full", water_depth_cm, water_tank_heigh_max_cm)
    result_percent = (water_depth_cm / water_tank_heigh_max_cm) * 100
    log.debug("Water tank %s %% full", result_percent)
    result_percent = round(result_percent)
    log.info("Water tank ~%s%% full", result_percent)

    if result_percent > 100:
      print("101")
    elif result_percent < 0:
      print("-1")
    else:
      print(round_down_to_nearest_ten(result_percent))

    sys.exit(0)
  except KeyboardInterrupt:
    GPIO.cleanup()
    print("Exit")
    sys.exit(0)


if __name__ == '__main__':
  main()
