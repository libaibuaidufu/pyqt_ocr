# -*- coding: utf-8 -*-
"""
@Date    : 2021/10/20
@Author  : libaibuaidufu
@Email   : libaibuaidufu@gmail.com
"""

import io
import os
import traceback
import uuid
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from PyQt5.QtCore import QByteArray
from paddleocr import PaddleOCR, PPStructure, save_structure_res


def init_paddleocr(lang='ch', is_table=False, cls_model_dir='', det_model_dir='', rec_model_dir=''):
    print(lang)
    if is_table:
        if all([cls_model_dir, det_model_dir, rec_model_dir]):
            ocr = PPStructure(show_log=False, use_gpu=False, table_model_dir=cls_model_dir, det_model_dir=det_model_dir,
                              rec_model_dir=rec_model_dir, lang=lang)
        else:
            ocr = PPStructure(show_log=False, use_gpu=False, lang=lang)
    else:
        if all([cls_model_dir, det_model_dir, rec_model_dir]):
            ocr = PaddleOCR(show_log=False, use_angle_cls=True, lang=lang,
                            use_gpu=False, cls_model_dir=cls_model_dir, det_model_dir=det_model_dir,
                            rec_model_dir=rec_model_dir)
        else:
            ocr = PaddleOCR(show_log=False, use_angle_cls=True, lang=lang,
                            use_gpu=False)

    return ocr


def get_content(img, ocr, x_box=15, y_box=10, num_box=0.5, save_folder=r'c:\表格'):
    try:
        if isinstance(ocr, PPStructure):
            if isinstance(img, QByteArray):
                image = Image.open(io.BytesIO(img.data()))
                img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            elif isinstance(img, str):
                # image = Image.open(img).convert('RGB')
                img = cv2.imread(img)
            else:
                return "读取出错！识别程序出错了！"
            now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
            img_path_name = now + str(uuid.uuid4())
            result = ocr(img)
            save_structure_res(result, save_folder, img_path_name)
            return os.path.join(save_folder, img_path_name)
        else:
            if isinstance(img, QByteArray):
                image = Image.open(io.BytesIO(img.data()))
            elif isinstance(img, str):
                image = Image.open(img)
            else:
                return "读取出错！识别程序出错了！"
            img = np.array(image)
            dt_boxes, rec_res = ocr(img, cls=True)
            dt_num = len(dt_boxes)
            rec_res_final = []
            for dno in range(dt_num):
                text, score = rec_res[dno]
                rec_res_final.append({
                    'text': text,
                    'confidence': float(score),
                    'text_region': dt_boxes[dno].astype(np.int).tolist()
                })
            return ocr_point_to_str(rec_res_final, x_box, y_box)
    except:
        traceback.print_exc()
        return "识别程序出错了！"


def ocr_point_to_str(result, x_box=15, y_box=10, confidence=0.5):
    """
    新版本 利用 矩形点位 拼接文字
    """

    try:
        if isinstance(x_box, str):
            x_box = int(x_box)
        if isinstance(y_box, str):
            y_box = int(y_box)
        min_x = 0
        max_x = 0
        data_boxes = []
        for index, line in enumerate(result):
            point_list = line.get("text_region")
            x1, y1, x2, y2 = [int(p) for p in point_list[0] + point_list[2]]
            if index == 0:
                max_x = x2
                min_x = x1
            min_x = min(x1, min_x)
            max_x = max(x2, max_x)
            data_boxes.append([x1, y1, x2, y2, x2 - x1, y2 - y1])
        content = ""
        last_box = []
        for box, data in zip(data_boxes, result):
            if data.get("confidence") < confidence:
                continue
            text = data.get("text")
            x1, y1, x2, y2, box_width, box_height = box
            if min_x in range(x1 - x_box, x1 + x_box):
                if last_box and last_box[2] not in range(max_x - x_box, max_x + x_box):
                    content += "\n" + text
                elif content and content[-1] in ["。", '!', '；', ';']:
                    content += "\n" + text
                else:
                    content += text
            elif last_box and last_box[3] in range(y2 - y_box, y2 + y_box):
                content += " " + text
            else:
                content += "\n" + text
            last_box = box
        return content
    except:
        traceback.print_exc()
        return "识别程序出错了！"
