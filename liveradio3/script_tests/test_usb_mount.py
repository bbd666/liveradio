import subprocess
from pathlib import Path
import os

#os.system('sh init_usb_daemon.sh')
os.system('sh get_usb_dev.sh')
f=open("dev_usb.txt")
usb_path=f.readline().strip('\n')
#usb_path="/dev/sda1"
print(usb_path)
mount_path = "/home/pierre/usb_disk_mount"
mp3_files=[]                          
                
def scan_USB_files():
    global usb_path
    global mount_path 
    global mp3_files
    audio_ext = [".mp3" ,".ogg", ".flac", ".wav"]
    subprocess.run(["sudo", "mount", usb_path, mount_path])
    p = Path(mount_path)
    mp3_files=[]
    if p.is_mount():
        mp3_files = [x for x in p.iterdir() if x.suffix in audio_ext]
    
def load_config(arg):
    global usb_path
    global mount_path 
    subprocess.run(["sudo", "mount", usb_path, mount_path])
    p = Path(mount_path)
    if p.is_mount():
        my_file = p/arg
        if my_file.is_file():
         my_file_target="/home/pierre/"+arg
         #shutil.copy(my_file,my_file_target)
         return 1
        else:
         return 0
    else:
        return 0
    subprocess.run(["sudo", "umount", mount_path])

s=scan_USB_files()
#print(s)
for i in range(0,len(mp3_files)):
	print(mp3_files[i])
err=load_config("data.ini")
print(err)
