# -*- coding: utf-8 -*-
"""
@Date    : 2021/10/20
@Author  : libaibuaidufu
@Email   : libaibuaidufu@gmail.com
"""

import io
import json
import os
import pathlib
import re
import traceback
import uuid
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from PyQt5.QtCore import QByteArray
from paddleocr import PaddleOCR, PPStructure, save_structure_res, draw_structure_result


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


def get_content(img, ocr, x_box=15, y_box=10, save_folder=r'c:\表格'):
    try:
        if isinstance(ocr, PPStructure):

            if isinstance(img, QByteArray):
                image = Image.open(io.BytesIO(img.data()))
                img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            elif isinstance(img, str):
                image = Image.open(img).convert('RGB')
                img = cv2.imread(img)
            else:
                return "读取出错！识别程序出错了！"
            now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
            img_path_name = now + str(uuid.uuid4())
            result = ocr(img)
            save_structure_res(result, save_folder, img_path_name)
            res_text = pathlib.Path(save_folder) / img_path_name / 'res.txt'
            rec_res_final = []
            dt_boxes = []
            content = ""
            with open(res_text, 'r', encoding='utf8') as f:
                for line in f.readlines():
                    line_list = line.split('	', 1)
                    if len(line_list[0]) < 10:
                        continue
                    text_num = line_list[-1].replace("('", "").replace(")", "").replace("\n", '').rsplit("',", 1)
                    text = text_num[0]
                    num = float(text_num[-1].strip())
                    box = json.loads(line_list[0])
                    rec_res_final.append({
                        "text": text,
                        'confidence': num,
                        'text_region': [[int(box[0]), int(box[1])], [int(box[2]), int(box[3])], [int(box[4]), int(5)],
                                        [int(box[6]), int(7)]]
                    })
                content = ocr_point_to_str(rec_res_final, x_box, y_box)

            im_show = draw_structure_result(image, result, font_path='./fonts/simfang.ttf')
            im_show = Image.fromarray(im_show)
            im_show.save(pathlib.Path(save_folder) / img_path_name / 'result.jpg')
            return content + '\n' + f'识别成功! 复制路径 \n {os.path.join(save_folder, img_path_name)} \n 打开查看'
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


def ocr_to_str(resp_json):
    """
    老版本文字拼接
    """
    content = ""
    last_num = 0
    is_end = False
    last_end = False
    for word_dict in resp_json:
        word = word_dict["text"]
        word_num = len(word)
        if last_end:
            is_end = True
        elif re.match("^\d[\.、]", word):
            is_end = True
        elif len(word.split(":")) == 2:
            is_end = True
        elif word[-1] == "。" and word_num > last_num + 3 and last_end != True:
            is_end = True
        if word[-1] in (".", ":", "。"):
            is_end = False
        else:
            is_end = False

        if last_end:
            content += "\n" + word
        elif is_end:
            content += "\n" + word
        elif word_num > last_num + 3:
            content += "\n" + word
        else:
            content += word

        if word[-1] in (".", ":", "。"):
            last_end = True
        else:
            last_end = False

        last_num = word_num
    return content.strip()


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
