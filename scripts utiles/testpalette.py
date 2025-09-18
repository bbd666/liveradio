from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk



root=Tk()
root.configure(bg='white')
window_height=350
window_width=400
screen_width=root.winfo_screenwidth()
screen_height=root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate+40, y_cordinate))
content = ttk.Frame(root,style='new.TFrame')
content.place(x=50, y=0, anchor="nw", width=window_width, height=window_height)
image=Image.open("palette.jpg")
image=image.resize((350,350),Image.Resampling.LANCZOS)
image_tk=ImageTk.PhotoImage(image)
canvas=ttk.Label(content,image=image_tk)
canvas.grid(column=0, row=0)

mainloop()
