import RPi.GPIO as GPIO
import sys
import time
import configparser

config = configparser.ConfigParser()
config.read('data.ini')
dtPin=int(config['RADIO SETTINGS']['pin_dt'])
clkPin=int(config['RADIO SETTINGS']['pin_clk'])
swPin=int(config['RADIO SETTINGS']['pin_sw'])
row_list=[int(config['RADIO SETTINGS']['pin_30']),int(config['RADIO SETTINGS']['pin_31']),int(config['RADIO SETTINGS']['pin_32'])]

source=""

globalCounter = 0
ROTARY_param=[0,0,0,0,-1]

col_list=[int(config['RADIO SETTINGS']['pin_33']),int(config['RADIO SETTINGS']['pin_34']),int(config['RADIO SETTINGS']['pin_35'])]


GPIO.setmode(GPIO.BCM)

GPIO.setup(clkPin, GPIO.IN)    # input mode
GPIO.setup(dtPin, GPIO.IN)
GPIO.setup(swPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#define PINs according to cabling
#row_list 
#boutons 30,31,32
#col_list 
#boutons 33,34,35

# set row pins to output, all to high
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
            GPIO.output(r, GPIO.HIGH) 
            return(key)
        GPIO.output(r, GPIO.HIGH)
	
# define swPin read function
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
	
# define Rotary encoder function
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

# main program
while True:
  try:   
    key=Keypad4x4Read(col_list, row_list)
    if key != None:
        source="clavier"
        print("You pressed: "+str(key)+" ; "+source)
        time.sleep(0.3)
    else:
        key=swpinRead()
        if key != None:
            ROTARY_param[4]=0
            source="Encoder button"
            print("You pressed: "+str(key)+" ; "+source)
            time.sleep(0.3) 
        else:   
            counter=ROTARY_param[3]
            rotaryDeal(ROTARY_param)
            if not(counter==ROTARY_param[3]):
                source="rotary"
                key=ROTARY_param[3]
                print("You pressed: "+str(key)+" ; "+source)
                time.sleep(0.3) 
                ROTARY_param[4]=-1
            else:
                source=""
            
  except KeyboardInterrupt:
    GPIO.cleanup()
    sys.exit()
