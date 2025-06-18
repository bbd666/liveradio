#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

#borne 38
clkPin = 9    # CLK Pin
#borne 37
dtPin = 22  # DT Pin
#borne 36
swPin = 11    # Button Pin

swPin=int(input())

GPIO.setmode(GPIO.BCM)
GPIO.setup(swPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
      det=GPIO.input(swPin)
      if (det==0):
         print ('ok')
         time.sleep(0.3)

