#import pyttsx3
#engine = pyttsx3.init()
#engine.say(u"传宗2不2")
#engine.runAndWait()

#import os
##word = 'espeak -vzh "编程"'
#os.system(word)


import os
import time

path_music_lockdown = '/home/Downloads/WWT_FrontServer_Cam_4Baddr/lockdown.mp3'
os.system('mplayer %s' % path_music_lockdown)