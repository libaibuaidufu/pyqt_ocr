#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/26 16:37
# @File    : ocr.py
# @author  : dfkai
# @Software: PyCharm
import base64
import json
import re

import requests


def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        file_rb = fp.read()
    return base64.b64encode(file_rb).decode('utf8')


def get_content(ocr_url=None, img_path=None, img_byte=None, is_precision=False):
    if not ocr_url:
        return "请设置OCR-APi"

    """ 读取图片 """
    # 指定post请求的headers为application/json方式
    headers = {"Content-Type": "application/json"}

    if not img_byte:
        image = get_file_content(img_path)
    else:
        image = base64.b64encode(img_byte).decode('utf8')
    data = {
        "images": [image]
    }
    try:
        resp = requests.post(url=ocr_url, headers=headers, data=json.dumps(data), proxies={"http": "", "https": ''})
    except Exception:
        return "请求失败，请查看地址和网络问题"
    resp_json = resp.json()
    if resp_json.get("status", '') != "0":
        return f"未扫描到内容或者扫描出错,提示：{resp_json.get('msg', '')}"

    content = ""
    last_num = 0
    is_end = False
    last_end = False
    for word_dict in resp_json.get("results")[0]:
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
    # print(content)
    return content.strip()
