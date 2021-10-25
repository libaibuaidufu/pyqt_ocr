# -*- coding: utf-8 -*-
"""
@Date    : 2021/10/20
@Author  : libaibuaidufu
@Email   : libaibuaidufu@gmail.com
"""

import io
import json
import os.path
import re
import sys
import traceback

import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

VERSION = 'paddleocr_offline_1.0'
BASE_DIR = os.path.expanduser("~/.paddleocr/")

DEFAULT_MODEL_VERSION = 'PP-OCR'
MODEL_URLS = {
    'PP-OCRv2': {
        'det': {
            'ch': {
                'url':
                    'https://paddleocr.bj.bcebos.com/PP-OCRv2/chinese/ch_PP-OCRv2_det_infer.tar',
            },
        },
        'rec': {
            'ch': {
                'url':
                    'https://paddleocr.bj.bcebos.com/PP-OCRv2/chinese/ch_PP-OCRv2_rec_infer.tar',
                'dict_path': './ppocr/utils/ppocr_keys_v1.txt'
            }
        }
    },
    DEFAULT_MODEL_VERSION: {
        'det': {
            'ch': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_det_infer.tar',
            },
            'en': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/en_ppocr_mobile_v2.0_det_infer.tar',
            },
            'structure': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/table/en_ppocr_mobile_v2.0_table_det_infer.tar'
            },
            'ch_server': {
                'url': 'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_server_v2.0_det_infer.tar'
            }
        },
        'rec': {
            'ch': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/ppocr_keys_v1.txt'
            },
            'ch_server': {
                'url': 'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_server_v2.0_rec_infer.tar'
            },
            'en': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/en_number_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/en_dict.txt'
            },
            'french': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/french_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/french_dict.txt'
            },
            'german': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/german_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/german_dict.txt'
            },
            'korean': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/korean_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/korean_dict.txt'
            },
            'japan': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/japan_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/japan_dict.txt'
            },
            'chinese_cht': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/chinese_cht_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/chinese_cht_dict.txt'
            },
            'ta': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/ta_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/ta_dict.txt'
            },
            'te': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/te_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/te_dict.txt'
            },
            'ka': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/ka_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/ka_dict.txt'
            },
            'latin': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/latin_ppocr_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/latin_dict.txt'
            },
            'arabic': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/arabic_ppocr_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/arabic_dict.txt'
            },
            'cyrillic': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/cyrillic_ppocr_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/cyrillic_dict.txt'
            },
            'devanagari': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/devanagari_ppocr_mobile_v2.0_rec_infer.tar',
                'dict_path': './ppocr/utils/dict/devanagari_dict.txt'
            },
            'structure': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/table/en_ppocr_mobile_v2.0_table_rec_infer.tar',
                'dict_path': 'ppocr/utils/dict/table_dict.txt'
            }
        },
        'cls': {
            'ch': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar',
            }
        },
        'table': {
            'en': {
                'url':
                    'https://paddleocr.bj.bcebos.com/dygraph_v2.0/table/en_ppocr_mobile_v2.0_table_structure_infer.tar',
                'dict_path': 'ppocr/utils/dict/table_structure_dict.txt'
            }
        }
    }
}


def init_paddleocr(lang='ch', cls_model_dir='', det_model_dir='', rec_model_dir=''):
    if all([cls_model_dir, det_model_dir, rec_model_dir]):
        ocr = PaddleOCR(use_angle_cls=True, lang=lang,
                        use_gpu=False, cls_model_dir=cls_model_dir, det_model_dir=det_model_dir,
                        rec_model_dir=rec_model_dir)  # need to run only once to download and load model into memory
    else:
        ocr = PaddleOCR(use_angle_cls=True, lang=lang,
                        use_gpu=False)  # need to run only once to download and load model into memory
    return ocr


def ocr_to_str(resp_json):
    content = ""
    last_num = 0
    is_end = False
    last_end = False
    print(json.dumps(resp_json,indent=4,ensure_ascii=False))
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
            # content += "1"
            content += word

        if word[-1] in (".", ":", "。"):
            last_end = True
        else:
            last_end = False

        last_num = word_num
    return content.strip()


def get_content(img, ocr):
    try:
        img = np.array(Image.open(io.BytesIO(img.data())))
        # if isinstance(img, np.ndarray) and len(img.shape) == 2:
        #     img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
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
        return ocr_to_str(rec_res_final)
    except:
        traceback.print_exc()
        return "识别程序出错了！"


def get_predict_content(img, ocr):
    try:
        # Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
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


def get_model_config(version, model_type, lang):
    if version not in MODEL_URLS:
        version = DEFAULT_MODEL_VERSION
    if model_type not in MODEL_URLS[version]:
        if model_type in MODEL_URLS[DEFAULT_MODEL_VERSION]:

            version = DEFAULT_MODEL_VERSION
        else:
            sys.exit(-1)
    if lang not in MODEL_URLS[version][model_type]:
        if lang in MODEL_URLS[DEFAULT_MODEL_VERSION][model_type]:

            version = DEFAULT_MODEL_VERSION
        else:
            sys.exit(-1)
    return MODEL_URLS[version][model_type][lang]


def confirm_model_dir_url(model_dir, default_model_dir, default_url):
    url = default_url
    if model_dir is None or is_link(model_dir):
        if is_link(model_dir):
            url = model_dir
        file_name = url.split('/')[-1][:-4]
        model_dir = default_model_dir
        model_dir = os.path.join(model_dir, file_name)
    return model_dir, url


def is_link(s):
    return s is not None and s.startswith('http')
