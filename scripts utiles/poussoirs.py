import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)


GPIO.setup(17, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(15, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(8, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(25, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(9, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(5, GPIO.IN, pull_up_down = GPIO.PUD_UP)

while True:
	appui='lacher'
	etat=GPIO.input(17)
	if (etat==GPIO.LOW):
		appui='preset'
	etat=GPIO.input(15)
	if (etat==GPIO.LOW):
		appui='home'
	etat=GPIO.input(23)
	if (etat==GPIO.LOW):
		appui='back'
	etat=GPIO.input(22)
	if (etat==GPIO.LOW):
		appui='forward'
	etat=GPIO.input(24)
	if (etat==GPIO.LOW):
		appui='stop'
	etat=GPIO.input(8)
	if (etat==GPIO.LOW):
		appui='rewind'
	etat=GPIO.input(25)
	if (etat==GPIO.LOW):
		appui='1'
	etat=GPIO.input(9)
	if (etat==GPIO.LOW):
		appui='2'
	etat=GPIO.input(5)
	if (etat==GPIO.LOW):
		appui='3'
	print(appui)
	time.sleep(0.3)
