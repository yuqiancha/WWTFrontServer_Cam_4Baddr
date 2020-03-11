import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import binascii

from Ui_Form import Ui_Form
import time as t
import logging
import logging.config

from os import path
from NewCamServer import TcpServer
from datetime import *

import os

log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging.config')
logging.config.fileConfig(log_file_path)

MyLog = logging.getLogger('ws_debug_log')         #log data
MyLog2 = logging.getLogger('ws_debug_log2')       #log net data
MajorLog = logging.getLogger('ws_error_log')      #log error
MyLogCam = logging.getLogger('ws_cam_log')          #cam log

class Main(QWidget,Ui_Form):
    signal_LockCMD = pyqtSignal(str)
    signal_test = pyqtSignal(str,str)
    def __init__(self):
        super(Main,self).__init__()
        self.setupUi(self)
        self.init()

    def init(self):
        self.ClearTextTag = 0
        self.handlAllTag = False
        self.tableWidget.setColumnCount(13)
        self.tableWidget.setRowCount(0)
        header = []
        header.append('锁地址')
        header.append('降锁时刻')
        header.append('升锁时刻')
        header.append('停车时间')
        header.append('配对情况')
        header.append('摇臂状态')
        header.append('车检状态')
        header.append('电量')
        header.append('Reserved')
        header.append('传感故障')
        header.append('机构故障')
        header.append('校验1')
        header.append('校验2')
        self.tableWidget.setHorizontalHeaderLabels(header)

        self.pushButton_Reset.clicked.connect(self.btnResetClicked)
        self.pushButton_LockUp.clicked.connect(self.btnLockUpClicked)
        self.pushButton_LockDown.clicked.connect(self.btnLockDownClicked)
        self.pushButton_LockDownRest.clicked.connect(self.btnLockDownAndRestClicked)
        self.pushButton_LightOn.clicked.connect(self.btnLedOnClicked)
        self.pushButton_LightOff.clicked.connect(self.btnLedOffClicked)
        self.pushButton_EnableAlarm.clicked.connect(self.btnEnableAlarmClicked)
        self.pushButton_DisableAlarm.clicked.connect(self.btnDisableAlarmClicked)
        self.pushButton_LockPowerOn.clicked.connect(self.btnLPowerOnClicked)
        self.pushButton_LockPowerOff.clicked.connect(self.btnPowerOffClicked)
        self.pushButton_webstatus.clicked.connect(self.webstatusClicked)
        self.pushButton_exit.clicked.connect(self.btnExitClicked)
        self.pushButton_exit.clicked.connect(self.formcloseClicked)
        self.pushButton_4GReboot.clicked.connect(self.btn4GRebootClicked)
        self.tableWidget.clicked.connect(self.tableWidgetClicked)
        self.pushButton_ChaoShengTest.clicked.connect(self.btnChaoShengTestClicked)
        self.pushButton_QuitTest.clicked.connect(self.btnQuitTestClicked)
        self.pushButton_ReScan.clicked.connect(self.btnRescanClicked)
        self.pushButton_handleAll.clicked.connect(self.btnHandleAllClicked)
        pass

    def btnRescanClicked(self):
        rs422.ThreadTag = False
        rs422.scanTag = False
        t.sleep(3)

        #不知道直接Clear行不行
#        self.tableWidget.clear()

        #删除所有行，每次都删除第一行
        row_count = self.tableWidget.rowCount()
        for row_index in range(row_count):
            self.tableWidget.removeRow(0)
        t.sleep(2)
        rs422.ThreadTag = True
        rs422.ScanPort()
        pass

    def btnHandleAllClicked(self):
        if self.pushButton_handleAll.text() == '切换统一操作':
            self.pushButton_handleAll.setText('切换单独操作')
            self.handlAllTag = True
        else:
            self.pushButton_handleAll.setText('切换统一操作')
            self.handlAllTag = False

        pass

    def tableWidgetClicked(self):
        row = self.tableWidget.currentRow()
        addr = self.tableWidget.item(row,0).text()
        self.comboBox.setCurrentText(addr)
        pass

    def btn4GRebootClicked(self):
        gpio.Route4GReboot()

        pass

    def btnExitClicked(self):
        rs422.ThreadTag = False
        webservice.mtimer.stop()
        rs422.mtimer.stop()
        pass

    def btnResetClicked(self):
        music_path = '/home/pi/Downloads/WWTFrontServer/errorcar.mp3'
        os.system('mplayer %s' % music_path)


        self.signal_test.emit('192.168.0.17', '沪A78787')

        addr = self.comboBox.currentText()
        cmd = '03'
        self.signal_LockCMD.emit(cmd+addr)
        pass

    def btnLockUpClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = '04'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = '04'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass

    def btnLockDownClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = '05'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = '05'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass

    def btnLockDownAndRestClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = '06'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = '06'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass

    def btnLedOnClicked(self):
        addr = self.comboBox.currentText()
        cmd = '07'
        self.signal_LockCMD.emit(cmd+addr)
        pass

    #Test LED OFF,Did not show in the protocol
    def btnLedOffClicked(self):
        addr = self.comboBox.currentText()
        cmd = '17'
        self.signal_LockCMD.emit(cmd+addr)
        pass

    def btnEnableAlarmClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = '08'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = '08'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass

    def btnDisableAlarmClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = '09'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = '09'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass

    def btnChaoShengTestClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = 'F1'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = 'F1'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass

    def btnQuitTestClicked(self):
        if self.handlAllTag==False:
            addr = self.comboBox.currentText()
            cmd = 'F4'
            self.signal_LockCMD.emit(cmd+addr)
        else:
            row_count = self.tableWidget.rowCount()
            for row_index in range(row_count):
                addr = self.tableWidget.item(row_index, 0).text()
                cmd = 'F4'
                self.signal_LockCMD.emit(cmd + addr)
                t.sleep(1)
        pass


    def btnLPowerOnClicked(self):
        gpio.LockPowerOn()
        pass

    def btnPowerOffClicked(self):
        gpio.LockPowerOff()
        pass

    def ShowID(self,str1):
        strTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        print("ShowID:"+str1)
        self.textBrowser_Cam.append(strTime+":"+str1)
        MyLog2.info(str1)
        self.ClearTextTag +=1
        if self.ClearTextTag > 20:
            self.ClearTextTag = 0
            self.textBrowser_Cam.clear()
            pass

    def ShowID2(self,str1):
        strTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        print("ShowID:"+str1)
        self.textBrowser_Cam.append("SendToServer--"+strTime+":"+str1)
        MyLog2.info(str1)
        self.ClearTextTag +=1
        if self.ClearTextTag > 20:
            self.ClearTextTag = 0
            self.textBrowser_Cam.clear()
            pass

    def ShowDebug(self,str1):
        print("ShowDebug:"+str1)
        self.textBrowser_Cam.append("ShowDebug--"+str1)
        pass

    def ShowLockDown3(self,str1):
        self.textBrowser_Cam.append("Temp--"+str1)
        pass

    def ShowNewLock(self,MyLock):
        row_count = self.tableWidget.rowCount();
        self.tableWidget.insertRow(row_count)
        self.comboBox.addItem(MyLock.addr)

        item0 = QTableWidgetItem(MyLock.addr)
        item1 = QTableWidgetItem(MyLock.reservd1)
        item2 = QTableWidgetItem(MyLock.reservd2)
        item3 = QTableWidgetItem(MyLock.reservd3)
        item4 = QTableWidgetItem(MyLock.mode)
        item5 = QTableWidgetItem(MyLock.arm)
        item6 = QTableWidgetItem(MyLock.car)
        item7 = QTableWidgetItem(MyLock.battery)
        item8 = QTableWidgetItem(MyLock.reservd4)
        item9 = QTableWidgetItem(MyLock.sensor)
        item10 = QTableWidgetItem(MyLock.machine)
        item11 = QTableWidgetItem(MyLock.crcH)
        item12 = QTableWidgetItem(MyLock.crcL)

        self.tableWidget.setItem(row_count,0,item0)
        self.tableWidget.setItem(row_count, 1, item1)
        self.tableWidget.setItem(row_count, 2, item2)
        self.tableWidget.setItem(row_count, 3, item3)
        self.tableWidget.setItem(row_count,4,item4)
        self.tableWidget.setItem(row_count, 5, item5)
        self.tableWidget.setItem(row_count, 6, item6)
        self.tableWidget.setItem(row_count, 7, item7)
        self.tableWidget.setItem(row_count,8,item8)
        self.tableWidget.setItem(row_count, 9, item9)
        self.tableWidget.setItem(row_count, 10, item10)
        self.tableWidget.setItem(row_count, 11, item11)
        self.tableWidget.setItem(row_count,12,item12)
        pass

    def ShowLock(self,MyLock):
        row_count = self.tableWidget.rowCount();
        for row_index in range(row_count):
            if self.tableWidget.item(row_index,0).text() == MyLock.addr:
                item0 = QTableWidgetItem(MyLock.addr)
                item1 = QTableWidgetItem(MyLock.reservd1)
                item2 = QTableWidgetItem(MyLock.reservd2)
                item3 = QTableWidgetItem(MyLock.reservd3)
            #    item1 = QTableWidgetItem(MyLock.carCome)
             #   item2 = QTableWidgetItem(MyLock.carLeave)
              #  item3 = QTableWidgetItem(MyLock.carStayTime)

                item4 = QTableWidgetItem(MyLock.licenseID)

                str_arm = '未知'
                if MyLock.arm=='55':
                    str_arm='升起'
                elif MyLock.arm=='ff':
                    str_arm='降下'
                elif MyLock.arm=='00':
                    str_arm='升降中'
                else:
                    str_arm = MyLock.arm
                item5 = QTableWidgetItem(str_arm)

                str_car = '未知'
                if MyLock.car=='00':
                    str_car='无车'
                elif MyLock.car=='ff':
                    str_car='有车'
                else:
                    str_car = MyLock.car
                item6 = QTableWidgetItem(str_car)

                item7 = QTableWidgetItem(MyLock.battery)

                item8 = QTableWidgetItem(MyLock.reservd4)

                str_sensor = '未知'
                if MyLock.sensor == '55':#地磁故障
                    str_sensor ='地磁故障'
                elif MyLock.sensor == '11':#探头1故障
                    str_sensor ='探头1故障'
                elif MyLock.sensor == '22':#探头2故障
                    str_sensor ='探头2故障'
                elif MyLock.sensor == '33':#两个探头都故障
                    str_sensor ='探头都故障'
                else:
                    str_sensor = MyLock.sensor

                item9 = QTableWidgetItem(str_sensor)

                str_machine = '未知'
                if MyLock.machine == '55':#摇臂遇阻
                    str_machine = '摇臂遇阻'
                elif MyLock.machine == 'FF':#摇臂破坏
                    str_machine = '摇臂破坏'
                elif MyLock.machine == '88':#电机连轴故障
                    str_machine = '电机连轴故障'
                else:
                    str_machine = MyLock.machine
                item10 = QTableWidgetItem(str_machine)

                item11 = QTableWidgetItem(MyLock.crcH)
                item12 = QTableWidgetItem(MyLock.crcL)

                self.tableWidget.setItem(row_index, 0, item0)
                self.tableWidget.setItem(row_index, 1, item1)
                self.tableWidget.setItem(row_index, 2, item2)
                self.tableWidget.setItem(row_index, 3, item3)
                self.tableWidget.setItem(row_index, 4, item4)
                self.tableWidget.setItem(row_index, 5, item5)
                self.tableWidget.setItem(row_index, 6, item6)
                self.tableWidget.setItem(row_index, 7, item7)
                self.tableWidget.setItem(row_index, 8, item8)
                self.tableWidget.setItem(row_index, 9, item9)
                self.tableWidget.setItem(row_index, 10, item10)
                self.tableWidget.setItem(row_index, 11, item11)
                self.tableWidget.setItem(row_index, 12, item12)

        pass

    def webstatusClicked(self):
        print(self.pushButton_webstatus.text())
        if self.pushButton_webstatus.text() == 'WebServiceOn':
            self.pushButton_webstatus.setText('WebServiceOff')
            webservice.run()
        else:
            self.pushButton_webstatus.setText('WebServiceOn')
            webservice.close()
        pass

    def formcloseClicked(self):
        webservice.close()
        t.sleep(1)
        QCoreApplication.quit()
        pass

if __name__ == '__main__':
    app=QApplication(sys.argv)
    ex=Main()
    ex.show()

    myTcpServer = TcpServer()
    myTcpServer.signal_detect.connect(rs422.LockCMDExcute2)
    myTcpServer.signal_showID.connect(ex.ShowID)
    myTcpServer.signal_blue_showID.connect(ex.ShowID2)


    sys.exit(app.exec_())