
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

volume_ini=100
time_var=""
date_var=""
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
        

def get_ir_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if (device.name == "gpio_ir_recv"):           
            return device          
dev = get_ir_device()

def set_time():
    now = datetime.now()
    global time_var
    global date_var
    time_var=now.strftime('%H:%M:%S')
    date_var = now.strftime("%d/%m/%Y")
    
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

config = configparser.ConfigParser()
config.read('data.ini')
nb=config['STREAMS']['NB']
liste_url=[]
liste_lbl=[]
for i in range(1,int(nb)+1):
  liste_url.append(config['STREAMS']['URL'+str(i)])
  liste_lbl.append(config['STREAMS']['LBL'+str(i)])
volume_ini=int(config['RADIO SETTINGS']['volume'])
channel_ini=int(config['RADIO SETTINGS']['index'])
url=liste_url[channel_ini]

oled=adafruit_ssd1306.SSD1306_SPI(128,64,board.SPI(),digitalio.DigitalInOut(board.D22),digitalio.DigitalInOut(board.D27),digitalio.DigitalInOut(board.D8)) 
oled.fill(0) #clear the OLED Display 
oled.show()  
font=ImageFont.load_default()  
width = 128
height = 64
image_blanche = Image.new('1',(128,64))
 
image2=Image.open("bbd-liveradio2.jpg")
image2 = image2.resize((width,height), Image.LANCZOS)
image2 = image2.convert("1")

image = Image.open("logo.jpg")
image_r = image.resize((width,height), Image.LANCZOS)
image_bw = image_r.convert("1")
oled.image(image_bw)

player = vlc.MediaPlayer()
player.set_mrl(url)
player.play()

font1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
font2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14) 
font3 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12) 

############################################################################################################
class Welcome():
  def __init__(self,  **Arguments):
      global time_var
      global date_var  
      global key
      draw=ImageDraw.Draw(image_bw) 
      
      while True:

        #oled.fill(0)
        oled.image(image_bw)

        draw.text((55,2),time_var,font=font1,size=1,fill=0)  
        draw.text((40,45),date_var,font=font2,size=1,fill=0)  
        set_time()
        draw.text((55,2),time_var,font=font1,size=1,fill=1)  
        draw.text((40,45),date_var,font=font2,size=1,fill=1)  
        #oled.text(self,'100',30,10,1, *, font_name="font5x8.bin", size=1)
        oled.show()
        
        event = dev.read_one()
        if (event):
            print(event.value)
            if event.value==3 :
                menu=Menu()
                self.logout
                break
                
        key=Keypad4x4Read(col_list, row_list)
        if key != None:
            print("You pressed: "+key)
            if key=="6" :
                menu=Menu()
                self.logout
                break
            time.sleep(0.3) # gives user enough time to release without having double inputs
            
  def logout(self):
      self.destroy()
 
############################################################################################################
class Menu():
  def __init__(self,  **Arguments):
      width = 128
      height = 64
      self.fillindex=0
      self.lastupcall=datetime.now()
      self.lastdowncall=datetime.now()
      items=["WEB STATIONS","ALARME","MEDIA USB"]
      draw=ImageDraw.Draw(image_blanche)
      
      while True:
      
        oled.image(image_blanche)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw.rectangle((0, 2+self.fillindex*15, 128, (self.fillindex+1)*15), outline=1, fill=1)
        
        for i in range(0,len(items)):
            if i==self.fillindex :
                draw.text((10,2+i*15),items[i],font=font3,size=1,fill=0)  
            else :
                draw.text((10,2+i*15),items[i],font=font3,size=1,fill=1)  
            
        oled.show()
        
        event = dev.read_one()

        if (event):           
            print(event.value)
            if event.value==32 :
                main=Welcome()
                self.logout                
                break
                
            if event.value==57 :
                now = datetime.now() 
                a = now-self.lastdowncall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastdowncall=now
                    self.fillindex=self.fillindex+1
                    self.fillindex=self.fillindex%len(items)

            if event.value==41:
                now = datetime.now() 
                a = now-self.lastupcall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastupcall=now
                    self.fillindex=self.fillindex-1
                    if self.fillindex<0:
                        self.fillindex=len(items)-1
                   
            if event.value==49:
                 if (self.fillindex==0):
                    webfen=WebRadio()
                    self.logout                
                    break
                 
        key=Keypad4x4Read(col_list, row_list)
        if key != None:
            print("You pressed: "+key)
            if key=="2" :
                oled.image(image_blanche)
                oled.show()
                main=Welcome()
                self.logout                
                break
            time.sleep(0.3) # gives user enough time to release without having double inputs
 
  def logout(self):
      self.destroy()
      
  
############################################################################################################
class WebRadio():
  def __init__(self,  **Arguments):
      width = 128
      height = 64
      self.fillindex=0
      self.decal=0
      self.lastupcall=datetime.now()
      self.lastdowncall=datetime.now()
      draw=ImageDraw.Draw(image_blanche)
      
      while True:
      
        oled.image(image_blanche)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw.rectangle((0, 2+(self.fillindex-self.decal)*15, 128, (self.fillindex-self.decal+1)*15), outline=1, fill=1)
        
        for i in range(0,len(liste_lbl)):
            if i==self.fillindex :
                draw.text((10,2+(i-self.decal)*15),liste_lbl[i],font=font3,size=1,fill=0)  
            else :
                draw.text((10,2+(i-self.decal)*15),liste_lbl[i],font=font3,size=1,fill=1)  
            
        oled.show()
        
        event = dev.read_one()

        if (event):           
            print(event.value)
            if event.value==32 :
                menu=Menu()
                self.logout                
                break
                
            if event.value==57 :
                now = datetime.now() 
                a = now-self.lastdowncall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastdowncall=now
                    self.fillindex=self.fillindex+1
                    if self.fillindex>3:
                        self.decal+=1
                        
                    self.fillindex=self.fillindex%len(liste_lbl)

            if event.value==41 :
                now = datetime.now() 
                a = now-self.lastupcall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastupcall=now
                    self.fillindex=self.fillindex-1
                    if self.fillindex<0:
                        self.fillindex=len(liste_lbl)-1
                   
            if event.value==49 :
                #if (self.fillindex==0):                                 
                    self.change_channel()

                 
        key=Keypad4x4Read(col_list, row_list)
        if key != None:
            print("You pressed: "+key)
            if key=="2" :
                oled.image(image_blanche)
                oled.show()
                main=Welcome()
                self.logout                
                break
            time.sleep(0.3) # gives user enough time to release without having double inputs
 
  def change_channel(self):
      url=liste_url[self.fillindex]
      player.set_mrl(url)
      player.play()
           
  def logout(self):
      self.destroy()
         
 
############################################################################################################

fen1=Welcome()


print("fin")
player.stop()

############################################################################################################
############################################################################################################


sind=str(volume_ini)
schannel=str(channel_ini)

config.set('RADIO SETTINGS', 'INDEX', schannel)
config.set('RADIO SETTINGS', 'VOLUME',sind )
with open('data.ini', 'w') as configfile:   
    config.write(configfile)
