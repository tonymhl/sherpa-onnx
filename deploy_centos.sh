#!/bin/bash

# Sherpa-ONNX TTS 离线部署脚本 (CentOS/RHEL)
# 版本: 1.0.0
# 模型: vits-melo-tts-zh_en (中英文混合)

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
    print_header "Sherpa-ONNX TTS 离线部署脚本 (CentOS)"
    echo ""
    echo "版本: 1.0.0"
    echo "模型: vits-melo-tts-zh_en (中英文混合)"
    echo "更新日期: 2024-10-21"
    echo ""
    print_header ""
    echo ""

    # 步骤 1: 检查 Python
    print_info "[步骤 1/6] 检查 Python 环境..."
    if ! command -v python3 &> /dev/null; then
        print_error "未检测到 Python3，请先安装"
        echo ""
        echo "安装命令（CentOS 7）："
        echo "  sudo yum install -y python3 python3-devel"
        echo ""
        echo "安装命令（CentOS 8/Stream）："
        echo "  sudo dnf install -y python3 python3-devel"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version)
    print_success "Python 环境检查通过: $PYTHON_VERSION"
    echo ""

    # 步骤 2: 检查系统依赖
    print_info "[步骤 2/6] 检查并安装系统依赖..."
    
    # 检测 CentOS 版本
    if [ -f /etc/centos-release ]; then
        CENTOS_VERSION=$(cat /etc/centos-release | grep -oE '[0-9]+' | head -1)
        print_info "检测到 CentOS $CENTOS_VERSION"
    elif [ -f /etc/redhat-release ]; then
        CENTOS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+' | head -1)
        print_info "检测到 RHEL $CENTOS_VERSION"
    else
        print_warning "无法确定系统版本，假设为 CentOS 7"
        CENTOS_VERSION=7
    fi

    # 安装系统依赖
    print_info "正在安装系统依赖（需要 sudo 权限）..."
    
    if [ "$CENTOS_VERSION" -ge 8 ]; then
        # CentOS 8/Stream
        if command -v dnf &> /dev/null; then
            sudo dnf install -y gcc gcc-c++ make python3-devel || {
                print_warning "部分依赖安装失败，但将继续尝试"
            }
        else
            sudo yum install -y gcc gcc-c++ make python3-devel || {
                print_warning "部分依赖安装失败，但将继续尝试"
            }
        fi
    else
        # CentOS 7
        sudo yum install -y gcc gcc-c++ make python3-devel || {
            print_warning "部分依赖安装失败，但将继续尝试"
        }
    fi

    print_success "系统依赖检查完成"
    echo ""

    # 步骤 3: 检查部署包完整性
    print_info "[步骤 3/6] 检查部署包完整性..."

    if [ ! -d "python-packages" ]; then
        print_error "找不到 python-packages 目录"
        echo "请确保部署包完整"
        exit 1
    fi

    if [ ! -d "models/vits-melo-tts-zh_en" ] && [ ! -d "vits-melo-tts-zh_en" ]; then
        print_error "找不到模型目录 vits-melo-tts-zh_en"
        echo "请确保模型文件已正确放置"
        exit 1
    fi

    print_success "部署包检查通过"
    echo ""

    # 步骤 4: 创建虚拟环境（推荐）
    print_info "[步骤 4/6] 创建 Python 虚拟环境（推荐）..."
    
    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv || {
            print_warning "虚拟环境创建失败，将使用系统 Python"
            USE_SYSTEM_PYTHON=1
        }
    fi

    if [ -z "$USE_SYSTEM_PYTHON" ]; then
        source venv/bin/activate
        print_success "虚拟环境已激活"
    fi
    echo ""

    # 步骤 5: 安装 Python 依赖
    print_info "[步骤 5/6] 安装 Python 依赖包..."
    print_info "这可能需要几分钟时间，请耐心等待..."
    echo ""

    pip3 install --no-index --find-links=python-packages sherpa-onnx soundfile || {
        print_error "依赖包安装失败"
        echo "请检查 python-packages 目录是否包含所有必要的包"
        exit 1
    }

    echo ""
    print_success "依赖包安装完成"
    echo ""

    # 验证安装
    print_info "验证安装..."
    
    python3 -c "import sherpa_onnx; print('sherpa-onnx 版本:', sherpa_onnx.__version__)" 2>/dev/null || {
        print_warning "无法导入 sherpa_onnx，但将继续尝试运行测试"
    }

    python3 -c "import soundfile; print('soundfile 导入成功')" 2>/dev/null || {
        print_warning "无法导入 soundfile，但将继续尝试运行测试"
    }

    print_success "验证完成"
    echo ""

    # 步骤 6: 运行测试
    print_info "[步骤 6/6] 运行 TTS 测试..."
    echo ""
    print_header ""
    echo ""

    # 运行测试脚本
    if [ -f "scripts/test_tts.py" ]; then
        cd scripts
        python3 test_tts.py
        TEST_RESULT=$?
        cd ..
    elif [ -f "test_tts.py" ]; then
        python3 test_tts.py
        TEST_RESULT=$?
    else
        print_error "找不到测试脚本 test_tts.py"
        exit 1
    fi

    echo ""
    print_header ""
    echo ""

    if [ $TEST_RESULT -eq 0 ]; then
        print_success "部署和测试完成！"
        echo ""
        echo "生成的音频文件位于当前目录"
        echo "您现在可以使用 sherpa-onnx 进行语音合成了"
        echo ""
        
        if [ -z "$USE_SYSTEM_PYTHON" ]; then
            print_info "提示：下次使用时，请先激活虚拟环境："
            echo "  source venv/bin/activate"
        fi
        
        echo ""
        print_info "查看生成的音频文件："
        echo "  ls -lh *.wav"
        echo ""
        print_info "播放音频（如果有音频设备）："
        echo "  aplay test_chinese.wav"
        
    else
        print_error "测试过程中出现错误"
        echo "请查看上面的错误信息并修复问题"
        exit 1
    fi

    echo ""
    print_header "部署完成"
    echo ""
}

# 捕获 Ctrl+C
trap 'echo ""; print_warning "部署被用户中断"; exit 130' INT

# 运行主函数
main "$@"

