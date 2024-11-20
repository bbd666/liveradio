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
#import subprocess

os.system('sh remote.sh')

now=datetime.now()
lastnow=datetime.now()
update=True       

def scan_wifis(ssids):
    networks = subprocess.check_output(['netsh', 'wlan', 'show', 'network'])
    networks = networks.decode('ascii')
    networks = networks.replace('\r', '')
    ssid = networks.split('\n')
    sid = ssid[4:]
    ssids = []
    x = 0
    while x < len(ssid):
        if x % 5 == 0:
            ssids.append(ssid[x])
        x += 1
   
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
            arg[3]=0
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
    
time_var=""
date_var=""    
def set_time():
    now = datetime.now()
    global time_var
    global date_var
    time_var=now.strftime('%H:%M:%S')
    date_var = now.strftime("%d/%m/%Y")      
                  
#Rotary encounter parameters
clkPin = 12    # CLK Pin
dtPin = 9    # DT Pin
swPin = 7    # Button Pin
#rotary encounter GPIO        
GPIO.setup(clkPin, GPIO.IN)    # input mode
GPIO.setup(dtPin, GPIO.IN)
GPIO.setup(swPin, GPIO.IN)

def rotaryDeal(arg):
   arg[1] = GPIO.input(dtPin)
   det=GPIO.input(swPin)
   if (det==0):
        global globalCounter      
        arg[3] = 0
        arg[4]=0
   else:
        arg[4]=-1
   while(not GPIO.input(clkPin)):
    arg[2] = GPIO.input(dtPin)
    arg[0] = 1
   if arg[0] == 1:
      arg[0] = 0
      if (arg[1] == 0) and (arg[2] == 1):
         arg[3] = arg[3] + 1
      if (arg[1] == 1) and (arg[2] == 0):
         arg[3] = arg[3] - 1
      arg[3]=max(min(arg[3],100),-100)   
      
#Load URL's from the database
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
font100 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
       
IR_param=[-100,time.perf_counter(),0,0]
ROTARY_param=[0,0,0,0,-1]
time_date=[0,0]

def init_menu(arg,items):
    global update
    global image_blanche
    global width
    global height
    global oled
    draw=ImageDraw.Draw(image_blanche)
    arg[1]=arg[3]//arg[0]
    arg[2]=arg[3]%arg[0]
    oled.image(image_blanche)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.rectangle((0, 2+arg[2]*15, 128, (arg[2]+1)*15), outline=1, fill=1)            
    for i in range(0,arg[0]):
        if i+arg[1]*arg[0]<len(items):
            if i+arg[1]*arg[0]==arg[3] :
                draw.text((10,2+i*15),items[i+arg[1]*arg[0]],font=font3,size=1,fill=0)  
            else :
                draw.text((10,2+i*15),items[i+arg[1]*arg[0]],font=font3,size=1,fill=1)
    oled.show()
    update=False
            
ST1_param=[4,0,0,0]#nb_lignes,shiftbloc,decal,fillindex
ST1_menu=["WEB STATIONS","ALARME","MEDIA USB"]
ST2_param=[4,0,0,0]
ST2_menu=liste_lbl
ST100_param=[0,0,0,0]
ST100_menu=[]

STATE=0

while True:
            
    key=trig_ir(IR_param)
    source="IR"
    if key==None: 
     key=Keypad4x4Read(col_list, row_list)
     source="clavier"
    if (key==None):       
        counter=ROTARY_param[3]
        rotaryDeal(ROTARY_param)
        if not(counter==ROTARY_param[3]):
         source="rotary"
         key=ROTARY_param[3]
        else:
         source=""
         

    if not(key==None):
         print(source)
         print(key)   
         
    if STATE==0:
            now=datetime.now()
            deltat=now-lastnow
            if (deltat.microseconds>950000):
                draw=ImageDraw.Draw(image_bw) 
                oled.image(image_bw)
                draw.text((55,2),time_var,font=font1,size=1,fill=0)  
                draw.text((40,45),date_var,font=font2,size=1,fill=0)  
                set_time()
                draw.text((55,2),time_var,font=font1,size=1,fill=1)  
                draw.text((40,45),date_var,font=font2,size=1,fill=1)  
                oled.show()
                lastnow=now
                if  ((source=="IR") and (key==0)):
                    STATE=100
            if ( (source=="IR") and (key==3) ) or ((source=="clavier") and (key==5) ):
                update=True
                STATE=1
                
    if STATE==1:#menus principaux
            if update:
                init_menu(ST1_param,ST1_menu)           
  
            if ( (source=="IR") and (key==57) ) :
                ST1_param[3]=ST1_param[3]+1
                if ST1_param[3]>len(ST1_menu)-1:
                    ST1_param[3]=0
                update=True
            if ( (source=="IR") and (key==41) ) :
                ST1_param[3]=ST1_param[3]-1
                update=True
            if (ST1_param[3]==0 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=2
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                STATE=0           
          #  if ((source=="IR") and (key==0)):
          #     STATE=100
                
    if STATE==2:#menus web radios
            if update:
                init_menu(ST2_param,ST2_menu)
                update=False

            if ( (source=="IR") and (key==57) ) :
                ST2_param[3]=ST2_param[3]+1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                update=True
            if ( (source=="IR") and (key==41) ) :
                ST2_param[3]=ST2_param[3]-1
                update=True
            if ( ((source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                url=liste_url[ST2_param[3]]
                player.set_mrl(url)
                player.play()
                player.audio_set_volume(200)
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                STATE=1            
                update=True
            if ((source=="IR") and (key==0)):
               STATE=100
                
    if STATE==100:#écran de veille
            now=datetime.now()
            deltat=now-lastnow
            if (deltat.microseconds>950000):
                draw=ImageDraw.Draw(image_blanche)
                oled.image(image_blanche)               
                draw.rectangle((0, 0, width, height), outline=0, fill=0)
                draw.text((55,2),time_var,font=font100,size=1,fill=0)  
                draw.text((40,45),date_var,font=font100,size=1,fill=0)  
                set_time()
                draw.text((55,2),time_var,font=font100,size=1,fill=1)  
                draw.text((40,45),date_var,font=font100,size=1,fill=1)  
                oled.show()
                lastnow=now
                if ((source=="IR") and (key==0)):
                    STATE=0

         

         
        
    
