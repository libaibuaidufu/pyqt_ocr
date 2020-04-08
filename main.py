#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by GJ on 2017/11/21
import os
import sys

import keyboard
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QPen, QColor
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QTextEdit, QAction, QMenu, QSystemTrayIcon, \
    QHBoxLayout

from orc import get_content


# class MyWin(QMainWindow):
class MyWin(QWidget):
    oksignal_content = pyqtSignal()

    def __init__(self):
        super(MyWin, self).__init__()
        self.initUi()

    def initUi(self):
        # 窗口大小设置为600*500
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("截图")
        self.resize(400, 300)
        self.setWindowIcon(QIcon("one3.ico"))

        hbox = QHBoxLayout()
        self.btn = QPushButton('截图', self, clicked=self.click_btn)
        self.btn2 = QPushButton('good截图', self, clicked=self.click_btn)
        # self.btn.clicked.connect(self.click_btn)
        # self.btn.setShortcut('F4')  # 设置快捷键
        hbox.addWidget(self.btn)
        hbox.addWidget(self.btn2)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        vbox.addWidget(self.textEdit)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.oksignal_content.connect(lambda: self.set_text_content())
        # keyboard.add_hotkey('ctrl+shift+a', print, args=('triggered', 'hotkey'))
        keyboard.add_hotkey('F4', self.btn.click)

        # self.addSystemTray()  # 设置系统托盘

    def addSystemTray(self):
        minimizeAction = QAction("Mi&nimize", self, triggered=self.hide)
        maximizeAction = QAction("Ma&ximize", self, triggered=self.showMaximized)
        restoreAction = QAction("&Restore", self, triggered=self.showNormal)
        # f4 = QAction("&截图", self, triggered=self.click_btn)
        # f4.setShortcut("F4")
        quitAction = QAction("&Quit", self, triggered=self.close)
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(minimizeAction)
        self.trayIconMenu.addAction(maximizeAction)
        self.trayIconMenu.addAction(restoreAction)
        # self.trayIconMenu.addAction(f4)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(quitAction)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon("one3.ico"))
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.show()

    def set_text_content(self):
        self.textEdit.setText(self.screenshot.content)
        self.screenshot.close()
        self.showNormal()

    def click_btn(self):
        self.showMinimized()
        self.screenshot = ScreenShotsWin(self.oksignal_content)
        # self.screenshot.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.screenshot.showFullScreen()


# class ScreenShotsWin(QMainWindow):
class ScreenShotsWin(QWidget):
    # 定义一个信号
    oksignal = pyqtSignal()

    def __init__(self, content_single):
        super(ScreenShotsWin, self).__init__()
        self.initUI()
        self.start = (0, 0)  # 开始坐标点
        self.end = (0, 0)  # 结束坐标点
        self.content_single = content_single
        self.content = None

    def initUI(self):
        # self.showFullScreen()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.05)
        # self.setWindowOpacity(0.5)
        # self.btn_ok = QPushButton('保存', self)

        self.oksignal.connect(lambda: self.screenshots(self.start, self.end))

    def screenshots(self, start, end):
        '''
        截图功能
        :param start:截图开始点
        :param end:截图结束点
        :return:
        '''
        # logger.debug('开始截图,%s, %s', start, end)

        x = min(start[0], end[0])
        y = min(start[1], end[1])
        width = abs(end[0] - start[0])
        height = abs(end[1] - start[1])

        des = QApplication.desktop()
        screen = QApplication.primaryScreen()
        if screen:
            self.setWindowOpacity(0.0)
            pix = screen.grabWindow(des.winId(), x, y, width, height)  # type:QPixmap
            # print(dir(pix))
            pix.save("test.jpg")
            self.content = get_content("test.jpg")
            os.remove("test.jpg")
            self.content_single.emit()
            # fileName = QFileDialog.getSaveFileName(self, '保存图片', '.', ".png;;.jpg")
            # if fileName[0]:
            #     pix.save(fileName[0] + fileName[1])

        self.close()

    def paintEvent(self, event):
        '''
        给出截图的辅助线
        :param event:
        :return:
        '''
        # logger.debug('开始画图')
        x = self.start[0]
        y = self.start[1]
        w = self.end[0] - x
        h = self.end[1] - y
        pp = QPainter(self)
        # col = QColor(0, 0, 0)
        # col.setNamedColor('#0099CC')
        pp.begin(self)
        pen = QPen(Qt.black, 1, Qt.SolidLine)
        pp.setPen(pen)
        pp.setBrush(QColor(200, 0, 0))
        pp.drawRect(x, y, w, h)
        pp.end()

    def mousePressEvent(self, event):
        # 点击左键开始选取截图区域
        if event.button() == Qt.LeftButton:
            self.start = (event.pos().x(), event.pos().y())
            # logger.debug('开始坐标：%s', self.start)

    def mouseReleaseEvent(self, event):
        # 鼠标左键释放开始截图操作
        if event.button() == Qt.LeftButton:

            self.end = (event.pos().x(), event.pos().y())
            # logger.debug('结束坐标：%s', self.end)
            x = self.start[0]
            y = self.start[1]
            w = self.end[0] - x
            h = self.end[1] - y
            if w == 0 and h == 0:
                self.close()
            else:
                self.oksignal.emit()
            # logger.debug('信号提交')
            # 进行重新绘制
            self.update()

    def mouseMoveEvent(self, event):
        # 鼠标左键按下的同时移动鼠标绘制截图辅助线
        if event.buttons() and Qt.LeftButton:
            self.end = (event.pos().x(), event.pos().y())
            # 进行重新绘制
            self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dbb = MyWin()
    dbb.show()
    sys.exit(app.exec_())
