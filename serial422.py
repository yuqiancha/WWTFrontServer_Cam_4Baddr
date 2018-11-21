import crcmod.predefined
import binascii
import os
from binascii import unhexlify
from binascii import hexlify
import serial.tools.list_ports
import time as t
from datetime import *
import threading
import serial
from Data import MyLock
from Data import SharedMemory
from os import path
from PyQt5 import QtCore
from PyQt5.QtCore import *
import logging
import configparser

MyLog = logging.getLogger('ws_debug_log')       #log data
MajorLog = logging.getLogger('ws_error_log')      #log error

class RS422Func(QThread):
    signal_newLock = pyqtSignal(MyLock)
    signal_Lock = pyqtSignal(MyLock)
    signal_ShowLockDown2 = pyqtSignal(str)
    signal_voice = pyqtSignal(str)
    def __init__(self):
        super(RS422Func, self).__init__()
        MyLog.info('Rs422Func init')
        MyLog.info('Rs422Func init')

        self.WaitCarComeTime = int(120)              #等待车子停进来的时间，2min不来就升锁
        self.WaitCarLeaveTime = int(300)             #车子停进来前5min，依旧是2min升锁，超出时间立刻升锁
        self.AfterCarLeaveTime = int(10)             #超出5min，认为车子是要走了，1min升锁
        self.ScanLockFreq = int(2)                   #默认2s扫描总线间隔
        try:
            self.cf = configparser.ConfigParser()
            self.cf.read(path.expandvars('$HOME') + '/Downloads/WWTFrontServer/Configuration.ini',encoding="utf-8-sig")

            self.WaitCarComeTime = self.cf.getint("StartLoad","WaitCarComeTime")
            self.WaitCarLeaveTime = self.cf.getint("StartLoad","WaitCarLeaveTime")
            self.AfterCarLeaveTime = self.cf.getint("StartLoad","AfterCarLeaveTime")
            self.ScanMaxLock = int(self.cf.get("StartLoad","ScanMaxLock")[2:],16)
            self.StartCount = int(self.cf.get("StartLoad","StartCount")[2:],16)
            self.ScanLockFreq = self.cf.getint("StartLoad","ScanLockFreq")
        except Exception as ex:
            MajorLog.error(ex+'From openfile /waitcartime')

        MyLog.debug("WaitCarComeTime:"+str(self.WaitCarComeTime))
        MyLog.debug("WaitCarLeaveTime:"+str(self.WaitCarLeaveTime))
        MyLog.debug("AfterCarLeaveTime:" + str(self.AfterCarLeaveTime))
        MyLog.debug("ScanMaxLock:" + str(self.ScanMaxLock))
        MyLog.debug("StartCount:" + str(self.StartCount))
        MyLog.debug("ScanLockFreq:" + str(self.ScanLockFreq))

        self.myEvent = threading.Event()
        self.mutex = threading.Lock()
        self.scanTag = False

        self.ThreadTag = True
#        global LockList
#        LockList = []
        global stridList
        stridList = []
        global crc16_xmode
        crc16_xmode = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xffff, xorOut=0x0000)

        self.mtimer = QTimer()
        self.mtimer.timeout.connect(self.LockAutoDown)
        self.mtimer.start(1000)

        self.mtimer2 = QTimer()
        self.mtimer2.timeout.connect(self.WaitCarStatusDisable)
        self.mtimer2.start(1000)

        # 2s一次，查询树莓派温度
        self.mtimer3 = QTimer()
        self.mtimer3.timeout.connect(self.QueryTemprature)
        self.mtimer3.start(2000)
        self.Temperature = 0

        pass

    def QueryTemprature(self):
        with open("/sys/class/thermal/thermal_zone0/temp") as tempFile:
            res = tempFile.read()
            res = str(int(int(res) / 1000))
            self.Temperature = res.zfill(2)


    def LockAutoDown(self):#定时器调用，检测无车满60s后自动发送升锁指令
        for lock in SharedMemory.LockList:
            if lock.arm == 'ff':                                                    #摇臂降下
                if lock.car == '00':                                                #车检状态为0代表没车
                    lock.nocaron += 1
                else:                                                               #车检状态不为0代表有车了
                    lock.nocaron = 0
                    lock.light = '01'

                if lock.detectlockdown:
                    lock.light = '10'  # 降锁绿灯
                    self.signal_voice.emit('lockdown')
                 #   music_path = '/home/pi/Downloads/WWTFrontServer/lockdown.mp3'
                 #   os.system('mplayer %s' % music_path)

                    lock.detectlockdown = False

                if lock.nocaron >= self.WaitCarComeTime and lock.waitcar == False:  #降锁后等待车子来停
                    lock.nocaron = 0
                    self.LockUp(lock.addr)
                    lock.carLeave = datetime.now()
                    lock.reservd2 = datetime.strftime(lock.carLeave, '%Y-%m-%d %H:%M:%S')
                #    lock.carStayTime = (str(lock.carLeave - lock.carCome).split('.'))[0]
                #    lock.reservd3 = lock.carStayTime
                    self.signal_Lock.emit(lock)
                    t.sleep(0.05)

                if lock.nocaron>=self.AfterCarLeaveTime and lock.carFinallyLeave==True:                        #车子离开等待60s就升锁
                    lock.carFinallyLeave = True
                    lock.nocaron = 0

                    self.LockUp(lock.addr)
                    t.sleep(10)
                    if lock.arm =='ff' and lock.car == '00':
                        self.LockUp(lock.addr)
                        t.sleep(10)
                    if lock.arm =='ff' and lock.car == '00':
                        self.LockUp(lock.addr)
                        t.sleep(10)

                    if lock.arm =='55':
                        lock.carLeave = datetime.now()
                        lock.reservd2 = datetime.strftime(lock.carLeave, '%Y-%m-%d %H:%M:%S')
                        #lock.carStayTime = (str(lock.carLeave - lock.carCome).split('.'))[0]
                        #lock.reservd3 = lock.carStayTime

                        lock.licenseID = '00000000'
                        self.signal_Lock.emit(lock)
                        t.sleep(0.05)



                    else:#连续多次未判断到升锁到位，认为出现故障
                        lock.machine = '88'
                        pass

            if lock.arm == '55' or lock.arm =='00':
                lock.nocaron = 0
        pass

    def WaitCarStatusDisable(self):
        for lock in SharedMemory.LockList:
            if lock.waitcar == True:
                lock.waitcartime +=1

            if lock.carFinallyLeave == False:
                lock.waitcartime2 +=1

            if lock.waitcartime >= self.WaitCarComeTime:
                lock.waitcar =False
                lock.waitcartime =0

            if lock.waitcartime2 >= self.WaitCarLeaveTime:
                lock.carFinallyLeave = True
                lock.waitcartime2 = 0
        pass

    def ScanPort(self):
        global ser
        MyLog.info("Enter ScanPort")
        MajorLog.info("Enter ScanPort")
        SharedMemory.LockList=[]
        stridList.clear()
        try:
            ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=0.1)
            if ser.isOpen():
                t = threading.Thread(target=InitPortList, args=(ser, self.ScanMaxLock, self.StartCount, self))
                t.start()
                t2 = threading.Thread(target=Normalchaxun, args=(ser, self))
                t2.start()
        except Exception as ex:
            MajorLog.error(ex)
            MyLog.error(ex)
            try:
                ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
                if ser.isOpen():
                    t = threading.Thread(target=InitPortList, args=(ser, self.ScanMaxLock, self.StartCount,self))
                    t.start()
                    t2 = threading.Thread(target=Normalchaxun, args=(ser, self))
                    t2.start()
            except Exception as ex:
                MajorLog.error(ex)
                MyLog.error(ex)

    def ChaXun(self,str):
        Address = str
        Tempstr = (Address + '0420010004').replace('\t', '').replace(' ', '').replace('\n', '').strip()
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
 #       print('ChaXun:'+SendStr)
        self.WriteToPort(SendStr)
        data = recv(ser, self)


    def LockCMDExcute2(self, str,license):
        MyLog.debug("触发Lockcmdexcute2----"+license)

        if len(str) == 10:
            if str[0:2] == '03':
                self.LockReset(str[2:10])
            elif str[0:2] == '04':
                self.LockUp(str[2:10])
            elif str[0:2] == '05':
                self.LockDown2(str[2:10],license)

            elif str[0:2] == '06':
                self.LockDownAndRest(str[2:10])
            elif str[0:2] == '07':
                self.LedOn(str[2:10])
            elif str[0:2] == '17':
                self.LedOff(str[2:10])
            elif str[0:2] == '08':
                self.EnableAlarm(str[2:10])
            elif str[0:2] == '09':
                self.DisableAlarm(str[2:10])
            elif str[0:2] == 'F1':
                self.ChaoShengTest(str[2:10])
            elif str[0:2] == 'F4':
                self.QuitTest(str[2:10])
            else:
                # to do other things here
                pass
        else:
            MyLog.error("FrontServer-->Lock的控制指令长度不正确")
            pass


    def LockCMDExcute(self, str):
        MyLog.debug("触发Lockcmdexcute")
        if len(str) == 10:
            if str[0:2] == '03':
                self.LockReset(str[2:10])
            elif str[0:2] == '04':
                self.LockUp(str[2:10])
            elif str[0:2] == '05':
                self.LockDown(str[2:10])
            elif str[0:2] == '06':
                self.LockDownAndRest(str[2:10])
            elif str[0:2] == '07':
                self.LedOn(str[2:10])
            elif str[0:2] == '17':
                self.LedOff(str[2:10])
            elif str[0:2] == '08':
                self.EnableAlarm(str[2:10])
            elif str[0:2] == '09':
                self.DisableAlarm(str[2:10])
            elif str[0:2] == 'F1':
                self.ChaoShengTest(str[2:10])
            elif str[0:2] == 'F4':
                self.QuitTest(str[2:10])
            else:
                # to do other things here
                pass
        else:
            MyLog.error("FrontServer-->Lock的控制指令长度不正确")
            pass

            # eb 90 08 01 05 10 02 FF 00 29 3A


    def ChaoShengTest(self, str):
        Address = str
        Tempstr = Address + '0601050300'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LockReset:' + SendStr)
        self.WriteToPort(SendStr)

    def QuitTest(self, str):
        Address = str
        Tempstr = Address + '0601050000'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LockReset:' + SendStr)

        self.WriteToPort(SendStr)


    def LockReset(self, str):
        Address = str
        Tempstr = Address + '051001FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LockReset:' + SendStr)

        self.WriteToPort(SendStr)

    def LockUp(self, str):
        Address = str
        Tempstr = Address + '051002FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LockUp:' + SendStr)
        self.WriteToPort(SendStr)
        for lock in SharedMemory.LockList:
            if lock.addr == Address:
                lock.light = '00'
        pass

    def LockDown2(self, str,license):
        print("LockDown2",str,license)
        self.signal_ShowLockDown2.emit("Start Sending LockDown:"+str)
        for lock in SharedMemory.LockList:
            if lock.addr ==str and lock.arm == '55':
                if lock.isBooked == True and lock.BookedID!=license:#已被预约，且来的车辆不是预约车辆
                    #声音提示已被预约
                    self.signal_voice.emit('booked')
                #    music_path = '/home/pi/Downloads/WWTFrontServer/booked.mp3'
                #    os.system('mplayer %s' % music_path)
                    pass
                else:#如果没有被预约，或预约车辆段傲来，直接降锁
                    Address = str
                    Tempstr = Address + '051003FF00'
                    strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
                    SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
                    MyLog.debug('LockDown:' + SendStr)
                    self.WriteToPort(SendStr)

                    self.signal_ShowLockDown2.emit("LockDownCMD Success！")

                    lock.isBooked = False#降锁后将预约状态清空
                    lock.car = '00'#将预约状态取消，通知后台

                    lock.waitcar = True
                    lock.waitcartime = 0
                    lock.waitcartime2 = 0

                    lock.carCome = datetime.now()
                    lock.reservd1 = datetime.strftime(lock.carCome,'%Y-%m-%d %H:%M:%S')
                    lock.reservd2 = ''
                    lock.reservd3 = ''
                    lock.carFinallyLeave = False

                    lock.licenseID = license
                    lock.StatusChanged = True
                    self.signal_Lock.emit(lock)

                   # lock.light='10' #降锁绿灯
                    lock.detectlockdown = True

                    pass
            else:#多次检测到车牌，会重复到这里，每次到这里就重新等待N分钟升锁，防止反复倒车时间不够
                lock.nocaron = 0

    def LockDown(self, str):
        Address = str
        Tempstr = Address + '051003FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LockDown:' + SendStr)
        self.WriteToPort(SendStr)

        for lock in SharedMemory.LockList:
            if lock.addr == Address:
                lock.waitcar = True
                lock.waitcartime = 0
                lock.waitcartime2 = 0

                lock.carCome = datetime.now()
                lock.reservd1 = datetime.strftime(lock.carCome,'%Y-%m-%d %H:%M:%S')
                lock.reservd2 = ''
                lock.reservd3 = ''
                lock.carFinallyLeave = False
                lock.isBooked = False  # 降锁后将预约状态清空
                lock.car = '00'  # 将预约状态取消，通知后台

             #   lock.light = '10'  # 降锁绿灯
                lock.detectlockdown = True

                pass

    def LockDownAndRest(self,str):
        Address = str
        Tempstr = Address + '051006FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LockDownAndRest:' + SendStr)
        self.WriteToPort(SendStr)

    def LedOn(self,str):
        Address = str
        Tempstr = Address + '051008FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LedOn:' + SendStr)
        self.WriteToPort(SendStr)


    def LedOff(self,str):
        Address = str
        Tempstr = Address + '051009FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('LedOff:' + SendStr)
        self.WriteToPort(SendStr)

    def EnableAlarm(self, str):
        Address = str
        Tempstr = Address + '051004FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('EnableAlarm:' + SendStr)
        self.WriteToPort(SendStr)

    def DisableAlarm(self, str):
        Address = str
        Tempstr = Address + '051005FF00'
        strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
        SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
        MyLog.debug('DisableAlarm:' + SendStr)
        self.WriteToPort(SendStr)

    def WriteToPort(self,SendStr):
 #       MyLog.info('SendToLock:' + SendStr)
        try:
            if ser.isOpen():
                self.mutex.acquire()
                d = bytes.fromhex(SendStr)
                ser.write(d)
                t.sleep(0.05)
                self.mutex.release()
        except Exception as ex4:
            print(ex4)
            print('Error from WriteToPort')
        pass


def InitPortList(ser,ScanMaxLock,StartCount,self):
    MyLog.info('Enter InitPortList')
 #   ScanMaxLock = 0x11000010

    if ser.isOpen():
        count = StartCount
        while count < ScanMaxLock:
            Address = hex(count)[2:].zfill(8)
            Tempstr = (Address + '0420010004').replace('\t', '').replace(' ', '').replace('\n', '').strip()
            count += 1

            strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
            SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
            d = bytes.fromhex(SendStr)
            ser.write(d)
            t.sleep(0.1)
            try:
                data = recv(ser,self)
            except Exception as ex:
                MyLog.error(ex)
        MyLog.debug(SharedMemory.LockList)

        count = StartCount
        while count < ScanMaxLock:
            Address = hex(count)[2:].zfill(8)
            Tempstr = (Address + '0420010004').replace('\t', '').replace(' ', '').replace('\n', '').strip()
            count += 1

            strcrc = hex(crc16_xmode(unhexlify(Tempstr)))[2:].zfill(4)
            SendStr = 'eb900b' + Tempstr + strcrc[2:4] + strcrc[0:2]
            d = bytes.fromhex(SendStr)
            ser.write(d)
            t.sleep(0.1)
            try:
                data = recv(ser, self)
            except Exception as ex:
                MyLog.error(ex)
        MyLog.debug(SharedMemory.LockList)

        self.scanTag = True
    else:
        MyLog.error('/dev/ttyAMA0 can not find!')


def Normalchaxun(serial,self):
    while self.scanTag==False:
        continue
    MyLog.info("ScanPortList Finished!")

    while self.ThreadTag:                                   #Main Loop is here!
        if serial.isOpen():
            if len(SharedMemory.LockList)>0:
                for lock in SharedMemory.LockList:
                    self.ChaXun(lock.addr)
                    t.sleep(0.05)                           #50ms等待时间，防止查询太快导致485紊乱，在Write和Recv中已有50ms延迟，此处可以省略
            else:
                MyLog.error('No Lock in the list from serial422.py Normalchaxun')
            t.sleep(self.ScanLockFreq)                                      #轮训间隔，每间隔N秒进行一次轮训获取连接车位锁的状态
    pass

def recv(serial,self):
    global data
    while self.ThreadTag:
        try:
            self.mutex.acquire()
            data = serial.read(30)
            t.sleep(0.05)
            self.mutex.release()
        except Exception as ex3:
            MyLog.error(ex3+'from serial422.py recv')
            pass
        if data =='':
            continue
        else:
        #    print(data)
            str_back = str(hexlify(data), "utf-8")
     #       MyLog.debug('RecvFromLock:' + str_back)
            if len(str_back)==38:
                if str_back[0:6]=='eb9010':
                    #strid = str_back[6:8]
                    strid = str_back[6:14]
                    MyLog.info('RecvFromLock:' + str_back)
                    if strid not in stridList:
                        stridList.append(strid)
                        #print('Not in the list and Add on')
                        newLock=MyLock()

                        newLock.addr = str_back[6:14]
                        newLock.reservd1 = ''
                        newLock.reservd2 = ''
                        newLock.reservd3 = ''
                        newLock.mode = str_back[20:22]
                        newLock.arm = str_back[22:24]
                        newLock.car = str_back[24:26]

                        #newLock.battery = str_back[26:28]
                        newLock.battery = str(self.Temperature)

                        newLock.reservd4 = str_back[28:30]
                        newLock.sensor = str_back[30:32]
                        newLock.machine = str_back[32:34]
                        newLock.crcH = str_back[34:36]
                        newLock.crcL = str_back[36:38]

                        newLock.camIP = str(self.cf.get("StartLoad",str_back[6:14]))

                        SharedMemory.LockList.append(newLock)
                        self.signal_newLock.emit(newLock)
                        MyLog.info('New lock detected!')
                    else:
                        for lock in SharedMemory.LockList:
                            if lock.addr == strid:

                                if lock.mode != str_back[20:22]:
                                    lock.mode = str_back[20:22]
                                    lock.StatusChanged = True

                                if lock.arm != str_back[22:24]:
                                    lock.arm = str_back[22:24]
                                    lock.StatusChanged = True

                                if lock.car == '55':#如果已被预约，不更新此状态，知道预约状态取消
                                    pass
                                else:
                                    if lock.car != str_back[24:26]:
                                        lock.car = str_back[24:26]
                                        lock.StatusChanged = True

                            #    if lock.battery != str_back[26:28]:
                            #        lock.battery = str_back[26:28]
                            #        lock.StatusChanged = True

                                lock.battery = str(self.Temperature)

                                if lock.reservd4 != str_back[28:30]:
                                    lock.reservd4 = str_back[28:30]
                                    lock.StatusChanged = True

                                if lock.sensor != str_back[30:32]:
                                    lock.sensor = str_back[30:32]
                                    lock.StatusChanged = True

                                if lock.machine != str_back[32:34]:
                                    lock.machine = str_back[32:34]
                                    lock.StatusChanged = True

                                lock.crcH = str_back[34:36]
                                lock.crcL = str_back[36:38]

                                self.signal_Lock.emit(lock)
            break
        t.sleep(0.05)

    return data
