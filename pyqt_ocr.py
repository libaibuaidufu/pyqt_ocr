import configparser
import os
import sys

import keyboard
from PyQt5.QtCore import Qt, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QPen, QColor, QCursor
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QTextEdit, QAction, QMenu, QSystemTrayIcon, \
    QHBoxLayout, QLabel, QLineEdit, QGridLayout

from ocr import get_content


class QPixmap2QByteArray(object):
    def __call__(self, q_image):
        """
            Args:
                 q_image: 待转化为字节流的QImage。
            Returns:
                 q_image转化成的byte array。
        """
        # 获取一个空的字节数组
        byte_array = QByteArray()
        # 将字节数组绑定到输出流上
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        # 将数据使用png格式进行保存
        q_image.save(buffer, "png", quality=100)
        return byte_array


class MyWin(QWidget):
    oksignal_content = pyqtSignal()
    oksignal_update_config = pyqtSignal()

    def __init__(self):
        super(MyWin, self).__init__()
        self.is_add = False
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.read_config()
        self.clipboard = QApplication.clipboard()
        self.initUi()

        # https://stackoverflow.com/questions/56949297/how-to-fix-importerror-unable-to-find-qt5core-dll-on-path-after-pyinstaller-b

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def initUi(self):
        # 窗口大小设置为600*500
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("截图")
        self.resize(400, 300)
        image_path = self.resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))

        hbox = QHBoxLayout()
        self.btn = QPushButton('普通识别', self, clicked=self.click_btn)
        self.btn2 = QPushButton('精度识别', self, clicked=self.click_btn2)
        self.btn3 = QPushButton('追加文本', self, clicked=self.click_btn3)
        self.btn_copy = QPushButton('复制文本', self, clicked=self.click_btn_copy)
        self.btn4 = QPushButton('修改配置', self, clicked=self.click_btn4)
        self.btn3.setCheckable(True)
        # self.btn.clicked.connect(self.click_btn)
        # self.btn.setShortcut('F4')  # 设置快捷键
        hbox.addWidget(self.btn)
        hbox.addWidget(self.btn2)
        hbox.addWidget(self.btn3)
        hbox.addWidget(self.btn_copy)
        hbox.addWidget(self.btn4)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        vbox.addWidget(self.textEdit)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.oksignal_content.connect(lambda: self.set_text_content())
        self.oksignal_update_config.connect(lambda: self.read_config())
        keyboard.add_hotkey('F4', self.btn.click)

        # self.addSystemTray()  # 设置系统托盘

    def addSystemTray(self):
        minimizeAction = QAction("Mi&nimize", self, triggered=self.hide)
        maximizeAction = QAction("Ma&ximize", self, triggered=self.showMaximized)
        restoreAction = QAction("&Restore", self, triggered=self.showNormal)
        quitAction = QAction("&Quit", self, triggered=self.close)
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(minimizeAction)
        self.trayIconMenu.addAction(maximizeAction)
        self.trayIconMenu.addAction(restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(quitAction)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon("image\logo.ico"))
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.show()

    def set_text_content(self):
        if self.is_add:
            value = self.textEdit.toPlainText()
            data = value + self.screenshot.content
        else:
            data = self.screenshot.content
        self.textEdit.setText(data)
        self.screenshot.close()
        self.showNormal()

    def read_config(self):
        self.config = configparser.ConfigParser()
        config_path = 'config.ini'
        self.config.read(config_path)
        # config_path = pkgutil.get_data('config', 'config.ini')
        # help_utf = config_path.decode('UTF-8', 'ignore')
        # self.config.read_string(help_utf)
        baidu = self.config["baidu"]
        self.APP_ID = baidu["APP_ID"]
        self.API_KEY = baidu["API_KEY"]
        self.SECRET_KEY = baidu["SECRET_KEY"]

    def click_btn(self):
        self.showMinimized()
        self.screenshot = ScreenShotsWin(self.APP_ID, self.API_KEY, self.SECRET_KEY, self.oksignal_content)
        # self.screenshot.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.screenshot.showFullScreen()

    def click_btn2(self):
        self.showMinimized()
        self.screenshot = ScreenShotsWin(self.APP_ID, self.API_KEY, self.SECRET_KEY, self.oksignal_content,
                                         is_precision=True)
        # self.screenshot.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.screenshot.showFullScreen()

    def click_btn3(self):
        if self.is_add:
            self.is_add = False
        else:
            self.is_add = True

    def click_btn4(self):
        self.update_config = UpdateConfig(self.oksignal_update_config)
        self.update_config.show()

    def click_btn_copy(self):
        value = self.textEdit.toPlainText()
        self.clipboard.setText(value)


class ScreenShotsWin(QWidget):
    # 定义一个信号
    oksignal = pyqtSignal()

    def __init__(self, APP_ID, API_KEY, SECRET_KEY, content_single, is_precision=False):
        super(ScreenShotsWin, self).__init__()
        self.initUI()
        self.start = (0, 0)  # 开始坐标点
        self.end = (0, 0)  # 结束坐标点
        self.content_single = content_single
        self.content = None
        self.is_precision = is_precision
        self.APP_ID = APP_ID
        self.API_KEY = API_KEY
        self.SECRET_KEY = SECRET_KEY
        self.setCursor(QCursor(Qt.CrossCursor))

    def initUI(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.05)

        self.oksignal.connect(lambda: self.screenshots(self.start, self.end))

    def screenshots(self, start, end):
        '''
        截图功能
        :param start:截图开始点
        :param end:截图结束点
        :return:
        '''

        x = min(start[0], end[0])
        y = min(start[1], end[1])
        width = abs(end[0] - start[0])
        height = abs(end[1] - start[1])

        des = QApplication.desktop()
        screen = QApplication.primaryScreen()
        if screen:
            self.setWindowOpacity(0.0)
            pix = screen.grabWindow(des.winId(), x, y, width, height)  # type:QPixmap
            img_byte = QPixmap2QByteArray()(pix.toImage())
            # pix.save('test.jpg')
            # self.content = get_content(self.APP_ID, self.API_KEY, self.SECRET_KEY, img_path='test.jpg',is_precision=self.is_precision)
            self.content = get_content(self.APP_ID, self.API_KEY, self.SECRET_KEY, img_byte=img_byte,
                                       is_precision=self.is_precision)
            self.content_single.emit()

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


class UpdateConfig(QWidget):

    def __init__(self, oksignal_update_config):
        super().__init__()
        self.oksignal_update_config = oksignal_update_config
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.config = configparser.ConfigParser()
        self.config_path = 'config.ini'
        self.config.read(self.config_path)
        # config_path = pkgutil.get_data('config', 'config.ini')
        # help_utf = config_path.decode('UTF-8', 'ignore')
        # self.config.read_string(help_utf)
        baidu = self.config["baidu"]
        self.APP_ID = baidu["APP_ID"]
        self.API_KEY = baidu["API_KEY"]
        self.SECRET_KEY = baidu["SECRET_KEY"]
        image_path = self.resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))
        self.initUI()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def initUI(self):
        title = QLabel('APP_ID')
        author = QLabel('API_KEY')
        review = QLabel('SECRET_KEY')
        register_net = QLabel('注册网址')

        self.app_id_Edit = QLineEdit()
        self.api_key_Edit = QLineEdit()
        self.secret_key_Edit = QLineEdit()
        self.secret_key_Edit2 = QLineEdit()
        self.app_id_Edit.setText(self.APP_ID)
        self.api_key_Edit.setText(self.API_KEY)
        self.secret_key_Edit.setText(self.SECRET_KEY)
        self.secret_key_Edit2.setText("https://cloud.baidu.com/product/ocr/general")
        # self.secret_key_Edit2.setDisabled(True)
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(title, 1, 0)
        grid.addWidget(self.app_id_Edit, 1, 1)

        grid.addWidget(author, 2, 0)
        grid.addWidget(self.api_key_Edit, 2, 1)

        grid.addWidget(review, 3, 0)
        grid.addWidget(self.secret_key_Edit, 3, 1)

        grid.addWidget(register_net, 4, 0)
        grid.addWidget(self.secret_key_Edit2, 4, 1)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.btn = QPushButton('保存', self, clicked=self.save_config)
        self.btn2 = QPushButton('恢复默认', self, clicked=self.update_default_config)
        vbox.addLayout(grid)
        hbox.addWidget(self.btn)
        hbox.addWidget(self.btn2)
        hbox.addStretch(1)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('修改百度api配置')

    def save_config(self):
        APP_ID = self.app_id_Edit.text()
        API_KEY = self.api_key_Edit.text()
        SECRET_KEY = self.secret_key_Edit.text()
        self.config.set("baidu", "APP_ID", APP_ID)  # set to modify
        self.config.set("baidu", "API_KEY", API_KEY)  # set to modify
        self.config.set("baidu", "SECRET_KEY", SECRET_KEY)  # set to modify
        with open(self.config_path, "w+") as f:
            self.config.write(f)
        self.oksignal_update_config.emit()
        self.close()

    def update_default_config(self):
        default = self.config["default"]
        default_APP_ID = default["APP_ID"]
        default_API_KEY = default["API_KEY"]
        default_SECRET_KEY = default["SECRET_KEY"]
        self.config.set("baidu", "APP_ID", default_APP_ID)  # set to modify
        self.config.set("baidu", "API_KEY", default_API_KEY)  # set to modify
        self.config.set("baidu", "SECRET_KEY", default_SECRET_KEY)  # set to modify
        with open(self.config_path, "w+") as f:
            self.config.write(f)
        self.app_id_Edit.setText(default_APP_ID)
        self.api_key_Edit.setText(default_API_KEY)
        self.secret_key_Edit.setText(default_SECRET_KEY)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 修改样式
    dbb = MyWin()
    dbb.show()
    sys.exit(app.exec_())
