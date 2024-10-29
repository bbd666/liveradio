
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

#rotary encounter parameters
clkPin = 12    # CLK Pin
dtPin = 9    # DT Pin
swPin = 7    # Button Pin
flag = 0
Last_dt_Status = 0
Current_dt_Status = 0

volume=100


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
##rotary encounter GPIO        
# GPIO.setup(clkPin, GPIO.IN)    # input mode
# GPIO.setup(dtPin, GPIO.IN)
# GPIO.setup(swPin, GPIO.IN)        

# def rotaryDeal():
   # global flag
   # global Last_dt_Status
   # global Current_dt_Status
   # global volume
   # Last_dt_Status = GPIO.input(dtPin)
   # while(not GPIO.input(clkPin)):
      # Current_dt_Status = GPIO.input(dtPin)
      # flag = 1
   # if flag == 1:
      # flag = 0
      # if (Last_dt_Status == 0) and (Current_dt_Status == 1):
         # volume = volume = max(volume - 1,0)         
        
      # if (Last_dt_Status == 1) and (Current_dt_Status == 0):
         # volume = min(volume + 1,200)

# def swISR(channel):
   # global volume
   # volume = 0

# def rotaryloop():
    # global volume
    # tmp = 0   # Rotary Temporary
    # det=GPIO.input(swPin)          
    # if (det==0):
        # global volume
        # volume=0
    # rotaryDeal()
    # if tmp != volume:
       # print ('globalCounter = %d' % volume)
       # tmp = volume
       # player.audio_set_volume(volume)
   
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
volume=int(config['RADIO SETTINGS']['volume'])
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
  global volume
  global date_var  
  global key
  draw=ImageDraw.Draw(image_bw) 
      
  capture01=0
  capture02=0
  capture3=0
  capture51=0
  capture43=0
    
  while True:
    
    
    event = dev.read_one()
    if (event) :                
            print("You pressed: ")
            print(event.value)   
            print(capture01)   
            print(capture02)   
            
            #traitement des actions sur la télécommande
            if event.value==0:
                 if capture01==0:
                    capture01=1
                 else:
                    capture02=1
            else:
                capture01=0
                capture02=0
                    
            if event.value==3 :
                capture3=1
            if event.value==51 :
                capture51=1
            if event.value==43 :
                capture43=1
                
            if capture3==1:
                menu=Menu()
                self.logout                
                break
                
            if capture51==1:
                volume = max(volume - 10,0)
                player.audio_set_volume(volume)
  
            if capture43==1:
                volume =  min(volume + 10,200)
                player.audio_set_volume(volume)
              
            if capture02==1 :
                player.audio_set_volume(0)                
                 # veille=pause_sound()
                 # self.logout
                 # break
    else :
            #rafraichissement de l'écran
            oled.image(image_bw)
            draw.text((55,2),time_var,font=font1,size=1,fill=0)  
            draw.text((40,45),date_var,font=font2,size=1,fill=0)  
            set_time()
            draw.text((55,2),time_var,font=font1,size=1,fill=1)  
            draw.text((40,45),date_var,font=font2,size=1,fill=1)  
            oled.show()
           
    # try:
        # rotaryloop()
    # except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        # destroy()
            
    # key=Keypad4x4Read(col_list, row_list)
    # if key != None:
        # print("You pressed: "+key)
        # if key=="6" :
            # menu=Menu()
            # self.logout
        #   break
        # time.sleep(0.3) # gives user enough time to release without having double inputs
            
  def logout(self):
      self.destroy()
 
############################################################################################################
class Menu():
  def __init__(self,  **Arguments):
      width = 128
      height = 64
      global volume
      self.nb_lignes = 4
      self.shiftbloc=0
      self.decal=0     
      self.fillindex=0
      self.lastupcall=datetime.now()
      self.lastdowncall=datetime.now()
      items=["WEB STATIONS","ALARME","MEDIA USB"]
      draw=ImageDraw.Draw(image_blanche)
      
      while True:
      
        
        timer = 0.0
        tolerance = 0.5 
        for event in dev.read_loop():
         if timer == 0.0 or time.time() > timer + tolerance:
            timer = time.time()           
            oled.image(image_blanche)
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            draw.rectangle((0, 2+self.fillindex*15, 128, (self.fillindex+1)*15), outline=1, fill=1)
            
            for i in range(0,self.nb_lignes):
                if i+self.shiftbloc*self.nb_lignes<len(items):
                    if i+self.shiftbloc*self.nb_lignes==self.fillindex :
                        draw.text((10,2+i*15),items[i+self.shiftbloc*self.nb_lignes],font=font3,size=1,fill=0)  
                    else :
                        draw.text((10,2+i*15),items[i+self.shiftbloc*self.nb_lignes],font=font3,size=1,fill=1)              
            oled.show()
            print("you pressed :")
            print(event.value)
            if event.value==32 :
                main=Welcome()
                self.logout                
                break
                
            # if event.value==0 :
                # veille=pause_sound()
                # self.logout
                # break         
                
            if event.value==57 :
            #move down 1 channel
                now = datetime.now() 
                a = now-self.lastdowncall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastdowncall=now
                    self.fillindex=self.fillindex+1
                    if self.fillindex>len(liste_lbl)-1:
                        self.fillindex=0

            if event.value==41 :
             #move up 1 channel
                now = datetime.now() 
                a = now-self.lastupcall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastupcall=now
                    self.fillindex=self.fillindex-1
                    
            if event.value==51 :
                volume = max(volume - 10,0)
                player.audio_set_volume(volume)
            if event.value==43 :
                volume =  min(volume + 10,200)
                player.audio_set_volume(volume)
                  
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
class pause_sound():
  def __init__(self,  **Arguments):
      global volume
      global channel_ini
      draw=ImageDraw.Draw(image_blanche)
      
      while True:
        oled.image(image_blanche)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        oled.show()
        
        event = dev.read_one()
        
        if (event):           
            print(event.value)
            if event.value==0 :
                menu=Menu()
                self.logout                
                break
        
  def logout(self):
      self.destroy() 
      
############################################################################################################
class WebRadio():
  def __init__(self,  **Arguments):
      global volume
      global channel_ini
      self.fillindex=channel_ini
      width = 128
      height = 64
      self.nb_lignes = 4
      self.fillindex=channel_ini
      self.shiftbloc=0
      self.decal=0
      self.lastupcall=datetime.now()
      self.lastdowncall=datetime.now()
      draw=ImageDraw.Draw(image_blanche)
      
      while True:
      
        self.shiftbloc=self.fillindex//self.nb_lignes
        self.decal=self.fillindex%self.nb_lignes

        oled.image(image_blanche)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw.rectangle((0, 2+(self.decal)*15, 128, (self.decal+1)*15), outline=1, fill=1)
        
        for i in range(0,self.nb_lignes):
            if i+self.shiftbloc*self.nb_lignes<len(liste_lbl):
                if i+self.shiftbloc*self.nb_lignes==self.fillindex :
                    draw.text((10,2+i*15),liste_lbl[i+self.shiftbloc*self.nb_lignes],font=font3,size=1,fill=0)  
                else :
                    draw.text((10,2+i*15),liste_lbl[i+self.shiftbloc*self.nb_lignes],font=font3,size=1,fill=1)  
            
        oled.show()
        
        event = dev.read_one()

        if (event):           
            print(event.value)
            if event.value==32 :
                menu=Menu()
                self.logout                
                break
            # if event.value==0 :
                # veille=pause_sound()
                # self.logout
                # break               
            if event.value==57 :
            #move down 1 channel
                now = datetime.now() 
                a = now-self.lastdowncall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastdowncall=now
                    self.fillindex=self.fillindex+1
                    if self.fillindex>len(liste_lbl)-1:
                        self.fillindex=0
                    channel_ini=self.fillindex

            if event.value==41 :
             #move up 1 channel
                now = datetime.now() 
                a = now-self.lastupcall    
                if (a.seconds>0) or ((a.seconds==0) and (a.microseconds>600000)):
                    self.lastupcall=now
                    self.fillindex=self.fillindex-1
                channel_ini=self.fillindex
                 
            if event.value==49 :
                #if (self.fillindex==0):                                 
                    self.change_channel()
                    
            if event.value==51 :
                volume = max(volume - 10,0)
                player.audio_set_volume(volume)
            if event.value==43 :
                volume =  min(volume + 10,200)
                player.audio_set_volume(volume)
                
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


sind=str(volume)
schannel=str(channel_ini)
config.set('RADIO SETTINGS', 'INDEX', schannel)
config.set('RADIO SETTINGS', 'VOLUME',sind )
with open('data.ini', 'w') as configfile:   
    config.write(configfile)
