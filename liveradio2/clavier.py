#
# Author: peppe8o
# Blog: https://peppe8o.com
# Date: May 11th, 2021
# Version: 1.0

import RPi.GPIO as GPIO
import sys
import time

# define PINs according to cabling
# following array matches 1,2,3,4 PINs from 4x4 Keypad Matrix
#boutons 30,31,32
row_list=[23,19,24]
# following array matches 5,6,7,8 PINs from 4x4 Keypad Matrix
#boutons 33,34,35
col_list=[26,4,16]


# set row pins to output, all to high
GPIO.setmode(GPIO.BCM)
for pin in row_list:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, GPIO.HIGH)

#set columns pins to input. We'll read user input here
for pin in col_list:
  GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

key_map=[["9","8","7"],\
        ["6","5","4"],\
        ["3","2","1"]]

# define Matrix Keypad read function
def Keypad4x4Read(cols,rows):
  for r in rows:
    GPIO.output(r, GPIO.LOW)
    result=[GPIO.input(cols[0]),GPIO.input(cols[1]),GPIO.input(cols[2])]
    if min(result)==0:
      key=key_map[int(rows.index(r))][int(result.index(0))]
      GPIO.output(r, GPIO.HIGH) # manages key keept pressed
      return(key)
    GPIO.output(r, GPIO.HIGH)

# main program
while True:
  try:
    key=Keypad4x4Read(col_list, row_list)
    if key != None:
      print("You pressed: "+key)
      time.sleep(0.3) # gives user enoght time to release without having double inputs
# PINs final cleaning on interrupt
  except KeyboardInterrupt:
    GPIO.cleanup()
    sys.exit()