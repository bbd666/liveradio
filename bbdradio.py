
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

ssid=config['WIFI']['SSID']
passwd=config['WIFI']['PASSWD']
alarm_set=int(config['ALARM']['set'])
alarm_clck_hour=int(config['ALARM']['hour'])
alarm_clck_min=int(config['ALARM']['min'])
alarm_source=config['ALARM']['source']
url=liste_url[channel_ini]
protocole='rc-5'
protocole=config['REMOTE']['prtcl']

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

# define PINs according to cabling
# following array matches 1,2,3,4 PINs from 4x4 Keypad Matrix
#boutons 30,31,32
# following array matches 5,6,7,8 PINs from 4x4 Keypad Matrix
#boutons 33,34,35


# set row pins to output, all to high
GPIO.setmode(GPIO.BCM)
for pin in row_list:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, GPIO.HIGH)

#set columns pins to input. We'll read user input here
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
    s="btn SCROLL: modif, >>| : ajout"
    #s=chr(708)+","+chr(709)+": modif, 'Select:' ajout"
    draw.text((5,5),s,font=font100,size=1,fill=1)  
    s="|<< : suppr, >|| : valid"
    #s=chr(1)+": suppr, "+">||: valid"
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
    config.set('RADIO SETTINGS', 'index', schannel)
    config.set('RADIO SETTINGS', 'volume',sind )
    config.set('ALARM', 'set',str(alarm_set) )
    config.set('ALARM', 'hour',str(alarm_clck_hour) )
    config.set('ALARM', 'min',str(alarm_clck_min) )
    config.set('ALARM', 'source',alarm_source )
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
  
#------------------------- protocole I2C-------------------------------------------------------------------  
SCL=3
SDA=2
i2c = busio.I2C(SCL, SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
#------------------------- protocole SPI-------------------------------------------------------------------  
#oled=adafruit_ssd1306.SSD1306_SPI(128,64,board.SPI(),digitalio.DigitalInOut(board.D22),digitalio.DigitalInOut(board.D27),digitalio.DigitalInOut(board.D8)) 
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
last_call=0
action=''

if (not(passwd=="") and (not(ssid==""))):
  connect_to(ssid,passwd)

try:
 while True:
            
    key=trig_ir()
    source="IR"
    if key==None: 
        key=Keypad4x4Read(col_list, row_list)
        source="clavier"

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
        if ( ((source=="IR") and (key==40)) or ((source=="clavier") and (key=='7'))) :
            action='square'
        if ( (source=="IR") and (key==43) ) :
            action='vol+'
        if ( (source=="IR") and (key==51) ) :
            action='vol-'
        if ( ((source=="IR") and (key==42)) or ((source=="clavier") and (key=='5')) ) :
            action='play'
        if ( ((source=="IR") and (key==57))or ((source=="clavier") and (key=='2')) ):
            action='arrow-'
        if ( ((source=="IR") and (key==41))or ((source=="clavier") and (key=='8')) ):
            action='arrow+'
        if (((source=="IR") and (key==49)) or ((source=="rotary") and (key==0) and (ROTARY_param[4]==0)) ) :
            action='select'
        if ( ((source=="IR") and (key==32)) or ((source=="clavier") and (key=='9')) ) : 
            action='back'
            #print('back')
 
    if protocole=='nec':
        action=''
        if ( ((source=="IR") and (key==538)) or ((source=="clavier") and (key=='6')) ) :
            action='home'
        if  (((source=="IR") and (key==516) ) or ((source=="clavier") and (key=='3'))):
            action='logout'
        if ((source=="rotary") and (ROTARY_param[4]==-1)):
            action='scroll'
        if ( ((source=="IR") and (key==520)) or ((source=="clavier") and (key=='7'))) :
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
 
    if protocole=='keyes':
        action=''
        if ( ((source=="IR") and (key==74)) or ((source=="clavier") and (key=='6')) ) :
            action='home'
        if  (((source=="IR") and (key==82) ) or ((source=="clavier") and (key=='3'))):
            action='logout'
        if ((source=="rotary") and (ROTARY_param[4]==-1)):
            action='scroll'
        if ( ((source=="IR") and (key==8)) or ((source=="clavier") and (key=='7'))) :
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
            
            if  (action=='select')  :
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
                
            if ( action=='vol+' ) :
                volume=min(volume+5,200)
                sound_box(volume)
                player.audio_set_volume(volume)
                
            if ( action=='vol-' ) :
                volume=max(volume-5,0)
                sound_box(volume)
                player.audio_set_volume(volume)
 
            if (action=='play') :
                if not(player.is_playing()):
                    player.play()
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
            
        if ( action=='arrow+' ) :
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
            
        if ( action=='arrow-' ) :
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
                                 
        if ( action=='arrow+' ) : #touche UP
            pwd=pwd+"-"
            update=True
            
        if ( action=='arrow-' ) : #touche DOWN
            pwd=pwd[:-1]  
            update=True
                        
        if (action=='scroll'):
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
            if (action=='logout' ):
                STATE=0
 
except KeyboardInterrupt:
    print("fin")
         
        
    
