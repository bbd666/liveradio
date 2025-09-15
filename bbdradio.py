#09/09/2025

import requests
import openmeteo_requests
import json
import pandas as pd
import requests_cache
from retry_requests import retry


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
from datetime import datetime,timedelta
import os
import subprocess
from pathlib import Path
import shutil
import busio

ssid=""
passwd=""
#Load URL's from the database
config = configparser.ConfigParser()
config.read('data.ini')
nb=config['STREAMS']['nb']
liste_url=[]
liste_lbl=[]
for i in range(1,int(nb)+1):
  liste_url.append(config['STREAMS']['url'+str(i)])
  liste_lbl.append(config['STREAMS']['lbl'+str(i)])
volume=int(config['RADIO SETTINGS']['volume'])
channel_ini=int(config['RADIO SETTINGS']['index'])
dtPin=int(config['RADIO SETTINGS']['pin_dt'])
clkPin=int(config['RADIO SETTINGS']['pin_clk'])
swPin=int(config['RADIO SETTINGS']['pin_sw'])
row_list=[int(config['RADIO SETTINGS']['pin_30']),int(config['RADIO SETTINGS']['pin_31']),int(config['RADIO SETTINGS']['pin_32'])]
col_list=[int(config['RADIO SETTINGS']['pin_33']),int(config['RADIO SETTINGS']['pin_34']),int(config['RADIO SETTINGS']['pin_35'])]
wiring_mode='MODIFIED'
wiring_mode=config['RADIO SETTINGS']['WIRING']
#wiring_mode : 'MODIFIED';'GENUINE';'REWELDED'

ssid=config['WIFI']['SSID']
passwd=config['WIFI']['PASSWD']
alarm_set=int(config['ALARM']['set'])
alarm_clck_hour=int(config['ALARM']['hour'])
alarm_clck_min=int(config['ALARM']['min'])
alarm_source=config['ALARM']['source']
jours_actifs=[False]*7
if (config['ALARM']['lundi']=='1'):
    jours_actifs[0]=True
if (config['ALARM']['mardi']=='1'):
    jours_actifs[1]=True
if (config['ALARM']['mercredi']=='1'):
    jours_actifs[2]=True
if (config['ALARM']['jeudi']=='1'):
    jours_actifs[3]=True
if (config['ALARM']['vendredi']=='1'):
    jours_actifs[4]=True
if (config['ALARM']['samedi']=='1'):
    jours_actifs[5]=True
if (config['ALARM']['dimanche']=='1'):
    jours_actifs[6]=True
meteo_location='liverdun'
meteo_location=config['METEO']['LOCATION']

url=liste_url[channel_ini]
protocole='rc-5'
protocole=config['REMOTE']['prtcl']

lcd_mode='I2C'
lcd_mode=config['LCD']['DISPLAY']

update_count=0
is_connected=True

def get_ir_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if (device.name == "gpio_ir_recv"):           
            return device          
dev = get_ir_device()

if (protocole=='nec') or (protocole=='keyes'):
    os.system('sh remote_nec.sh')
if protocole=='rc-5':
    os.system('sh remote_rc5.sh')
 
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


usb_path = "/dev/sda1"
mount_path = "/home/pierre/usb_disk_mount"
mp3_files=[]             
           
def get_weather_description(code: int) -> str:
    """Convert Open-Meteo weather code to a textual description."""
    if code == 0:
        return "Ciel clair"
    elif code in (1, 2, 3):
        return "Couvert"
    elif code in (45, 48):
        return "Brouillard"
    elif code in (51, 53, 55):
        return "Brume"
    elif code in (56, 57):
        return "Brouillard verglacant"
    elif code in (61, 63, 65):
        return "Pluie"
    elif code in (66, 67):
        return "pluie verglacante"
    elif code in (71, 73, 75):
        return "Chute de neige"
    elif code == 77:
        return "Flocons"
    elif code in (80, 81, 82):
        return "Averses"
    elif code in (85, 86):
        return "Giboulées de neige"
    elif code == 95:
        return "Orages"
    elif code in (96, 99):
        return "Orages avec grêle"
    else:
        return "Aucune prévision"

def get_meteo():
    global update
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    city=meteo_location
    result_city = requests.get(url='https://geocoding-api.open-meteo.com/v1/search?name=' + city)
    location = result_city.json()

    longitude=str(location['results'][0]['longitude'])
    latitude=str(location['results'][0]['latitude'])

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "precipitation", "precipitation_probability", "weather_code", "wind_speed_10m", "rain"],
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    #print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    #print(f"Elevation: {response.Elevation()} m asl")
    #print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(2).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_rain = hourly.Variables(5).ValuesAsNumpy()
    update=False
    return hourly
    

def display_meteo_prev(id,err):
    global width
    global height
    global oled
    global draw
    if (err):
        if hourly_weather_code[id] ==0:
            image_meteo=Image.open("meteo_icons/clair.jpg")
        elif hourly_weather_code[id] in (1, 2, 3):
            image_meteo=Image.open("meteo_icons/part_couvert.jpg")
        elif hourly_weather_code[id] in (45, 48):
            image_meteo=Image.open("meteo_icons/brouillard.jpg")
        elif hourly_weather_code[id] in (51, 53, 55):
            image_meteo=Image.open("meteo_icons/brume.jpg")
        elif hourly_weather_code[id] in (56, 57):
            image_meteo=Image.open("meteo_icons/brouillard-verg.jpg")
        elif hourly_weather_code[id] in (61, 63, 65):
            image_meteo=Image.open("meteo_icons/pluie.jpg")
        elif hourly_weather_code[id] in (66, 67):
            image_meteo=Image.open("meteo_icons/pluie-verg.jpg")
        elif hourly_weather_code[id] in (71, 73, 75):
            image_meteo=Image.open("meteo_icons/neige.jpg")
        elif hourly_weather_code[id] == 77:
            image_meteo=Image.open("meteo_icons/flocon.jpg")
        elif hourly_weather_code[id] in (80, 81, 82):
            image_meteo=Image.open("meteo_icons/averse.jpg")
        elif hourly_weather_code[id] in (85, 86):
            image_meteo=Image.open("meteo_icons/gib-neige.jpg")
        elif hourly_weather_code[id] == 95:
            image_meteo=Image.open("meteo_icons/orage.jpg")
        elif hourly_weather_code[id] in (96, 99):
            image_meteo=Image.open("meteo_icons/grele.jpg")
        else:
            image_meteo=Image.open("meteo_icons/na.jpg")
        image_r = image_meteo.resize((width,height), Image.LANCZOS)
        fond_meteo = image_r.convert("1")        
        draw=ImageDraw.Draw(fond_meteo)
        t=datetime.now()
        t=t+ timedelta(id//24,0)
        d=t.date() 
        h=f"{id%24:02d}"
        item=meteo_location[0:8]+' '+d.strftime(' %d, %b %Y')+' '+h+':00'
        draw.text((10,2),item,font=font4,size=1,fill=1)
        item='TEMPERATURE : '+str(f"{hourly_temperature_2m[id]:.2f}")+' deg°C'
        draw.text((10,12),item,font=font100,size=1,fill=1)
        item='PRECIPITATIONS : '+str(f"{hourly_precipitation[id]:.2f}")+' mm (prob : '+str(f"{hourly_precipitation_probability[id]:.2f}")+'%)'
        draw.text((10,22),item,font=font100,size=1,fill=1)
        item='VENT : '+str(f"{hourly_wind_speed_10m[id]:.2f}")+' km/h'
        draw.text((10,32),item,font=font100,size=1,fill=1)
        item=get_weather_description(hourly_weather_code[id])
        draw.text((10,42),item,font=font100,size=1,fill=1)
        item='heure '+h+':00 '
        draw.text((10,52),item,font=font4,size=1,fill=1)
    else:
        fond_meteo = Image.new('1',(128,64))
        draw=ImageDraw.Draw(fond_meteo)
        item='ERREUR: Lieu inexact'
        draw.text((10,32),item,font=font4,size=1,fill=1)
        item='ou serveur ne repond pas'
        draw.text((10,47),item,font=font4,size=1,fill=1)      
    oled.image(fond_meteo)
    oled.show()
         
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
    ch = "sudo nmcli device wifi connect "+ssid+" password "+password
    ch_mod=ch.split()
    try:
      proc = subprocess.run(
        ch_mod,
        stdout=subprocess.PIPE,
        input="topgun12",
        encoding="utf8",
      )
      print(f"Connecté à {ssid} : {proc.stdout.strip()}")
      return True
    except subprocess.CalledProcessError as e:
      print(f"Erreur nmcli : {e.stderr.strip()}")
      return False
    except Exception as e:
      print(f"Erreur système : {str(e)}")
      return False

def connect_to_saved(ssid: str):
    if not is_wifi_available(ssid):
        return False
    subprocess.call(['nmcli', 'c', 'up', ssid])
    return is_connected_to(ssid)
   
def trig_ir():
    global last_call
    event = dev.read_one()
    result=None
    if (event) :
        a = event.value
        if not(event.code==0):
           t=time.perf_counter()
           if t-last_call>1:
            last_call=t
            return a

GPIO.setmode(GPIO.BCM)
if (wiring_mode=='REWELDED'):
#poussoirs
    GPIO.setup(17, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(15, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(22, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(24, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(8, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(25, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(9, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(5, GPIO.IN, pull_up_down = GPIO.PUD_UP)
else:
# define PINs according to cabling
# following array matches 1,2,3,4 PINs from 4x4 Keypad Matrix
#boutons 30,31,32
# following array matches 5,6,7,8 PINs from 4x4 Keypad Matrix
#boutons 33,34,35
############ set row pins to output, all to high
    for pin in row_list:
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
############ set columns pins to input. We'll read user input here
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
      sleep(0.3)
      return(key)
    GPIO.output(r, GPIO.HIGH)

def clavier():
    appui=None
    etat=GPIO.input(17)
    if (etat==GPIO.LOW):
       appui='3'
    etat=GPIO.input(15)
    if (etat==GPIO.LOW):
       appui='6'
    etat=GPIO.input(23)
    if (etat==GPIO.LOW):
       appui='9'
    etat=GPIO.input(22)
    if (etat==GPIO.LOW):
       appui='2'
    etat=GPIO.input(24)
    if (etat==GPIO.LOW):
       appui='5'
    etat=GPIO.input(8)
    if (etat==GPIO.LOW):
       appui='8'
    etat=GPIO.input(25)
    if (etat==GPIO.LOW):
       appui='1'
    etat=GPIO.input(9)
    if (etat==GPIO.LOW):
       appui='4'
    etat=GPIO.input(5)
    if (etat==GPIO.LOW):
       appui='7'
    if not(appui==None):
       sleep(0.3)
    return appui

# define swPin read function when wiring_mode='GENUINE'
def swpinRead():
    global ROTARY_param
    GPIO.output(int(row_list[0]), GPIO.LOW)
    result=GPIO.input(swPin)
    if (result==0):
        key=0
        GPIO.output(int(row_list[0]), GPIO.HIGH) 
        globalCounter=0
        ROTARY_param[4]=0
        return(key)
    GPIO.output(int(row_list[0]), GPIO.HIGH)
    
time_var=["",""]
date_var=["",""] 
   
def set_time(arg):
    now = datetime.now()
    global time_var
    global date_var
    time_var[arg] = now.strftime('%H:%M:%S')
    date_var[arg] = now.strftime("%d/%m/%Y")      
                  
#Rotary encounter parameters
#borne 37
# CLK Pin
#borne 38
# DT Pin
#borne 36
# Button Pin
#Rotary encounter GPIO        
GPIO.setup(clkPin, GPIO.IN)    # input mode
GPIO.setup(dtPin, GPIO.IN)
GPIO.setup(swPin, GPIO.IN)

def rotaryDeal(arg):
   arg[1] = GPIO.input(dtPin)
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
    
def will_you_save(arg):
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
        draw.text((30,35),"Fichiers copies",font=font3,size=1,fill=1)
    else:
        if arg[1]==2:
            draw.text((30,35),"echec SAUVEGARDE",font=font3,size=1,fill=1)
        else:
            draw.text((5,5),"Lancement de la sauvegarde ?",font=font4,size=1,fill=1)
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
    
def draw_msg(arg):
    global update
    global image_blanche
    global oled
    global draw
    image_blanche = Image.new('1',(128,64))
    draw=ImageDraw.Draw(image_blanche)
    draw.text((10,35),arg,font=font100,size=1,fill=1)
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
    s="SCROLL ou fleches H/B : modif"
    draw.text((5,0),s,font=font200,size=1,fill=1)  
    s=" >>| : ajout"
    draw.text((5,10),s,font=font100,size=1,fill=1)  
    s=" |<< : suppr"
    draw.text((5,20),s,font=font100,size=1,fill=1)  
    s=">|| : valid"
    draw.text((5,30),s,font=font100,size=1,fill=1)  
    for i in range(len(arg)):
        draw.text(((5+10*i)%(width-10),45+10*((5+10*i)//(width-10))),str(arg[i]),font=font100,size=1,fill=1)  
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
    config.set('RADIO SETTINGS', 'index', schannel)
    config.set('RADIO SETTINGS', 'volume',sind )
    config.set('ALARM', 'set',str(alarm_set) )
    config.set('ALARM', 'hour',str(alarm_clck_hour) )
    config.set('ALARM', 'min',str(alarm_clck_min) )
    config.set('ALARM', 'source',alarm_source )
    if (jours_actifs[0]):
        config.set('ALARM', 'lundi','1')
    else:
        config.set('ALARM', 'lundi','0')
    if (jours_actifs[1]):
        config.set('ALARM', 'mardi','1')
    else:
        config.set('ALARM', 'mardi','0')
    if (jours_actifs[2]):
        config.set('ALARM', 'mercredi','1')
    else:
        config.set('ALARM', 'mercredi','0')        
    if (jours_actifs[3]):
        config.set('ALARM', 'jeudi','1')
    else:
        config.set('ALARM', 'jeudi','0')
    if (jours_actifs[4]):
        config.set('ALARM', 'vendredi','1')
    else:
        config.set('ALARM', 'vendredi','0')
    if (jours_actifs[5]):
        config.set('ALARM', 'samedi','1')
    else:
        config.set('ALARM', 'samedi','0')
    if (jours_actifs[6]):
        config.set('ALARM', 'dimanche','1')
    else:
        config.set('ALARM', 'dimanche','0')        
    config.set('WIFI', 'SSID',ssid )
    config.set('WIFI', 'PASSWD', passwd)
    with open('data.ini', 'w') as configfile:   
        config.write(configfile)
        
def scan_USB_files():
    global update_usb
    global usb_path
    global mount_path 
    global mp3_files
    os.system('sh get_usb_dev.sh')
    f=open("dev_usb.txt")
    usb_path=f.readline().strip('\n')
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
    os.system('sh get_usb_dev.sh')
    f=open("dev_usb.txt")
    usb_path=f.readline().strip('\n')
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
    
def save_config(arg):
    global usb_path
    global mount_path 
    os.system('sh get_usb_dev.sh')
    f=open("dev_usb.txt")
    usb_path=f.readline().strip('\n')
    subprocess.run(["sudo", "mount", usb_path, mount_path])
    p = Path(mount_path)
    if p.is_mount():
        my_file_target = p/arg
        my_file="/home/pierre/"+arg
        #shutil.copyfile(my_file,my_file_target)
        os.system('sudo cp ' +str(my_file) +'  '+ str(my_file_target) )       
        return 1
    else:
        return 0
    subprocess.run(["sudo", "umount", mount_path])
  
if (lcd_mode=='I2C'):
#------------------------- protocole I2C-------------------------------------------------------------------  
    SCL=3
    SDA=2
    i2c = busio.I2C(SCL, SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
#------------------------- protocole SPI-------------------------------------------------------------------  
else:
    oled=adafruit_ssd1306.SSD1306_SPI(128,64,board.SPI(),digitalio.DigitalInOut(board.D22),digitalio.DigitalInOut(board.D27),digitalio.DigitalInOut(board.D8)) 
#----------------------------------------------------------------------------------------------------------  

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
image = Image.open("logo_connected.jpg")
image_r = image.resize((width,height), Image.LANCZOS)
image_bw = image_r.convert("1")
oled.image(image_bw_connected)
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
   
ST1_param=[4,0,0,0]#nb_lignes,shiftbloc,decal,fillindex
ST1_menu=["WEB STATIONS","ALARME","WIFI","USB","ADRESSE IP","METEO"]
ST2_param=[4,0,0,channel_ini]
ST2_menu=liste_lbl
ST3_param=[4,0,0,0]
ST3_menu=["ACTIVATION","REGLAGE","SOURCE SONORE","MELODIES","JOURS ACTIFS"]
ST100_param=[0,0,0,0]
ST100_menu=[]
ST5_param=[4,0,0,0]
ST5_menu=[]
ST4_param=[4,0,0,0]
ST4_menu=["MEDIAS","MAJ SYSTEME","MAJ CONFIG","SAUVEGARDE"]
ST41_param=[4,0,0,0]
ST41_menu=[]
ST6_param=[4,0,0,0]
ST6_menu=[]
ST7_param=[4,0,0,0]
ST8_param=[4,0,0,0]
ST8_menu=["LOCALISATION","PREVISIONS"]


def update_alarm_days(arg,items):
    global update
    global image_blanche
    global width
    global height
    global oled
    global draw
    days=["LUNDI","MARDI","MERCREDI","JEUDI","VENDREDI","SAMEDI","DIMANCHE"]
    image_blanche = Image.new('1',(128,64))
    draw=ImageDraw.Draw(image_blanche)
    arg[1]=arg[3]//arg[0]   #n° de bloc de 4 lignes
    arg[2]=arg[3]%arg[0]    #n° de ligne (entre 0 et 3)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.rectangle((0, 2+arg[2]*15, 70, (arg[2]+1)*15), outline=1, fill=1)            
    for i in range(0,arg[0]):
        if i+arg[1]*arg[0]<len(days):
            if (items[i+arg[1]*arg[0]]==True):
                draw.text((90,2+i*15),'*',font=font3,size=1,fill=1)  
            if i+arg[1]*arg[0]==arg[3] :
                draw.text((10,2+i*15),days[i+arg[1]*arg[0]],font=font3,size=1,fill=0)  
            else :
                draw.text((10,2+i*15),days[i+arg[1]*arg[0]],font=font3,size=1,fill=1)
    oled.image(image_blanche)
    oled.show()
    update=False
    
STATE=0
digit_sel=0
last_rotary_position=ROTARY_param[3]
last_call=0
action=''

if (not(passwd=="") and (not(ssid==""))):
  connect_to(ssid,passwd)

try:
 while True:
            
    key=trig_ir()
    source="IR"
    if key==None: 
        if (wiring_mode=='REWELDED'):
            key=clavier()
        else:
            key=Keypad4x4Read(col_list, row_list)
        source="clavier"
    
    if key==None: 
        if (wiring_mode=='GENUINE'):
            key=swpinRead()
            if key != None:
                ROTARY_param[4]=0
                source="clavier"
                sleep(0.3)   
        else:
            #wiring_mode=='MODIFIED'
            det=GPIO.input(swPin)
            if (det==0):
                 globalCounter=0      
                 source="rotary"
                 key=0
                 ROTARY_param[4]=0
                 sleep(0.3)

    if (key==None):       
        counter=ROTARY_param[3]
        rotaryDeal(ROTARY_param)
        if not(counter==ROTARY_param[3]):
         source="rotary"
         key=ROTARY_param[3]
         ROTARY_param[4]=-1
        else:
         source=""
         
    if not(key==None):
        print(source)
        print(key)   
    
    if protocole=='rc-5':
        action=''
        if (((source=="IR") and (key==3)) or ((source=="clavier") and (key=='6'))) :
            action='home'
        if  (((source=="IR") and (key==0) ) or ((source=="clavier") and (key=='3'))):
            action='logout'
        if ((source=="rotary") and (ROTARY_param[4]==-1)):
            action='scroll'
        if ( (source=="IR") and (key==40)) :
            action='square'
        if ( (source=="IR") and (key==43) ) :
            action='vol+'
        if ( (source=="IR") and (key==51) ) :
            action='vol-'
        if ( ((source=="IR") and (key==42)) or ((source=="clavier") and (key=='5')) ) :
            action='play'
        if ( ((source=="IR") and (key==57)) ):
            action='arrow-'
        if ( ((source=="IR") and (key==41)) ):
            action='arrow+'
        if ( ((source=="IR") and (key==48))or ((source=="clavier") and (key=='2')) ):
            action='arrow--'
        if ( ((source=="IR") and (key==50))or ((source=="clavier") and (key=='8')) ):
            action='arrow++'
        if (((source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            action='select'
        if ( ((source=="IR") and (key==32)) or ((source=="clavier") and (key=='9')) ) : 
            action='back'
        if ( (source=="clavier") and (key=='1') ) :
            action='prev'
        if ( (source=="clavier") and (key=='7') ) :
            action='next'
        #print('back')
 
    if protocole=='nec':
        action=''
        if ( ((source=="IR") and (key==538)) or ((source=="clavier") and (key=='6')) ) :
            action='home'
        if  (((source=="IR") and (key==516) ) or ((source=="clavier") and (key=='3'))):
            action='logout'
        if ((source=="rotary") and (ROTARY_param[4]==-1)):
            action='scroll'
        if ( (source=="IR") and (key==520)) :
            action='square'
        if ( (source=="IR") and (key==518) ) :
            action='vol+'
        if ( (source=="IR") and (key==517) ) :
            action='vol-'
        if ( ((source=="IR") and (key==512)) or ((source=="clavier") and (key=='5')) ) :
            action='play'
        if ( ((source=="IR") and (key==513))or ((source=="clavier") and (key=='2')) ):
            action='arrow-'
        if ( ((source=="IR") and (key==514))or ((source=="clavier") and (key=='8')) ):
            action='arrow+'
        if (((source=="IR") and (key==536)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            action='select'
        if (( (source=="IR") and (key==521)  ) or ( (source=="clavier") and (key=='9') )) : 
            action='back'
        if ( (source=="clavier") and (key=='1') ) :
            action='prev'
        if ( (source=="clavier") and (key=='7') ) :
            action='next'
            
    if protocole=='keyes':
        action=''
        if ( ((source=="IR") and (key==74)) or ((source=="clavier") and (key=='6')) ) :
            action='home'
        if  (((source=="IR") and (key==82) ) or ((source=="clavier") and (key=='3'))):
            action='logout'
        if ((source=="rotary") and (ROTARY_param[4]==-1)):
            action='scroll'
        if ( (source=="IR") and (key==8)) :
            action='square'
        if ( (source=="IR") and (key==70) ) :
            action='vol+'
        if ( (source=="IR") and (key==21) ) :
            action='vol-'
        if ( ((source=="IR") and (key==28)) or ((source=="clavier") and (key=='5')) ) :
            action='play'
        if ( ((source=="IR") and (key==67))or ((source=="clavier") and (key=='2')) ):
            action='arrow-'
        if ( ((source=="IR") and (key==68))or ((source=="clavier") and (key=='8')) ):
            action='arrow+'
        if (((source=="IR") and (key==64)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            action='select'
        if (( (source=="IR") and (key==66)  ) or ( (source=="clavier") and (key=='9') )) : 
            action='back'
        if ( (source=="clavier") and (key=='1') ) :
            action='prev'
        if ( (source=="clavier") and (key=='7') ) :
            action='next'
            
    now=datetime.now()
    
    if ((alarm_set==1) and (jours_actifs[now.weekday()]==True) and (now.hour==alarm_clck_hour) and (now.minute==alarm_clck_min) and (now.second<20) ):
        if not(player.is_playing()):
            player.set_mrl(alarm_source)
            player.play()
            player.audio_set_volume(volume)
            STATE=0

    match STATE:
     case 0:#ecran d'accueil                
            now=datetime.now()
            deltat=now-lastnow
            if (deltat.microseconds>950000):
                update_count=(update_count+1)%30
                if (update_count==0):
                    is_connected=is_connected_to(ssid)
                if is_connected:
                    draw=ImageDraw.Draw(image_bw_connected)
                else:
                    draw=ImageDraw.Draw(image_bw)                
                draw.text((55,2),time_var[0],font=font1,size=1,fill=0)  
                draw.text((40,45),date_var[0],font=font2,size=1,fill=0)  
                set_time(0)
                draw.text((55,2),time_var[0],font=font1,size=1,fill=1)  
                draw.text((40,45),date_var[0],font=font2,size=1,fill=1)  
                if is_connected:
                    oled.image(image_bw_connected)
                else:
                    oled.image(image_bw)
                oled.show()
                lastnow=now            
            
            if  (action=='select'):
                update=True                
                STATE=1
                
            if  (action=='logout' ):
                save=True
                STATE=100
                
            if (action=='scroll'):
                if key>last_rotary_position:
                    volume=min(volume+1,200)
                if key<last_rotary_position:
                    volume=max(volume-1,0)
                sound_box(volume)
                player.audio_set_volume(volume)
                last_rotary_position=ROTARY_param[3]
                
            if ( action=='vol+' ):
                volume=min(volume+5,200)
                sound_box(volume)
                player.audio_set_volume(volume)
                
            if ( action=='vol-' ):
                volume=max(volume-5,0)
                sound_box(volume)
                player.audio_set_volume(volume)
 
            if (action=='play'):
                if not(player.is_playing()):
                    player.play()
                    player.audio_set_volume(volume)
                else:
                    player.pause()                   
                
     case 1:#menus principaux
            if update==True:
               init_menu(ST1_param,ST1_menu)           
   
            if ( action=='arrow-' ) :
                ST1_param[3]=ST1_param[3]+1
                if ST1_param[3]>len(ST1_menu)-1:
                    ST1_param[3]=0
                update=True
                
            if ( action=='arrow+' ) :
                ST1_param[3]=ST1_param[3]-1
                if ST1_param[3]<0:
                    ST1_param[3]=len(ST1_menu)-1
                update=True
                
            if (action=='scroll'):
                print('scroll')
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
                    
            if (ST1_param[3]==0 and (action=='select')) :
                update=True
                STATE=2         #web radio
                
            if (ST1_param[3]==1 and (action=='select')) :
                update=True
                STATE=3         #alarm
                
            if (ST1_param[3]==2 and (action=='select')) :
                update=True
                STATE=5         #wifi                              
                
            if (ST1_param[3]==3 and (action=='select')) :
                update=True
                STATE=4         #USB
                
            if (ST1_param[3]==4 and (action=='select')) :
                update=True
                STATE=6         #IP
 
            if (ST1_param[3]==5 and (action=='select')) :
                update=True
                STATE=7         #METEO
 
            if (action=='back') : 
                STATE=0
                            
            if (action=='home') : 
                STATE=0   
                               
            if  (action=='logout' ):
                save=True
                STATE=100
  
     case 2:#menus web radios
            if update:
                init_menu(ST2_param,ST2_menu)

            if ( action=='arrow-' ) :
                ST2_param[3]=ST2_param[3]+1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                update=True
                
            if ( action=='arrow+' ) :
                ST2_param[3]=ST2_param[3]-1
                if ST2_param[3]<0:
                    ST2_param[3]=len(ST2_menu)-1
                update=True
                
            if (action=='scroll'):
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

            if (action=='select' ) :
                url=liste_url[ST2_param[3]]
                player.set_mrl(url)
                channel_ini=ST2_param[3]
                player.play()
                
            if ( action=='vol+') :
                volume=min(volume+5,200)
                sound_box(volume)
                player.audio_set_volume(volume)
                update=True
                
            if ( action=='vol-') :
                volume=max(volume-5,0)
                sound_box(volume)
                player.audio_set_volume(volume)
                update=True
                
            if (action=='back') : 
                STATE=1            
                update=True
                
            if (action=='home')  : 
                STATE=0   

            if (action=='logout'):
                save=True
                STATE=100
  
     case 3:#menus settings alarme
            if update:
                init_menu(ST3_param,ST3_menu)

            if ( action=='arrow-' ) :
                ST3_param[3]=ST3_param[3]+1
                if ST3_param[3]>len(ST3_menu)-1:
                    ST3_param[3]=0
                update=True
            if ( action=='arrow+') :
                ST3_param[3]=ST3_param[3]-1
                if ST3_param[3]<0:
                    ST3_param[3]=len(ST3_menu)-1
                update=True
                
            if (action=='scroll'):
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

            if (ST3_param[3]==0 and (action=='select') ) :
                update=True
                STATE=30
                
            if (ST3_param[3]==1 and (action=='select') ) :
                update=True
                digit_sel=0
                STATE=31     
                
            if (ST3_param[3]==2 and (action=='select' )) :
               update=True
               STATE=32
                
            if (ST3_param[3]==3 and (action=='select')) :
                update=True
                STATE=33

            if (ST3_param[3]==4 and (action=='select')) :
                update=True
                STATE=34
                
            if (action=='back' ) : 
                update=True
                STATE=1 
                
            if  (action=='logout') :
                save=True
                STATE=100

            if ( action=='home')  : 
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
            
        if (action=='back' ) :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=3               
            
        if (action=='select') :
            if alarm_set==1:
                alarm_set=0 
            else:
                alarm_set=1
            update=True
            
        if  (action=='logout'):
                save=True
                STATE=100

        if (action=='home')  : 
            STATE=0   
            
     case 31:#menus reglage alarme
        if update:
            h=[alarm_clck_hour//10,alarm_clck_hour%10,alarm_clck_min//10,alarm_clck_min%10,digit_sel]
            set_hour(h)
            
        if (action=='back') :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=3       
            
        if (action=='select' ) :
            digit_sel=(digit_sel+1)%4
            update=True
            
        if (( action=='arrow+' ) or ( action=='arrow++' )):
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
            
        if (( action=='arrow-' ) or ( action=='arrow--' )):
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
                        
        if  (action=='logout' ):
                save=True
                STATE=100
 
        if ( action=='home' )  : 
            STATE=0   
 
     case 32:#menus selection source alarme
            if update:
                init_menu(ST2_param,ST2_menu)

            if ( action=='arrow-' ) :
                ST2_param[3]=ST2_param[3]+1
                if ST2_param[3]>len(ST2_menu)-1:
                    ST2_param[3]=0
                update=True
                
            if ( action=='arrow+' ) :
                ST2_param[3]=ST2_param[3]-1
                if ST2_param[3]<0:
                    ST2_param[3]=len(ST2_menu)-1
                update=True                
                
            if (action=='scroll'):
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

            if ( action=='select' ) :
                alarm_source=liste_url[ST2_param[3]]

            if (action=='back') : 
                update=True
                STATE=3            

            if  (action=='logout'):
                save=True
                STATE=100
                
            if ( action=='home' )  : 
                STATE=0   

     case 33:#menus selection melodie
            if update:
                init_menu(ST_melodies,liste_melodies)

            if ( action=='arrow-' ) :
                ST_melodies[3]=ST_melodies[3]+1
                if ST_melodies[3]>len(liste_melodies)-1:
                    ST_melodies[3]=0
                update=True
                
            if ( action=='arrow+' ) :
                ST_melodies[3]=ST_melodies[3]-1
                if ST_melodies[3]<0:
                    ST_melodies[3]=len(liste_melodies)-1
                update=True                
                
            if (action=='scroll'):
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

            if ( action=='select' ) :
                alarm_source=liste_melodies[ST_melodies[3]]

            if (action=='back') : 
                update=True
                STATE=3            

            if  (action=='logout'):
                save=True
                STATE=100
                
            if ( action=='home' )  : 
                STATE=0   

     case 34:#menus selection jours de la semaine
            if update:
                update_alarm_days(ST7_param,jours_actifs)

            if ( action=='arrow-' ) :
                ST7_param[3]=ST7_param[3]+1
                if ST7_param[3]>len(jours_actifs)-1:
                    ST7_param[3]=0
                update=True
                
            if ( action=='arrow+' ) :
                ST7_param[3]=ST7_param[3]-1
                if ST7_param[3]<0:
                    ST7_param[3]=len(jours_actifs)-1
                update=True                
                
            if (action=='scroll'):
                if key>last_rotary_position:
                    ST7_param[3]=ST7_param[3]+1
                if key<last_rotary_position:
                    ST7_param[3]=ST7_param[3]-1
                if ST7_param[3]>len(jours_actifs)-1:
                    ST7_param[3]=0
                if ST7_param[3]<0:
                    ST7_param[3]=len(jours_actifs)-1
                last_rotary_position=ROTARY_param[3]
                update=True

            if ( action=='select' ) :
                if (jours_actifs[ST7_param[3]]):
                    jours_actifs[ST7_param[3]]=False
                else:
                    jours_actifs[ST7_param[3]]=True
                update=True

            if (action=='back') : 
                update=True
                STATE=3            

            if  (action=='logout'):
                save=True
                STATE=100
                
            if ( action=='home' )  : 
                STATE=0   
                
     case 4:#menu USB
            if update:
                init_menu(ST4_param,ST4_menu)

            if ( action=='arrow-' ) :
                ST4_param[3]=ST4_param[3]+1
                if ST4_param[3]>len(ST4_menu)-1:
                    ST4_param[3]=0
                update=True
            if ( action=='arrow+' ) :
                ST4_param[3]=ST4_param[3]-1
                if ST4_param[3]<0:
                    ST4_param[3]=len(ST4_menu)-1
                update=True
                
            if (action=='scroll'):
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

            if (ST4_param[3]==0 and (action=='select')) :
                update=True
                update_usb=True
                STATE=41
                
            if (ST4_param[3]==1 and (action=='select')) :
                update=True
                rep=[0,0]
                STATE=42     

            if (ST4_param[3]==2 and (action=='select')) :
                update=True
                rep=[0,0]
                STATE=43     

            if (ST4_param[3]==3 and (action=='select')) :
                update=True
                rep=[0,0]
                STATE=44   
                
            if (action=='back') : 
                update=True
                STATE=1 
                
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0   

     case 41:#menu USB Medias
            if update_usb:
                s=scan_USB_files()
                ST41_menu=[]
                for i in range(0,len(mp3_files)):
                    ST41_menu.append(mp3_files[i].name)
            if update:
                init_menu(ST41_param,ST41_menu)

            if ( action=='arrow-' ) :
                ST41_param[3]=ST41_param[3]+1
                if ST41_param[3]>len(ST41_menu)-1:
                    ST41_param[3]=0
                update=True
            if ( action=='arrow+' ) :
                ST41_param[3]=ST41_param[3]-1
                if ST41_param[3]<0:
                    ST41_param[3]=len(ST41_menu)-1
                update=True
                
            if (action=='scroll'):
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

            if  (action=='select') :
                if (len(mp3_files)>ST41_param[3]):
                    url=mp3_files[ST41_param[3]]
                    player.set_mrl(url)
                    player.play()
                
            if (action=='back') : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
                
            if  (action=='logout'):
                update_usb=True
                save=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=100

            if ( action=='home' )  : 
                update_usb=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=0   

     case 42:#menu USB MAJ SYSTEME
            if update:
                will_you_load(rep)

            if ( action=='arrow-' ) :
                update=True
                rep[0]=(rep[0]+1)%2
                will_you_load(rep)

            if ( action=='arrow+' ) :
                update=True
                rep[0]=(rep[0]-1)%2
                will_you_load(rep)
               
            if (action=='scroll'):
                if key>last_rotary_position:
                    rep[0]=(rep[0]+1)%2
                if key<last_rotary_position:
                    rep[0]=(rep[0]-1)%2
                update=True
                last_rotary_position=ROTARY_param[3]
                will_you_load(rep)

            if  (action=='select') :
                update=True
                if rep[0]==0:
                    err=load_config("bbdradio.py")
                    if (err==1):
                        rep[1]=1
                        will_you_load(rep)
                    else:
                        rep[1]=2
                        will_you_load(rep)
                else:
                    STATE=1
 
            if (action=='back') : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
 
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0   

     case 43:#menu USB MAJ CONFIG
            if update:
                will_you_load(rep)

            if ( action=='arrow-' ) :
                update=True
                rep[0]=(rep[0]+1)%2
                will_you_load(rep)

            if ( action=='arrow+' ) :
                update=True
                rep[0]=(rep[0]-1)%2
                will_you_load(rep)
               
            if (action=='scroll'):
                if key>last_rotary_position:
                    rep[0]=(rep[0]+1)%2
                if key<last_rotary_position:
                    rep[0]=(rep[0]-1)%2
                update=True
                last_rotary_position=ROTARY_param[3]
                will_you_load(rep)

            if  (action=='select') :
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
 
            if (action=='back') : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
 
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0   

     case 44:#menu USB SAUVEGARDE
            if update:
                will_you_save(rep)

            if ( action=='arrow-' ) :
                update=True
                rep[0]=(rep[0]+1)%2
                will_you_save(rep)

            if ( action=='arrow+' ) :
                update=True
                rep[0]=(rep[0]-1)%2
                will_you_save(rep)
               
            if (action=='scroll'):
                if key>last_rotary_position:
                    rep[0]=(rep[0]+1)%2
                if key<last_rotary_position:
                    rep[0]=(rep[0]-1)%2
                update=True
                last_rotary_position=ROTARY_param[3]
                will_you_save(rep)

            if  (action=='select') :
                update=True
                if rep[0]==0:
                    err1=save_config("data.ini")
                    err2=save_config("bbdradio.py")
                    if (err1==1) and (err2==1):
                        rep[1]=1
                        will_you_save(rep)
                    else:
                        rep[1]=2
                        will_you_save(rep)
                else:
                    STATE=1
 
            if (action=='back') : 
                update_usb=True
                update=True
                subprocess.run(["sudo", "umount", mount_path])
                STATE=1 
 
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0   

     case 5:#menu wifi
            if update:
                s=scan_wifi()
                ST5_menu=[]
                for i in range(0,len(s)):
                    w=s[i].split(":")
                    ST5_menu.append(w[0])
                init_menu(ST5_param,ST5_menu)

            if ( action=='arrow-' ) :
                ST5_param[3]=ST5_param[3]+1
                if ST5_param[3]>len(ST5_menu)-1:
                    ST5_param[3]=0
                update=True
            if ( action=='arrow+' ) :
                ST5_param[3]=ST5_param[3]-1
                if ST5_param[3]<0:
                    ST5_param[3]=len(ST5_menu)-1
                update=True
                
            if (action=='scroll'):
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

            if  (action=='select') :
                update=True
                pwd=passwd
                ssid=ST5_menu[ST3_param[3]]
                STATE=50                
                
            if (action=='back') : 
                update=True
                STATE=1 
                
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0   

     case 50:#menu wifi passwd
        if update:
           set_passwd(pwd)
            
        if (action=='back') :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=5       
                                 
        if ( action=='arrow++' ) : #touche UP
            pwd=pwd+"-"
            update=True
            
        if ( action=='arrow--' ) : #touche DOWN
            pwd=pwd[:-1]  
            update=True
                        
        if (action=='scroll'):
            if len(pwd)>0:
                if key>last_rotary_position:
                    r=ord(pwd[len(pwd)-1])+1
                if key<last_rotary_position:
                    r=ord(pwd[len(pwd)-1])-1
                if r>126:
                    r=32
                else:
                    if r<32:
                        r=126
                pwd=pwd[:len(pwd)-1]+chr(r)
                last_rotary_position=ROTARY_param[3]
                update=True
                
        if (action=='arrow+') : 
            if len(pwd)>0:
                r=ord(pwd[len(pwd)-1])+1
                if r>126:
                    r=32
                else:
                    if r<32:
                        r=126
                pwd=pwd[:len(pwd)-1]+chr(r)
                update=True
            
        if (action=='arrow-') : 
            if len(pwd)>0:
                r=ord(pwd[len(pwd)-1])-1
                if r>126:
                    r=32
                else:
                    if r<32:
                        r=126
                pwd=pwd[:len(pwd)-1]+chr(r)
                update=True
            
        if ( action=='play' ) :
            passwd=pwd
            res=connect_to(ssid,passwd)
            if (res):
                s="connecté à : "+ssid
                draw_msg(s)
            else:
                s="echec connection"
                draw_msg(s)
                
        if  (action=='logout'):
                save=True
                STATE=100
 
        if ( action=='home' )  : 
            STATE=0   
 
     case 6:#menu IP
            if update:
              try:
                os.system('sh get_ip.sh')
                f=open("ip.txt")
                ip=f.readline().strip('\n')
                ST6_menu=[]
                ST6_menu.append(ip)
                init_menu(ST6_param,ST6_menu)
              except:
                print('error')
                STATE=1   
                 
            if (action=='back') : 
                update=True
                STATE=1 
                
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0 
                
     case 7:#menus METEO
            if update:
                init_menu(ST8_param,ST8_menu)

            if ( action=='arrow-' ) :
                ST8_param[3]=ST8_param[3]+1
                if ST8_param[3]>len(ST8_menu)-1:
                    ST8_param[3]=0
                update=True
                
            if ( action=='arrow+' ) :
                ST8_param[3]=ST8_param[3]-1
                if ST8_param[3]<0:
                    ST8_param[3]=len(ST8_menu)-1
                update=True
                
            if (action=='scroll'):
                if key>last_rotary_position:
                    ST8_param[3]=ST8_param[3]+1
                if key<last_rotary_position:
                    ST8_param[3]=ST8_param[3]-1
                if ST8_param[3]>len(ST8_menu)-1:
                    ST8_param[3]=0
                if ST8_param[3]<0:
                    ST8_param[3]=len(ST8_menu)-1
                last_rotary_position=ROTARY_param[3]
                update=True
                
            if (ST8_param[3]==0 and (action=='select')) :
                update=True
                meteo_loc=meteo_location
                STATE=71         #METEO change Location

            if (ST8_param[3]==1 and (action=='select')) :
                update=True
                meteo_prev_id=0
                STATE=72         #METEO previsions
                
            if ( action=='vol+') :
                volume=min(volume+5,200)
                sound_box(volume)
                player.audio_set_volume(volume)
                update=True
                
            if ( action=='vol-') :
                volume=max(volume-5,0)
                sound_box(volume)
                player.audio_set_volume(volume)
                update=True
                
            if (action=='back') : 
                STATE=1            
                update=True
                
            if (action=='home')  : 
                STATE=0   

            if (action=='logout'):
                save=True
                STATE=100

     case 71:#menu METEO change location
        if update:
           set_passwd(meteo_loc)
            
        if (action=='back') :            
            update=True
            last_rotary_position=ROTARY_param[3]
            STATE=7       
                                 
        if ( action=='arrow+' ) : #touche UP
            meteo_loc=meteo_loc+"-"
            update=True
            
        if ( action=='arrow-' ) : #touche DOWN
            meteo_loc=meteo_loc[:-1]  
            update=True
                        
        if (action=='scroll'):
            if len(meteo_loc)>0:
                if key>last_rotary_position:
                    r=ord(meteo_loc[len(meteo_loc)-1])+1
                if key<last_rotary_position:
                    r=ord(meteo_loc[len(meteo_loc)-1])-1
                if r>126:
                    r=32
                else:
                    if r<32:
                        r=126
                meteo_loc=meteo_loc[:len(meteo_loc)-1]+chr(r)
                last_rotary_position=ROTARY_param[3]
                update=True
                
        if (action=='arrow++') : 
            if len(meteo_loc)>0:
                r=ord(meteo_loc[len(meteo_loc)-1])+1
                if r>126:
                    r=32
                else:
                    if r<32:
                        r=126
                meteo_loc=meteo_loc[:len(meteo_loc)-1]+chr(r)
                update=True
            
        if (action=='arrow--') : 
            if len(meteo_loc)>0:
                r=ord(meteo_loc[len(meteo_loc)-1])-1
                if r>126:
                    r=32
                else:
                    if r<32:
                        r=126
                meteo_loc=meteo_loc[:len(meteo_loc)-1]+chr(r)
                update=True
            
        if ( action=='play' ) :
            meteo_location=meteo_loc
                
        if  (action=='logout'):
                save=True
                STATE=100
 
        if ( action=='home' )  : 
            STATE=0   

     case 72:#menu METEO previsions
            if update:
              try:
                h=get_meteo()
                hourly_temperature_2m = h.Variables(0).ValuesAsNumpy()
                hourly_precipitation = h.Variables(1).ValuesAsNumpy()
                hourly_precipitation_probability = h.Variables(2).ValuesAsNumpy()
                hourly_weather_code = h.Variables(3).ValuesAsNumpy()
                hourly_wind_speed_10m = h.Variables(4).ValuesAsNumpy()
                hourly_rain = h.Variables(5).ValuesAsNumpy()
                err=True
                display_meteo_prev(meteo_prev_id,err)
              except:
                 err=False
                 display_meteo_prev(meteo_prev_id,err)  
              update=False 
              
            if ( action=='arrow-' ) :
                    meteo_prev_id=meteo_prev_id-1
                    if meteo_prev_id==-1:
                        meteo_prev_id=167                     
                    meteo_prev_id=meteo_prev_id%len(hourly_temperature_2m)
                    display_meteo_prev(meteo_prev_id,err)
                    update=True

            if ( action=='arrow+' ) :
                    meteo_prev_id=meteo_prev_id+1
                    if meteo_prev_id==167:
                        meteo_prev_id=0                    
                    meteo_prev_id=meteo_prev_id%len(hourly_temperature_2m)
                    display_meteo_prev(meteo_prev_id,err)
                    update=True
                
            if ( action=='arrow--' ) :
                    meteo_prev_id=meteo_prev_id-12
                    if meteo_prev_id==-1:
                        meteo_prev_id=167                     
                    meteo_prev_id=meteo_prev_id%len(hourly_temperature_2m)
                    display_meteo_prev(meteo_prev_id,err)
                    update=True
                    
            if ( action=='arrow++' ) :
                    meteo_prev_id=meteo_prev_id+12
                    if meteo_prev_id==167:
                        meteo_prev_id=0                    
                    meteo_prev_id=meteo_prev_id%len(hourly_temperature_2m)
                    display_meteo_prev(meteo_prev_id,err)
                    update=True

            if (action=='scroll'):
                if key>last_rotary_position:
                    meteo_prev_id=meteo_prev_id+1
                    if meteo_prev_id==167:
                        meteo_prev_id=0                    
                    meteo_prev_id=meteo_prev_id%len(hourly_temperature_2m)
                if key<last_rotary_position:
                    meteo_prev_id=meteo_prev_id-1
                    if meteo_prev_id==-1:
                        meteo_prev_id=167                     
                    meteo_prev_id=meteo_prev_id%len(hourly_temperature_2m)
                last_rotary_position=ROTARY_param[3]
                display_meteo_prev(meteo_prev_id,err)
                update=True

            if (action=='back') : 
                update=True
                STATE=7 
                
            if  (action=='logout'):
                save=True
                STATE=100

            if ( action=='home' )  : 
                STATE=0 
                                
     case 100:#écran de veille
            if save:
                save_params()
                save=False
            now=datetime.now()
            deltat=now-lastnow
            if (deltat.microseconds>950000):
                player.audio_set_volume(0)            
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
            if (action=='logout' ):
                STATE=0
 
except KeyboardInterrupt:
    print("fin")
         
        
    