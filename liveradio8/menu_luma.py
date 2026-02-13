"""
3.5 inch 480x320 TFT with SPI ILI9488
on Raspberry Pi 4B using Python/luma.lcd
basic menu
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import ili9488
from PIL import Image, ImageOps, ImageDraw,ImageFont
import os
import time
import RPi.GPIO as GPIO

serial = spi(port=0, device=0, gpio_DC=23, gpio_RST=24, spi_speed_hz=64000000)

device = ili9488(serial, rotate=2,
                 gpio_LIGHT=18, active_low=False) # BACKLIGHT PIN = GPIO 18, active High

device.backlight(False) # Turn OFF backlight first

BACKLIGHT_PIN = 18

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)
pwm.start(0)

image = Image.open("bbd.jpg")
img_resized = image.resize((200, 200), Image.LANCZOS)
background=Image.new(device.mode,device.size,"black")
background.paste(img_resized)
draw=ImageDraw.Draw(background)
font=ImageFont.load_default()
font2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
menu=["item1","item2","item3","item4","item5","item6","item7","item8","item9","item10","item11","item12"]

def fade_in():
    for duty_cycle in range(0, 101, 20):
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.01)

def fade_out():
    for duty_cycle in range(100, -1, -20):
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.01)

def init_menu(menu,i):
    global ini
    left=200
    width=500
    nb_lines=9
    size_menu=len(menu)
    bloc_indice=i//nb_lines
    line_select=i%nb_lines
    decalage=bloc_indice*nb_lines   
    
    for j in range(0,min(nb_lines,len(menu)-decalage)): 
         if j==line_select:
             color="yellow"
         else:
             color="blue"	
         draw.rectangle((left,j*35,min(left+width,475),min(j*35+35,318)),outline="white",fill=color)
         draw.text((left,j*35),menu[j+decalage],font=font2,fill="red")
    draw.rectangle((left,(j+1)*35,min(left+width,475),318),outline="black",fill="black") 
    if (i%nb_lines==nb_lines-1) or (i==size_menu-1) or ini:
       switch=True
    else:
       switch=False

    if switch:
       fade_out()
    device.display(background)
    if switch:
       fade_in()
    ini=False
         
images_folder = "/home/pierre"
files = os.listdir(images_folder)
jpg_files = [file for file in files if file.endswith('.jpg')]
jpg_file_list = sorted(jpg_files)

print("=== Start ===")
print("# of file:", len(jpg_file_list))


l=7
ini=True
fade_in()
while True:
        init_menu(menu,l)
 #       ini=False
        l-=1
        l=l%len(menu)
        time.sleep(0.5)
