import RPi.GPIO as GPIO
import evdev
import os
import time

def get_ir_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if (device.name == "gpio_ir_recv"):           
            return device    
            
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
    
def rotaryDeal(arg):
#arg[1] : Last_dt_Status
#arg[2] : Current_dt_Status
#arg[3] : Counter
#arg[4] : -1 if rotary ; 0 if button (swPin)
	arg[1] = GPIO.input(dtPin)
	det=GPIO.input(swPin)
	if (det==0):
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
	  
def rotaryDeal2(channel):
    global counter
    a1_state = GPIO.input(dtPin)
    b1_state = GPIO.input(clkPin)    
    # Check direction for Encoder 
    if a1_state != a1_last_state:
        if b1_state != a1_state:
            counter += 1  # Clockwise
        else:
            counter -= 1  # Counter-clockwise

def poll_for_data():	
	key=trig_ir()
    source="IR"
    if key==None: 
        key=Keypad4x4Read(col_list, row_list)
        source="clavier"
        if (key==None):       
            count=ROTARY_param[3]
            rotaryDeal(ROTARY_param)
            if (not(count==ROTARY_param[3])) or (ROTARY_param[4]==0) :
                source="rotary"
                key=ROTARY_param[3]
        # if (key==None):
                # if not(counter==ROTARY_param[3]):
                    # ROTARY_param[3]=counter
                    # source="rotary"
                    # key=ROTARY_param[3]
            else:
                source=""          
    if (key==None):            
		print(key)
	root.after(300, poll_for_data)
    
os.system('sh remote.sh')
dev = get_ir_device()
#Keypad Parameters
row_list=[23,19,24]
col_list=[26,14,16]
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
last_call=0
ROTARY_param=[0,0,0,0,-1]
###########################################################                  
#Rotary encounter parameters
clkPin = 20    # CLK Pin
dtPin = 15    # DT Pin
swPin = 22    # Button Pin
#rotary encounter GPIO        
GPIO.setup(clkPin, GPIO.IN,pull_up_down=GPIO.PUD_UP)    # input mode
GPIO.setup(dtPin, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(swPin, GPIO.IN,pull_up_down=GPIO.PUD_UP)
#GPIO.add_event_detect(dtPin, GPIO.BOTH, callback=rotaryDeal2)
#counter=0	  
 
root.after(300, poll_for_data)
root.mainloop()
	  
