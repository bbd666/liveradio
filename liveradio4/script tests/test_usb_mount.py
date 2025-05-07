import subprocess
from pathlib import Path

usb_path = "/dev/sda1"
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
    
s=scan_USB_files()
print(s)