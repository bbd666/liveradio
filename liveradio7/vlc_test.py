import vlc

url ="http://direct.fipradio.fr/live/fip-midfi.aac"
player = vlc.MediaPlayer()
player.set_mrl(url)
player.play()
while 1:
  pass
