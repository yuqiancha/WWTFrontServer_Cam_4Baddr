import os
import time
import threading
from PyQt5.QtCore import *
import logging.config

MajorLog = logging.getLogger('ws_error_log')      #log error
class SpeakVoice(QThread):
    def __init__(self):
        super(SpeakVoice,self).__init__()

    def Voice(self,str):
        if str=='booked':
            music_path = '/home/pi/Downloads/WWTFrontServer/booked.mp3'
            os.system('mplayer %s' % music_path)
        elif str=='errorcar':
            music_path = '/home/pi/Downloads/WWTFrontServer/errorcar2.mp3'
            os.system('mplayer %s' % music_path)
        elif str=='lockdown':
            music_path = '/home/pi/Downloads/WWTFrontServer/lockdown.mp3'
            os.system('mplayer %s' % music_path)
        else:
            pass