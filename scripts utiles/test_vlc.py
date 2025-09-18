import time
import vlc

url='composition_Theodor.mp3' 
player = vlc.MediaPlayer()
player.set_mrl(url)
player.play()
time.sleep(10)

    
