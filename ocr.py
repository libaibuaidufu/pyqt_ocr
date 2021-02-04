#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/26 16:37
# @File    : ocr.py
# @author  : dfkai
# @Software: PyCharm
import re

from aip import AipOcr


# def get_content(img_path, is_precision=False):
def get_content(APP_ID, API_KEY, SECRET_KEY, img_path=None, img_byte=None, is_precision=False):
    """ 你的 APPID AK SK """
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

    """ 读取图片 """

    def get_file_content(filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    if not img_byte:
        image = get_file_content(img_path)
    else:
        image = img_byte
    """ 调用通用文字识别, 图片参数为本地图片 """
    if is_precision:
        rsp = client.basicAccurate(image)
    else:
        rsp = client.basicGeneral(image)
    if "error_code" in rsp:
        return "百度配置出错 或者 未扫描到内容"
    # {'error_code': 14, 'error_msg': 'IAM Certification failed'}
    # print(rsp["words_result"])
    content = ""
    last_num = 0
    is_end = False
    last_end = False
    for word_dict in rsp.get("words_result"):
        word = word_dict["words"]
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
