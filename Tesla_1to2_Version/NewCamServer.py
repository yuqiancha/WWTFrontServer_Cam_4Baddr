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
from binascii import hexlify, unhexlify
import logging
import configparser
import os

MyLog2 = logging.getLogger('ws_debug_log2')  # log data
MajorLog = logging.getLogger('ws_error_log')  # log error
MyLogCam = logging.getLogger('ws_cam_log')  # cam log


class TcpServer(QThread):
    signal_detect = pyqtSignal(str, str)
    signal_blue_detect = pyqtSignal(str, str)
    signal_showID = pyqtSignal(str)
    signal_blue_showID = pyqtSignal(str)

    def __init__(self):
        super(TcpServer, self).__init__()
        print("TcpServer In")
        MyLogCam.info('TcpServer In')
        try:
            self.cf = configparser.ConfigParser()
            self.cf.read(path.expandvars('$HOME') + '/Downloads/WWTFrontServer/Configuration.ini', encoding="utf-8-sig")

        except Exception as ex:
            MajorLog(ex)

        self.ThreadTag = True

        host = ''
        port = 9005
        bufsize = 1024
        addr = (host, port)

        tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        tcpServer.bind(addr)
        tcpServer.listen(10)

        t2 = threading.Thread(target=AcceptConnection, args=(tcpServer, self))
        t2.start()

    def close(self):
        self.ThreadTag = False


def AcceptConnection(tcpServer, self):
    print('Waiting for connection ... ')

    while self.ThreadTag:
        tcpClient, addr = tcpServer.accept()

        t = threading.Thread(target=RecvFromCamera, args=(tcpClient, addr, self))
        t.start()


def RecvFromCamera(tcpClient, clientaddr, self):
    print('connect from ', clientaddr)

    timenow = int(0)
    timelast = int(0)
    timeSpent = int(0)

    tcpClient.send('1ACFCD0109D7'.encode('utf-8'))  # 连接上摄像机时候初始化为红灯
    time.sleep(0.5)
    tcpClient.send('1ACFCD1009D7'.encode('utf-8'))  # 连接上摄像机时候初始化为绿灯
    time.sleep(0.5)
    tcpClient.send('1ACFCD1109D7'.encode('utf-8'))  # 连接上摄像机时候初始化为黄灯
    time.sleep(0.5)
    tcpClient.send('1ACFCD0009D7'.encode('utf-8'))  # 连接上摄像机时候初始化为无灯
    time.sleep(0.5)

    lastLightStatus = 'ff'

    LeftLight = 'ff'
    RightLight = 'ff'

    LastLeftStatus ='ff'
    LastRightStatus ='ff'

    while self.ThreadTag:

        # 如果需要控制灯光，在接收前发送一次
        # 同时判断2个锁，只要有一个处于降锁无车，就绿灯
        for item in SharedMemory.LockList:
            if item.addr == str(self.cf.get("StartLoad", clientaddr[0]+"_L")):
                LeftLight = item.light

            if item.addr == str(self.cf.get("StartLoad", clientaddr[0]+"_R")):
                RightLight = item.light

            if LastRightStatus == RightLight and LastLeftStatus == LeftLight:
                pass
            else:
                if LeftLight == '10' or RightLight == '10':           # 左右只要有一个处于降锁无车状态就是绿灯
                    tcpClient.send('1ACFCD1009D7'.encode('utf-8'))
                elif LeftLight == '01' and RightLight == '01':        # 左右只要全部处于降锁有车状态就是红灯
                    tcpClient.send('1ACFCD0109D7'.encode('utf-8'))
                else:                                                 # 其余状态不亮
                    tcpClient.send('1ACFCD0109D7'.encode('utf-8'))
                    pass
                LastLeftStatus = LeftLight
                LastRightStatus = RightLight


        RecvStr = ''
        try:
            RecvStr = tcpClient.recv(1024).decode('utf-8')
        except Exception as ex:
            print(ex)
            MyLog2.error(ex)
            break
        print('[- data]', clientaddr[0], RecvStr)

        data = RecvStr.upper()
        if len(data) >= 18:
            if data == 'EB90A5FFFFFFFF09D7':
                pass
            elif data[0:4] == 'EB90':
                a1 = str.find('F1F')
                a2 = str.find('F2F')
                a3 = str.find('F3F')
                a4 = str.find('F4F')
                a5 = str.find('F5F')
                a6 = str.find('F6F')
                a7 = str.find('F7F')
                a8 = str.find('F8F')
                # 初始化DX1和DX2
                self.DX1 = 0
                self.DX2 = 0
                if a1 != -1 and a2 != -1 and a2 - a1 > 3:
                    self.Dlisence = str[a1 + 3:a2]
                if a2 != -1 and a3 != -1 and a3 - a2 > 3:
                    self.DColor = str[a2 + 3:a3]
                if a3 != -1 and a4 != -1 and a4 - a3 > 3:
                    self.DCarFlag = str[a3 + 3:a4]
                if a4 != -1 and a5 != -1 and a5 - a4 > 3:
                    self.DX1 = str[a4 + 3:a5]
                if a5 != -1 and a6 != -1 and a6 - a5 > 3:
                    self.DY1 = str[a5 + 3:a6]
                if a6 != -1 and a7 != -1 and a7 - a6 > 3:
                    self.DX2 = str[a6 + 3:a7]
                if a7 != -1 and a8 != -1 and a8 - a7 > 3:
                    self.DY2 = str[a7 + 3:a8]
                print(self.Dlisence + ',' + self.DColor + ',' + self.DCarFlag +
                      ',' + self.DX1 + ',' + self.DY1 + ',' + self.DX2 + ',' + self.DY2)

                # Only Tesla Can LockDown
                if self.DCarFlag == '50' and int(self.DX1) > 0 and int(self.DX2) > 0:
                    XValue = (int(self.DX1) + int(self.DX2)) / 2
                    # 发送日志显示
                    MyLogCam.info(
                        str(clientaddr[0]) + "-" + str(XValue) + "-" + str(
                            self.cf.get("StartLoad", clientaddr[0])) + ':' + self.Dlisence)

                    # 中轴判断线
                    JudgeValue = self.cf.getint("StartLoad", clientaddr[0]+'_Judge')

                    if JudgeValue >= XValue > 0:
                        timenow = int(time.time())
                        timeSpent = timenow - timelast
                        timelast = timenow
                        if timeSpent > 5:
                            self.signal_detect.emit('05' + str(self.cf.get("StartLoad", clientaddr[0]+"_L")), self.Dlisence)
                            self.signal_showID.emit(str(self.cf.get("StartLoad", clientaddr[0]+"_L")) + ':' + self.Dlisence)
                    elif 1920 >= XValue > JudgeValue:
                        timenow = int(time.time())
                        timeSpent = timenow - timelast
                        timelast = timenow
                        if timeSpent > 5:
                            self.signal_detect.emit('05' + str(self.cf.get("StartLoad", clientaddr[0])+"_R"), self.Dlisence)
                            self.signal_showID.emit(str(self.cf.get("StartLoad", clientaddr[0]+"_R")) + ':' + self.Dlisence)
                    else:
                        MyLogCam.info("Error XValue Range")

        else:
            print('收到数据长度不正确！')

    print('Exit RecvFromCamera')
    pass
