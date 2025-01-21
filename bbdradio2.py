import vlc
from tkinter import *
from tkinter import ttk
from tkinter import font as tkFont
from PIL import Image, ImageTk
from time import sleep
from time import strftime
from datetime import datetime
import configparser
import os
import subprocess
from pathlib import Path
import re
import shutil
import evdev
import RPi.GPIO as GPIO
import shutil

os.system('sh remote.sh')

now=datetime.now()
lastnow=datetime.now()
update=True 
update_usb=True      
###########################################################
liste=os.listdir("/home/pierre/Documents")
liste_melodies=[]
for f in liste:
    extension = os.path.splitext(f)[1]
    if ( (extension==".mp3") or (extension==".wav") ):
        liste_melodies.append(f)
###########################################################
ssid=""
passwd=""
###########################################################
usb_path = "/dev/sda1"
mount_path = "/home/pierre/usb_disk_mount"
mp3_files=[]
###########################################################
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
###########################################################            
dev = get_ir_device()
#Keypad Parameters
row_list=[2,19,3]
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
###########################################################    
time_var=["",""]
date_var=["",""]    
#time_var = StringVar()
###########################################################                  
#Rotary encounter parameters
clkPin = 18    # CLK Pin
dtPin = 20    # DT Pin
swPin = 22    # Button Pin
#rotary encounter GPIO        
GPIO.setup(clkPin, GPIO.IN)    # input mode
GPIO.setup(dtPin, GPIO.IN)
GPIO.setup(swPin, GPIO.IN)
###########################################################
player = vlc.MediaPlayer()
player.set_mrl(url)
###########################################################
maincolor='#FAAF2C'    
os.environ.__setitem__('DISPLAY', ':0.0')
###########################################################    
#-------------création de l'interface graphique---------------
#Création de la fenêtre et de son titre
root=Tk()
root.configure(bg='darkorchid4')
helv36 = tkFont.Font(family='Helvetica', size=36, weight=tkFont.BOLD)
window_height=350
window_width=400
screen_width=root.winfo_screenwidth()
screen_height=root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate+40, y_cordinate))
content = ttk.Frame(root,style='new.TFrame')
content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)
image=Image.open("38081587.jpg")
image=image.resize((190,190),Image.Resampling.LANCZOS)
image_tk=ImageTk.PhotoImage(image)
style_1 = ttk.Style()
style_1.configure('TFrame',background=maincolor)    
style_2 = ttk.Style()
style_2.configure('TButton', font=('Helvetica', 20),background='blue')
style_3 = ttk.Style()
style_3.configure('click.TButton', font=('Helvetica', 20),background='yellow')


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

def Keypad4x4Read(cols,rows):
#Define Matrix Keypad read function
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

def set_time(arg):
    now = datetime.now()
    global time_var
    global date_var
    time_var[arg] = now.strftime('%H:%M:%S')
    date_var[arg] = now.strftime("%d/%m/%Y")      

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

def clear_all_inside_content():
    # Iterate through every widget inside the frame
    for widget in content.winfo_children():
        widget.destroy()
        
def set_time():
    time_var.set(strftime('%H:%M:%S'))
    root.after(1000, set_time)
    
def lo():
    quit()
  
def init_menu(arg): 
    global root, content
    global update
     
    clear_all_inside_content()
    content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)
    canvas=ttk.Label(content,image=image_tk)

    watch=ttk.Label(content,font=('Arial', 30, 'bold'),textvariable=time_var,background=maincolor,foreground="yellow")
    set_time()
    
    states_btn_ind=[0,0,0,0,0]
    states_btn_ind[arg]=1
    states_btn=['TButton','click.TButton']
  
    w=12
    radiobutton=ttk.Button(content, text='WEB STATIONS',width=w,style=states_btn[states_btn_ind[0]],command=lo)
    alarmbutton=ttk.Button(content, text='ALARME',width=w,style=states_btn[states_btn_ind[1]],command=lo)
    wifibutton=ttk.Button(content, text='WIFI',width=w,style=states_btn[states_btn_ind[2]],command=lo)
    usbbutton=ttk.Button(content, text='USB',width=w,style=states_btn[states_btn_ind[3]],command=lo)
    ipbutton=ttk.Button(content, text='ADRESSE IP',width=w,style=states_btn[states_btn_ind[4]],command=lo)

    content.grid(column=0, row=0)
    canvas.grid(column=0, row=0,rowspan=5)
    watch.grid(column=0,row=5,sticky='n')
    radiobutton.grid(column=1,row=0,padx=(3,0))
    alarmbutton.grid(column=1,row=1,padx=(3,0))
    wifibutton.grid(column=1,row=2,padx=(3,0))
    usbbutton.grid(column=1,row=3,padx=(3,0))
    ipbutton.grid(column=1,row=4,padx=(3,0))
    update=False   

def menu_liste(arg,items): 
    global root, content
    global update
    
    clear_all_inside_content()
    content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)

    arg[1]=arg[3]//arg[0]
    arg[2]=arg[3]%arg[0]
    #arg:nb_lignes,shiftbloc,decal,fillindex    
    content = ttk.Frame(root,style='new.TFrame')
    content.place(x=0, y=0, anchor="nw", width=window_width, height=window_height)
    w=25
    button=[]
    for i in range(0,arg[0]):
        if i+arg[1]*arg[0]<len(items):
            if i+arg[1]*arg[0]==arg[3] :
                button.append(ttk.Button(content, text=items[i+arg[1]*arg[0]],width=w,style='click.TButton',command=lo))
                button[i].grid(column=0,row=i,padx=(0,0))                
            else :
                button.append(ttk.Button(content, text=items[i+arg[1]*arg[0]],width=w,style='TButton',command=lo))
                button[i].grid(column=0,row=i,padx=(0,0))                
    update=False   

def menu_volume(arg): 
    global root, content
    
    clear_all_inside_content()
    content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)
   
    progressbar=ttk.Progressbar(content, length=200, orient='horizontal', value=arg, mode='determinate',maximum=200)
    progressbar.grid(row=0,column=0, pady=100, padx=100)    

def will_you_load(arg):
   global root, content
   global update
    
    clear_all_inside_content()
    content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)
    
   w=5
   
   if arg[1]==1:
       msg=ttk.Label(content,font=('Arial', 30, 'bold'),text="MAJ reussie",background=maincolor,foreground="yellow")
       msg.grid(column=0,row=0,padx=(100,100),pady=(100,100),sticky='n')  
   else:
       if arg[1]==2:
          msg=ttk.Label(content,font=('Arial', 30, 'bold'),text="echec MAJ",background=maincolor,foreground="yellow")
          msg.grid(column=0,row=0,padx=(100,100),pady=(100,100),sticky='n')  
       else:
          msg=ttk.Label(content,font=('Arial', 22, 'bold'),text="Chargement de la MAJ ?",background=maincolor,foreground="yellow") 
          if arg[0]==0:
              oui=ttk.Button(content, text='OUI',width=w,style='TButton',command=lo)              
              non=ttk.Button(content, text='NON',width=w,style='click.TButton',command=lo)
          else:
              oui=ttk.Button(content, text='OUI',width=w,style='click.TButton',command=lo)              
              non=ttk.Button(content, text='NON',width=w,style='TButton',command=lo)
          msg.grid(column=0,row=1,padx=(30),pady=(20,20),columnspan=2)    
          oui.grid(column=0,row=2,pady=(20,20))    
          non.grid(column=1,row=2,pady=(20,20))    
   update=False   
              
def load_config(arg):
    global usb_path
    global mount_path 
    subprocess.run(["sudo", "mount", usb_path, mount_path])
    p = Path(mount_path)
    if p.is_mount():
        my_file = p/arg
        if my_file.is_file():
         my_file_target="/home/pierre/Documents/"+arg
         shutil.copy(my_file,my_file_target)
         return 1
        else:
         return 0
    else:
        return 0
    subprocess.run(["sudo", "umount", mount_path])             
 
def set_hour(arg):
   global update
   global root, content
    
    clear_all_inside_content()
    content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)
   
   sf=30  
   if arg[4]==0:
    h1=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[0]),background="yellow",foreground="black")
   else:   
    h1=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[0]),background="black",foreground="yellow")
   if arg[4]==1:
    h2=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[1]),background="yellow",foreground="black")
   else:   
    h2=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[1]),background="black",foreground="yellow")
   if arg[4]==2:
    m1=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[2]),background="yellow",foreground="black")
   else:   
    m1=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[2]),background="black",foreground="yellow")
   if arg[4]==3:
    m2=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[3]),background="yellow",foreground="black")
   else:   
    m2=ttk.Label(content,font=('Arial', sf, 'bold'),text=str(arg[3]),background="black",foreground="yellow")
   separator=ttk.Label(content,font=('Arial', sf, 'bold'),text=':',background=maincolor,foreground="yellow")
 
   h1.grid(column=0,row=0,padx=(30),pady=(100))    
   h2.grid(column=1,row=0,padx=(30))    
   separator.grid(column=2,row=0,padx=(30))    
   m1.grid(column=3,row=0,padx=(30))    
   m2.grid(column=4,row=0,padx=(30))    
   update=False   
  
def set_passwd():
   global update
   global root, content
    
   clear_all_inside_content()
   content.place(x=0, y=0, anchor="nw", width=window_width, height=window_height)
   
   key=[]
   l=12

   s=chr(708)+","+chr(709)+" : modification"
   titre1=ttk.Label(content,font=('Arial', 12, 'bold'),text=s,background="grey")
   titre1.place(x=10,y=20)
   s="'Select' : ajout"
   titre2=ttk.Label(content,font=('Arial', 12, 'bold'),text=s,background="grey")
   titre2.place(x=180,y=20)
   s="■ : suppression"
   titre3=ttk.Label(content,font=('Arial', 12, 'bold'),text=s,background="grey")
   titre3.place(x=10,y=60)
   s=">|| : validation"
   titre4=ttk.Label(content,font=('Arial', 12, 'bold'),text=s,background="grey")
   titre4.place(x=180,y=60)
   
   for i in range(len(passwd)-1):
    key.append(ttk.Label(content,font=('Arial', 12, 'bold'),text=passwd[i],background='black',foreground='yellow'))
    key[i].place(x=i%l*25+15,y=i//l*30+120,width=20)
   i=len(passwd)-1
   key.append(ttk.Label(content,font=('Arial', 12, 'bold'),text=passwd[i],background='yellow',foreground='black'))
   key[i].place(x=i%l*25+15,y=i//l*30+120,width=20)
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
    
a=[6,0,0,6]
#menu_liste(a,liste_lbl)
#init_menu(1)
#menu_volume(120)
a=[0,0]
#will_you_load(a)
a=['1','3','2','7','2']
set_hour(a)
root.mainloop()