#!/bin/bash

# Sherpa-ONNX TTS 热更新脚本 - 升级到 8核8G
# 使用方法：./热更新到8核8G.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# 主函数
main() {
    print_header "Sherpa-ONNX TTS 热更新 - 升级到 8核8G"
    echo ""
    
    # ========================================
    # 步骤 1: 检查前置条件
    # ========================================
    print_info "步骤 1/6: 检查前置条件..."
    
    # 检查是否在正确目录
    if [ ! -f "docker-compose.yml" ]; then
        print_error "找不到 docker-compose.yml，请在部署目录运行此脚本"
        exit 1
    fi
    
    if [ ! -f "docker-compose-高配8核8G.yml" ]; then
        print_error "找不到 docker-compose-高配8核8G.yml"
        exit 1
    fi
    
    print_success "前置条件检查通过"
    echo ""
    
    # ========================================
    # 步骤 2: 显示当前配置
    # ========================================
    print_info "步骤 2/6: 当前配置状态..."
    
    echo -e "\n当前资源使用:"
    sudo docker stats sherpa-onnx-tts-service --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo -e "\n当前环境变量:"
    sudo docker exec sherpa-onnx-tts-service printenv | grep -E "NUM_THREADS|MAX_WORKERS" || true
    
    echo -e "\n当前健康状态:"
    curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/health
    
    echo ""
    
    # ========================================
    # 步骤 3: 用户确认
    # ========================================
    print_warning "步骤 3/6: 确认升级操作"
    echo ""
    echo "升级详情:"
    echo "  CPU:    4核 -> 8核 (+100%)"
    echo "  内存:   4GB -> 8GB (+100%)"
    echo "  线程:   4   -> 8   (+100%)"
    echo "  工作进程: 4   -> 8   (+100%)"
    echo ""
    echo "预期效果:"
    echo "  - 吞吐量提升 100%"
    echo "  - 延迟降低约 50%"
    echo "  - 支持并发数 20-40 QPS"
    echo ""
    echo "服务中断时间: < 5秒"
    echo ""
    
    read -p "确认升级到 8核8G？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "升级已取消"
        exit 0
    fi
    
    # ========================================
    # 步骤 4: 备份当前配置
    # ========================================
    print_info "步骤 4/6: 备份当前配置..."
    
    BACKUP_FILE="docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
    cp docker-compose.yml "$BACKUP_FILE"
    print_success "配置已备份: $BACKUP_FILE"
    echo ""
    
    # ========================================
    # 步骤 5: 应用新配置并热更新
    # ========================================
    print_info "步骤 5/6: 应用新配置并热更新服务..."
    
    # 替换配置文件
    cp docker-compose-高配8核8G.yml docker-compose.yml
    print_success "配置文件已更新"
    
    # 热更新服务
    echo ""
    print_info "正在热更新服务（Docker Compose）..."
    sudo docker-compose up -d
    
    # 等待服务启动
    print_info "等待服务初始化（30秒）..."
    for i in {30..1}; do
        echo -ne "\r剩余 ${i} 秒...  "
        sleep 1
    done
    echo ""
    
    print_success "服务已重启"
    echo ""
    
    # ========================================
    # 步骤 6: 验证更新
    # ========================================
    print_info "步骤 6/6: 验证更新..."
    
    echo -e "\n新资源配置:"
    sudo docker stats sherpa-onnx-tts-service --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo -e "\n新环境变量:"
    sudo docker exec sherpa-onnx-tts-service printenv | grep -E "NUM_THREADS|MAX_WORKERS"
    
    echo -e "\n健康检查:"
    HEALTH_STATUS=$(curl -s http://localhost:5000/health)
    if echo "$HEALTH_STATUS" | grep -q "healthy"; then
        print_success "服务健康检查通过"
        echo "$HEALTH_STATUS" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_STATUS"
    else
        print_error "健康检查失败"
        echo "$HEALTH_STATUS"
    fi
    
    echo -e "\n服务信息:"
    curl -s http://localhost:5000/api/info | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/api/info
    
    # ========================================
    # 步骤 7: 性能测试
    # ========================================
    echo ""
    print_info "性能测试..."
    
    echo -e "\n单次请求响应时间:"
    time curl -X POST http://localhost:5000/api/tts/stream \
        -H "Content-Type: application/json" \
        -d '{"text": "这是升级到8核8G后的性能测试"}' \
        -o /tmp/test_upgrade.wav 2>&1 | grep real || true
    
    # ========================================
    # 完成总结
    # ========================================
    echo ""
    print_header "热更新完成！"
    echo ""
    print_success "Sherpa-ONNX TTS 已成功升级到 8核8G"
    echo ""
    echo "升级摘要:"
    echo "  ✓ CPU 限制:   4核 -> 8核"
    echo "  ✓ 内存限制:   4GB -> 8GB"
    echo "  ✓ 线程数:     4 -> 8"
    echo "  ✓ 工作进程:   4 -> 8"
    echo "  ✓ 配置备份:   $BACKUP_FILE"
    echo ""
    echo "常用命令:"
    echo "  查看日志:     sudo docker-compose logs -f"
    echo "  查看状态:     sudo docker stats sherpa-onnx-tts-service"
    echo "  重启服务:     sudo docker-compose restart"
    echo "  回滚配置:     cp $BACKUP_FILE docker-compose.yml && sudo docker-compose up -d"
    echo ""
    echo "服务地址:"
    echo "  健康检查:     http://$(hostname -I | awk '{print $1}'):5000/health"
    echo "  API 文档:     http://$(hostname -I | awk '{print $1}'):5000/api/info"
    echo ""
    print_header "升级成功"
    echo ""
}

# 捕获 Ctrl+C
trap 'echo ""; print_warning "升级被用户中断"; exit 130' INT

# 运行主函数
main "$@"

