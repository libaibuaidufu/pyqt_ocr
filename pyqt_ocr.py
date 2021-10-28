import configparser
import os
import pathlib
import sys
import traceback

# import keyboard
from PyQt5.QtCore import Qt, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QPen, QColor, QCursor, QFont
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QLabel, QLineEdit, \
    QGridLayout, QFontDialog, QComboBox, QFileDialog, QButtonGroup, QRadioButton

from ocr_paddle import get_content, init_paddleocr, get_model_config, VERSION, BASE_DIR, confirm_model_dir_url, \
    MODEL_URLS, DEFAULT_MODEL_VERSION


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


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


class OcrWidget(QWidget):
    oksignal_content = pyqtSignal()
    oksignal_update_config = pyqtSignal()

    def __init__(self):
        # QApplication.setQuitOnLastWindowClosed(False)  # 禁止默认的closed方法，只能使用qapp.quit()的方法退出程序
        super(OcrWidget, self).__init__()
        self.is_add = False
        self.is_warp = False
        self.config_path = 'config.ini'
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
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

    def set_push_button(self, name, func):
        btn = QPushButton(name, self)
        btn.clicked[bool].connect(func)
        return btn

    def init_ui(self):
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("飞桨识别离线版")
        self.resize(400, 300)
        image_path = resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))

        hbox = QHBoxLayout()
        ocr_btn = self.set_push_button('飞桨识别', self.click_btn)
        ocr_btn.setShortcut('F4')  # 设置快捷键
        add_text_btn = self.set_push_button('追加文本', self.click_btn_add)
        add_text_btn.setCheckable(True)
        btn_list = [
            ocr_btn,
            self.set_push_button('图片识别', self.click_btn_file),
            add_text_btn,
            self.set_push_button('复制文本', self.click_btn_copy),
            self.set_push_button('修改配置', self.click_btn_config)
        ]
        for btn in btn_list:
            hbox.addWidget(btn)
        hbox.addStretch(1)
        vbox = QVBoxLayout()
        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        vbox.addWidget(self.textEdit)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.oksignal_content.connect(lambda: self.set_text_content())
        self.oksignal_update_config.connect(lambda: self.read_config())
        # keyboard.add_hotkey('F5', ocr_btn.click)

    def set_text_content(self):
        if self.is_add:
            value = self.textEdit.toPlainText()
            if self.is_warp:
                data = value + '\n' + self.screenshot.content
            else:
                data = value + self.screenshot.content
        else:
            data = self.screenshot.content
        self.textEdit.setText(data)
        self.screenshot.close()
        self.showNormal()
        self.click_btn_copy()

    def click_btn_file(self):
        directory = QFileDialog.getOpenFileNames(self, caption="选取多个文件", directory="C:/",
                                                 filter="All Files (*);;JPEG Files(*.jpg);;PNG Files(*.png)")
        content = self.textEdit.toPlainText() if self.is_add else ''
        for path_index, img_path in enumerate(directory[0]):
            if path_index == 0 and content == "":
                content += get_content(img_path, self.ocr)
            elif self.is_warp:
                content += "\n" + get_content(img_path, self.ocr)
            else:
                content += get_content(img_path, self.ocr)
        self.textEdit.setText(content)

    def click_btn(self):
        self.showMinimized()
        self.screenshot = ScreenShotsWin(self.oksignal_content, self)
        # self.screenshot.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.screenshot.showFullScreen()

    def click_btn_add(self):
        if self.is_add:
            self.is_add = False
        else:
            self.is_add = True

    def click_btn_config(self):
        self.update_config = UpdateConfig(self.oksignal_update_config, self)
        self.update_config.show()

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
                f.write('FONT_SIZE = 12\n')
                f.write('WARP = 否')

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
        WARP = paddleocr['WARP']
        self.FONT = paddleocr['FONT']
        self.FONT_SIZE = paddleocr["FONT_SIZE"]
        self.ocr = init_paddleocr(lang=self.lang_dict.get(lang, 'ch'), cls_model_dir=cls_path, det_model_dir=det_path,
                                  rec_model_dir=rec_path)
        if WARP == "是":
            self.is_warp = True
        else:
            self.is_warp = False
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

        self.font = ''

        self.config = configparser.ConfigParser()
        self.config_path = 'config.ini'
        self.config.read(self.config_path, encoding='utf8')
        self.paddleocr = self.config["paddleocr"]
        self.lang = self.paddleocr.get('LANG')
        self.config_warp = self.paddleocr.get('WARP', '否')
        self.cls_path = self.paddleocr.get('CLS_PATH')
        self.det_path = self.paddleocr.get('DET_PATH')
        self.rec_path = self.paddleocr.get('REC_PATH')

        image_path = resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))
        self.init_ui()

    def set_push_button(self, name, func):
        btn = QPushButton(name, self)
        btn.clicked[bool].connect(func)
        return btn

    def init_ui(self):
        try:
            # 默认配置
            author = QLabel('作者')
            author_edit = QLineEdit()
            author_edit.setText("libaibuaidufu")

            github_url = QLabel('github')
            github_url_edit = QLineEdit()
            github_url_edit.setText("https://github.com/libaibuaidufu/pyqt_ocr")

            paddleocr_github_url = QLabel('paddleocr')
            paddleocr_github_url_edit = QLineEdit()
            paddleocr_github_url_edit.setText("https://github.com/PaddlePaddle/PaddleOCR")

            lang = QLabel('识别语言')
            lang_box = QComboBox()
            for key in self.OcrWidget.lang_dict.keys():
                lang_box.addItem(key)
            lang_box.setCurrentText(self.paddleocr.get('LANG', '中文'))

            cls = QLabel('cls模型路径')
            cls_file_btn = self.set_push_button(self.cls_path or '选择cls模型路径', self.btn_cls_choose_file)

            det = QLabel('det模型路径')
            det_file_btn = self.set_push_button(self.det_path or '选择det模型路径', self.btn_det_choose_file)

            rec = QLabel('rec模型路径')
            rec_file_btn = self.set_push_button(self.rec_path or '选择rec模型路径', self.btn_rec_choose_file)

            auto_warp = QLabel('自动换行')
            auto_warp_group = QButtonGroup(self)
            group_warp_yes = QRadioButton('是', self)
            group_warp_no = QRadioButton('否', self)
            auto_warp_group.addButton(group_warp_yes, 1)
            auto_warp_group.addButton(group_warp_no, 0)
            if self.config_warp == "是":
                group_warp_yes.click()
            else:
                group_warp_no.click()
            auto_warp_group.buttonClicked.connect(self.rbclicked)

            font_size = QLabel('字体设置')
            font_btn = self.set_push_button(
                f"字体：{self.paddleocr.get('FONT')}  大小：{self.paddleocr.get('FONT_SIZE')}" or '字体修改', self.click_btn_font)

            # 布局
            grid = QGridLayout()
            grid.setSpacing(10)

            hbox_lang = QHBoxLayout()
            hbox_lang.addWidget(lang_box)
            hbox_lang.addStretch(1)

            hbox_font = QHBoxLayout()
            hbox_font.addWidget(font_btn)
            hbox_font.addStretch(1)

            hbox_warp = QHBoxLayout()
            hbox_warp.addWidget(group_warp_yes)
            hbox_warp.addWidget(group_warp_no)
            hbox_warp.addStretch(1)

            grid_dict = {
                lang: hbox_lang,
                cls: cls_file_btn,
                det: det_file_btn,
                rec: rec_file_btn,
                auto_warp: hbox_warp,
                font_size: hbox_font,
                author: author_edit,
                github_url: github_url_edit,
                paddleocr_github_url: paddleocr_github_url_edit
            }
            index = 0
            for key, value in grid_dict.items():
                grid.addWidget(key, index + 1, 0)
                if isinstance(value, QHBoxLayout):
                    grid.addLayout(value, index + 1, 1)
                else:
                    grid.addWidget(value, index + 1, 1)
                index += 1

            vbox = QVBoxLayout()
            hbox = QHBoxLayout()
            btn = self.set_push_button('保存', self.save_config)
            reset_btn = self.set_push_button('恢复默认', self.reset_config)

            vbox.addLayout(grid)
            hbox.addStretch(1)
            hbox.addWidget(reset_btn)
            hbox.addWidget(btn)
            vbox.addLayout(hbox)
            self.setLayout(vbox)

            self.lang_box = lang_box
            self.auto_warp_group = auto_warp_group
            self.font_btn = font_btn

            self.setGeometry(300, 300, 350, 300)
            self.setWindowTitle('修改OCR配置')
        except:
            traceback.print_exc()

    def rbclicked(self):
        sender = self.sender()
        if self.auto_warp_group.checkedId() == 1:
            self.config_warp = '是'
        else:
            self.config_warp = '否'

    def btn_cls_choose_file(self):
        self.cls_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('CLS_PATH') or "C:/")  # 起始路径
        self.cls_file_btn.setText(self.cls_path)

    def btn_det_choose_file(self):
        self.det_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('DET_PATH') or "C:/")  # 起始路径
        self.det_file_btn.setText(self.det_path)

    def btn_rec_choose_file(self):
        self.rec_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('REC_PATH') or "C:/")  # 起始路径
        self.rec_file_btn.setText(self.rec_path)

    def click_btn_font(self):
        font_name = self.paddleocr.get('FONT')
        font_size = self.paddleocr.get('FONT_SIZE')
        font, isok = QFontDialog.getFont(QFont(font_name, int(font_size)), self)
        if isok:
            self.font = font
            font_name = str(self.font.family())
            font_size = str(self.font.pointSize())
            self.font_btn.setText(f"字体：{font_name}，大小：{font_size}")

    def reset_config(self):
        if os.path.isfile(self.config_path):
            os.remove(self.config_path)
        self.OcrWidget.reset_config()
        self.OcrWidget.save_config_to_paddleocr()
        self.close()

    def save_config(self):
        try:
            if self.font:
                self.config.set("paddleocr", "FONT", str(self.font.family()))
                self.config.set("paddleocr", "FONT_SIZE", str(self.font.pointSize()))
                self.OcrWidget.set_font(self.font)
            self.config.set("paddleocr", "WARP", self.config_warp)

            lang_box_value = self.lang_box.currentText()
            self.config.set("paddleocr", "LANG", lang_box_value)
            if lang_box_value != self.lang:
                lang = self.OcrWidget.lang_dict.get(lang_box_value)
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
