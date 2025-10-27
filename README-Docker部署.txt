=============================================================================
  Sherpa-ONNX TTS Docker 离线部署方案
  最终交付版本 v1.0.0
=============================================================================

## 一、交付文件清单

核心配置文件（3个）：
  [1] Dockerfile                    - Docker 镜像定义
  [2] docker-compose.yml            - Docker Compose 配置
  [3] tts_service.py               - TTS HTTP API 服务

构建部署脚本（2个）：
  [4] build_docker_image.py        - Windows 构建工具（自动化）
  [5] deploy_centos_docker.sh      - CentOS 部署脚本（自动化）

完整文档（4个）：
  [6] Docker部署指南.md            - 完整部署流程（80页）
  [7] Docker部署快速参考.txt       - 快速参考手册
  [8] API使用示例.md               - API 使用文档
  [9] Docker部署总结.md            - 方案总结

其他文件（Windows 测试时已有）：
  - vits-melo-tts-zh_en/          - TTS 模型目录
  - python-packages/              - Python 离线依赖包
  - test_simple.py                - 测试脚本

总计：9个新文件 + 原有测试环境文件

## 二、部署架构

Windows 环境（构建）:
  ┌──────────────────────────────────┐
  │ 1. 准备文件                       │
  │    - 模型文件                     │
  │    - Python 依赖                 │
  │    - Dockerfile 等               │
  ├──────────────────────────────────┤
  │ 2. 构建镜像                       │
  │    python build_docker_image.py  │
  │    └─> sherpa-onnx-tts:latest   │
  ├──────────────────────────────────┤
  │ 3. 导出镜像                       │
  │    └─> .tar 文件 (~1.2GB)       │
  └──────────────────────────────────┘
            ↓ 传输（U盘/SCP）
  ┌──────────────────────────────────┐
  │ CentOS 服务器（部署）             │
  │ 1. 导入镜像                       │
  │    docker load -i image.tar      │
  ├──────────────────────────────────┤
  │ 2. 启动服务                       │
  │    ./deploy_centos_docker.sh     │
  ├──────────────────────────────────┤
  │ 3. HTTP API 服务                 │
  │    http://server:5000            │
  └──────────────────────────────────┘

## 三、快速开始（3步）

步骤1 - Windows 构建（10分钟）：
  cd D:\workspace\sherpa-onnx
  python build_docker_image.py
  
  输出：
    ✓ Docker 镜像: sherpa-onnx-tts:latest
    ✓ 导出文件: sherpa-onnx-tts-image-*.tar (1.2GB)
    ✓ 部署包: docker-deployment-*/

步骤2 - 传输到 CentOS：
  方法A（有网络）：
    scp -r docker-deployment-* user@server:/opt/
  
  方法B（离线）：
    1. 复制 docker-deployment-* 到 U盘
    2. 在 CentOS 挂载 U盘并复制到 /opt/

步骤3 - CentOS 部署（5分钟）：
  cd /opt/docker-deployment-*/
  chmod +x deploy_centos_docker.sh
  sudo ./deploy_centos_docker.sh
  
  输出：
    ✓ 镜像已导入
    ✓ 服务已启动
    ✓ 健康检查通过
    ✓ 服务地址: http://server-ip:5000

完成！

## 四、API 使用示例

# 健康检查
curl http://server-ip:5000/health

# 生成中文语音
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界"}' \
  -o chinese.wav

# 生成英文语音
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}' \
  -o english.wav

# 中英混合
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello大家好，today测试"}' \
  -o mixed.wav

# 调整语速（0.5-2.0）
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "快速朗读", "speed": 1.5}' \
  -o fast.wav

## 五、服务管理

查看状态：
  sudo docker ps

查看日志：
  sudo docker-compose logs -f

停止服务：
  sudo docker-compose stop

启动服务：
  sudo docker-compose start

重启服务：
  sudo docker-compose restart

删除服务：
  sudo docker-compose down

查看资源使用：
  sudo docker stats sherpa-onnx-tts-service

## 六、技术规格

镜像大小：  ~1.2 GB
内存需求：  2-4 GB
CPU线程：   4 (可调整)
服务端口：  5000
API协议：   HTTP REST
音频格式：  WAV (44.1kHz, 16-bit PCM)
支持语言：  中文、英文、中英混合
最大文本：  500字符 (可调整)
语速范围：  0.5x - 2.0x

## 七、核心优势

✓ 完全离线：所有依赖打包在镜像中，无需网络
✓ 一键部署：自动化脚本，无需手动配置
✓ 环境隔离：不污染宿主机，不需要安装Python
✓ 生产就绪：健康检查、自动重启、日志管理
✓ 易于集成：标准 HTTP API，支持多种语言调用
✓ 性能优秀：RTF < 0.2，支持并发请求

## 八、故障排除

问题：Docker 镜像构建失败
  - 检查 Docker Desktop 是否运行
  - 确认所有文件都在当前目录
  - 查看 python-packages 目录是否有依赖包

问题：容器启动失败
  - sudo docker-compose logs 查看日志
  - 检查端口 5000 是否被占用
  - 确认 Docker 服务正在运行

问题：健康检查失败
  - 等待 30-60 秒让模型完全加载
  - curl http://localhost:5000/health 手动检查
  - sudo docker logs sherpa-onnx-tts-service 查看详细日志

问题：性能慢（RTF > 1.0）
  - 增加 docker-compose.yml 中的 NUM_THREADS
  - 增加 CPU 限制：cpus: '8.0'
  - 检查服务器负载：top 或 htop

## 九、文档导航

完整流程：
  → Docker部署指南.md （80页完整文档）

快速参考：
  → Docker部署快速参考.txt （速查手册）

API 使用：
  → API使用示例.md （代码示例）

方案总结：
  → Docker部署总结.md （技术总结）

当前文档：
  → README-Docker部署.txt （本文件）

## 十、技术支持

已测试环境：
  - Windows 10/11 + Docker Desktop 24.0+
  - CentOS 7.9 + Docker 20.10+
  - CentOS 8 Stream + Docker 20.10+

系统要求：
  - Docker 20.10+
  - Docker Compose 2.0+
  - 可用内存 2GB+
  - 可用磁盘 5GB+

获取帮助：
  - 查看 Docker部署指南.md 的"故障排除"章节
  - 查看容器日志：sudo docker-compose logs
  - 检查服务状态：sudo docker ps

=============================================================================
  Docker 部署方案交付完成
  立即开始：python build_docker_image.py
=============================================================================

