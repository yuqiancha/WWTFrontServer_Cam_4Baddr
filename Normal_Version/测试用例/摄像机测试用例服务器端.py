from socket import *
from time import ctime
import os

#host = ''
#port = 13140

host  = input('IP地址>>> ').encode(encoding="utf-8")
port  = int(input('端口号>>> ').encode(encoding="utf-8"))

bufsize = 1024
addr = (host,port)

tcpServer = socket(AF_INET,SOCK_STREAM)
tcpServer.bind(addr)
tcpServer.listen(5) #这里设置监听数为5(默认值),有点类似多线程。

while True:
    print('Waiting for connection...')
    tcpClient,addr = tcpServer.accept() #拿到5个中一个监听的tcp对象和地址
    print('[+]...connected from:',addr)

    while True:
        data=''
        try:
            data = tcpClient.recv(bufsize).decode(encoding="utf-8")
        except:
            print("异常退出，可能编码格式不正确")
            input('输入任何按钮退出>>> ').encode(encoding="utf-8")

        print('   [-]data:',data)
        if not data:
            print('not data,recv err')
            tcpClient.send("Recved Failed".encode(encoding="utf-8"))
            break
        else:
            str = data.upper()
            if len(str)>=18:
                printstr = '收到信息:'
                if str=='EB90A5FFFFFFFF09D7':
                    tcpClient.send(("Recvd Heart".encode(encoding="utf-8")))
                elif str[0:4]=='EB90' and str[-4:]=='09D7':
                    if len(str)>=42:
                        a1 = str.find('F1F')
                        a2 = str.find('F2F')
                        a3 = str.find('F3F')
                        a4 = str.find('F4F')
                        a5 = str.find('F5F')
                        a6 = str.find('F6F')
                        a7 = str.find('F7F')
                        a8 = str.find('F8F')
                        if a1!=-1 and a2!=-1 and a2-a1>3:
                            printstr += "车牌["+str[a1+3:a2]+"]\n"
                        if a2!= -1 and a3!= -1 and a3-a2>3:
                            printstr += "颜色[" + str[a2+3:a3] + "]\n"
                        if a3 != -1 and a4 != -1 and a4 - a3 > 3:
                            printstr += "车标[" + str[a3 + 3:a4] + "]\n"
                        if a4 != -1 and a5 != -1 and a5 - a4 > 3:
                            printstr += "坐标X1[" + str[a4 + 3:a5] + "]\n"
                        if a5 != -1 and a6 != -1 and a6 - a5 > 3:
                            printstr += "坐标Y1[" + str[a5 + 3:a6] + "]\n"
                        if a6 != -1 and a7 != -1 and a7 - a6 > 3:
                            printstr += "坐标X2[" + str[a6 + 3:a7] + "]\n"
                        if a7 != -1 and a8 != -1 and a8 - a7 > 3:
                            printstr += "坐标Y2[" + str[a7 + 3:a8] + "]\n"
                        tcpClient.send(printstr.encode(encoding="utf-8"))
                    else:
                        tcpClient.send("收到识别信息长度不满足最小长度".encode(encoding="utf-8"))
                else:
                    tcpClient.send("收到信息帧头帧尾不满足格式".encode(encoding="utf-8"))
            else:
                tcpClient.send("收到数据长度小于心跳长度".encode(encoding="utf-8"))

    tcpClient.close() #
    print(addr,'End')
tcpServer.close() #两次关闭，第一次是tcp对象，第二次是tcp服务器
