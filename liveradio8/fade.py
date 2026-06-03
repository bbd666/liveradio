"""
3.5 inch 480x320 TFT with SPI ILI9488
on Raspberry Pi 4B using Python/luma.lcd
Show images in Slideshow, with fade-in/fade-out.
"""

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import ili9488
from PIL import Image, ImageOps
import os
import time
import RPi.GPIO as GPIO

serial = spi(port=0, device=0, gpio_DC=23, gpio_RST=24, spi_speed_hz=32000000)

device = ili9488(serial, rotate=2,
                 gpio_LIGHT=18, active_low=False) # BACKLIGHT PIN = GPIO 18, active High

device.backlight(False) # Turn OFF backlight first

BACKLIGHT_PIN = 18

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)
pwm.start(0)

def fade_in():
    for duty_cycle in range(0, 101, 1):
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.01)

def fade_out():
    for duty_cycle in range(100, -1, -1):
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.01)

# Because the image source is 1024x768
# and the LCD display is 480x320
# so resize 1024x768 to 426x320
# expand to 480x320, with border of 27 pixel, (480-426)/2 = 27.
def showImage(image_source):
    image = Image.open(image_source)
    print("Open image:", image_source)
    img_resized = image.resize((426, 320), Image.LANCZOS)
    img_expanded = ImageOps.expand(img_resized, border=(27, 0), fill='black')

    device.display(img_expanded)

images_folder = "/home/pierre"
files = os.listdir(images_folder)
jpg_files = [file for file in files if file.endswith('.jpg')]
jpg_file_list = sorted(jpg_files)

print("=== Start ===")
print("# of file:", len(jpg_file_list))

while True:
    for i in range(0, len(jpg_file_list)):
        ImagePath = os.path.join(images_folder, jpg_file_list[i])
        showImage(ImagePath)
        
        fade_in()
        time.sleep(3)
        fade_out()
