
from time import strftime
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import vlc

player = vlc.MediaPlayer()
player.set_mrl('http://direct.fipradio.fr/live/fip-midfi.aac')
maincolor='#FAAF2C'

root=Tk()
s = ttk.Style()
s.configure('new.TFrame',background=maincolor)
content = ttk.Frame(root,style='new.TFrame')
image=Image.open("bbd.jpg")
image=image.resize((190,190),Image.Resampling.LANCZOS)
image_tk=ImageTk.PhotoImage(image)

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
  
def lo():
  exit()

def main_fen():
  global root,content,image_tk
  
  def set_time():
    time_var.set(strftime('%H:%M:%S'))
    root.after(1000, set_time)

  content.destroy()
  
  root.configure(background=maincolor)

  root.title("blackbird")
  window_height=240
  window_width=320
  screen_width=root.winfo_screenwidth()
  screen_height=root.winfo_screenheight()
  x_cordinate = int((screen_width/2) - (window_width/2))
  y_cordinate = int((screen_height/2) - (window_height/2))
  root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

  v1=DoubleVar()

  content = ttk.Frame(root,style='new.TFrame')

  canvas=ttk.Label(content,image=image_tk)
  canvas.grid(column=0, row=0,rowspan=2)
  time_var = StringVar()

  watch=ttk.Label(content,font=('Arial', 30, 'bold'),textvariable=time_var,background=maincolor)
  set_time()
  radiobutton=ttk.Button(content, text='play/stop FIP',command=play)
  setbutton=ttk.Button(content, text='quitter',command=lo)

  content.grid(column=0, row=0)
  watch.grid(column=0,row=3,sticky='n')
  radiobutton.grid(column=1,row=0,padx=(10,0))
  setbutton.grid(column=1,row=1,padx=(10,0))
    
def play():
  if not(player.is_playing()):
        player.play()
  else:
        player.pause()

main_fen()

try:
 while True:
     print('ok')
     mainloop()

except KeyboardInterrupt:
        print("fin")



