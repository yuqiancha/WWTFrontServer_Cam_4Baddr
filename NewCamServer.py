import http.client
import time
import threading
from Data import MyLock
from Data import SharedMemory
from PyQt5 import QtCore
from PyQt5.QtCore import *
import urllib.parse
import logging.config
from os import path
import socket
from binascii import hexlify,unhexlify
import logging
import configparser
import os

MyLog2 = logging.getLogger('ws_debug_log2')       #log data
MajorLog = logging.getLogger('ws_error_log')      #log error
MyLogCam = logging.getLogger('ws_cam_log')          #cam log

class TcpServer(QThread):
    signal_detect = pyqtSignal(str,str)
    signal_blue_detect = pyqtSignal(str,str)
    signal_showID = pyqtSignal(str)
    signal_blue_showID = pyqtSignal(str)
    def __init__(self):
        super(TcpServer,self).__init__()
        print("TcpServer In")
        MyLogCam.info('TcpServer In')
        try:
            self.cf = configparser.ConfigParser()
            self.cf.read(path.expandvars('$HOME') + '/Downloads/WWTFrontServer/Configuration.ini',encoding="utf-8-sig")

        except Exception as ex:
            MajorLog(ex)


        self.ThreadTag = True

        host = ''
        port = 9005
        bufsize = 1024
        addr = (host,port)

        tcpServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        tcpServer.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

        tcpServer.bind(addr)
        tcpServer.listen(10)


        t2=threading.Thread(target = AcceptConnection,args=(tcpServer,self))
        t2.start()


    def close(self):
        self.ThreadTag = False

def AcceptConnection(tcpServer,self):
    print('Waiting for connection ... ')

    while self.ThreadTag:
        tcpClient, addr = tcpServer.accept()

        t = threading.Thread(target=RecvFromCamera, args=(tcpClient,addr,self))
        t.start()


def RecvFromCamera(tcpClient,clientaddr,self):
    print('connect from ',clientaddr)

    timenow = int(0)
    timelast = int(0)
    timeSpent = int(0)

    tcpClient.send('1ACFCD0109D7'.encode('utf-8'))#连接上摄像机时候初始化为红灯
    time.sleep(0.5)
    tcpClient.send('1ACFCD1009D7'.encode('utf-8'))#连接上摄像机时候初始化为绿灯
    time.sleep(0.5)
    tcpClient.send('1ACFCD1109D7'.encode('utf-8'))#连接上摄像机时候初始化为黄灯
    time.sleep(0.5)
    tcpClient.send('1ACFCD0009D7'.encode('utf-8'))#连接上摄像机时候初始化为无灯
    time.sleep(0.5)

    lastLightStatus ='ff'

    while self.ThreadTag:

        #如果需要控制灯光，在接收前发送一次
        for item in SharedMemory.LockList:
            if item.addr == str(self.cf.get("StartLoad",clientaddr[0])):
                if item.light == 'ff' or item.light==lastLightStatus:
                    pass
                else:
                    cmdstr = '1ACFCD'+item.light+'09D7'
                    tcpClient.send(cmdstr.encode('utf-8'))
                    lastLightStatus = item.light                                #把此次状态记录，下次还是相同状态则不发送
                    item.light = 'ff'



        RecvStr = ''
        try:
            RecvStr = tcpClient.recv(1024).decode('utf-8')
        except Exception as ex:
            print(ex)
            MyLog2.error(ex)
            break

        print('[- data]',clientaddr[0],RecvStr)

        data = RecvStr.upper()
        if len(data)>=18:
            if data=='EB90A5FFFFFFFF09D7':
                pass
            elif data[0:4]=='EB90':
                a1 = data.find('F1')
                a2 = data.find('F2')
                a3 = data.find('F3')
                if a1!=-1 and a2!=-1:
                    DColor = data[a2+2:a3]
                    Dlisence = data[a1+2:a2]
                    print(Dlisence,DColor)
                    if DColor=='绿色' or DColor=='绿':
                        MyLogCam.info(str(clientaddr[0])+str(self.cf.get("StartLoad",clientaddr[0]))+':'+Dlisence+"绿")

                        if Dlisence[0:2]=='沪AF':
                            MyLogCam.info("混动绿牌不降低锁")
                        else:
                            timenow = int(time.time())
                            timeSpent = timenow - timelast
                            timelast = timenow

                            if timeSpent > 5:
                                self.signal_detect.emit('05'+ str(self.cf.get("StartLoad",clientaddr[0])),Dlisence)
                                self.signal_showID.emit(str(self.cf.get("StartLoad",clientaddr[0]))+':'+Dlisence)

                    elif DColor =='蓝色' or DColor=='蓝':
                        MyLogCam.info(str(clientaddr[0])+str(self.cf.get("StartLoad",clientaddr[0]))+':'+Dlisence+"蓝")
                        self.signal_blue_detect.emit(str(self.cf.get("StartLoad",clientaddr[0])),Dlisence)
                        self.signal_blue_showID.emit(str(self.cf.get("StartLoad", clientaddr[0])) + ':' + Dlisence)
                    else:
                        MyLogCam.info(str(clientaddr[0]) + str(self.cf.get("StartLoad", clientaddr[0])) + ':' + Dlisence + DColor)
                        self.signal_blue_detect.emit(str(self.cf.get("StartLoad", clientaddr[0])), Dlisence)
                        self.signal_blue_showID.emit(str(self.cf.get("StartLoad", clientaddr[0])) + ':' + Dlisence)
                        pass

        else:
            print('收到数据长度不正确！')

    print('Exit RecvFromCamera')
    pass