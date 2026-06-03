

import os
import subprocess
from pathlib import Path
import shutil

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
    
def disconnect(ssid:str):
    if not is_wifi_available(ssid):
        return False
    err=False
    ch= "nmcli connection delete "+ssid
    ch_mod=ch.split()
    try:
      proc = subprocess.run(
        ch_mod,
        stdout=subprocess.PIPE,
        encoding="utf8",
      )
      err=True
      #print(f"Déconnecté de {ssid} : {proc.stdout.strip()}")
    except subprocess.CalledProcessError as e:
      #print(f"Erreur nmcli : {e.stderr.strip()}")
      err= False
    except Exception as e:
      #print(f"Erreur système : {str(e)}")
      err= False
    return err

def connect_to(ssid: str, password: str):
    if not is_wifi_available(ssid):
        return False
    err=False
    disconnect(ssid)
    ch = "nmcli device wifi connect "+ssid+" password "+password
    ch_mod=ch.split()
    try:
      proc = subprocess.run(
        ch_mod,
        stdout=subprocess.PIPE,
        encoding="utf8",
      )
      err=True
      print(f"Connecté à {ssid} : {proc.stdout.strip()}")
    except subprocess.CalledProcessError as e:
      print(f"Erreur nmcli : {e.stderr.strip()}")
      err= False
    except Exception as e:
      print(f"Erreur système : {str(e)}")
      err= False
    scan=get_wifi_snr()
    if (scan[0]==ssid):
        err=True
    else:
        err=False
    return err

def connect_to_saved(ssid: str):
    if not is_wifi_available(ssid):
        return False
    subprocess.call(['nmcli', 'c', 'up', ssid])
    return is_connected_to(ssid)

         
connect_to("blackbird","12345678")
        
    
