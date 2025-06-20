import vlc

url="composition-Theodor.wav"
url ="http://direct.fipradio.fr/live/fip-midfi.aac"
url="OSR_us_000_0019_8k_R.wav"
player = vlc.MediaPlayer()
player.set_mrl(url)
player.play()
while 1:
  pass
