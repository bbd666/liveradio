from smbus3 import SMBus
import time
from time import sleep
import RPi.GPIO as GPIO
from rpi_hardware_pwm import HardwarePWM
from PIL import Image, ImageDraw, ImageFont

class LcdDisplay:
	def __init__(self,address=0x3f):
		self.FRAME_BUFFER= Image.new('1',(132,80))
		self.police1= ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
		self.SEND_COMMAND=0x00                       #A0=0
		self.SEND_DATA=0x40                          #A0=1
		self.SET_F=0x20
		self.SET_H01=self.SET_F | 0x01                            #H1=0 H0=1
		self.SET_H10=self.SET_F | 0x02                            #H1=1 H0=0
		self.SET_H00=self.SET_F | 0x00                            #H1=0 H0=0
		self.SET_H11=self.SET_F | 0x03                            #H1=1 H0=1
		self.SET_POWER_DOWN=self.SET_F | 0x04
		self.SOFTWARE_RESET=0x03
		self.SET_BIAS_9=0x12                         #BIAS=1/9  BS0=0  BS1=1 BS2=0
		self.SET_BIAS_10=0x11                        #BIAS=1/10 BS0=0  BS1=0 BS2=1
		self.SET_V0_LOWER_BITS=0x8f          #VOP0=VOP1=VOP2=VOP3=1 VOP4=VOP5=VOP6=0
		self.SET_V0_RANGE=0x05                       #PRS=1 => 9.198V(=8*0.042+8.862)
		self.SET_MSB=0x08                            #Bit de poids fort en haut (DO=0)
		self.SET_LSB=0x0c                            #Bit de poids fort en bas (DO=1)
		self.SET_VERTICAL_ADDRESSING=0x01
		self.SET_HORIZONTAL_ADDRESSING=0x00
		self.SET_NORMAL_DISPLAY=0x0c
		self.SET_DISPLAY_OFF=0x08
		self.SET_ALL_SEGMENTS_ON=0x09
		self.SET_INVERSE_VIDEO_MODE=0x0d
		self.SET_FRAME_50HZ=0x08
		self.SET_FRAME_73HZ=0x0b
		self.SET_FRAME_150HZ=0x0f

		Reset_Pin=4
#		GPIO.setmode(GPIO.BCM)				USELESS
#		GPIO.setup(Reset_Pin,GPIO.OUT)			USELESS
#		GPIO.output(Reset_Pin,GPIO.LOW)			USELESS
		time.sleep(0.05)
#		GPIO.output(Reset_Pin,GPIO.HIGH)		USELESS
		time.sleep(0.05)
		self.address=address
		self.bus=SMBus(1)
		wrdata = [self.SEND_COMMAND,self.SET_H00]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.05)
		wrdata = [self.SEND_COMMAND,self.SET_DISPLAY_OFF]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.01)
		wrdata = [self.SEND_COMMAND,self.SET_H01]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.001)
		wrdata = [self.SEND_COMMAND,self.SET_LSB|self.SET_HORIZONTAL_ADDRESSING]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_BIAS_9]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.001)
		wrdata = [self.SEND_COMMAND,self.SET_V0_LOWER_BITS]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.01)
		wrdata = [self.SEND_COMMAND,self.SET_H00]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.01)
		wrdata = [self.SEND_COMMAND,self.SET_V0_RANGE]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.05)
		wrdata = [self.SEND_COMMAND,self.SET_H11]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.02)
		wrdata = [self.SEND_COMMAND,self.SET_FRAME_73HZ]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.01)
		wrdata = [self.SEND_COMMAND,self.SET_H10]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0x04]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_H00]
		self.bus.i2c_wr(self.address,wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_NORMAL_DISPLAY]
		time.sleep(1)
		self.i2c_write (self.address, wrdata)
	
	def i2c_write (self,devaddr,regdata):
		for attempt in range(10):
			try:
				self.bus.i2c_wr(devaddr,regdata)
				return True
			except IOError:
				pass
				return None

	def draw_pixel(self,x,y):
######### x colonne, y ligne  ####################################
		wrdata = [self.SEND_COMMAND,self.SET_H00]
		self.bus.i2c_wr(self.address,wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_DISPLAY_OFF]
		self.i2c_write (self.address, wrdata)
		x=min(x,131)
		xlow=x & 0x0f
		xhigh=(0xf0 & x) >> 4
		wrdata = [self.SEND_COMMAND,0xe0|xlow]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0xf0|xhigh]
		self.i2c_write (self.address, wrdata)
		ypage=y//10
		wrdata = [self.SEND_COMMAND,0x40|ypage]
		self.i2c_write (self.address, wrdata)
		ysegment=2**(y%10)
		wrdata = [self.SEND_DATA,ysegment]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.01)
		wrdata = [self.SEND_COMMAND,self.SET_NORMAL_DISPLAY]
		self.i2c_write (self.address, wrdata)

	def draw_vert_segment(self,x,y):
######### x colonne, y ligne  ####################################
		wrdata = [self.SEND_COMMAND,self.SET_H00]
		self.bus.i2c_wr(self.address,wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_DISPLAY_OFF]
		self.i2c_write (self.address, wrdata)
		x=min(x,131)
		xlow=x & 0x0f
		xhigh=(0xf0 & x) >> 4
		wrdata = [self.SEND_COMMAND,0xe0|xlow]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0xf0|xhigh]
		self.i2c_write (self.address, wrdata)
		ypage=y//10
		wrdata = [self.SEND_COMMAND,0x40|ypage]
		self.i2c_write (self.address, wrdata)
		ysegment=2**(y%10)
		wrdata = [self.SEND_DATA,0xff]
		self.i2c_write (self.address, wrdata)
		time.sleep(0.01)
		wrdata = [self.SEND_COMMAND,self.SET_NORMAL_DISPLAY]
		self.i2c_write (self.address, wrdata)


	def display_map(self,map):
		wrdata = [self.SEND_COMMAND,self.SET_H00]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_DISPLAY_OFF]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0xe0|0x00] #SET X ADDRESS (L)  0000
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0xf0|0x00] #SET X ADDRESS (H)  0000
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0x40|0x00] #SET Y ADDRESS      0000
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0x07]      #READ / MODIFY / WRITE
		self.i2c_write (self.address, wrdata)
		for i in range(1320):
			wrdata = [self.SEND_DATA,map[i]]
			self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,0x06]      #END
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_NORMAL_DISPLAY]
		self.i2c_write (self.address, wrdata)

	def clean_display(self):
		self.FRAME_BUFFER=Image.new('1',(132,80))
		map=self.tohex(self.FRAME_BUFFER)
		self.display_map(map)
		
	def set_intensity(self,s):
		pwm = HardwarePWM(pwm_channel=0, hz=50, chip=0)
		pwm.start(100) # full duty cycle
		intensity=int(s*100)
		pwm.change_duty_cycle(intensity)

	def set_normal_display(self):
		wrdata = [self.SEND_COMMAND,self.SET_DISPLAY_OFF]
		self.i2c_write (self.address, wrdata)
		wrdata = [self.SEND_COMMAND,self.SET_NORMAL_DISPLAY]
		self.i2c_write (self.address, wrdata)

	def tohex(self,image):
		res=[]
		for n in range(0,10):
			for x in range(0, 132):
				byte=""
				for y in range(8*n, 8*(n+1)):
					bit = "0"
					if  image.getpixel((x,y)) != 0:
						bit = "1"
					byte=byte+bit
					if y % 8 == 7:
						res.append(int(byte,2))
		return res

	def load_image(self,image):
		self.FRAME_BUFFER=image

	def refresh(self):
		map=self.tohex(self.FRAME_BUFFER)
		self.display_map(map)

	def draw_rectangle(self,x1,y1,x2,y2, param_fill, param_outline, param_width):
	#param_outline=None or 1; Color to use for the outline
	#param_fill=None or 1; Color to use for the fill.
		draw=ImageDraw.Draw(self.FRAME_BUFFER)
		draw.rectangle([(x1,y1),(x2,y2)],fill=param_fill, outline=param_outline, width=param_width)		

	def draw_text(self,x,y,param_text,param_fill,font_file,font_size,param_anchor,param_spacing,param_align):
        #align must be “left”, “center” or “right”.
	#param_fill=None or 1; Color to use for the text.
        #spacing number of pixels between lines
		draw=ImageDraw.Draw(self.FRAME_BUFFER)
		police=ImageFont.truetype(font_file, font_size)
		draw.text((x,y),param_text,font=police,fill=param_fill,anchor=param_anchor,spacing=param_spacing,align=param_align)

