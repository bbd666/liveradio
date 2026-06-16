import time
import vlc

url='composition Theodor.mp3' 
player = vlc.MediaPlayer()
player.set_mrl(url)
player.play()
player.audio_set_volume(60)
time.sleep(60)

    
