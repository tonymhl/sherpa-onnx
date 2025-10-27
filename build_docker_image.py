#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker 镜像构建和导出工具
用于在 Windows 上构建镜像并导出为 tar 文件，以便离线部署
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class DockerImageBuilder:
    def __init__(self):
        self.image_name = "sherpa-onnx-tts"
        self.image_tag = "latest"
        self.full_image_name = f"{self.image_name}:{self.image_tag}"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def print_step(self, step_num, total_steps, message):
        """打印步骤信息"""
        print(f"\n[{step_num}/{total_steps}] {message}")
        print("-" * 70)
        
    def check_docker(self):
        """检查 Docker 是否可用"""
        self.print_step(1, 7, "检查 Docker 环境")
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"[OK] Docker 已安装: {result.stdout.strip()}")
            
            # 检查 Docker 是否运行
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                check=True
            )
            print("[OK] Docker 服务正在运行")
            return True
            
        except subprocess.CalledProcessError:
            print("[ERROR] 错误：Docker 未安装或未运行")
            print("\n请确保：")
            print("  1. Docker Desktop 已安装")
            print("  2. Docker 服务正在运行")
            return False
        except FileNotFoundError:
            print("[ERROR] 错误：找不到 docker 命令")
            print("\n请安装 Docker Desktop:")
            print("  https://www.docker.com/products/docker-desktop")
            return False
    
    def download_dependencies(self):
        """下载 Python 依赖包（Linux 兼容）"""
        try:
            print("   下载 Python 依赖包（为 Linux 平台）...")
            print("   提示：下载预编译的 wheel 文件，避免编译...")
            
            # 方案1：下载所有依赖（包括预编译的 sherpa-onnx wheel）
            # 不指定 --no-binary，让 pip 自动选择最佳版本
            subprocess.run([
                "pip", "download",
                "--platform", "manylinux2014_x86_64",
                "--only-binary=:all:",
                "--python-version", "310",
                "numpy", "sherpa-onnx", "soundfile", "flask", "flask-cors", "waitress",
                "-d", "python-packages"
            ], check=True)
            
            print("[OK] 依赖下载完成（使用预编译 wheel）")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] 首选方案失败: {e}")
            print("\n尝试备用方案（自动选择格式）...")
            
            try:
                # 备用方案：让 pip 自动选择（可能包括源码包）
                subprocess.run([
                    "pip", "download",
                    "numpy", "sherpa-onnx", "soundfile", "flask", "flask-cors", "waitress",
                    "-d", "python-packages"
                ], check=True)
                print("[OK] 备用方案成功")
                return True
            except subprocess.CalledProcessError:
                print("[ERROR] 所有下载方案都失败")
                return False
    
    def check_prerequisites(self):
        """检查前置条件"""
        self.print_step(2, 7, "检查构建前置条件")
        
        required_items = {
            "模型目录": "vits-melo-tts-zh_en",
            "Dockerfile": "Dockerfile",
            "docker-compose.yml": "docker-compose.yml",
            "TTS 服务": "tts_service.py",
            "测试脚本": "test_simple.py",
        }
        
        missing_items = []
        for name, path in required_items.items():
            if os.path.exists(path):
                print(f"[OK] {name}: {path}")
            else:
                print(f"[ERROR] 缺少 {name}: {path}")
                missing_items.append(name)
        
        # 检查 python-packages 目录
        if not os.path.exists("python-packages"):
            print("\n[WARNING] 警告：python-packages 目录不存在")
            print("   正在创建并下载依赖...")
            
            os.makedirs("python-packages", exist_ok=True)
            if not self.download_dependencies():
                missing_items.append("python-packages")
        else:
            # 检查是否包含 Linux 兼容的包
            files = os.listdir("python-packages")
            has_win_only = any("win_amd64" in f or "win32" in f for f in files)
            
            if has_win_only:
                print(f"[WARNING] 警告：python-packages 包含 Windows 平台的包，需要重新下载 Linux 兼容包")
                print("   正在重新下载...")
                
                # 清空目录
                shutil.rmtree("python-packages")
                os.makedirs("python-packages")
                
                if not self.download_dependencies():
                    missing_items.append("python-packages")
            else:
                print(f"[OK] Python 依赖包: python-packages")
        
        if missing_items:
            print(f"\n[ERROR] 缺少以下项目: {', '.join(missing_items)}")
            return False
        
        print("\n[OK] 所有前置条件满足")
        return True
    
    def build_image(self):
        """构建 Docker 镜像"""
        self.print_step(3, 7, "构建 Docker 镜像")
        
        print(f"镜像名称: {self.full_image_name}")
        print("这可能需要 5-10 分钟，请耐心等待...\n")
        
        try:
            # 构建镜像
            subprocess.run([
                "docker", "build",
                "-t", self.full_image_name,
                "."
            ], check=True)
            
            print(f"\n[OK] Docker 镜像构建成功: {self.full_image_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Docker 镜像构建失败")
            return False
    
    def verify_image(self):
        """验证镜像"""
        self.print_step(4, 7, "验证 Docker 镜像")
        
        try:
            # 检查镜像是否存在
            result = subprocess.run([
                "docker", "images",
                self.full_image_name,
                "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"
            ], capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                print(f"[OK] 镜像信息:")
                print(f"  {result.stdout.strip()}")
                return True
            else:
                print("[ERROR] 镜像不存在")
                return False
                
        except subprocess.CalledProcessError:
            print("[ERROR] 无法验证镜像")
            return False
    
    def test_container(self):
        """测试容器运行"""
        self.print_step(5, 7, "测试容器运行")
        
        container_name = "sherpa-onnx-tts-test"
        
        try:
            print("启动测试容器...")
            
            # 停止并删除旧容器（如果存在）
            subprocess.run([
                "docker", "rm", "-f", container_name
            ], capture_output=True)
            
            # 运行容器
            subprocess.run([
                "docker", "run",
                "-d",
                "--name", container_name,
                "-p", "5000:5000",
                self.full_image_name
            ], check=True)
            
            print(f"[OK] 容器已启动: {container_name}")
            print("\n等待服务初始化（30秒）...")
            
            import time
            for i in range(30, 0, -1):
                print(f"\r剩余 {i} 秒...", end="", flush=True)
                time.sleep(1)
            print("\n")
            
            # 检查健康状态
            print("检查服务健康状态...")
            try:
                import requests
                response = requests.get("http://localhost:5000/health", timeout=10)
                if response.status_code == 200:
                    print("[OK] 服务健康检查通过")
                    print(f"  响应: {response.json()}")
                else:
                    print(f"[WARNING] 健康检查返回状态码: {response.status_code}")
            except ImportError:
                print("[WARNING] 未安装 requests，跳过健康检查")
                print("  可以手动访问: http://localhost:5000/health")
            except Exception as e:
                print(f"[WARNING] 健康检查失败: {e}")
            
            # 停止测试容器
            print("\n停止测试容器...")
            subprocess.run([
                "docker", "stop", container_name
            ], check=True)
            
            subprocess.run([
                "docker", "rm", container_name
            ], check=True)
            
            print("[OK] 测试完成，容器已清理")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] 容器测试失败: {e}")
            # 尝试清理
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
            return False
    
    def export_image(self):
        """导出镜像为 tar 文件"""
        self.print_step(6, 7, "导出 Docker 镜像")
        
        output_file = f"sherpa-onnx-tts-image-{self.timestamp}.tar"
        
        print(f"导出文件: {output_file}")
        print("这可能需要几分钟...\n")
        
        try:
            subprocess.run([
                "docker", "save",
                "-o", output_file,
                self.full_image_name
            ], check=True)
            
            # 检查文件大小
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            print(f"[OK] 镜像已导出: {output_file}")
            print(f"  文件大小: {file_size:.1f} MB")
            
            return output_file
            
        except subprocess.CalledProcessError:
            print("[ERROR] 镜像导出失败")
            return None
    
    def create_deployment_package(self, image_file):
        """创建部署包"""
        self.print_step(7, 7, "创建部署包")
        
        package_dir = f"docker-deployment-{self.timestamp}"
        
        try:
            # 创建部署目录
            os.makedirs(package_dir, exist_ok=True)
            print(f"[OK] 创建目录: {package_dir}")
            
            # 复制镜像文件
            shutil.copy(image_file, package_dir)
            print(f"[OK] 复制镜像文件")
            
            # 复制配置文件
            files_to_copy = [
                "docker-compose.yml",
                "docker-compose-中配6核6G.yml",
                "docker-compose-高配8核8G.yml",
                "docker-compose-高配16核16G.yml",
                "deploy_centos_docker.sh",
                "热更新到8核8G.sh",
                "Docker部署指南.md",
                "资源扩容和热更新指南.md",
                "资源扩容快速参考.txt",
            ]
            
            for file in files_to_copy:
                if os.path.exists(file):
                    shutil.copy(file, package_dir)
                    print(f"[OK] 复制: {file}")
                else:
                    print(f"[WARNING] 文件不存在: {file}")
            
            # 创建 README
            readme_content = f"""
# Sherpa-ONNX TTS Docker 部署包（含音量优化 v1.1.0）

## 📦 包含内容

### 核心文件
- {os.path.basename(image_file)} - Docker 镜像文件
- docker-compose.yml - Docker Compose 配置（标准 4核4G）
- deploy_centos_docker.sh - CentOS 自动部署脚本

### 资源扩容配置（可选）
- docker-compose-中配6核6G.yml - 中等配置（性能 +50%）
- docker-compose-高配8核8G.yml - 高配配置（性能 +100%）⭐ 推荐
- docker-compose-高配16核16G.yml - 极高配置（性能 +300%）
- 热更新到8核8G.sh - 一键热更新脚本

### 文档
- Docker部署指南.md - 详细部署文档
- 资源扩容和热更新指南.md - 扩容指南
- 资源扩容快速参考.txt - 快速参考卡片

## 🚀 快速部署（CentOS）

1. 上传整个目录到 CentOS 服务器：
   scp -r {package_dir} user@server:/opt/

2. 在服务器上运行部署脚本：
   cd /opt/{package_dir}
   chmod +x deploy_centos_docker.sh
   ./deploy_centos_docker.sh

3. 访问服务：
   http://server-ip:5000

## ⚡ 资源扩容（如果出现卡顿）

如果服务出现卡顿或延迟，可以热更新到高配：

### 方法 1: 一键热更新（推荐）
chmod +x 热更新到8核8G.sh
./热更新到8核8G.sh

### 方法 2: 手动更新
cp docker-compose-高配8核8G.yml docker-compose.yml
sudo docker-compose up -d

## 🎯 配置方案对比

| 配置 | CPU | 内存 | 适用场景 | 性能提升 |
|------|-----|------|---------|---------|
| 标准 | 4核 | 4G | 轻量级 QPS<10 | - |
| 中配 | 6核 | 6G | 中等 QPS 10-20 | +50% |
| 高配⭐ | 8核 | 8G | 高并发 QPS 20-40 | +100% |
| 极高 | 16核 | 16G | 超高 QPS 40-80 | +300% |

## 🔊 音量优化说明（v1.1.0 新特性）

本版本默认音量已提升至 1.5 倍：
- 默认音量: 1.5x（无需配置）
- 可选范围: 0.5x - 3.0x

小智配置示例：
```json
{{
  "text": "{{prompt_text}}",
  "speed": 1.0,
  "volume": 2.0  // 可选，需要更大音量时添加
}}
```

## 📚 详细文档

参见：
- Docker部署指南.md - 完整部署流程
- 资源扩容和热更新指南.md - 扩容详细说明
- 资源扩容快速参考.txt - 快速命令参考

---
版本: v1.1.0（含音量优化）
创建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            readme_file = os.path.join(package_dir, "README.txt")
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"[OK] 创建 README.txt")
            
            # 打包（可选）
            print("\n是否打包为 .tar.gz? (y/N): ", end="")
            response = input().strip().lower()
            
            if response == 'y':
                import tarfile
                archive_name = f"{package_dir}.tar.gz"
                
                print(f"正在打包: {archive_name}")
                with tarfile.open(archive_name, "w:gz") as tar:
                    tar.add(package_dir, arcname=os.path.basename(package_dir))
                
                file_size = os.path.getsize(archive_name) / (1024 * 1024)
                print(f"[OK] 已打包: {archive_name} ({file_size:.1f} MB)")
            
            print(f"\n[OK] 部署包创建完成: {package_dir}")
            return package_dir
            
        except Exception as e:
            print(f"[ERROR] 创建部署包失败: {e}")
            return None
    
    def build(self):
        """执行完整构建流程"""
        print("=" * 70)
        print("Sherpa-ONNX TTS Docker 镜像构建工具")
        print("=" * 70)
        print()
        
        # 检查 Docker
        if not self.check_docker():
            return False
        
        # 检查前置条件
        if not self.check_prerequisites():
            return False
        
        # 构建镜像
        if not self.build_image():
            return False
        
        # 验证镜像
        if not self.verify_image():
            return False
        
        # 测试容器（可选）
        print("\n是否测试容器运行? (Y/n): ", end="")
        response = input().strip().lower()
        
        if response != 'n':
            self.test_container()
        
        # 导出镜像
        image_file = self.export_image()
        if not image_file:
            return False
        
        # 创建部署包
        package_dir = self.create_deployment_package(image_file)
        if not package_dir:
            return False
        
        # 总结
        print("\n" + "=" * 70)
        print("构建完成！")
        print("=" * 70)
        print(f"\nDocker 镜像: {self.full_image_name}")
        print(f"导出文件: {image_file}")
        print(f"部署包: {package_dir}")
        print("\n下一步:")
        print(f"  1. 将 {package_dir} 目录传输到 CentOS 服务器")
        print(f"  2. 在服务器上运行: ./deploy_centos_docker.sh")
        print(f"  3. 访问服务: http://server-ip:5000")
        print("\n详细说明请查看: Docker部署指南.md")
        print("=" * 70)
        
        return True

def main():
    builder = DockerImageBuilder()
    
    try:
        success = builder.build()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[WARNING] 构建被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

