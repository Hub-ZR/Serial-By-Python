import sys
import time
import threading
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from cls_ui import *


class MyWindow(QMainWindow, Ui_Dialog):  # 继承UI中用于定义窗口及其控件的类：Ui_Dialog
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("ZR")
        # 数据成员初始化
        self.Com_Dict = {}
        self.Com = serial.Serial()
        self.byte_interval = 0.0
        self.send_log = ""
        self.rx_log = ""
        self.tx_data_total = 0
        self.rx_data_total = 0
        self.lineEdit_2.setText("Tx:0")
        self.lineEdit_3.setText("Rx:0")
        self.__thread = True

        # 定时发送数据
        self.send_timer = QTimer()
        self.send_timer.timeout.connect(self.send_data)
        self.checkBox_2.stateChanged.connect(self.send_data_cyclic)

        self.pushButton_3.clicked.connect(self.send_data)
        self.pushButton.clicked.connect(self.serial_toggle)
        self.commandLinkButton_3.clicked.connect(self.reset_counter)
        self.commandLinkButton_4.clicked.connect(self.clear_win)


    def reset_counter(self):
        self.lineEdit_2.setText("Tx:0")
        self.lineEdit_3.setText("Rx:0")
        self.tx_data_total = 0
        self.rx_data_total = 0

    def clear_win(self):
        self.ReadBrowser.clear()
        self.plainTextEdit.clear()
        self.lineEdit_2.setText("Tx:0")
        self.lineEdit_3.setText("Rx:0")
        self.tx_data_total = 0
        self.rx_data_total = 0

    # 获取当前时间
    @staticmethod
    def get_current_time():
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return current_time

    def port_check(self):
        port_list = list()
        port_list2 = list()
        while True:
            port_list2 = serial.tools.list_ports.comports()
            port_list2.sort()
            if port_list != port_list2:
                port_list = port_list2
                self.ComboBox_3.clear()
                for port in port_list:
                    self.Com_Dict["%s" % port[0]] = "%s" % port[1]

                    self.ComboBox_3.addItem(port[0])
                if len(self.Com_Dict) == 0:
                    self.ComboBox_3.setText(" 无串口")
            else:
                pass
            time.sleep(2)

    def serial_toggle(self):
        if self.Com.isOpen():
            self.__thread = False   # 停止接收线程对串口的监听
            self.Com.close()
            self.ComboBox_2.setDisabled(False)
            self.ComboBox_3.setEnabled(True)
            self.ComboBox_4.setEnabled(True)
            self.ComboBox_5.setEnabled(True)
            self.ComboBox_6.setEnabled(True)
            self.pushButton.setText("打开串口")
            return
        self.Com.port = self.ComboBox_3.currentText()
        self.Com.parity = self.ComboBox_4.currentText()[0]
        self.Com.baudrate = int(self.ComboBox_2.currentText())
        self.Com.bytesize = int(self.ComboBox_5.currentText())
        self.Com.stopbits = int(self.ComboBox_6.currentText())

        try:
            self.Com.open()
        except:
            QMessageBox.critical(self, "错误", "串口可能被占用！请检查")
            return None
        if self.Com.isOpen():
            self.ComboBox_2.setEnabled(False)
            self.ComboBox_3.setEnabled(False)
            self.ComboBox_4.setEnabled(False)
            self.ComboBox_5.setEnabled(False)
            self.ComboBox_6.setEnabled(False)
            self.pushButton.setText("关闭串口")
            self.byte_interval = (1/self.Com.baudrate)*(1 + self.Com.bytesize + self.Com.stopbits + 1)
            self.byte_interval = float(format(float(self.byte_interval), '.3f')) + 0.001    # 计算波特率对应2字节间隔
            thread_rx = threading.Thread(target=self.rx_data)  # 创建接收线程
            thread_rx.start()

    def send_data(self):
        if self.Com.isOpen():
            input_data = self.plainTextEdit.toPlainText()

            # 数据自动添加回车换行
            if self.checkBox.isChecked():
                if self.radioButton_2.isChecked():
                    input_data = input_data + "0D0A"
                else:
                    input_data = input_data + "\r\n"
            else:
                pass

            if input_data != "":
                if self.radioButton_2.isChecked():  # 16进制
                    input_data = input_data.strip()
                    send_list = []
                    while input_data != "":
                        try:
                            send_num = int(input_data[0:2], 16)
                        except ValueError:
                            QMessageBox.critical(self, '错误', '请输入十六进制数据，以空格分开!')
                            return None
                        input_data = input_data[2:].strip()
                        send_list.append(send_num)
                    input_data = bytes(send_list)
                else:
                    input_data = str(input_data).encode("utf-8")

                send_num = self.Com.write(input_data)
                current_time = self.get_current_time()
                self.send_log = "[" + str(current_time) + "]发→" + input_data.decode('utf-8')
                self.ReadBrowser.append(self.send_log)  # 显示发送数据log
                self.ReadBrowser.moveCursor(self.ReadBrowser.textCursor().End)  # 滚轮效果实现
                self.tx_data_total += send_num
                self.lineEdit_2.setText("Tx:" + str(self.tx_data_total))   # 发送计数
        else:
            QMessageBox.critical(self, "错误", "串口未打开！")
            return None

    def send_data_cyclic(self):
        if self.checkBox_2.isChecked():
            if not self.Com.isOpen():
                self.checkBox_2.setCheckState(False)  # 关闭循环发送
                QMessageBox.critical(self, "错误", "串口未打开！")
            elif not self.plainTextEdit.toPlainText():
                self.checkBox_2.setCheckState(False)  # 关闭循环发送
                QMessageBox.critical(self, "错误", "输入为空！")
            else:
                try:
                    self.send_timer.start(int(self.lineEdit.text()))
                    self.lineEdit.setEnabled(False)
                    self.plainTextEdit.setEnabled(False)
                    self.pushButton_3.setEnabled(False)
                except ValueError:
                    self.checkBox_2.setCheckState(False)  # 关闭循环发送
                    QMessageBox.critical(self, "错误", "循环时间为空！")
                    return None
        else:
            self.checkBox_2.setCheckState(False)  # 关闭循环发送
            self.send_timer.stop()
            self.lineEdit.setEnabled(True)
            self.plainTextEdit.setEnabled(True)
            self.pushButton_3.setEnabled(True)

    def rx_data(self):
        while self.__thread:    # 串口关闭时的问题
            try:
                if not self.Com.in_waiting:
                    time.sleep(0.01)
                    continue
                else:
                    rx_num = self.Com.inWaiting()
                    # time.sleep(0.001)
                    time.sleep(self.byte_interval)
                    if rx_num != self.Com.in_waiting:
                        continue
                    rx_data = self.Com.read(rx_num)
                    self.rx_data_total += rx_num
                    current_time = self.get_current_time()
                    if self.radioButton_3.isChecked():
                        self.rx_log = "[" + str(current_time) + "]收→" + rx_data.decode('utf-8')
                    else:
                        out_s = ''
                        for i in range(0, len(rx_data)):
                            out_s = out_s + '{:02X}'.format(rx_data[i]) + ' '
                        self.rx_log = "[" + str(current_time) + "]收→" + out_s
                    self.ReadBrowser.append(self.rx_log)  # 显示接收数据log
                    self.ReadBrowser.moveCursor(self.ReadBrowser.textCursor().End)  # 滚轮效果实现
                    self.lineEdit_3.setText("Rx:" + str(self.rx_data_total))  # 接收计数
            except:
                self.serial_toggle()
                return None



if __name__ == '__main__':
    app = QApplication(sys.argv)    # 创建QApplication对象，创建QT窗口
    myWin = MyWindow()
    thread_PortCheck = threading.Thread(target=myWin.port_check)  # 创建串口检测线程
    thread_PortCheck.start()
    myWin.show()
    sys.exit(app.exec_())
