# Sherpa-ONNX TTS Docker Image
# 基于 Python 3.10 官方镜像
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（使用官方源，带重试机制）
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
        libsndfile1 \
        ca-certificates \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 验证 libsndfile 运行库是否正确安装
RUN ldconfig && \
    ldconfig -p | grep libsndfile && \
    echo "✓ libsndfile installed successfully"

# 设置工作目录
WORKDIR /app

# 复制模型文件
COPY vits-melo-tts-zh_en /app/models/vits-melo-tts-zh_en

# 复制 Python 依赖包（离线安装）
COPY python-packages /app/python-packages

# 升级 pip 和安装构建工具
RUN pip install --upgrade pip setuptools wheel

# 安装 Python 依赖（从本地）
RUN pip install --no-index --find-links=/app/python-packages \
    numpy \
    sherpa-onnx \
    soundfile \
    flask \
    flask-cors \
    waitress \
    && rm -rf /app/python-packages

# 复制应用代码
COPY tts_service.py /app/
COPY test_simple.py /app/

# 创建输出目录
RUN mkdir -p /app/output

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# 启动服务
CMD ["python", "tts_service.py"]

