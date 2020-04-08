#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/26 16:37
# @File    : orc.py
# @author  : dfkai
# @Software: PyCharm
import re

from aip import AipOcr


def get_content(img_path):
    """ 你的 APPID AK SK """
    APP_ID = 'APP_ID'
    API_KEY = 'API_KEY'
    SECRET_KEY = 'SECRET_KEY'

    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

    """ 读取图片 """

    def get_file_content(filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    image = get_file_content(img_path)

    """ 调用通用文字识别, 图片参数为本地图片 """
    # rsp = client.basicAccurate(image)
    rsp = client.basicGeneral(image)
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
            # print(content)
            content += "1"
            # print(word)
            content += word

        if word[-1] in (".", ":", "。"):
            last_end = True
        else:
            last_end = False

        last_num = word_num
    # print(content)
    return content


if __name__ == '__main__':
    get_content("D:/W截图_20190904_17-32-11.jpg")
