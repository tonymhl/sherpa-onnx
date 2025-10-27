
# Sherpa-ONNX TTS Docker 部署包

## 包含内容

- sherpa-onnx-tts-image-20251022_150650.tar - Docker 镜像文件
- docker-compose.yml - Docker Compose 配置
- deploy_centos_docker.sh - CentOS 自动部署脚本
- Docker部署指南.md - 详细部署文档

## 快速部署（CentOS）

1. 上传整个目录到 CentOS 服务器：
   scp -r docker-deployment-20251022_150650 user@server:/opt/

2. 在服务器上运行部署脚本：
   cd /opt/docker-deployment-20251022_150650
   chmod +x deploy_centos_docker.sh
   ./deploy_centos_docker.sh

3. 访问服务：
   http://server-ip:5000

## 手动部署步骤

参见 Docker部署指南.md

---
创建时间: 2025-10-22 15:12:32
