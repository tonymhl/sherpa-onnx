# 🐳 Sherpa-ONNX TTS Docker 离线部署完整指南

## 📋 目录

- [方案概述](#方案概述)
- [Windows 构建环境准备](#windows-构建环境准备)
- [构建 Docker 镜像](#构建-docker-镜像)
- [导出镜像包](#导出镜像包)
- [传输到 CentOS](#传输到-centos)
- [CentOS 部署](#centos-部署)
- [服务使用](#服务使用)
- [故障排除](#故障排除)

---

## 🎯 方案概述

### 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│  Windows (构建环境)                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. 准备文件                                           │   │
│  │    - 模型文件 (vits-melo-tts-zh_en)                  │   │
│  │    - Python 依赖包                                    │   │
│  │    - TTS 服务代码                                     │   │
│  │    - Dockerfile                                       │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 2. 构建镜像                                           │   │
│  │    docker build -t sherpa-onnx-tts:latest .          │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 3. 导出镜像                                           │   │
│  │    docker save -o image.tar sherpa-onnx-tts:latest   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ 传输（U盘/scp）
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CentOS (离线服务器)                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. 导入镜像                                           │   │
│  │    docker load -i image.tar                          │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 2. 启动服务                                           │   │
│  │    docker-compose up -d                              │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 3. 提供 API 服务                                      │   │
│  │    http://server-ip:5000                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

- **基础镜像**: Python 3.10-slim
- **TTS 引擎**: sherpa-onnx
- **Web 框架**: Flask + Waitress
- **模型**: vits-melo-tts-zh_en (中英混合)
- **容器编排**: Docker Compose

### 优势

✅ **完全离线**: 所有依赖打包在镜像中  
✅ **环境隔离**: 不污染宿主机环境  
✅ **快速部署**: 一键启动服务  
✅ **易于管理**: Docker Compose 统一管理  
✅ **资源控制**: 可限制 CPU 和内存使用  
✅ **自动重启**: 容器异常自动恢复  

---

## 🪟 Windows 构建环境准备

### 1. 安装 Docker Desktop

**下载地址**: https://www.docker.com/products/docker-desktop

**安装步骤**:
1. 下载 Docker Desktop for Windows
2. 运行安装程序
3. 重启计算机
4. 启动 Docker Desktop

**验证安装**:
```powershell
docker --version
docker ps
```

应该看到类似输出：
```
Docker version 24.0.6, build ed223bc
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

### 2. 准备构建文件

确保以下文件在同一目录下：

```
D:\workspace\sherpa-onnx\
├── vits-melo-tts-zh_en/       # 模型目录（含 dict 子目录）
├── python-packages/            # Python 离线安装包
├── Dockerfile                  # Docker 镜像定义
├── docker-compose.yml          # Docker Compose 配置
├── tts_service.py             # TTS API 服务
├── test_simple.py             # 测试脚本
├── build_docker_image.py      # 镜像构建工具
└── deploy_centos_docker.sh    # CentOS 部署脚本
```

### 3. 下载 Python 依赖包（如果还没有）

```powershell
# 创建目录
mkdir python-packages

# 下载依赖
pip download sherpa-onnx soundfile flask flask-cors waitress -d python-packages
```

---

## 🔨 构建 Docker 镜像

### 方法A：使用自动化脚本（推荐）

```powershell
# 运行构建脚本
python build_docker_image.py
```

**脚本会自动**:
1. ✅ 检查 Docker 环境
2. ✅ 验证所有必要文件
3. ✅ 构建 Docker 镜像
4. ✅ 测试容器运行
5. ✅ 导出镜像为 tar 文件
6. ✅ 创建完整部署包

**预期输出**:
```
======================================================================
Sherpa-ONNX TTS Docker 镜像构建工具
======================================================================

[1/7] 检查 Docker 环境
----------------------------------------------------------------------
✓ Docker 已安装: Docker version 24.0.6
✓ Docker 服务正在运行

[2/7] 检查构建前置条件
----------------------------------------------------------------------
✓ 模型目录: vits-melo-tts-zh_en
✓ Dockerfile: Dockerfile
✓ docker-compose.yml: docker-compose.yml
✓ TTS 服务: tts_service.py
✓ 测试脚本: test_simple.py
✓ Python 依赖包: python-packages

✓ 所有前置条件满足

[3/7] 构建 Docker 镜像
----------------------------------------------------------------------
镜像名称: sherpa-onnx-tts:latest
这可能需要 5-10 分钟，请耐心等待...

... (构建过程输出) ...

✓ Docker 镜像构建成功: sherpa-onnx-tts:latest

[4/7] 验证 Docker 镜像
----------------------------------------------------------------------
✓ 镜像信息:
  sherpa-onnx-tts:latest	1.2GB

[5/7] 测试容器运行
----------------------------------------------------------------------
✓ 容器已启动: sherpa-onnx-tts-test
等待服务初始化（30秒）...
✓ 服务健康检查通过
✓ 测试完成，容器已清理

[6/7] 导出 Docker 镜像
----------------------------------------------------------------------
导出文件: sherpa-onnx-tts-image-20241021_143022.tar
这可能需要几分钟...

✓ 镜像已导出: sherpa-onnx-tts-image-20241021_143022.tar
  文件大小: 1234.5 MB

[7/7] 创建部署包
----------------------------------------------------------------------
✓ 创建目录: docker-deployment-20241021_143022
✓ 复制镜像文件
✓ 复制: docker-compose.yml
✓ 复制: deploy_centos_docker.sh
✓ 复制: Docker部署指南.md
✓ 创建 README.txt

✓ 部署包创建完成: docker-deployment-20241021_143022

======================================================================
构建完成！
======================================================================

Docker 镜像: sherpa-onnx-tts:latest
导出文件: sherpa-onnx-tts-image-20241021_143022.tar
部署包: docker-deployment-20241021_143022

下一步:
  1. 将 docker-deployment-20241021_143022 目录传输到 CentOS 服务器
  2. 在服务器上运行: ./deploy_centos_docker.sh
  3. 访问服务: http://server-ip:5000
```

### 方法B：手动构建

```powershell
# 1. 构建镜像
docker build -t sherpa-onnx-tts:latest .

# 2. 验证镜像
docker images sherpa-onnx-tts:latest

# 3. 测试运行
docker run -d --name tts-test -p 5000:5000 sherpa-onnx-tts:latest

# 4. 检查健康状态
curl http://localhost:5000/health

# 5. 停止测试容器
docker stop tts-test
docker rm tts-test

# 6. 导出镜像
docker save -o sherpa-onnx-tts-image.tar sherpa-onnx-tts:latest
```

---

## 📦 导出镜像包

### 镜像导出

镜像文件通常较大（约 1-1.5 GB），导出需要几分钟。

```powershell
# 导出镜像
docker save -o sherpa-onnx-tts-image.tar sherpa-onnx-tts:latest

# 检查文件大小
ls -lh sherpa-onnx-tts-image.tar
```

### 创建部署包结构

```
docker-deployment-20241021_143022/
├── sherpa-onnx-tts-image-20241021_143022.tar  # Docker 镜像（~1.2GB）
├── docker-compose.yml                          # Compose 配置
├── deploy_centos_docker.sh                     # 部署脚本
├── Docker部署指南.md                            # 本文档
└── README.txt                                  # 快速开始
```

### 可选：压缩部署包

```powershell
# 使用 tar.gz 压缩（可节省 20-30% 空间）
tar -czf docker-deployment.tar.gz docker-deployment-20241021_143022/

# 或使用 7-Zip 压缩
7z a docker-deployment.7z docker-deployment-20241021_143022/
```

---

## 🚚 传输到 CentOS

### 方法A：SCP 传输（如果有网络连接）

```bash
# 从 Windows 传输到 CentOS
scp -r docker-deployment-20241021_143022 user@server-ip:/opt/

# 或使用 WinSCP、FileZilla 等 GUI 工具
```

### 方法B：U盘/移动硬盘传输（离线环境）

**在 Windows 上**:
1. 复制整个 `docker-deployment-*` 目录到 U盘
2. 安全弹出 U盘

**在 CentOS 上**:
```bash
# 1. 挂载 U盘（假设设备为 /dev/sdb1）
sudo mkdir -p /mnt/usb
sudo mount /dev/sdb1 /mnt/usb

# 2. 复制文件
sudo cp -r /mnt/usb/docker-deployment-* /opt/

# 3. 卸载 U盘
sudo umount /mnt/usb
```

---

## 🐧 CentOS 部署

### 前置条件检查

```bash
# 检查 Docker
docker --version

# 检查 Docker Compose
docker-compose --version
# 或
docker compose version

# 检查 Docker 服务状态
sudo systemctl status docker
```

**如果 Docker 未安装**:
```bash
# CentOS 7
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# CentOS 8/Stream
sudo dnf install -y docker-ce
sudo systemctl start docker
sudo systemctl enable docker
```

**如果 Docker Compose 未安装**:
```bash
# 方法1：使用 pip
sudo yum install -y python3-pip
sudo pip3 install docker-compose

# 方法2：下载二进制（需要网络）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 自动部署（推荐）

```bash
# 1. 进入部署目录
tar -xzf docker-deployment-*.tar.gz
cd docker-deployment-*/
sed -i 's/\r$//' *.sh scripts/*.sh

# 2. 赋予执行权限
chmod +x deploy_centos_docker.sh

# 3. 运行部署脚本
sudo ./deploy_centos_docker.sh
```

**部署脚本会自动**:
1. ✅ 检查 Docker 环境
2. ✅ 导入镜像
3. ✅ 创建必要目录
4. ✅ 启动服务
5. ✅ 执行健康检查

**预期输出**:
```
============================================================
Sherpa-ONNX TTS Docker 离线部署脚本
============================================================

版本: 1.0.0
目标: CentOS 7/8/Stream
要求: Docker 和 Docker Compose 已安装

============================================================

[信息] [步骤 1/6] 检查 Docker 环境...
[成功] Docker 已安装: Docker version 24.0.6
[成功] Docker 服务正在运行

[信息] [步骤 2/6] 检查 Docker Compose...
[成功] Docker Compose 已安装: Docker Compose version v2.20.0

[信息] [步骤 3/6] 查找并导入 Docker 镜像...
[信息] 找到镜像文件: ./sherpa-onnx-tts-image-20241021_143022.tar
[信息] 文件大小: 1.2G
[信息] 正在导入镜像（这可能需要几分钟）...
[成功] 镜像导入成功
[成功] 镜像验证成功:
  sherpa-onnx-tts:latest	1.2GB

[信息] [步骤 4/6] 检查配置文件...
[成功] 找到 docker-compose.yml
[信息] 创建必要的目录...
[成功] 目录创建完成: output, logs

[信息] [步骤 5/6] 检查并清理旧容器...
[信息] 无旧容器需要清理

[信息] [步骤 6/6] 启动 TTS 服务...
[信息] 正在启动容器...
[成功] 容器启动成功

[信息] 等待服务初始化（30秒）...
[信息] 检查容器状态...
[成功] 容器正在运行

容器信息:
  容器ID: a1b2c3d4e5f6
  状态: Up
  端口: 0.0.0.0:5000->5000/tcp

[信息] 执行健康检查...
[成功] 服务健康检查通过
  响应: {"status":"healthy","model":"vits-melo-tts-zh_en","timestamp":"2024-10-21T14:30:45"}

============================================================
部署完成！
============================================================

[成功] Sherpa-ONNX TTS 服务已成功部署

服务信息:
  - 服务地址: http://192.168.1.100:5000
  - API 文档: http://192.168.1.100:5000/api/info
  - 健康检查: http://192.168.1.100:5000/health

常用命令:
  查看日志:   sudo docker-compose logs -f
  停止服务:   sudo docker-compose stop
  启动服务:   sudo docker-compose start
  重启服务:   sudo docker-compose restart
  删除服务:   sudo docker-compose down
  查看状态:   sudo docker ps
```

### 手动部署

如果自动部署脚本失败，可以手动执行：

```bash
# 1. 导入镜像
sudo docker load -i sherpa-onnx-tts-image-*.tar

# 2. 验证镜像
sudo docker images | grep sherpa-onnx-tts

# 3. 创建目录
mkdir -p output logs

# 4. 启动服务
sudo docker-compose up -d

# 5. 检查状态
sudo docker ps | grep sherpa-onnx-tts

# 6. 查看日志
sudo docker-compose logs -f
```

---

## 🚀 服务使用

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页（HTML） |
| `/health` | GET | 健康检查 |
| `/api/info` | GET | 服务信息 |
| `/api/tts` | POST | 生成语音（返回JSON） |
| `/api/tts/stream` | POST | 生成语音（直接返回WAV） |
| `/api/download/<file_id>` | GET | 下载音频文件 |

### 使用示例

#### 1. 健康检查

```bash
curl http://server-ip:5000/health
```

**响应**:
```json
{
  "status": "healthy",
  "model": "vits-melo-tts-zh_en",
  "timestamp": "2024-10-21T14:30:45"
}
```

#### 2. 获取服务信息

```bash
curl http://server-ip:5000/api/info
```

**响应**:
```json
{
  "service": "Sherpa-ONNX TTS",
  "model": "vits-melo-tts-zh_en",
  "version": "1.0.0",
  "capabilities": {
    "languages": ["zh", "en"],
    "mixed_language": true,
    "max_text_length": 500,
    "speed_range": [0.5, 2.0]
  }
}
```

#### 3. 生成语音（中文）

```bash
curl -X POST http://server-ip:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界，这是语音合成测试。", "speed": 1.0}'
```

**响应**:
```json
{
  "success": true,
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav",
  "duration": 3.45,
  "sample_rate": 44100,
  "text_length": 15,
  "generation_time": 0.52,
  "rtf": 0.151,
  "file_size": 607200,
  "download_url": "/api/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2024-10-21T14:30:45"
}
```

#### 4. 下载生成的音频

```bash
curl -o output.wav http://server-ip:5000/api/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### 5. 直接生成并下载（流式）

```bash
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "speed": 1.0}' \
  -o output.wav
```

#### 6. 中英混合

```bash
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello大家好，today我们测试TTS功能。"}' \
  -o mixed.wav
```

#### 7. 调整语速

```bash
# 慢速（0.8倍）
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "慢速朗读测试", "speed": 0.8}' \
  -o slow.wav

# 快速（1.5倍）
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "快速朗读测试", "speed": 1.5}' \
  -o fast.wav
```

### Python 客户端示例

```python
import requests

# TTS 服务地址
BASE_URL = "http://server-ip:5000"

# 生成语音
response = requests.post(
    f"{BASE_URL}/api/tts",
    json={"text": "你好世界", "speed": 1.0}
)

if response.status_code == 200:
    result = response.json()
    print(f"生成成功: {result['filename']}")
    print(f"时长: {result['duration']}秒")
    print(f"RTF: {result['rtf']}")
    
    # 下载音频
    file_id = result['file_id']
    audio_response = requests.get(f"{BASE_URL}/api/download/{file_id}")
    
    with open("output.wav", "wb") as f:
        f.write(audio_response.content)
    
    print("音频已保存到 output.wav")
```

---

## 🔧 服务管理

### 常用命令

```bash
# 查看运行状态
sudo docker ps

# 查看所有容器（包括停止的）
sudo docker ps -a

# 查看实时日志
sudo docker-compose logs -f

# 查看最近100行日志
sudo docker-compose logs --tail=100

# 停止服务
sudo docker-compose stop

# 启动服务
sudo docker-compose start

# 重启服务
sudo docker-compose restart

# 删除服务（保留镜像）
sudo docker-compose down

# 删除服务和镜像
sudo docker-compose down --rmi all

# 进入容器
sudo docker exec -it sherpa-onnx-tts-service bash

# 查看容器资源使用
sudo docker stats sherpa-onnx-tts-service
```

### 配置调整

编辑 `docker-compose.yml`:

```yaml
environment:
  - NUM_THREADS=8        # 增加线程数（根据CPU核心数）
  - MAX_TEXT_LENGTH=1000 # 增加最大文本长度
  - MAX_WORKERS=8        # 增加并发处理数
```

重启服务使配置生效：
```bash
sudo docker-compose down
sudo docker-compose up -d
```

---

## 🐛 故障排除

### 问题1：镜像导入失败

**错误信息**:
```
Error loading image from .tar
```

**解决方案**:
```bash
# 检查文件完整性
ls -lh sherpa-onnx-tts-image-*.tar

# 检查磁盘空间
df -h

# 清理 Docker 缓存
sudo docker system prune -a
```

### 问题2：容器启动失败

**查看日志**:
```bash
sudo docker-compose logs
```

**常见原因**:
1. 端口被占用
   ```bash
   # 检查端口
   sudo netstat -tulpn | grep 5000
   
   # 修改端口
   # 编辑 docker-compose.yml，将 "5000:5000" 改为 "5001:5000"
   ```

2. 权限问题
   ```bash
   # 确保目录权限正确
   sudo chown -R 1000:1000 output logs
   ```

### 问题3：健康检查失败

```bash
# 检查容器状态
sudo docker ps

# 查看详细日志
sudo docker logs sherpa-onnx-tts-service

# 手动测试
curl http://localhost:5000/health
```

### 问题4：性能问题（RTF > 1.0）

**优化方案**:

1. **增加线程数**
   ```yaml
   environment:
     - NUM_THREADS=8  # 根据CPU核心数调整
   ```

2. **增加CPU限制**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '8.0'
         memory: 8G
   ```

3. **检查系统负载**
   ```bash
   top
   htop
   ```

### 问题5：容器自动退出

```bash
# 查看退出原因
sudo docker logs sherpa-onnx-tts-service

# 检查内存限制
sudo docker inspect sherpa-onnx-tts-service | grep -i memory

# 增加内存限制
# 编辑 docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G
```

---

## 📊 性能监控

### 实时监控

```bash
# 监控资源使用
sudo docker stats sherpa-onnx-tts-service

# 输出示例
CONTAINER ID   NAME                       CPU %     MEM USAGE / LIMIT   MEM %     NET I/O          BLOCK I/O
a1b2c3d4e5f6   sherpa-onnx-tts-service   25.5%     2.1GB / 4GB         52.5%     1.2MB / 3.4MB    100MB / 50MB
```

### 日志分析

```bash
# 查看错误日志
sudo docker-compose logs | grep ERROR

# 统计请求数
sudo docker-compose logs | grep "TTS generated successfully" | wc -l

# 查看平均 RTF
sudo docker-compose logs | grep "RTF=" | awk -F'RTF=' '{print $2}' | awk '{sum+=$1; n++} END {print sum/n}'
```

---

## 🔒 安全建议

### 1. 网络隔离

```yaml
# docker-compose.yml
networks:
  tts-network:
    driver: bridge
    internal: true  # 内部网络，不允许外部访问
```

### 2. 添加认证

在 `tts_service.py` 中添加 API Key 认证：

```python
from functools import wraps

API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/tts', methods=['POST'])
@require_api_key
def text_to_speech():
    # ...
```

### 3. 限制访问来源

```yaml
# docker-compose.yml
ports:
  - "127.0.0.1:5000:5000"  # 只允许本地访问
```

### 4. 使用防火墙

```bash
# 只允许特定IP访问
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="5000" protocol="tcp" accept'
sudo firewall-cmd --reload
```

---

## 📝 总结

### 部署检查清单

- [ ] Windows 上 Docker Desktop 已安装并运行
- [ ] 模型文件完整（含 dict 目录）
- [ ] Python 依赖包已下载
- [ ] Docker 镜像构建成功
- [ ] 镜像已导出为 tar 文件
- [ ] 部署包已传输到 CentOS 服务器
- [ ] CentOS 上 Docker 和 Docker Compose 已安装
- [ ] 镜像导入成功
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] API 测试成功

### 关键文件

| 文件 | 说明 | 位置 |
|------|------|------|
| Dockerfile | 镜像定义 | Windows 构建环境 |
| docker-compose.yml | 服务配置 | 部署包 |
| tts_service.py | API 服务 | 镜像内部 |
| build_docker_image.py | 构建工具 | Windows 构建环境 |
| deploy_centos_docker.sh | 部署脚本 | 部署包 |

### 下一步

1. ✅ 服务已部署并运行
2. 🔗 集成到您的应用中
3. 📊 监控服务性能
4. 🔄 根据需要扩展（多实例部署）

---

**文档版本**: 1.0.0  
**最后更新**: 2024-10-21  
**适用环境**: Windows 10/11 + CentOS 7/8/Stream  
**Docker 版本**: 20.10+  
**Docker Compose 版本**: 2.0+

