
from time import strftime
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk

maincolor='#FAAF2C'

def lo():
  exit()

root=Tk()
s = ttk.Style()
s.configure('new.TFrame',background=maincolor)
content = ttk.Frame(root,style='new.TFrame')
image=Image.open("C:/Users/pierre.lemerle/Desktop/bbd.jpg")
image=image.resize((190,190),Image.Resampling.LANCZOS)
image_tk=ImageTk.PhotoImage(image)

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
  radiobutton=ttk.Button(content, text='menu suivant',command=second_fen)
  setbutton=ttk.Button(content, text='quitter',command=lo)

  content.grid(column=0, row=0)
  watch.grid(column=0,row=3,sticky='n')
  radiobutton.grid(column=1,row=0,padx=(10,0))
  setbutton.grid(column=1,row=1,padx=(10,0))
    
def second_fen():
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


  radiobutton=ttk.Button(content, text='menu initial',command=main_fen)
  setbutton=ttk.Button(content, text='quitter',command=lo)

  content.grid(column=0, row=0)
  radiobutton.grid(column=0,row=0,padx=(100,100),pady=(20,20))
  setbutton.grid(column=0,row=1,padx=(100,100),pady=(20,20))
    


main_fen()

mainloop()


