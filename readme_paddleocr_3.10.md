### windows11上Paddleocr环境安装

使用:python3.10.11

```bash
# 二选一
# 如果您的机器是CPU，请运行以下命令安装 (无脑选CPU肯定可以运行)
pip install paddlepaddle
# 如果您的机器安装的是CUDA9或CUDA10，请运行以下命令安装
pip install paddlepaddle-gpu

pip install -U https://paddleocr.bj.bcebos.com/whl/layoutparser-0.0.0-py3-none-any.whl

# 下载： https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
pip install Shapely
# 下载： https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-levenshtein
pip install python_Levenshtein

pip install "paddleocr>=2.0.1"

pip install PyQt5 --only-binary=:all:

pip install pyinstaller
```


### pyinstaller 打包

#### 调试

```bash
# 此处设置为自己的虚拟环境位置
SET PADDLEOCR_PATH=E:\Python\me_project\pyqt_ocr-paddleocr-offline\ocr_venv\Lib\site-packages
# --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*.txt;.\ppocr\utils 
# 可以单独列出自己所需要的文件，但是太麻烦了太长了，因此直接用*.txt,但是它会把子文件夹的文件也复制到当前文件夹，但是文件不大就几百kb。方便好用。
# 多文件 每次运行不需要解压 （启动快点）
pyinstaller --clean -y -D  --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\tools;.\tools --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*.txt;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas

# 单文件 每次运行需要临时解压（启动慢点）
pyinstaller --clean -y -F  --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\tools;.\tools --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*.txt;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas
```

#### 正式

```bash
# 此处设置为自己的虚拟环境位置
SET PADDLEOCR_PATH=E:\Python\me_project\pyqt_ocr-paddleocr-offline\ocr_venv\Lib\site-packages

# 多文件 每次运行不需要解压 （启动快点）
pyinstaller --clean -y -D -w --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\tools;.\tools --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*.txt;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas

# 单文件 每次运行需要临时解压（启动慢点）
pyinstaller --clean -y -F -w --exclude matplotlib  pyqt_ocr.py -i image/logo.ico --add-data image/logo.ico;image --add-data %PADDLEOCR_PATH%\paddleocr\tools;.\tools --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\*.txt;.\ppocr\utils --add-data %PADDLEOCR_PATH%\paddleocr\ppocr\utils\dict\*;.\ppocr\utils\dict  -p %PADDLEOCR_PATH%\paddle\libs;%PADDLEOCR_PATH%\paddleocr;%PADDLEOCR_PATH%\paddleocr\ppocr\utils\e2e_utils; --add-binary %PADDLEOCR_PATH%\paddle\libs;.  --additional-hooks-dir=.   --hidden-import extract_textpoint_slow --hidden-import scipy.spatial.transform._rotation_groups --hidden-import scipy.special.cython_special --hidden-import sklearn.utils._cython_blas
```