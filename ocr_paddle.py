# -*- coding: utf-8 -*-
"""
@Date    : 2021/10/20
@Author  : libaibuaidufu
@Email   : libaibuaidufu@gmail.com
"""

import io
import traceback

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR


def get_content(img):
    try:
        # Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
        # 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
        ocr = PaddleOCR(use_angle_cls=True, lang="ch",
                        use_gpu=False)  # need to run only once to download and load model into memory
        pil_img = Image.open(io.BytesIO(img.data()))
        result = ocr.ocr(np.array(pil_img), cls=True)
        boxes = [line[0] for line in result]
        min_x = 0
        min_y = 0
        max_x = 0
        max_y = 0
        data_boxes = []
        for index, x in enumerate(boxes):
            b = [int(v) for v in x[0]] + [int(j) for j in x[2]]
            if index == 0:
                max_x = b[2]
                min_x = b[0]
                min_y = b[3] - b[1]
            min_x = min(b[0], min_x)
            min_y = min(b[3] - b[1], min_y)
            max_x = max(b[2], max_x)
            data_boxes.append(b)
        # print(data_boxes)
        # print(min_x, max_x, min_y, max_x - min_x)
        content = ""
        last_box = []
        for index, data in enumerate(result):
            text = data[1][0]
            print(text)
            box = data[0]
            box_four = [int(v) for v in box[0]] + [int(j) for j in box[2]]
            box_width = box_four[2] - box_four[0]
            box_four.append(box_width)
            # print(text)
            # print(box_four)
            if min_x in range(box_four[0] - 5, box_four[0] + 5):
                if last_box and last_box[4] not in range(max_x - 10, max_x + 10):
                    content += "\n" + text
                elif content and content[-1] in ["。", '!', '；', ';']:
                    content += "\n" + text
                else:
                    content += text
            else:
                content += "\n" + text
            last_box = box_four
        return content
    except:
        traceback.print_exc()
        return "识别程序出错了！"
