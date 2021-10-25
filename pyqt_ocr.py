import configparser
import os
import pathlib
import sys
import traceback

import keyboard
from PyQt5.QtCore import Qt, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QPen, QColor, QCursor, QFont
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QTextEdit, QAction, QMenu, QSystemTrayIcon, \
    QHBoxLayout, QLabel, QLineEdit, QGridLayout, QFontDialog, QComboBox, QFileDialog

from ocr_paddle import get_content, init_paddleocr, get_model_config, VERSION, BASE_DIR, confirm_model_dir_url, \
    MODEL_URLS, DEFAULT_MODEL_VERSION


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


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class OcrWidget(QWidget):
    oksignal_content = pyqtSignal()
    oksignal_update_config = pyqtSignal()

    def __init__(self):
        super(OcrWidget, self).__init__()
        self.is_add = False
        self.config_path = 'config.ini'
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.clipboard = QApplication.clipboard()
        self.lang_dict = dict(中文='ch', 中文服务端版='ch_server', 英文='en', 法文='french', 德文='german', 韩文='korean', 日文='japan',
                              中文繁体='chinese_cht', 泰卢固文='te', 卡纳达文='ka', 泰米尔文='ta', 拉丁文='latin', 阿拉伯字母='arabic',
                              斯拉夫字母='cyrillic', 梵文字母='devanagari')
        self.MODEL_VERSION = 'PP-OCRv2'
        self.ocr_path = pathlib.Path(BASE_DIR) / VERSION / 'ocr'
        self.read_config()
        self.init_ui()
        self.set_font()

        # https://stackoverflow.com/questions/56949297/how-to-fix-importerror-unable-to-find-qt5core-dll-on-path-after-pyinstaller-b

    def set_font(self, font=None):
        if not font:
            font = QFont(self.FONT, int(self.FONT_SIZE))
        self.textEdit.setFont(font)

    def init_ui(self):
        # 窗口大小设置为600*500
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("飞桨识别离线版")
        self.resize(400, 300)
        image_path = resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))

        hbox = QHBoxLayout()
        self.btn = QPushButton('飞桨识别', self, clicked=self.click_btn)
        self.btn3 = QPushButton('追加文本', self, clicked=self.click_btn3)
        self.btn_copy = QPushButton('复制文本', self, clicked=self.click_btn_copy)
        self.btn4 = QPushButton('修改配置', self, clicked=self.click_btn4)
        self.btn5 = QPushButton('字体修改', self, clicked=self.click_btn5)

        self.btn3.setCheckable(True)
        # self.btn.clicked.connect(self.click_btn)
        # self.btn.setShortcut('F4')  # 设置快捷键
        hbox.addWidget(self.btn)
        hbox.addWidget(self.btn3)
        hbox.addWidget(self.btn_copy)
        hbox.addWidget(self.btn5)
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
        self.click_btn_copy()

    def click_btn(self):
        self.showMinimized()
        self.screenshot = ScreenShotsWin(self.oksignal_content, self)
        # self.screenshot.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.screenshot.showFullScreen()

    def click_btn3(self):
        if self.is_add:
            self.is_add = False
        else:
            self.is_add = True

    def click_btn4(self):
        self.update_config = UpdateConfig(self.oksignal_update_config, self)
        self.update_config.show()

    def click_btn5(self):
        font, isok = QFontDialog.getFont(QFont(self.FONT, int(self.FONT_SIZE)), self)
        if isok:
            self.FONT = str(font.family())
            self.FONT_SIZE = str(font.pointSize())
            self.config.set("paddleocr", "FONT", self.FONT)
            self.config.set("paddleocr", "FONT_SIZE", self.FONT_SIZE)
            with open(self.config_path, "w+", encoding='utf8') as f:
                self.config.write(f)
            self.set_font(font)

    def click_btn_copy(self):
        value = self.textEdit.toPlainText()
        self.clipboard.setText(value)

    def reset_config(self):
        if not os.path.isfile(self.config_path):
            cls_path = self.download_path('cls', 'ch')
            det_path = self.download_path('det', 'ch')
            rec_path = self.download_path('rec', 'ch')
            with open("config.ini", 'w', encoding='utf8') as f:
                f.write('[paddleocr]\n')
                f.write('LANG = 中文\n')
                f.write(f'CLS_PATH = {cls_path}\n')
                f.write(f'DET_PATH = {det_path}\n')
                f.write(f'REC_PATH = {rec_path}\n')
                f.write('FONT = Arial\n')
                f.write('FONT_SIZE = 12')

    def read_config(self):
        if not os.path.isfile(self.config_path):
            self.reset_config()
        self.save_config_to_paddleocr()

    def save_config_to_paddleocr(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path, encoding='utf8')
        paddleocr = self.config["paddleocr"]
        lang = paddleocr['LANG']
        cls_path = paddleocr['CLS_PATH']
        det_path = paddleocr['DET_PATH']
        rec_path = paddleocr['REC_PATH']
        self.FONT = paddleocr['FONT']
        self.FONT_SIZE = paddleocr["FONT_SIZE"]
        self.ocr = init_paddleocr(lang=self.lang_dict.get(lang, 'ch'), cls_model_dir=cls_path, det_model_dir=det_path,
                                  rec_model_dir=rec_path)
        return self.ocr

    def download_path(self, model, lang):
        model_config = get_model_config(self.MODEL_VERSION, model, lang)
        if model == 'cls':
            model_path, _ = confirm_model_dir_url(None, self.ocr_path / model, model_config['url'])
        else:
            model_path, _ = confirm_model_dir_url(None, self.ocr_path / model / lang, model_config['url'])
        return model_path


class ScreenShotsWin(QWidget):
    # 定义一个信号
    oksignal = pyqtSignal()

    def __init__(self, content_single, OcrWidget, is_precision=False):
        super(ScreenShotsWin, self).__init__()
        self.init_ui()
        self.start = (0, 0)  # 开始坐标点
        self.end = (0, 0)  # 结束坐标点
        self.content_single = content_single
        self.content = None
        self.is_precision = is_precision
        self.setCursor(QCursor(Qt.CrossCursor))
        self.OcrWidget = OcrWidget

    def init_ui(self):
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
            self.content = get_content(img_byte, self.OcrWidget.ocr)
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

    def __init__(self, oksignal_update_config, OcrWidget):
        super().__init__()
        self.oksignal_update_config = oksignal_update_config
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.OcrWidget = OcrWidget

        self.cls_path = ''
        self.det_path = ''
        self.rec_path = ''
        self.config = configparser.ConfigParser()
        self.config_path = 'config.ini'
        self.config.read(self.config_path, encoding='utf8')
        self.paddleocr = self.config["paddleocr"]
        self.LANG = self.paddleocr.get('LANG')

        image_path = resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))
        self.init_ui()



    def btn_cls_choose_file(self):
        self.cls_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('CLS_PATH') or "C:/")  # 起始路径
        self.cls_file_btn.setText(self.cls_path)

    def btn_det_choose_file(self):
        self.det_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('DET_PATH') or "C:/")  # 起始路径
        self.det_file_btn.setText(self.det_path)

    def btn_rec_choose_file(self):
        self.rec_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('REC_PATH') or "C:/")  # 起始路径
        self.rec_file_btn.setText(self.rec_path)

    def init_ui(self):
        lang = QLabel('识别语言：')
        cls = QLabel('cls模块路径：')
        det = QLabel('det模块路径：')
        rec = QLabel('rec模块路径：')
        author = QLabel('作者：')
        github_url = QLabel('github：')
        paddleocr_github_url = QLabel('paddleocr:')

        self.lang_Box = QComboBox()

        self.cls_file_btn = QPushButton(self.paddleocr.get('CLS_PATH') or '选择cls模块路径', self,
                                        clicked=self.btn_cls_choose_file)
        self.det_file_btn = QPushButton(self.paddleocr.get('DET_PATH') or '选择det模块路径', self,
                                        clicked=self.btn_det_choose_file)
        self.rec_file_btn = QPushButton(self.paddleocr.get('REC_PATH') or '选择rec模块路径', self,
                                        clicked=self.btn_rec_choose_file)
        self.author_Edit = QLineEdit()
        self.github_url_Edit = QLineEdit()
        self.paddleocr_github_url_Edit = QLineEdit()
        # 设置默认值
        for key in self.OcrWidget.lang_dict.keys():
            self.lang_Box.addItem(key)
        # self.lang_Box.setCurrentIndex(list(self.OcrWidget.lang_dict.keys()).index(self.paddleocr.get('LANG')))
        self.lang_Box.setCurrentText(self.paddleocr.get('LANG', '中文'))

        self.author_Edit.setText("libaibuaidufu")
        self.github_url_Edit.setText("https://github.com/libaibuaidufu/pyqt_ocr")
        self.paddleocr_github_url_Edit.setText("https://github.com/PaddlePaddle/PaddleOCR")
        # self.secret_key_Edit2.setDisabled(True)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid_dict = {
            lang: self.lang_Box,
            cls: self.cls_file_btn,
            det: self.det_file_btn,
            rec: self.rec_file_btn,
            author: self.author_Edit,
            github_url: self.github_url_Edit,
            paddleocr_github_url: self.paddleocr_github_url_Edit
        }
        index = 0
        for key, value in grid_dict.items():
            grid.addWidget(key, index + 1, 0)
            grid.addWidget(value, index + 1, 1)
            index += 1

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.btn = QPushButton('保存', self, clicked=self.save_config)
        self.reset_btn = QPushButton('恢复默认', self, clicked=self.reset_config)
        vbox.addLayout(grid)
        hbox.addStretch(1)
        hbox.addWidget(self.reset_btn)
        hbox.addWidget(self.btn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('修改OCR-API配置')

    def reset_config(self):
        if os.path.isfile(self.config_path):
            os.remove(self.config_path)
        self.OcrWidget.reset_config()
        self.OcrWidget.save_config_to_paddleocr()
        self.close()

    def save_config(self):
        try:
            self.config.set("paddleocr", "LANG", self.lang_Box.currentText())
            if self.lang_Box.currentText() != self.LANG:
                lang = self.OcrWidget.lang_dict.get(self.lang_Box.currentText())
                if lang in MODEL_URLS[DEFAULT_MODEL_VERSION]['rec'].keys():
                    if lang in MODEL_URLS[DEFAULT_MODEL_VERSION]['det'].keys():
                        det_lang = lang
                    else:
                        det_lang = 'en'
                    self.config.set("paddleocr", "DET_PATH", self.OcrWidget.download_path('det', det_lang))
                    self.config.set("paddleocr", "REC_PATH", self.OcrWidget.download_path('rec', lang))
                    self.config.set("paddleocr", "CLS_PATH", self.OcrWidget.download_path('cls', 'ch'))
            else:
                self.config.set("paddleocr", "CLS_PATH", self.cls_path) if self.cls_path else None
                self.config.set("paddleocr", "DET_PATH", self.det_path) if self.det_path else None
                self.config.set("paddleocr", "REC_PATH", self.rec_path) if self.rec_path else None
            with open(self.config_path, "w+", encoding='utf8') as f:
                self.config.write(f)
            self.oksignal_update_config.emit()
            self.close()
        except:
            traceback.print_exc()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 修改样式
    dbb = OcrWidget()
    dbb.show()
    sys.exit(app.exec_())
