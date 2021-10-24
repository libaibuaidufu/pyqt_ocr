### windows上Paddleocr环境安装

使用：python3.7.9

```bash
# 二选一
# 如果您的机器是CPU，请运行以下命令安装 (无脑选CPU肯定可以运行)
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
# 如果您的机器安装的是CUDA9或CUDA10，请运行以下命令安装
pip install paddlepaddle-gpu -i https://mirror.baidu.com/pypi/simple

# 下载： https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
pip install Shapely-1.7.1-cp37-cp37m-win_amd64.whl
# 下载： https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-levenshtein
pip install python_Levenshtein-0.12.2-cp37-cp37m-win_amd64.whl

pip install "paddleocr>=2.0.1"
```

### pyqt_ocr环境安装

```bash
pip install -r requirements.txt
```

### pyinstaller 打包

#### 调试

```bash
# 此处设置为自己的虚拟环境位置
SET PADDLEOCR_PATH=E:\Python\venv\paddleocr_venv_37\Lib\site-packages

# 多文件 每次运行不需要解压 （启动快点）
pyinstaller --clean -y -D  --clean --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas

# 单文件 每次运行需要临时解压（启动慢点）
pyinstaller --clean -y -F  --clean --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas
```

#### 正式

```bash
# 此处设置为自己的虚拟环境位置
SET PADDLEOCR_PATH=E:\Python\venv\paddleocr_venv_37\Lib\site-packages

# 多文件 每次运行不需要解压 （启动快点）
pyinstaller --clean -y -D -w --clean --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas

# 单文件 每次运行需要临时解压（启动慢点）
pyinstaller --clean -y -F -w --clean --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas
```

---------------------------------------
#### 其他注意事项
---------------------------------------

#### pyinstall 打包问题总结

* 1 找不到资源问题和matplotlib报错

matplotlib报错，通过 --exclude 屏蔽matplotlib（我的项目不用） 资源找不到，通过打包 --add-binary --add-data 解决

```bash
pyinstaller -D -w --clean --exclude matplotlib -p C:\Anaconda2\envs\paddleocr\Lib\site-packages\paddleocr;C:\Anaconda2\envs\paddleocr\Lib\site-packages\paddle\libs textshot.py -i textshot.ico --add-binary C:\Anaconda2\envs\paddleocr\Lib\site-packages\paddle\libs;. --add-data C:\opencode\ocr\textshot_paddle\model;.\model --additional-hooks-dir=.
```

* 2 进程无线启动问题

* 2.1 分析

经过多次排除法尝试，只要存在以下语句"from paddleocr import PaddleOCR"就会导致进程不停启动 通过命令行运行打包进程“txt.exe", 手动强杀进程（Ctrl+C）发现以下报错：

```
c:\opencode\ocr\textshot_paddle>C:\opencode\ocr\textshot_paddle\dist\txt\txt.exe
Traceback (most recent call last):
  File "txt.py", line 200, in <module>
    out, err = import_cv2_proc.communicate()
  File "subprocess.py", line 964, in communicate
  File "subprocess.py", line 1296, in _communicate
  File "threading.py", line 1044, in join
  File "threading.py", line 1060, in _wait_for_tstate_lock
KeyboardInterrupt
[448] Failed to execute script txt
```

于是查看 paddle\dataset\image.py 代码，发现200行如下

```python
if six.PY3:
    import subprocess
    import sys

    import_cv2_proc = subprocess.Popen(
        [sys.executable, "-c", "import cv2"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = import_cv2_proc.communicate()
    retcode = import_cv2_proc.poll()
    if retcode != 0:
        cv2 = None
    else:
        import cv2
else:
    try:
        import cv2
    except ImportError:
        cv2 = None
```

然后根据pyinstaller issue帖子
<a href="https://github.com/pyinstaller/pyinstaller/issues/4067">4067</a>
和<a href="https://github.com/pyinstaller/pyinstaller/issues/4110">4110</a>分析，怀疑subprocess.Popen导致问题 于是写测试程序，打包测试

```python

import io
import os
import sys

import subprocess
import sys

import_cv2_proc = subprocess.Popen(
    [sys.executable, "-c", "import cv2"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
out, err = import_cv2_proc.communicate()
retcode = import_cv2_proc.poll()
if retcode != 0:
    cv2 = None
else:
    import cv2

# from paddleocr import PaddleOCR

if __name__ == "__main__":
    print("is ok!!!!!!!!!!!!!!!!!")
    args = input('input where you think:')
    print(args)
```

果然，重现问题，无线启动新进程。

* 2.3 解决方案

解决方案简单粗暴，修改image.py 39行开始代码，屏蔽subprocess调用

```python
# if six.PY3:
#     import subprocess
#     import sys
#     import_cv2_proc = subprocess.Popen(
#         [sys.executable, "-c", "import cv2"],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE)
#     out, err = import_cv2_proc.communicate()
#     retcode = import_cv2_proc.poll()
#     if retcode != 0:
#         cv2 = None
#     else:
#         import cv2
# else:
#     try:
#         import cv2
#     except ImportError:
#         cv2 = None
try:
    import cv2
except ImportError:
    cv2 = None
```

* 3 skimage.feature._orb_descriptor_positions 打包遇到此问题

这个时候可以打包看看了，不出意外还会出现新的错误。

错误提示为：

ModuleNotFoundError: No module named ‘skimage.feature._orb_descriptor_positions’

这个的原因是scikit-image版本太高，降级就可以了

`pip install -U scikit-image==0.15.0`

* 4 pyinstaller可执行文件报错astor

降低版本 0.7.1
`pip install astor==0.7.1`

* 5 pyinstaller可执行文件报错 geos.dll

`Unable to find "d:\python\envs\paddleocr-venv-37\lib\site-packages\shapely\DLLs\geos.dll" when adding binary and data files.`
没有找到geos.dll，去`lib\site-packages\shapely\DLLs` 复制 `geos_c.dll` 为 `geos.dll`

问题解决。

#### 参考

1. https://toscode.gitee.com/lazytech_group/scr2txt/raw/master/README.md
2. https://www.jianshu.com/p/e21fb89d38f8
3. https://blog.csdn.net/m0_50125842/article/details/108539569
4. https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.3/README_ch.md