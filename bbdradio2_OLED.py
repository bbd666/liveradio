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
import subprocess
from pathlib import Path
import re
import shutil
from board import SCL, SDA
import busio

i2c = busio.I2C(SCL, SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

os.system('sh remote.sh')
 
now=datetime.now()
lastnow=datetime.now()
update=True 
update_usb=True      

liste=os.listdir("/home/pierre")
liste_melodies=[]
for f in liste:
    extension = os.path.splitext(f)[1]
    if ( (extension==".mp3") or (extension==".wav") ):
        liste_melodies.append(f)
ST_melodies=[4,0,0,0]

ssid=""
passwd=""

usb_path = "/dev/sda1"
mount_path = "/home/pierre/usb_disk_mount"
mp3_files=[]
                
                
def what_wifi():
    process = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        return process.stdout.decode('utf-8').strip().split(':')[1]
    else:
        return ''

def is_connected_to(ssid: str):
    return what_wifi() == ssid   

def scan_wifi():
    process = subprocess.run(['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        return process.stdout.decode('utf-8').strip().split('\n')
    else:
        return []
        
def is_wifi_available(ssid: str):
    return ssid in [x.split(':')[0] for x in scan_wifi()]

def connect_to(ssid: str, password: str):
    if not is_wifi_available(ssid):
        return False
    subprocess.call(['nmcli', 'd', 'wifi', 'connect', ssid, 'password', password])
    return is_connected_to(ssid)

def connect_to_saved(ssid: str):
    if not is_wifi_available(ssid):
        return False
    subprocess.call(['nmcli', 'c', 'up', ssid])
    return is_connected_to(ssid)
   
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
row_list=[23,19,24]
col_list=[26,4,16]
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
    
time_var=["",""]
date_var=["",""]    
def set_time(arg):
    now = datetime.now()
    global time_var
    global date_var
    time_var[arg] = now.strftime('%H:%M:%S')
    date_var[arg] = now.strftime("%d/%m/%Y")      
                  
#Rotary encounter parameters
clkPin = 18    # CLK Pin
dtPin = 20    # DT Pin
swPin = 22    # Button Pin
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
ssid=config['WIFI']['SSID']
passwd=config['WIFI']['PASSWD']
alarm_set=int(config['ALARM']['SET'])
alarm_clck_hour=int(config['ALARM']['HOUR'])
alarm_clck_min=int(config['ALARM']['MIN'])
alarm_source=config['ALARM']['SOURCE']
url=liste_url[channel_ini]

oled.fill(0) #clear the OLED Display 
oled.show()  
font=ImageFont.load_default()  
width = 128
height = 64
image_blanche = Image.new('1',(128,64))

image = Image.open("logo.jpg")
image_r = image.resize((width,height), Image.LANCZOS)
image_bw = image_r.convert("1")
oled.image(image_bw)
draw=ImageDraw.Draw(image_blanche)

player = vlc.MediaPlayer()
player.set_mrl(url)
#player.play()

font1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
font2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14) 
font3 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
font4 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
font100 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
font200 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 7)
       
IR_param=[-100,time.perf_counter(),0,0]
ROTARY_param=[0,0,0,0,-1]
time_date=[0,0]

def init_menu(arg,items):
    global update
    global image_blanche
    global width
    global height
    global oled
    global draw
    image_blanche = Image.new('1',(128,64))
    draw=ImageDraw.Draw(image_blanche)
    arg[1]=arg[3]//arg[0]
    arg[2]=arg[3]%arg[0]
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.rectangle((0, 2+arg[2]*15, 128, (arg[2]+1)*15), outline=1, fill=1)            
    for i in range(0,arg[0]):
        if i+arg[1]*arg[0]<len(items):
            if i+arg[1]*arg[0]==arg[3] :
                draw.text((10,2+i*15),items[i+arg[1]*arg[0]],font=font3,size=1,fill=0)  
            else :
                draw.text((10,2+i*15),items[i+arg[1]*arg[0]],font=font3,size=1,fill=1)
    oled.image(image_blanche)
    oled.show()
    update=False
               
def sound_box(arg):
    global image_blanche
    global width
    global height
    global oled
    global draw
    image_blanche = Image.new('1',(128,64))
    draw=ImageDraw.Draw(image_blanche)
    space=2
    draw.rectangle((round(width/4), round(height/2-5), round(3*width/4),  round(height/2+5)), outline=1, fill=0)
    draw.rectangle((round(width/4+space), round(height/2-5+space),round(arg/200*width/2+width/4-space),round(height/2+5-space)), outline=1, fill=1)            
    oled.image(image_blanche)
    oled.show()

def will_you_load(arg):
    global update
    global image_blanche
    global width
    global height
    global oled
    global draw
    largeur=5
    hauteur=6
    image_blanche = Image.new('1',(128,64))
    draw=ImageDraw.Draw(image_blanche)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    if arg[1]==1:
        draw.text((30,35),"MAJ reussie",font=font3,size=1,fill=1)
    else:
        if arg[1]==2:
            draw.text((30,35),"echec MAJ",font=font3,size=1,fill=1)
        else:
            draw.text((5,5),"Chargement de la MAJ ?",font=font4,size=1,fill=1)
            if arg[0]==0:
               draw.rectangle((30-largeur, 40+hauteur, 60+largeur, 30-hauteur), outline=1, fill=1) 
               draw.text((30,30),"OUI",font=font3,size=1,fill=0)
               draw.text((80,30),"NON",font=font3,size=1,fill=1)
            else:
               draw.rectangle((80-largeur, 40+hauteur, 110+largeur, 30-hauteur), outline=1, fill=1) 
               draw.text((30,30),"OUI",font=font3,size=1,fill=1)
               draw.text((80,30),"NON",font=font3,size=1,fill=0)
    oled.image(image_blanche)
    oled.show()
    update=False

def set_hour(arg):
    global update
    global image_blanche
    global width
    global height
    global oled
    global draw
    largeur=5
    hauteur=6
    draw=ImageDraw.Draw(image_blanche)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)          
    for i in range(4):
        j=i//2
        if arg[4]==i:
            draw.rectangle((25+20*i+j*20-largeur,40+hauteur,35+20*i+j*20+largeur,30-hauteur), outline=1, fill=1)          
            draw.text((25+20*i+j*20,30),str(arg[i]),font=font3,size=1,fill=0)  
        else :
            draw.text((25+20*i+j*20,30),str(arg[i]),font=font3,size=1,fill=1)
    draw.text((65,30),":",font=font3,size=1,fill=1)
    oled.image(image_blanche)
    oled.show()
    update=False    

def set_passwd(arg):
    global update
    global image_blanche
    global width
    global height
    global oled
    global draw
    largeur=5
    hauteur=6
    draw=ImageDraw.Draw(image_blanche)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)          
    s=chr(708)+","+chr(709)+": modif, 'Select:' ajout"
    draw.text((5,5),s,font=font100,size=1,fill=1)  
    s=chr(1)+": suppr, "+">||: valid"
    draw.text((5,15),s,font=font100,size=1,fill=1)  
    for i in range(len(arg)):
        draw.text(((5+10*i)%(width-10),30+10*((5+10*i)//(width-10))),str(arg[i]),font=font4,size=1,fill=1)  
    oled.image(image_blanche)
    oled.show()
    update=False     

def save_params():
    global volume
    global channel_ini
    global alarm_set
    global alarm_clck_hour
    global alarm_clck_min
    global alarm_source
    sind=str(volume)
    schannel=str(channel_ini)
    config.set('RADIO SETTINGS', 'INDEX', schannel)
    config.set('RADIO SETTINGS', 'VOLUME',sind )
    config.set('ALARM', 'SET',str(alarm_set) )
    config.set('ALARM', 'HOUR',str(alarm_clck_hour) )
    config.set('ALARM', 'MIN',str(alarm_clck_min) )
    config.set('ALARM', 'SOURCE',alarm_source )
    config.set('WIFI', 'SSID',ssid )
    config.set('WIFI', 'PASSWD',passwd )
    with open('data.ini', 'w') as configfile:   
        config.write(configfile)
        
def scan_USB_files():
    global update_usb
    global usb_path
    global mount_path 
    global mp3_files
    audio_ext = [".mp3" ,".ogg", ".flac", ".wav"]
    subprocess.run(["sudo", "mount", usb_path, mount_path])
    p = Path(mount_path)
    mp3_files=[]
    if p.is_mount():
        mp3_files = [x for x in p.iterdir() if x.suffix in audio_ext]
    update_usb=False
            
def load_config(arg):
    global usb_path
    global mount_path 
    subprocess.run(["sudo", "mount", usb_path, mount_path])
    p = Path(mount_path)
    if p.is_mount():
        my_file = p/arg
        if my_file.is_file():
         my_file_target="/home/pierre/"+arg
         shutil.copy(my_file,my_file_target)
         return 1
        else:
         return 0
    else:
        return 0
    subprocess.run(["sudo", "umount", mount_path])
   
ST1_param=[4,0,0,0]#nb_lignes,shiftbloc,decal,fillindex
ST1_menu=["WEB STATIONS","ALARME","WIFI","USB","ADRESSE IP"]
ST2_param=[4,0,0,channel_ini]
ST2_menu=liste_lbl
ST3_param=[4,0,0,0]
ST3_menu=["ACTIVATION","REGLAGE","SOURCE SONORE","MELODIES"]
ST100_param=[0,0,0,0]
ST100_menu=[]
ST5_param=[4,0,0,0]
ST5_menu=[]
ST4_param=[4,0,0,0]
ST4_menu=["MEDIAS","MAJ SYSTEME","MAJ CONFIG"]
ST41_param=[4,0,0,0]
ST41_menu=[]
ST6_param=[4,0,0,0]
ST6_menu=[]

STATE=0
digit_sel=0
last_rotary_position=ROTARY_param[3]

try:
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
    
    now=datetime.now()
    if ((alarm_set==1) and (now.hour==alarm_clck_hour) and (now.minute==alarm_clck_min) and (now.second<20) ):
        if not(player.is_playing()):
            player.set_mrl(alarm_source)
            player.play()
            STATE=0
    
    match STATE:
     case 0:#ecran d'accueil
            now=datetime.now()
            deltat=now-lastnow
            if (deltat.microseconds>950000):
                draw=ImageDraw.Draw(image_bw) 
                draw.text((55,2),time_var[0],font=font1,size=1,fill=0)  
                draw.text((40,45),date_var[0],font=font2,size=1,fill=0)  
                set_time(0)
                draw.text((55,2),time_var[0],font=font1,size=1,fill=1)  
                draw.text((40,45),date_var[0],font=font2,size=1,fill=1)  
                oled.image(image_bw)
                oled.show()
                lastnow=now            
            
            if  ((source=="IR") and ((key==3) or (key==49)) or ( (source=="clavier") and (key==5) ))  :
                update=True                
                STATE=1
                
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    volume=min(volume+1,200)
                if key<last_rotary_position:
                    volume=max(volume-1,0)
                sound_box(volume)
                player.audio_set_volume(volume)
                last_rotary_position=ROTARY_param[3]
                
            if ( (source=="IR") and (key==43) ) :
                volume=min(volume+5,200)
                sound_box(volume)
                player.audio_set_volume(volume)
                
            if ( (source=="IR") and (key==51) ) :
                volume=max(volume-5,0)
                sound_box(volume)
                player.audio_set_volume(volume)
 
            if ( ((source=="IR") and (key==42)) or ((source=="clavier") and (key==5)) ) :
                if not(player.is_playing()):
                    player.play()
                else:
                    player.pause()                   
                
     case 1:#menus principaux
            if update==True:
               init_menu(ST1_param,ST1_menu)           
   
            if ( (source=="IR") and (key==57) ) :
                ST1_param[3]=ST1_param[3]+1
                if ST1_param[3]>len(ST1_menu)-1:
                    ST1_param[3]=0
                update=True
                
            if ( (source=="IR") and (key==41) ) :
                ST1_param[3]=ST1_param[3]-1
                if ST1_param[3]<0:
                    ST1_param[3]=len(ST1_menu)-1
                update=True
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST1_param[3]=ST1_param[3]+1
                if key<last_rotary_position:
                    ST1_param[3]=ST1_param[3]-1
                if ST1_param[3]>len(ST1_menu)-1:
                    ST1_param[3]=0
                if ST1_param[3]<0:
                    ST1_param[3]=len(ST1_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True
                    
            if (ST1_param[3]==0 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=2         #web radio
                
            if (ST1_param[3]==1 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=3         #alarm
                
            if (ST1_param[3]==2 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=5         #wifi                              
                
            if (ST1_param[3]==3 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=4         #USB
                
            if (ST1_param[3]==4 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=6         #IP
 
            if (( (source=="IR") and ((key==32) or (key==3)) ) or ( (source=="clavier") and (key==9) )) : 
                STATE=0   
                
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100
  
     case 2:#menus web radios
            if update:
                init_menu(ST2_param,ST2_menu)

            if ( (source=="IR") and (key==57) ) :
                ST2_param[3]=ST2_param[3]+1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                update=True
                
            if ( (source=="IR") and (key==41) ) :
                ST2_param[3]=ST2_param[3]-1
                if ST2_param[3]<0:
                    ST2_param[3]=len(ST2_menu)-1
                update=True
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST2_param[3]=ST2_param[3]+1
                if key<last_rotary_position:
                    ST2_param[3]=ST2_param[3]-1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                if ST2_param[3]<0:
                    ST2_param[3]=len(ST2_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if ( ((source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                url=liste_url[ST2_param[3]]
                player.set_mrl(url)
                channel_ini=ST2_param[3]
                player.play()
                
            if ( (source=="IR") and (key==43) ) :
                volume=min(volume+5,200)
                sound_box(volume)
                player.audio_set_volume(volume)
                update=True
                
            if ( (source=="IR") and (key==51) ) :
                volume=max(volume-5,0)
                sound_box(volume)
                player.audio_set_volume(volume)
                update=True
                
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                STATE=1            
                update=True
                
            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

            if ((source=="IR") and (key==0)):
                save=True
                STATE=100
  
     case 3:#menus settings alarme
            if update:
                init_menu(ST3_param,ST3_menu)

            if ( (source=="IR") and (key==57) ) :
                ST3_param[3]=ST3_param[3]+1
                if ST3_param[3]>len(ST3_menu)-1:
                    ST3_param[3]=0
                update=True
            if ( (source=="IR") and (key==41) ) :
                ST3_param[3]=ST3_param[3]-1
                if ST3_param[3]<0:
                    ST3_param[3]=len(ST3_menu)-1
                update=True
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST3_param[3]=ST3_param[3]+1
                if key<last_rotary_position:
                    ST3_param[3]=ST3_param[3]-1
                if ST3_param[3]>len(ST3_menu)-1:
                    ST3_param[3]=0
                if ST3_param[3]<0:
                    ST3_param[3]=len(ST3_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if (ST3_param[3]==0 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=30
                
            if (ST3_param[3]==1 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                digit_sel=0
                STATE=31     
                
            if (ST3_param[3]==2 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
               update=True
               STATE=32
                
            if (ST3_param[3]==3 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                STATE=33
                
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update=True
                STATE=1 
                
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 30:#menus activation alarme
        if update:
            draw=ImageDraw.Draw(image_blanche)
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            if alarm_set==1:
                draw.text((10,30),"ALARME ACTIVE",font=font4,size=1,fill=1)
            else:            
                draw.text((10,30),"ALARME DESACTIVEE",font=font4,size=1,fill=1)
            oled.image(image_blanche)
            oled.show()
            update=False  
            
        if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=3               
            
        if (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            if alarm_set==1:
                alarm_set=0 
            else:
                alarm_set=1
            update=True
            
        if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

        if ( (source=="IR") and (key==3) )  : 
            STATE=0   
            
     case 31:#menus reglage alarme
        if update:
            h=[alarm_clck_hour//10,alarm_clck_hour%10,alarm_clck_min//10,alarm_clck_min%10,digit_sel]
            set_hour(h)
            
        if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=3       
            
        if (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            digit_sel=(digit_sel+1)%4
            update=True
            
        if ( (source=="IR") and (key==41) ) :
            match digit_sel:
             case 0:
                alarm_clck_hour=min(alarm_clck_hour+10,23)
             case 1:
                alarm_clck_hour=min(alarm_clck_hour+1,23)
             case 2:
                alarm_clck_min=min(alarm_clck_min+10,59)
             case 3:
                alarm_clck_min=min(alarm_clck_min+1,59)
            update=True
            
        if ( (source=="IR") and (key==57) ) :
            match digit_sel:
             case 0:
                alarm_clck_hour=max(alarm_clck_hour-10,0)
             case 1:
                alarm_clck_hour=max(alarm_clck_hour-1,0)
             case 2:
                alarm_clck_min=max(alarm_clck_min-10,0)
             case 3:
                alarm_clck_min=max(alarm_clck_min-1,0)                
            update=True      
                        
        if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100
 
        if ( (source=="IR") and (key==3) )  : 
            STATE=0   
 
     case 32:#menus selection source alarme
            if update:
                init_menu(ST2_param,ST2_menu)

            if ( (source=="IR") and (key==57) ) :
                ST2_param[3]=ST2_param[3]+1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                update=True
                
            if ( (source=="IR") and (key==41) ) :
                ST2_param[3]=ST2_param[3]-1
                if ST2_param[3]<0:
                    ST2_param[3]=len(ST2_menu)-1
                update=True                
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST2_param[3]=ST2_param[3]+1
                if key<last_rotary_position:
                    ST2_param[3]=ST2_param[3]-1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                if ST2_param[3]<0:
                    ST2_param[3]=len(ST2_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if ( ((source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                alarm_source=liste_url[ST2_param[3]]

            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update=True
                STATE=3            

            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100
                
            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 33:#menus selection melodie
            if update:
                init_menu(ST_melodies,liste_melodies)

            if ( (source=="IR") and (key==57) ) :
                ST_melodies[3]=ST_melodies[3]+1
                if ST_melodies[3]>len(liste_melodies)-1:
                    ST_melodies[3]=0
                update=True
                
            if ( (source=="IR") and (key==41) ) :
                ST_melodies[3]=ST_melodies[3]-1
                if ST_melodies[3]<0:
                    ST_melodies[3]=len(liste_melodies)-1
                update=True                
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST_melodies[3]=ST_melodies[3]+1
                if key<last_rotary_position:
                    ST_melodies[3]=ST_melodies[3]-1
                if ST_melodies[3]>len(liste_melodies)-1:
                    ST_melodies[3]=0
                if ST_melodies[3]<0:
                    ST_melodies[3]=len(liste_melodies)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if ( ((source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                alarm_source=liste_melodies[ST_melodies[3]]

            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update=True
                STATE=3            

            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100
                
            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 4:#menu USB
            if update:
                init_menu(ST4_param,ST4_menu)

            if ( (source=="IR") and (key==57) ) :
                ST4_param[3]=ST4_param[3]+1
                if ST4_param[3]>len(ST4_menu)-1:
                    ST4_param[3]=0
                update=True
            if ( (source=="IR") and (key==41) ) :
                ST4_param[3]=ST4_param[3]-1
                if ST4_param[3]<0:
                    ST4_param[3]=len(ST4_menu)-1
                update=True
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST4_param[3]=ST4_param[3]+1
                if key<last_rotary_position:
                    ST4_param[3]=ST4_param[3]-1
                if ST4_param[3]>len(ST4_menu)-1:
                    ST4_param[3]=0
                if ST4_param[3]<0:
                    ST4_param[3]=len(ST4_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if (ST4_param[3]==0 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                update_usb=True
                STATE=41
                
            if (ST4_param[3]==1 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                rep=[0,0]
                STATE=42     

            if (ST4_param[3]==2 and (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) )) :
                update=True
                rep=[0,0]
                STATE=43     
                
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update=True
                STATE=1 
                
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 41:#menu USB Medias
            if update_usb:
                s=scan_USB_files()
                ST41_menu=[]
                for i in range(0,len(mp3_files)):
                    ST41_menu.append(mp3_files[i].name)
            if update:
                init_menu(ST41_param,ST41_menu)

            if ( (source=="IR") and (key==57) ) :
                ST41_param[3]=ST41_param[3]+1
                if ST41_param[3]>len(ST41_menu)-1:
                    ST41_param[3]=0
                update=True
            if ( (source=="IR") and (key==41) ) :
                ST41_param[3]=ST41_param[3]-1
                if ST41_param[3]<0:
                    ST41_param[3]=len(ST41_menu)-1
                update=True
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST41_param[3]=ST41_param[3]+1
                if key<last_rotary_position:
                    ST41_param[3]=ST41_param[3]-1
                if ST41_param[3]>len(ST41_menu)-1:
                    ST41_param[3]=0
                if ST41_param[3]<0:
                    ST41_param[3]=len(ST41_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if  (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                url=mp3_files[ST41_param[3]]
                player.set_mrl(url)
                player.play()
                
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
                
            if  ((source=="IR") and (key==0) ):
                update_usb=True
                save=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                update_usb=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=0   

     case 42:#menu USB MAJ SYSTEME
            if update:
                will_you_load(rep)

            if ( (source=="IR") and (key==57) ) :
                update=True
                rep[0]=(rep[0]+1)%2
                will_you_load(rep)

            if ( (source=="IR") and (key==41) ) :
                update=True
                rep[0]=(rep[0]-1)%2
                will_you_load(rep)
               
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    rep[0]=(rep[0]+1)%2
                if key<last_rotary_position:
                    rep[0]=(rep[0]-1)%2
                update=True
                last_rotary_position=ROTARY_param[3]
                will_you_load(rep)

            if  (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                update=True
                if rep[0]==0:
                    err=load_config("data.ini")
                    if (err==1):
                        rep[1]=1
                        will_you_load(rep)
                    else:
                        rep[1]=2
                        will_you_load(rep)
                else:
                    STATE=1
 
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
 
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 43:#menu USB MAJ CONFIG
            if update:
                will_you_load(rep)

            if ( (source=="IR") and (key==57) ) :
                update=True
                rep[0]=(rep[0]+1)%2
                will_you_load(rep)

            if ( (source=="IR") and (key==41) ) :
                update=True
                rep[0]=(rep[0]-1)%2
                will_you_load(rep)
               
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    rep[0]=(rep[0]+1)%2
                if key<last_rotary_position:
                    rep[0]=(rep[0]-1)%2
                update=True
                last_rotary_position=ROTARY_param[3]
                will_you_load(rep)

            if  (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                update=True
                if rep[0]==0:
                    err=load_config("bbdradio2_OLED.py")
                    if (err==1):
                        rep[1]=1
                        will_you_load(rep)
                    else:
                        rep[1]=2
                        will_you_load(rep)
                else:
                    STATE=1
 
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
 
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 5:#menu wifi
            if update:
                s=scan_wifi()
                ST5_menu=[]
                for i in range(0,len(s)):
                    w=s[i].split(":")
                    ST5_menu.append(w[0])
                init_menu(ST5_param,ST5_menu)

            if ( (source=="IR") and (key==57) ) :
                ST5_param[3]=ST5_param[3]+1
                if ST5_param[3]>len(ST5_menu)-1:
                    ST5_param[3]=0
                update=True
            if ( (source=="IR") and (key==41) ) :
                ST5_param[3]=ST5_param[3]-1
                if ST5_param[3]<0:
                    ST5_param[3]=len(ST5_menu)-1
                update=True
                
            if ((source=="rotary") and (ROTARY_param[4]==-1)):
                if key>last_rotary_position:
                    ST5_param[3]=ST5_param[3]+1
                if key<last_rotary_position:
                    ST5_param[3]=ST5_param[3]-1
                if ST5_param[3]>len(ST5_menu)-1:
                    ST5_param[3]=0
                if ST5_param[3]<0:
                    ST5_param[3]=len(ST5_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if  (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
                update=True
                pwd=passwd
                ssid=ST5_menu[ST3_param[3]]
                STATE=50                
                
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update=True
                STATE=1 
                
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                STATE=0   

     case 50:#menu wifi passwd
        if update:
           set_passwd(pwd)
            
        if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=5       
            
        if (( (source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            pwd=pwd+"-"
            update=True
          
        if ( (source=="IR") and (key==40) ) : #touche square
            pwd=pwd[:-1]  
            update=True
            
        if ( (source=="IR") and (key==41) ) : #touche UP
            r=ord(pwd[len(pwd)-1])+1
            if r>126:
                r=32
            else:
                if r<32:
                    r=126
            pwd=pwd[:len(pwd)-1]+chr(r)
            update=True
            
        if ( (source=="IR") and (key==57) ) : #touche DOWN
            r=ord(pwd[len(pwd)-1])-1
            if r>126:
                r=32
            else:
                if r<32:
                    r=126
            pwd=pwd[:len(pwd)-1]+chr(r)
            update=True
                        
        if ( ((source=="IR") and (key==42)) or ((source=="clavier") and (key==5)) ) :
            passwd=pwd
            connect_to(ssid,passwd)

        if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100
 
        if ( (source=="IR") and (key==3) )  : 
            STATE=0   
 
     case 6:#menu IP
            if update:
                cmd = "ifconfig wlan0 | grep 'inet '"
                ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                output = ps.communicate()[0]
                output= output.decode("utf-8")
                output = re.split("inet",output)
                output=output[1]
                output = re.split("netmask",output)
                ST6_menu=[]
                ST6_menu.append(output[0])
                init_menu(ST6_param,ST6_menu)
                
            if (( (source=="IR") and (key==32) ) or ( (source=="clavier") and (key==9) )) : 
                update=True
                STATE=1 
                
            if  ((source=="IR") and (key==0) ):
                save=True
                STATE=100

            if ( (source=="IR") and (key==3) )  : 
                STATE=0 
                
     case 100:#écran de veille
            if save:
                save_params()
                save=False
            now=datetime.now()
            deltat=now-lastnow
            if (deltat.microseconds>950000):
                if player.is_playing():
                    player.stop()
                draw=ImageDraw.Draw(image_blanche)
                draw.rectangle((0, 0, width, height), outline=0, fill=0)
                draw.text((50,2),time_var[1],font=font100,size=1,fill=0)  
                draw.text((40,45),date_var[1],font=font100,size=1,fill=0)  
                set_time(1)
                draw.text((50,2),time_var[1],font=font100,size=1,fill=1)  
                draw.text((40,45),date_var[1],font=font100,size=1,fill=1)  
                oled.image(image_blanche)               
                oled.show()
                lastnow=now
            if ((source=="IR") and (key==0) ):
                STATE=0
 
except KeyboardInterrupt:
    save_params()
         
        
    
