
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import ili9488
from time import strftime
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk

serial = spi(port=0, device=0, gpio_DC=23, gpio_RST=24, spi_speed_hz=32000000)

device = ili9488(serial, rotate=2,
                 gpio_LIGHT=18, active_low=False) # BACKLIGHT PIN = GPIO 18, active High

device.backlight(True)

maincolor='#FAAF2C'
maincolor='red'

root=Tk()

s = ttk.Style()
s.configure('new.TFrame',background=maincolor)
content = ttk.Frame(root,style='new.TFrame')
image=Image.open("bbd666.bmp")
image=image.resize((200,200),Image.LANCZOS)
image_tk=ImageTk.PhotoImage(image)

radio_style=ttk.Style()
set_style=ttk.Style()
radio_style.configure("radio.TButton",font=('Helvetica',20),background='yellow')
set_style.configure("set.TButton",font=('Helvetica',20),background='yellow')

  
def lo():
  exit()

def main_fen():
  global root,content,image_tk
  global radiobutton
  global setbutton

  def set_time():
    time_var.set(strftime('%H:%M:%S'))
    root.after(1000, set_time)

  content.destroy()
  
  root.configure(background=maincolor)

  root.title("blackbird")
  window_height=240
  window_width=320
  screen_width=480#root.winfo_screenwidth()
  screen_height=320#root.winfo_screenheight()
  x_cordinate = 100#int((screen_width/2) - (window_width/2))
  y_cordinate = 100#int((screen_height/2) - (window_height/2))
  root.geometry("{}x{}+{}+{}".format(screen_width, screen_height,0,0))
 #  root.attributes('-fullscreen',True)
  v1=DoubleVar()

  content = ttk.Frame(root,style='new.TFrame')

  canvas=ttk.Label(content,image=image_tk)
  canvas.grid(column=0, row=0,rowspan=2)
  time_var = StringVar()

  watch=ttk.Label(content,font=('Arial', 30, 'bold'),textvariable=time_var,background=maincolor)
  set_time()
  setbutton=ttk.Button(content, text='quitter',style='radio.TButton',command=lo)
  radiobutton=ttk.Button(content, text='play/stop FIP',style='set.TButton')

  content.grid(column=0, row=0)
  watch.grid(column=0,row=3,sticky='n')
  setbutton.grid(column=1,row=0,padx=(10,0))
  radiobutton.grid(column=1,row=1,padx=(10,0))


def change(btn):
   global radiobutton
   global setbutton
   if btn=='n':
     if radio_style.lookup("radio.TButton",'background')=='blue':
       color='yellow'
       colori='blue'
     else:
       color='blue'
       colori='yellow'
     radio_style.configure("radio.TButton",background=color)
     set_style.configure("set.TButton",background=colori)
     

def poll_for_data():
    key=input('press key')
    if (key=='n'):
        change(key)
    if key=='r':
        print('out')
        setbutton.invoke()
    if key=='x':
        lo()
    root.after(300,poll_for_data)

main_fen()

try:
 while True:
     print('ok')
     root.after(300,poll_for_data)
     mainloop()

except KeyboardInterrupt:
        print("fin")



