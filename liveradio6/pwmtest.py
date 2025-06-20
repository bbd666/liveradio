from driver_LCD import LcdDisplay
import time
import RPi.GPIO as  GPIO
#s=input()
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(18,GPIO.OUT)
#p=GPIO.PWM(18,50)
#p.start(0)
p=LcdDisplay()
while 1:
	for dc in range(0,101,1):
#		p.ChangeDutyCycle(dc)
		d=dc/100
		p.set_intensity(d)
		time.sleep(0.01)
	for dc in range(100,-1,-1):
#		p.ChangeDutyCycle(dc)
		d=dc/100
		p.set_intensity(d)
		time.sleep(0.01)
