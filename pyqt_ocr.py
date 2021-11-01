import configparser
import os
import pathlib
import sys
import traceback
from os.path import exists

import keyboard
from PyQt5.QtCore import Qt, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QPen, QColor, QCursor, QFont
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QLabel, QLineEdit, \
    QGridLayout, QFontDialog, QComboBox, QFileDialog, QButtonGroup, QRadioButton, QInputDialog
from paddleocr import PPStructure

from ocr_paddle import get_content, init_paddleocr

BASE_DIR = os.path.expanduser("~/")


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
            self.close()
            # todo:做一个提示消息框
            self.content = get_content(img_byte, self.OcrWidget.ocr, x_box=self.OcrWidget.x_pad_num,
                                       y_box=self.OcrWidget.y_pad_num, num_box=self.OcrWidget.num_box,
                                       save_folder=self.OcrWidget.structure_path)
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


class OcrWidget(QWidget):
    oksignal_content = pyqtSignal()
    oksignal_update_config = pyqtSignal()

    def __init__(self):
        # QApplication.setQuitOnLastWindowClosed(False)  # 禁止默认的closed方法，只能使用qapp.quit()的方法退出程序
        super(OcrWidget, self).__init__()
        self.is_add = False
        self.is_warp = False
        self.is_table = False
        self.use_model = False
        self.x_pad_num = 15
        self.y_pad_num = 10
        self.num_box = 0.5
        self.hot_key_call = None
        self.is_top = False
        self.config_path = 'config.ini'
        self.clipboard = QApplication.clipboard()
        self.lang_dict = dict(中文='ch', 英文='en', 法文='french', 德文='german', 韩文='korean', 日文='japan',
                              中文繁体='chinese_cht', 泰卢固文='te', 卡纳达文='ka', 泰米尔文='ta', 拉丁文='latin', 阿拉伯字母='arabic',
                              斯拉夫字母='cyrillic', 梵文字母='devanagari')
        self.read_config()
        self.init_ui()
        self.set_font()
        self.show()

        # https://stackoverflow.com/questions/56949297/how-to-fix-importerror-unable-to-find-qt5core-dll-on-path-after-pyinstaller-b

    def set_font(self, font=None):
        if not font:
            font = QFont(self.FONT, int(self.FONT_SIZE))
        self.textEdit.setFont(font)

    def set_hot_key(self, key):
        if self.hot_key_call:
            keyboard.remove_hotkey(self.hot_key_call)
        self.hot_key_call = keyboard.add_hotkey(key, self.ocr_btn.click)

    def set_top(self):
        self.is_top = not self.is_top
        if self.is_top:
            self.setWindowTitle("飞桨识别离线版--置顶")
            self.setWindowFlag(Qt.WindowStaysOnTopHint)
        else:
            self.setWindowTitle("飞桨识别离线版")
            self.setWindowFlag(Qt.Widget)
        self.show()

    def set_push_button(self, name, func):
        btn = QPushButton(name, self)
        btn.clicked[bool].connect(func)
        return btn

    def set_text_content(self):
        if isinstance(self.ocr, PPStructure):
            if self.is_add:
                value = self.textEdit.toPlainText()
                if value:
                    data = value + '\n' + self.screenshot.content
                else:
                    data = f'识别成功! 路径已经自动复制到剪贴板 \n {self.screenshot.content} '
            else:
                data = f'识别成功! 路径已经自动复制到剪贴板 \n {self.screenshot.content} '
            self.click_btn_copy(self.screenshot.content)
        else:
            if self.is_add:
                value = self.textEdit.toPlainText()
                if self.is_warp:
                    data = value + '\n' + self.screenshot.content
                else:
                    data = value + self.screenshot.content
            else:
                data = self.screenshot.content
            self.click_btn_copy()
        self.textEdit.setText(data)
        self.showNormal()

    def init_ui(self):
        self.setWindowTitle("飞桨识别离线版")
        self.resize(400, 300)
        image_path = resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))

        hbox = QHBoxLayout()
        self.ocr_btn = self.set_push_button('飞桨识别', self.click_btn)
        # self.ocr_btn.setShortcut('F4')  # 设置快捷键
        add_text_btn = self.set_push_button('追加文本', self.click_btn_add)
        add_text_btn.setCheckable(True)
        self.top_btn = self.set_push_button('置顶', self.set_top)
        self.top_btn.setShortcut(self.top_key)
        self.top_btn.hide()
        btn_list = [
            self.ocr_btn,
            self.set_push_button('图片识别', self.click_btn_file),
            add_text_btn,
            self.set_push_button('复制文本', self.click_btn_copy),
            self.top_btn,
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

        self.set_hot_key(self.hot_key)

    def click_btn_file(self):
        directory = QFileDialog.getOpenFileNames(self, caption="选取多个文件", directory=BASE_DIR,
                                                 filter="All Files (*);;JPEG Files(*.jpg);;PNG Files(*.png)")
        content = self.textEdit.toPlainText() if self.is_add else ''
        text = ''
        for path_index, img_path in enumerate(directory[0]):
            text = get_content(img_path, self.ocr, x_box=self.x_pad_num, y_box=self.y_pad_num, num_box=self.num_box,
                               save_folder=self.structure_path)
            if isinstance(self.ocr, PPStructure):
                if path_index == 0 and content == "":
                    content += f'识别成功! 路径已经自动复制到剪贴板 \n {text} '
                else:
                    content += "\n" + text
            else:
                if path_index == 0 and content == "":
                    content += text
                elif self.is_warp:
                    content += "\n" + text
                else:
                    content += text
        self.textEdit.setText(content)
        self.showNormal()
        if isinstance(self.ocr, PPStructure):
            self.click_btn_copy(text)
        else:
            self.click_btn_copy()

    def click_btn(self):
        self.showMinimized()
        self.screenshot = ScreenShotsWin(self.oksignal_content, self)
        self.screenshot.showFullScreen()

    def click_btn_add(self):
        if self.is_add:
            self.is_add = False
        else:
            self.is_add = True

    def click_btn_config(self):
        self.update_config = UpdateConfig(self.oksignal_update_config, self)
        self.update_config.show()

    def click_btn_copy(self, value=None):
        if not value:
            value = self.textEdit.toPlainText()
        self.clipboard.setText(value)

    def reset_config(self):
        if not os.path.isfile(self.config_path):
            STRUCTURE_PATH = pathlib.Path(BASE_DIR) / '表格'
            if not exists(STRUCTURE_PATH):
                os.mkdir(STRUCTURE_PATH)
            with open("config.ini", 'w', encoding='utf8') as f:
                f.write('[paddleocr]\n')
                f.write('LANG = 中文\n')
                f.write('TABLE = 关闭\n')
                f.write('USE_MODEL = 关闭\n')
                f.write(f'CLS_PATH = \n')
                f.write(f'DET_PATH = \n')
                f.write(f'REC_PATH = \n')
                f.write(f'STRUCTURE_PATH = {STRUCTURE_PATH}\n')
                f.write('FONT = Arial\n')
                f.write('FONT_SIZE = 12\n')
                f.write('WARP = 关闭\n')
                f.write('X_PAD = 15\n')
                f.write('Y_PAD = 10\n')
                f.write('NUM_BOX = 0.5\n')
                f.write('TOP = 关闭\n')
                f.write('HOT_KEY = F4\n')

    def read_config(self):
        if not os.path.isfile(self.config_path):
            self.reset_config()
        self.save_config_to_paddleocr()

    def save_config_to_paddleocr(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path, encoding='utf8')
        paddleocr = self.config["paddleocr"]
        lang = paddleocr['LANG']
        table = paddleocr['TABLE']
        use_model = paddleocr['USE_MODEL']
        cls_path = paddleocr['CLS_PATH']
        det_path = paddleocr['DET_PATH']
        rec_path = paddleocr['REC_PATH']
        warp = paddleocr['WARP']
        self.top = paddleocr['TOP']
        self.hot_key = paddleocr['HOT_KEY']
        self.top_key = paddleocr['TOP_KEY']
        self.structure_path = paddleocr['STRUCTURE_PATH']
        self.FONT = paddleocr['FONT']
        self.FONT_SIZE = paddleocr["FONT_SIZE"]
        if warp == "启动":
            self.is_warp = True
        else:
            self.is_warp = False
        if use_model == "启动":
            self.use_model = True
        else:
            self.use_model = False
        if table == "启动":
            self.is_table = True
        else:
            self.is_table = False

        self.x_pad_num = paddleocr['X_PAD']
        self.y_pad_num = paddleocr['Y_PAD']
        self.num_box = paddleocr['NUM_BOX']

        if self.use_model:
            self.ocr = init_paddleocr(lang=self.lang_dict.get(lang, 'ch'), is_table=self.is_table,
                                      cls_model_dir=cls_path,
                                      det_model_dir=det_path,
                                      rec_model_dir=rec_path)
        else:
            self.ocr = init_paddleocr(lang=self.lang_dict.get(lang, 'ch'), is_table=self.is_table)
        return self.ocr


class UpdateConfig(QWidget):

    def __init__(self, oksignal_update_config, OcrWidget):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.oksignal_update_config = oksignal_update_config
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.OcrWidget = OcrWidget

        self.font = ''
        self.set_hot_key = False
        self.set_top_key = False
        self.event_key = None

        self.config = configparser.ConfigParser()
        self.config_path = 'config.ini'
        self.config.read(self.config_path, encoding='utf8')
        self.paddleocr = self.config["paddleocr"]
        self.lang = self.paddleocr.get('LANG')
        self.config_warp = self.paddleocr.get('WARP', '关闭')
        self.config_custom_model = self.paddleocr.get('USE_MODEL', '关闭')
        self.config_table = self.paddleocr.get('TABLE', '关闭')
        self.config_hot_key = self.paddleocr.get("HOT_KEY", 'F4')
        self.config_top_key = self.paddleocr.get("TOP_KEY", 'F5')
        self.cls_path = self.paddleocr.get('CLS_PATH')
        self.det_path = self.paddleocr.get('DET_PATH')
        self.rec_path = self.paddleocr.get('REC_PATH')
        self.structure_path = self.paddleocr.get('STRUCTURE_PATH')
        self.x_pad_num = self.paddleocr.get("X_PAD", str(15))
        self.y_pad_num = self.paddleocr.get("Y_PAD", str(10))
        self.num_box = self.paddleocr.get("NUM_BOX", str(0.5))

        image_path = resource_path("image\logo.ico")
        self.setWindowIcon(QIcon(image_path))
        self.lang_box, self.auto_warp_group, self.font_btn, self.cls_file_btn, self.det_file_btn, self.rec_file_btn, self.x_btn, self.y_btn, self.use_custom_model_group, self.structure_file_btn, self.table_group, self.num_box_btn, self.hot_key_btn, self.top_key_btn = self.init_ui()

    def set_push_button(self, name, func):
        btn = QPushButton(name, self)
        btn.clicked[bool].connect(func)
        return btn

    def click_btn_x_or_y(self):
        sender = self.sender()
        if sender == self.x_btn:
            text, ok = QInputDialog.getInt(self, '修改X轴偏差', '请输入X轴偏差偏差范围：', value=int(self.x_pad_num), min=0)
            if ok:
                self.x_pad_num = str(text)
                self.x_btn.setText(f"x轴：{self.x_pad_num}")
        elif sender == self.y_btn:
            text, ok = QInputDialog.getInt(self, '修改Y轴偏差', '请输入Y轴偏差偏差范围：', value=int(self.y_pad_num), min=0)
            if ok:
                self.y_pad_num = str(text)
                self.y_btn.setText(f"y轴：{self.y_pad_num}")
        elif sender == self.num_box_btn:
            text, ok = QInputDialog.getDouble(self, '修改识别得分', '请输入保留大于多少的识别得分（0-1）：', value=float(self.num_box), min=0,
                                              max=1)
            if ok:
                self.num_box = str(text)
                self.num_box_btn.setText(f'识别得分低于{self.num_box}丢弃')
        elif sender == self.hot_key_btn:
            # todo:通过按键检测直接设置快捷键，可以实现但是对应按键太多，太麻烦了
            self.set_hot_key = True
            # text, ok = QInputDialog.getText(self, '修改快捷键', '请输入快捷键：', text=self.config_hot_key)
            # if ok:
            #     self.config_hot_key = str(text)
            #     self.hot_key_btn.setText(f'{self.config_hot_key}')
        elif sender == self.top_key_btn:
            self.set_top_key = True

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

            table = QLabel('识别表格')
            table_group = QButtonGroup(self)
            group_table_yes = QRadioButton('启动', self)
            group_table_no = QRadioButton('关闭', self)
            table_group.addButton(group_table_yes, 1)
            table_group.addButton(group_table_no, 0)
            if self.config_table == "启动":
                group_table_yes.click()
            else:
                group_table_no.click()
            table_group.buttonClicked.connect(self.rbclicked)

            # top = QLabel('置顶')
            # top_group = QButtonGroup(self)
            # group_top_yes = QRadioButton('启动', self)
            # group_top_no = QRadioButton('关闭', self)
            # top_group.addButton(group_top_yes, 1)
            # top_group.addButton(group_top_no, 0)
            # if self.config_top == "启动":
            #     group_top_yes.click()
            # else:
            #     group_top_no.click()
            # top_group.buttonClicked.connect(self.rbclicked)

            num_box = QLabel("识别得分")
            num_box_btn = self.set_push_button(f'识别得分低于{self.num_box}丢弃', self.click_btn_x_or_y)

            hot_key_label = QLabel("截图快捷键")
            hot_key_btn = self.set_push_button(f'{self.config_hot_key}', self.click_btn_x_or_y)

            top_key_label = QLabel("置顶快捷键")
            top_key_btn = self.set_push_button(f'{self.config_top_key}', self.click_btn_x_or_y)

            structure = QLabel('表格路径')
            structure_file_btn = self.set_push_button(self.structure_path or '选择表格识别文件保存路径',
                                                      self.btn_structure_choose_file)

            use_custom_model = QLabel('自定义模型')
            use_custom_model_group = QButtonGroup(self)
            group_model_yes = QRadioButton('启动', self)
            group_model_no = QRadioButton('关闭', self)
            use_custom_model_group.addButton(group_model_yes, 1)
            use_custom_model_group.addButton(group_model_no, 0)
            if self.config_custom_model == "启动":
                group_model_yes.click()
            else:
                group_model_no.click()
            use_custom_model_group.buttonClicked.connect(self.rbclicked)

            cls = QLabel('cls|table模型路径')
            cls_file_btn = self.set_push_button(self.cls_path or '选择自定义cls|table模型路径', self.btn_cls_choose_file)

            det = QLabel('det模型路径')
            det_file_btn = self.set_push_button(self.det_path or '选择自定义det模型路径', self.btn_det_choose_file)

            rec = QLabel('rec模型路径')
            rec_file_btn = self.set_push_button(self.rec_path or '选择自定义rec模型路径', self.btn_rec_choose_file)

            auto_warp = QLabel('自动换行')
            auto_warp_group = QButtonGroup(self)
            group_warp_yes = QRadioButton('启动', self)
            group_warp_no = QRadioButton('关闭', self)
            auto_warp_group.addButton(group_warp_yes, 1)
            auto_warp_group.addButton(group_warp_no, 0)
            if self.config_warp == "启动":
                group_warp_yes.click()
            else:
                group_warp_no.click()
            auto_warp_group.buttonClicked.connect(self.rbclicked)

            xy_pad = QLabel("轴向偏差范围")
            x_btn = self.set_push_button('修改X轴偏差', self.click_btn_x_or_y)
            x_btn.setText(f"x轴：{self.x_pad_num}")
            y_btn = self.set_push_button('修改Y轴偏差', self.click_btn_x_or_y)
            y_btn.setText(f"y轴：{self.y_pad_num}")

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

            # hbox_top = QHBoxLayout()
            # hbox_top.addWidget(group_top_yes)
            # hbox_top.addWidget(group_top_no)
            # hbox_top.addStretch(1)

            hbox_table = QHBoxLayout()
            hbox_table.addWidget(group_table_yes)
            hbox_table.addWidget(group_table_no)
            hbox_table.addStretch(1)

            hbox_model = QHBoxLayout()
            hbox_model.addWidget(group_model_yes)
            hbox_model.addWidget(group_model_no)
            hbox_model.addStretch(1)

            hbox_warp = QHBoxLayout()
            hbox_warp.addWidget(group_warp_yes)
            hbox_warp.addWidget(group_warp_no)
            hbox_warp.addStretch(1)

            hbox_xy_pad = QHBoxLayout()
            # hbox_xy_pad.addWidget(x_pad)
            hbox_xy_pad.addWidget(x_btn)
            # hbox_xy_pad.addWidget(y_pad)
            hbox_xy_pad.addWidget(y_btn)
            hbox_xy_pad.addStretch(1)

            grid_dict = {
                lang: hbox_lang,
                num_box: num_box_btn,
                table: hbox_table,
                structure: structure_file_btn,
                auto_warp: hbox_warp,
                # top: hbox_top,
                use_custom_model: hbox_model,
                cls: cls_file_btn,
                det: det_file_btn,
                rec: rec_file_btn,
                hot_key_label: hot_key_btn,
                top_key_label: top_key_btn,
                xy_pad: hbox_xy_pad,
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

            self.setGeometry(300, 300, 350, 300)
            self.setWindowTitle('修改OCR配置')
            return lang_box, auto_warp_group, font_btn, cls_file_btn, det_file_btn, rec_file_btn, x_btn, y_btn, use_custom_model_group, structure_file_btn, table_group, num_box_btn, hot_key_btn, top_key_btn
        except:
            traceback.print_exc()

    def rbclicked(self):
        try:
            sender = self.sender()
            if sender == self.auto_warp_group:
                if self.auto_warp_group.checkedId() == 1:
                    self.config_warp = '启动'
                else:
                    self.config_warp = '关闭'
            elif sender == self.use_custom_model_group:
                if self.use_custom_model_group.checkedId() == 1:
                    self.config_custom_model = '启动'
                else:
                    self.config_custom_model = '关闭'
            elif sender == self.table_group:
                if self.table_group.checkedId() == 1:
                    self.config_table = '启动'
                else:
                    self.config_table = '关闭'
            elif sender == self.top_group:
                if self.top_group.checkedId() == 1:
                    self.config_top = '启动'
                else:
                    self.config_top = '关闭'
        except:
            traceback.print_exc()

    def btn_structure_choose_file(self):
        structure_path = QFileDialog.getExistingDirectory(None, "选取文件夹",
                                                          self.paddleocr.get('STRUCTURE_PATH') or BASE_DIR)  # 起始路径
        if structure_path:
            self.structure_path = structure_path
            self.structure_file_btn.setText(self.structure_path)

    def btn_cls_choose_file(self):
        cls_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('CLS_PATH') or BASE_DIR)  # 起始路径
        if cls_path:
            self.cls_path = cls_path
            self.cls_file_btn.setText(self.cls_path)

    def btn_det_choose_file(self):
        det_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('DET_PATH') or BASE_DIR)  # 起始路径
        if det_path:
            self.det_path = det_path
            self.det_file_btn.setText(self.det_path)

    def btn_rec_choose_file(self):
        rec_path = QFileDialog.getExistingDirectory(None, "选取文件夹", self.paddleocr.get('REC_PATH') or BASE_DIR)  # 起始路径
        if rec_path:
            self.rec_path = rec_path
            self.rec_file_btn.setText(self.rec_path)

    # 检测键盘回车按键
    def keyPressEvent(self, event):
        press_dict = {65: 'a', 66: 'b', 67: 'c', 68: 'd', 69: 'e', 70: 'f', 71: 'g', 72: 'h', 73: 'i', 74: 'j', 75: 'k',
                      76: 'l', 77: 'm', 78: 'n', 79: 'o', 80: 'p', 81: 'q', 82: 'r', 83: 's', 84: 't', 85: 'u', 86: 'v',
                      87: 'w', 88: 'x', 89: 'y', 90: 'z', 48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6',
                      55: '7', 56: '8', 57: '9', 16777264: 'F1', 16777265: 'F2', 16777266: 'F3', 16777267: 'F4',
                      16777268: 'F5', 16777269: 'F6', 16777270: 'F7', 16777271: 'F8', 16777272: 'F9', 16777273: 'F10',
                      16777274: 'F11', 16777275: 'F12'}
        try:
            if self.set_hot_key:
                self.event_key = press_dict[event.key()]
                self.hot_key_btn.setText(self.event_key)
                self.config_hot_key = self.event_key

            elif self.set_top_key:
                self.event_key = press_dict[event.key()]
                self.top_key_btn.setText(self.event_key)
                self.config_top_key = self.event_key
        except:
            traceback.print_exc()

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
            self.config.set("paddleocr", "HOT_KEY", self.config_hot_key)
            self.OcrWidget.set_hot_key(self.config_hot_key)
            self.config.set("paddleocr", "TOP_KEY", self.config_top_key)
            # self.OcrWidget.set_top_key(self.config_top_key)
            self.OcrWidget.top_btn.setShortcut(self.config_top_key)
            self.config.set("paddleocr", "WARP", self.config_warp)
            self.config.set("paddleocr", "NUM_BOX", self.num_box)
            self.config.set("paddleocr", "X_PAD", self.x_pad_num)
            self.config.set("paddleocr", "Y_PAD", self.y_pad_num)
            self.config.set("paddleocr", "LANG", self.lang_box.currentText())
            self.config.set("paddleocr", "TABLE", self.config_table)
            self.config.set("paddleocr", "USE_MODEL", self.config_custom_model)
            self.config.set("paddleocr", "STRUCTURE_PATH", self.structure_path) if self.structure_path else ...
            self.config.set("paddleocr", "CLS_PATH", self.cls_path) if self.cls_path else ...
            self.config.set("paddleocr", "DET_PATH", self.det_path) if self.det_path else ...
            self.config.set("paddleocr", "REC_PATH", self.rec_path) if self.rec_path else ...
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
    sys.exit(app.exec_())
