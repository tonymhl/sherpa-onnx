#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
离线部署包制作工具
自动收集所有必要的文件并打包
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import tarfile
import zipfile
from datetime import datetime

class OfflinePackageBuilder:
    def __init__(self, output_dir="tts-deploy-package"):
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def print_step(self, step_num, total_steps, message):
        """打印步骤信息"""
        print(f"\n[{step_num}/{total_steps}] {message}")
        print("-" * 60)
        
    def check_prerequisites(self):
        """检查前置条件"""
        self.print_step(1, 6, "检查前置条件")
        
        # 检查 Python
        print("✅ Python 版本:", sys.version.split()[0])
        
        # 检查 pip
        try:
            result = subprocess.run(["pip", "--version"], 
                                    capture_output=True, text=True, check=True)
            print("✅ pip 可用")
        except subprocess.CalledProcessError:
            print("❌ 错误：pip 不可用")
            return False
        
        # 检查模型文件
        model_dir = Path("vits-melo-tts-zh_en")
        if not model_dir.exists():
            print(f"❌ 错误：找不到模型目录 {model_dir}")
            print("\n请先运行: python download_model.py")
            return False
        
        required_files = ["model.onnx", "lexicon.txt", "tokens.txt"]
        for file_name in required_files:
            file_path = model_dir / file_name
            if not file_path.exists():
                print(f"❌ 错误：缺少文件 {file_name}")
                return False
        
        print(f"✅ 模型文件完整")
        
        return True
    
    def download_dependencies(self):
        """下载 Python 依赖包"""
        self.print_step(2, 6, "下载 Python 依赖包")
        
        packages_dir = self.output_dir / "python-packages"
        packages_dir.mkdir(parents=True, exist_ok=True)
        
        print("正在下载依赖包...")
        print("这可能需要几分钟时间，请耐心等待...")
        
        try:
            # 下载主要依赖
            subprocess.run([
                "pip", "download",
                "sherpa-onnx",
                "soundfile",
                "-d", str(packages_dir)
            ], check=True)
            
            print("\n✅ 依赖包下载完成")
            
            # 统计下载的包数量和大小
            packages = list(packages_dir.glob("*.whl")) + list(packages_dir.glob("*.tar.gz"))
            total_size = sum(p.stat().st_size for p in packages) / 1024 / 1024
            
            print(f"   共下载 {len(packages)} 个包")
            print(f"   总大小: {total_size:.1f} MB")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ 依赖包下载失败: {e}")
            return False
    
    def copy_models(self):
        """复制模型文件"""
        self.print_step(3, 6, "复制模型文件")
        
        models_dir = self.output_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        model_src = Path("vits-melo-tts-zh_en")
        model_dst = models_dir / "vits-melo-tts-zh_en"
        
        if model_dst.exists():
            print(f"删除旧模型目录...")
            shutil.rmtree(model_dst)
        
        print(f"复制 {model_src} -> {model_dst}")
        shutil.copytree(model_src, model_dst)
        
        # 计算模型大小
        total_size = sum(f.stat().st_size for f in model_dst.rglob("*") if f.is_file())
        print(f"✅ 模型复制完成 ({total_size / 1024 / 1024:.1f} MB)")
        
        return True
    
    def copy_scripts(self):
        """复制脚本文件"""
        self.print_step(4, 6, "复制脚本和文档")
        
        scripts_dir = self.output_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # 要复制的文件列表
        files_to_copy = {
            "test_tts.py": scripts_dir,
            "download_model.py": scripts_dir,
            "deploy_windows.bat": self.output_dir,
            "deploy_centos.sh": self.output_dir,
            "部署指南.md": self.output_dir,
            "快速开始指南.md": self.output_dir,
        }
        
        for src_file, dst_dir in files_to_copy.items():
            src_path = Path(src_file)
            if not src_path.exists():
                print(f"⚠️  警告：找不到文件 {src_file}，跳过")
                continue
            
            dst_path = dst_dir / src_file
            shutil.copy2(src_path, dst_path)
            print(f"✅ 复制: {src_file}")
        
        # 设置脚本执行权限（Linux/Mac）
        if sys.platform != "win32":
            deploy_script = self.output_dir / "deploy_centos.sh"
            if deploy_script.exists():
                os.chmod(deploy_script, 0o755)
                print(f"✅ 设置执行权限: deploy_centos.sh")
        
        return True
    
    def create_readme(self):
        """创建 README 文件"""
        readme_content = f"""# Sherpa-ONNX TTS 离线部署包

## 📦 包信息

- **创建时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **模型**: vits-melo-tts-zh_en
- **支持语言**: 中文 + 英文
- **Python 版本**: {sys.version.split()[0]}

## 📂 目录结构

```
tts-deploy-package/
├── models/
│   └── vits-melo-tts-zh_en/     # TTS 模型文件
├── python-packages/              # Python 离线安装包
├── scripts/
│   ├── test_tts.py              # 测试脚本
│   └── download_model.py        # 模型下载脚本
├── deploy_windows.bat           # Windows 自动部署脚本
├── deploy_centos.sh             # CentOS 自动部署脚本
├── 部署指南.md                   # 详细部署指南
├── 快速开始指南.md               # 快速入门
└── README.md                    # 本文件

## 🚀 快速开始

### Windows 环境

1. 确保已安装 Python 3.8+
2. 双击运行 `deploy_windows.bat`

### Linux/CentOS 环境

1. 确保已安装 Python 3.8+
2. 运行以下命令：
   ```bash
   chmod +x deploy_centos.sh
   ./deploy_centos.sh
   ```

## 📝 手动部署

### 1. 安装依赖

```bash
pip install --no-index --find-links=python-packages sherpa-onnx soundfile
```

### 2. 运行测试

```bash
cd scripts
python test_tts.py
```

## 📚 文档

- **快速开始**: 查看 `快速开始指南.md`
- **详细部署**: 查看 `部署指南.md`
- **官方文档**: https://k2-fsa.github.io/sherpa/onnx/tts/

## 🔗 资源链接

- GitHub: https://github.com/k2-fsa/sherpa-onnx
- 模型下载: https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models

## 📞 技术支持

如有问题，请访问：
- GitHub Issues: https://github.com/k2-fsa/sherpa-onnx/issues
- 官方文档: https://k2-fsa.github.io/sherpa/onnx/

---

**版本**: 1.0.0
**构建时间**: {self.timestamp}
"""
        
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        print(f"✅ 创建 README.md")
        
        return True
    
    def create_archive(self, format="tar.bz2"):
        """打包成压缩文件"""
        self.print_step(5, 6, f"创建压缩包 ({format})")
        
        archive_name = f"{self.output_dir.name}-{self.timestamp}"
        
        if format == "tar.bz2":
            archive_path = Path(f"{archive_name}.tar.bz2")
            
            print(f"正在创建 {archive_path}...")
            with tarfile.open(archive_path, "w:bz2") as tar:
                tar.add(self.output_dir, arcname=self.output_dir.name)
            
            print(f"✅ 创建成功: {archive_path}")
            print(f"   大小: {archive_path.stat().st_size / 1024 / 1024:.1f} MB")
            
        elif format == "zip":
            archive_path = Path(f"{archive_name}.zip")
            
            print(f"正在创建 {archive_path}...")
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.output_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.output_dir.parent)
                        zipf.write(file_path, arcname)
            
            print(f"✅ 创建成功: {archive_path}")
            print(f"   大小: {archive_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        else:
            print(f"❌ 不支持的格式: {format}")
            return False
        
        return archive_path
    
    def cleanup(self):
        """清理临时文件"""
        response = input("\n是否删除临时目录? (y/N): ").strip().lower()
        if response == 'y':
            print(f"删除 {self.output_dir}...")
            shutil.rmtree(self.output_dir)
            print("✅ 清理完成")
        else:
            print(f"保留目录: {self.output_dir.absolute()}")
    
    def build(self):
        """构建离线部署包"""
        print("=" * 70)
        print("Sherpa-ONNX TTS 离线部署包制作工具")
        print("=" * 70)
        print()
        
        # 检查前置条件
        if not self.check_prerequisites():
            return False
        
        # 下载依赖
        if not self.download_dependencies():
            return False
        
        # 复制模型
        if not self.copy_models():
            return False
        
        # 复制脚本
        if not self.copy_scripts():
            return False
        
        # 创建 README
        if not self.create_readme():
            return False
        
        # 打包
        self.print_step(6, 6, "最终打包")
        
        print("\n选择压缩格式：")
        print("  1. tar.bz2 (推荐用于 Linux)")
        print("  2. zip (推荐用于 Windows)")
        print("  3. 两者都创建")
        choice = input("请选择 (1-3，默认 1): ").strip() or "1"
        
        archives = []
        if choice in ["1", "3"]:
            archive = self.create_archive("tar.bz2")
            if archive:
                archives.append(archive)
        
        if choice in ["2", "3"]:
            archive = self.create_archive("zip")
            if archive:
                archives.append(archive)
        
        # 总结
        print("\n" + "=" * 70)
        print("✅ 离线部署包创建完成！")
        print("=" * 70)
        print()
        print("生成的文件：")
        for archive in archives:
            print(f"  📦 {archive}")
            print(f"     大小: {archive.stat().st_size / 1024 / 1024:.1f} MB")
        
        print(f"\n临时目录: {self.output_dir.absolute()}")
        print()
        print("下一步：")
        print("  1. 将压缩包复制到目标服务器")
        print("  2. 解压并运行部署脚本")
        print()
        
        # 清理
        self.cleanup()
        
        return True

def main():
    builder = OfflinePackageBuilder()
    
    try:
        success = builder.build()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

