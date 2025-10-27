@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo Sherpa-ONNX TTS 离线部署脚本 (Windows)
echo ============================================================
echo.
echo 版本: 1.0.0
echo 模型: vits-melo-tts-zh_en (中英文混合)
echo 更新日期: 2024-10-21
echo.
echo ============================================================
echo.

REM 检查 Python
echo [步骤 1/5] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

python --version
echo [成功] Python 环境检查通过
echo.

REM 检查必要目录
echo [步骤 2/5] 检查部署包完整性...

if not exist "python-packages" (
    echo [错误] 找不到 python-packages 目录
    echo 请确保部署包完整
    pause
    exit /b 1
)

if not exist "models\vits-melo-tts-zh_en" (
    if not exist "vits-melo-tts-zh_en" (
        echo [错误] 找不到模型目录 vits-melo-tts-zh_en
        echo 请确保模型文件已正确放置
        pause
        exit /b 1
    )
)

echo [成功] 部署包检查通过
echo.

REM 安装依赖
echo [步骤 3/5] 安装 Python 依赖包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pip install --no-index --find-links=python-packages sherpa-onnx soundfile
if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖包安装失败
    echo 请检查 python-packages 目录是否包含所有必要的包
    pause
    exit /b 1
)

echo.
echo [成功] 依赖包安装完成
echo.

REM 验证安装
echo [步骤 4/5] 验证安装...

python -c "import sherpa_onnx; print('sherpa-onnx 版本:', sherpa_onnx.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo [警告] 无法导入 sherpa_onnx，但将继续尝试运行测试
)

python -c "import soundfile; print('soundfile 导入成功')" 2>nul
if %errorlevel% neq 0 (
    echo [警告] 无法导入 soundfile，但将继续尝试运行测试
)

echo [成功] 验证完成
echo.

REM 运行测试
echo [步骤 5/5] 运行 TTS 测试...
echo.
echo ============================================================
echo.

REM 切换到脚本目录（如果存在）
if exist "scripts\test_tts.py" (
    cd scripts
    python test_tts.py
    cd ..
) else if exist "test_tts.py" (
    python test_tts.py
) else (
    echo [错误] 找不到测试脚本 test_tts.py
    pause
    exit /b 1
)

echo.
echo ============================================================
echo.

if %errorlevel% equ 0 (
    echo [成功] 部署和测试完成！
    echo.
    echo 生成的音频文件位于当前目录
    echo 您现在可以使用 sherpa-onnx 进行语音合成了
) else (
    echo [失败] 测试过程中出现错误
    echo 请查看上面的错误信息并修复问题
)

echo.
echo ============================================================
echo.
pause

