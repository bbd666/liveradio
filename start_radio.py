import time
import evdev
import os
import subprocess
import psutil
    
def get_ir_device():
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if (device.name == "gpio_ir_recv"):           
                return device          
   
    
def trig_ir():
    global last_call
    global s
    event = dev.read_one()
    result = None   
    if event is None:
        return
    else:    
     if not(event.code==0): 
      t = time.perf_counter() 
      if t - last_call > 0.5:
        last_call = t
        value = event.value
        return value
                    
dev = get_ir_device()
os.system('sh remote.sh')
last_call =time.perf_counter() 
processlist=list()
prog='bbdradio2.py'
proc=['python',prog]

while True:
    key=trig_ir()
    if (key==0):
         processlist.clear()
         for process in psutil.process_iter():
           processlist.append(process.cmdline())
         if processlist.count(proc)==0:
           print('launching')
           process = subprocess.Popen(["python", "bbdradio2.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         else:
          os.system("pkill -f 'bbdradio2.py'")  
         

        
