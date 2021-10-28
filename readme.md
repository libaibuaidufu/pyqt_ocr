# pyqt_orc 离线版

### 离线版环境及pyinstaller打包

文档可看 [paddleocr离线版打包文档](https://github.com/libaibuaidufu/pyqt_ocr/blob/paddleocr-offline/readme_paddleocr.md)
###### 2021-10-28 更新
1. 增加自动换行设置
2. 增加上传图片识别，可以多选，但是无法保证顺序。因此单选然后依次追加比较准确。
3. 可以截图识别加图片上传识别结合。
###### 2021-10-25 更新
1. 优化结构
2. 优化了text、box合并方法
3. 直接选择识别语言，自动下载即可。无需自动选择模型，除非自己有必要。
###### 2021-10-24 更新
1. 增加 识别语言设置
2. 增加 方向模型路径设置、检测模型路径设置、识别模型路径设置，可以自己配置，也可以直接选择识别语言自动下载。
3. [点击进入模型下载地址](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.3/doc/doc_ch/models_list.md)
4. 如果不会就不要乱选择，万一不能运行了。就删除config.ini或者恢复默认设置。
5. 识别模型默认是轻量版本10M左右，选择中文服务端版本，这个150M左右。这些都是需要在线下载的。
6. **注意：下载模型是需要时间，因此你点了保存，他就会下载，所以完成时间跟你的网速有关。不要重复点击保存。**
7. 后续在更新更多的配置设置
###### 2021-10-22 更新
1. 增加 飞桨离线服务整合版（包很大 200M）[paddleocr离线版](https://github.com/libaibuaidufu/pyqt_ocr/tree/paddleocr-offline)
2. 离线版扫描纯文档效果还行，其他的还是有很多问题。等着后续优化。
###### 2021-10-19 更新
1. 增加 飞桨在线测试接口使用（同时默认使用在线测试接口）
###### 2021-07-29 更新
1. 增加 字体样式和大小 修改
###### 2021-07-28 更新

1. 增加飞桨paddleocr 接口支持
2. 增加识别后，自动复制

###### 2021-2-4 更新

1. 支持单文件打包 需要自己复制config.ini 到已打包配置里面，单文件真的大
2. 自动切换壁纸 tkinter程序中学习而来的, [auto-change-wallhaven](https://github.com/libaibuaidufu/auto-change-wallhaven)

###### 2020-1-12 更新

1. 已经更新为省去图片保存 直接转byte
2. 同时修改 鼠标样式 更加显著的 截图标识
3. ~~发现问题 应用 必须要自己打包使用，因为配置保存只能此次打开有用。~~
4. ~~3的问题有缘再解决了~~
5. 增加Fusion样式

### 问题

~~图片会保存本地 再删除 耽误时间 可以更好的直接传送字节过去 省去这一步~~

### 预览

![image](https://github.com/libaibuaidufu/pyqt_orc/blob/paddleocr-offline/preview.png)
![image](https://github.com/libaibuaidufu/pyqt_orc/blob/paddleocr-offline/preview2.png)