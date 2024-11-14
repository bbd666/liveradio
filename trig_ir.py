import vlc
import time
import board
from time import strftime
from PIL import Image, ImageDraw,ImageFont
import configparser
import RPi.GPIO as GPIO
import sys
from time import sleep
import digitalio  
import adafruit_ssd1306 
import evdev
from datetime import datetime
import os

os.system('sh remote.sh')
   
def get_ir_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if (device.name == "gpio_ir_recv"):           
            return device          
dev = get_ir_device()


def trig_ir(arg):
    event = dev.read_one()
    result=None
    if (event) :
        a = event.value
        if not(a==0):
            result= a
        else:
            if arg[3]==1:
                result=a
                arg[3]=0
            else:
                result=None
                arg[3]=1
    else:
        arg[3]=0
    if not(result==None):
        last_result=result
        arg[2] = time.perf_counter()
        if not(last_result==arg[0]) or (arg[2]-arg[1])>1:
            arg[1] = time.perf_counter()
            arg[0]=last_result
            return result
          
#Rotary encounter parameters
clkPin = 12    # CLK Pin
dtPin = 9    # DT Pin
swPin = 7    # Button Pin

#Keypad Parameters
row_list=[23,24,25]
col_list=[4,5,6]
GPIO.setmode(GPIO.BCM)
for pin in row_list:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, GPIO.HIGH)
for pin in col_list:
  GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
key_map=[["9","8","7"],
        ["6","5","4"],
        ["3","2","1"]]
last_key=-100
        
#Define Matrix Keypad read function
def Keypad4x4Read(cols,rows):
  global last_key
  for r in rows:
    GPIO.output(r, GPIO.LOW)
    result=[GPIO.input(cols[0]),GPIO.input(cols[1]),GPIO.input(cols[2])]
    if min(result)==0:
      key=key_map[int(rows.index(r))][int(result.index(0))]
      GPIO.output(r, GPIO.HIGH) # manages key keept pressed
      if not(key==last_key):
       last_key=key
       return key
    GPIO.output(r, GPIO.HIGH)
    
        
def set_time():
    now = datetime.now()
    global time_var
    global date_var
    time_var=now.strftime('%H:%M:%S')
    date_var = now.strftime("%d/%m/%Y")       
        
IR_param=[-100,time.perf_counter(),0,0]

while True:
    key=trig_ir(IR_param)
    if key==None:
     key=Keypad4x4Read(col_list, row_list)
    if not(key==None):
     print(key)
    
