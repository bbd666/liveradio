import time
from PIL import Image, ImageDraw,ImageFont
import RPi.GPIO as GPIO
from time import sleep
import adafruit_ssd1306 
from board import SCL, SDA
import board
import digitalio  

#installer le driver : pip  install adafruit-circuitpython-ssd1306 --break-system-packages
#activer le mode i2c : sudo raspi-config


oled=adafruit_ssd1306.SSD1306_SPI(128,64,board.SPI(),digitalio.DigitalInOut(board.D22),digitalio.DigitalInOut(board.D27),digitalio.DigitalInOut(board.D8)) 

oled.fill(0) #clear the OLED Display 
oled.show()  
font=ImageFont.load_default()  
width = 128
height = 64

image = Image.open("logo.jpg")
image_r = image.resize((width,height), Image.LANCZOS)
image_bw = image_r.convert("1")
oled.image(image_bw)
draw=ImageDraw.Draw(image_bw)
oled.show()

