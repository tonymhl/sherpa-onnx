#!/bin/bash

# Sherpa-ONNX TTS Docker 离线部署脚本（CentOS）
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

# 主函数
main() {
    print_header "Sherpa-ONNX TTS Docker 离线部署脚本"
    echo ""
    echo "版本: 1.0.0"
    echo "目标: CentOS 7/8/Stream"
    echo "要求: Docker 和 Docker Compose 已安装"
    echo ""
    print_header ""
    echo ""
    
    # 步骤 1: 检查 Docker
    print_info "[步骤 1/6] 检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        echo ""
        echo "请先安装 Docker:"
        echo "  sudo yum install -y docker"
        echo "  sudo systemctl start docker"
        echo "  sudo systemctl enable docker"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version)
    print_success "Docker 已安装: $DOCKER_VERSION"
    
    # 检查 Docker 是否运行
    if ! sudo systemctl is-active --quiet docker; then
        print_warning "Docker 服务未运行，正在启动..."
        sudo systemctl start docker
        sleep 2
    fi
    
    if sudo systemctl is-active --quiet docker; then
        print_success "Docker 服务正在运行"
    else
        print_error "Docker 服务启动失败"
        exit 1
    fi
    
    echo ""
    
    # 步骤 2: 检查 Docker Compose
    print_info "[步骤 2/6] 检查 Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_success "Docker Compose 已安装: $COMPOSE_VERSION"
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version)
        print_success "Docker Compose (plugin) 已安装: $COMPOSE_VERSION"
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose 未安装"
        echo ""
        echo "请先安装 Docker Compose:"
        echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo "  sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi
    
    echo ""
    
    # 步骤 3: 查找并导入镜像
    print_info "[步骤 3/6] 查找并导入 Docker 镜像..."
    
    IMAGE_FILE=$(find . -name "sherpa-onnx-tts-image-*.tar" | head -1)
    
    if [ -z "$IMAGE_FILE" ]; then
        print_error "找不到镜像文件 (sherpa-onnx-tts-image-*.tar)"
        echo ""
        echo "请确保镜像文件在当前目录"
        exit 1
    fi
    
    print_info "找到镜像文件: $IMAGE_FILE"
    
    # 检查文件大小
    FILE_SIZE=$(du -h "$IMAGE_FILE" | cut -f1)
    print_info "文件大小: $FILE_SIZE"
    
    print_info "正在导入镜像（这可能需要几分钟）..."
    
    if sudo docker load -i "$IMAGE_FILE"; then
        print_success "镜像导入成功"
    else
        print_error "镜像导入失败"
        exit 1
    fi
    
    # 验证镜像
    if sudo docker images | grep -q "sherpa-onnx-tts"; then
        IMAGE_INFO=$(sudo docker images sherpa-onnx-tts:latest --format "{{.Repository}}:{{.Tag}}\t{{.Size}}")
        print_success "镜像验证成功:"
        echo "  $IMAGE_INFO"
    else
        print_error "镜像验证失败"
        exit 1
    fi
    
    echo ""
    
    # 步骤 4: 检查配置文件
    print_info "[步骤 4/6] 检查配置文件..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "找不到 docker-compose.yml"
        exit 1
    fi
    
    print_success "找到 docker-compose.yml"
    
    # 创建必要的目录
    print_info "创建必要的目录..."
    mkdir -p output logs
    print_success "目录创建完成: output, logs"
    
    echo ""
    
    # 步骤 5: 停止旧容器（如果存在）
    print_info "[步骤 5/6] 检查并清理旧容器..."
    
    if sudo docker ps -a | grep -q "sherpa-onnx-tts-service"; then
        print_warning "发现旧容器，正在清理..."
        sudo $COMPOSE_CMD down
        print_success "旧容器已清理"
    else
        print_info "无旧容器需要清理"
    fi
    
    echo ""
    
    # 步骤 6: 启动服务
    print_info "[步骤 6/6] 启动 TTS 服务..."
    
    print_info "正在启动容器..."
    
    if sudo $COMPOSE_CMD up -d; then
        print_success "容器启动成功"
    else
        print_error "容器启动失败"
        echo ""
        echo "查看日志:"
        echo "  sudo $COMPOSE_CMD logs"
        exit 1
    fi
    
    echo ""
    print_info "等待服务初始化（30秒）..."
    
    for i in {30..1}; do
        echo -ne "\r剩余 ${i} 秒...  "
        sleep 1
    done
    echo ""
    
    # 检查容器状态
    print_info "检查容器状态..."
    
    if sudo docker ps | grep -q "sherpa-onnx-tts-service"; then
        print_success "容器正在运行"
        
        # 显示容器信息
        echo ""
        echo "容器信息:"
        sudo docker ps | grep "sherpa-onnx-tts-service" | awk '{print "  容器ID: " $1 "\n  状态: " $7 "\n  端口: " $6}'
    else
        print_error "容器未运行"
        echo ""
        echo "查看日志:"
        echo "  sudo $COMPOSE_CMD logs"
        exit 1
    fi
    
    # 健康检查
    echo ""
    print_info "执行健康检查..."
    
    sleep 5  # 额外等待
    
    HEALTH_CHECK=$(curl -s http://localhost:5000/health || echo "failed")
    
    if echo "$HEALTH_CHECK" | grep -q "healthy"; then
        print_success "服务健康检查通过"
        echo "  响应: $HEALTH_CHECK"
    else
        print_warning "健康检查未通过，但容器正在运行"
        echo "  可能需要更多时间初始化"
        echo "  手动检查: curl http://localhost:5000/health"
    fi
    
    # 总结
    echo ""
    print_header "部署完成！"
    echo ""
    print_success "Sherpa-ONNX TTS 服务已成功部署"
    echo ""
    echo "服务信息:"
    echo "  - 服务地址: http://$(hostname -I | awk '{print $1}'):5000"
    echo "  - API 文档: http://$(hostname -I | awk '{print $1}'):5000/api/info"
    echo "  - 健康检查: http://$(hostname -I | awk '{print $1}'):5000/health"
    echo ""
    echo "常用命令:"
    echo "  查看日志:   sudo $COMPOSE_CMD logs -f"
    echo "  停止服务:   sudo $COMPOSE_CMD stop"
    echo "  启动服务:   sudo $COMPOSE_CMD start"
    echo "  重启服务:   sudo $COMPOSE_CMD restart"
    echo "  删除服务:   sudo $COMPOSE_CMD down"
    echo "  查看状态:   sudo docker ps"
    echo ""
    echo "API 使用示例:"
    echo "  # 生成语音"
    echo "  curl -X POST http://localhost:5000/api/tts \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"text\": \"你好世界\", \"speed\": 1.0}'"
    echo ""
    echo "  # 下载音频"
    echo "  curl -X POST http://localhost:5000/api/tts/stream \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"text\": \"Hello World\"}' \\"
    echo "    -o output.wav"
    echo ""
    print_header "部署成功"
    echo ""
}

# 捕获 Ctrl+C
trap 'echo ""; print_warning "部署被用户中断"; exit 130' INT

# 运行主函数
main "$@"

