from driver_LCD import LcdDisplay
import time
from time import sleep
from PIL import Image, ImageDraw,ImageFont

lcd=LcdDisplay()
lcd.set_intensity(1)
image_raw=Image.open("logo.bmp")
#image=image_raw.resize((132,80),Image.LANCZOS)
#lcd.clean_display()
#lcd.load_image(image)
#lcd.draw_rectangle(60,20,120,10,1,1,2)
#lcd.draw_text(80,60,"HELLO WORLD",1,"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12,"ms",0,"left")
#lcd.draw_rectangle(30,60,130,70,1,1,2)
#lcd.draw_text(80,70,"HELLO WORLD",0,"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12,"ms",0,"left")
#lcd.update_display()

#lcd.clean_display()
#image=image_raw.resize((132,80),Image.LANCZOS)
#lcd.load_image(image)
#lcd.draw_rectangle(60,20,120,10,1,1,2)
#lcd.draw_text(80,60,"SALUT",1,"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12,"ms",0,"left")
#lcd.update_display()

#GPIO.cleanup()
i=1
while 1:
  if (i%2):
   image=image_raw.resize((132,80),Image.LANCZOS)
   lcd.load_image(image)
  else:
   lcd.clean_display()
   lcd.draw_text(80,60,"SALUT",1,"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12,"ms",0,"left")
  lcd.update_display()
  i=i+1
#  pass
