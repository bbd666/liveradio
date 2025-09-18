
import time
from time import strftime
import vlc
from time import sleep
from datetime import datetime,timedelta
import os
import subprocess

lastnow=datetime.now()
update_count=0
ssid='blackbird'
player = vlc.MediaPlayer()


def get_wifi_snr():
    r=[]    
    process = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        a=process.stdout.decode('utf-8').strip().split('\n')
        for i in range(0,len(a)):
            b=a[i].split(':')
            if (b[0]=='yes') or (b[0]=='oui') :
                r.append(b[1])
                r.append(b[2])
    r.append('xxx')
    r.append('0')
    return r

def is_connected_to(ssid: str):
    a=get_wifi_snr()    
    return a[0] == ssid   

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
   
alarm_clck_hour=9
alarm_clck_min=26

alarm_radio='http://direct.fipradio.fr/live/fip-midfi.aac'
alarm_source=alarm_radio
player.set_mrl(alarm_source)

try:
 while True:               
    now=datetime.now()
    
    if ( (now.hour==alarm_clck_hour) and (now.minute==alarm_clck_min) and (now.second<20) ):
        alarm_src=alarm_source
        if (alarm_source==alarm_radio):
                is_connected=is_connected_to(ssid)
                if not(is_connected):
                    alarm_src='composition Theodor.mp3'                    
                    player.set_mrl(alarm_src)
        if not(player.is_playing()):
            player.play()

    now=datetime.now()
    deltat=now-lastnow
    if (deltat.microseconds>950000):
        update_count=(update_count+1)%10  
        # teste le signal wifi toutes les 10 s
        if (update_count==1):
            scan=get_wifi_snr()
        if (scan[0]==ssid):
            print(scan[1])
        else:
            print('WIFI deconnecte')
        lastnow=now            
                              
 
except KeyboardInterrupt:
    print("fin")
         
        
    
