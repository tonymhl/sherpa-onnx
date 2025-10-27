#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型下载脚本
自动下载 vits-melo-tts-zh_en 模型
"""

import os
import sys
import urllib.request
import tarfile
from pathlib import Path

def download_file(url, filename):
    """下载文件并显示进度"""
    print(f"正在下载: {filename}")
    print(f"下载地址: {url}")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100.0 / total_size, 100)
        mb_downloaded = downloaded / 1024 / 1024
        mb_total = total_size / 1024 / 1024
        
        # 清除当前行并打印进度
        sys.stdout.write(f"\r进度: {percent:.1f}% ({mb_downloaded:.1f} MB / {mb_total:.1f} MB)")
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, report_progress)
        print("\n✅ 下载完成!")
        return True
    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
        return False

def extract_tarfile(filename, extract_path="."):
    """解压 tar.bz2 文件"""
    print(f"\n正在解压: {filename}")
    
    try:
        with tarfile.open(filename, "r:bz2") as tar:
            tar.extractall(path=extract_path)
        print("✅ 解压完成!")
        return True
    except Exception as e:
        print(f"❌ 解压失败: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("Sherpa-ONNX 模型下载工具")
    print("=" * 70)
    print()
    
    # 模型信息
    model_name = "vits-melo-tts-zh_en"
    model_url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{model_name}.tar.bz2"
    model_filename = f"{model_name}.tar.bz2"
    
    print(f"模型名称: {model_name}")
    print(f"模型大小: 约 163 MB")
    print(f"支持语言: 中文 + 英文")
    print()
    
    # 检查模型是否已存在
    if os.path.exists(model_name) and os.path.isdir(model_name):
        print(f"⚠️  模型目录 '{model_name}' 已存在")
        response = input("是否重新下载? (y/N): ").strip().lower()
        if response != 'y':
            print("跳过下载")
            return
        
        # 删除旧模型
        import shutil
        shutil.rmtree(model_name)
        print(f"已删除旧模型目录")
    
    # 下载模型
    print("\n开始下载模型...")
    print("提示：如果下载失败，您可以手动从以下地址下载：")
    print(f"  {model_url}")
    print()
    
    if not download_file(model_url, model_filename):
        print("\n❌ 自动下载失败")
        print("\n请手动下载模型：")
        print(f"  1. 访问: {model_url}")
        print(f"  2. 下载文件到当前目录")
        print(f"  3. 运行以下命令解压:")
        print(f"     python download_model.py --extract {model_filename}")
        sys.exit(1)
    
    # 解压模型
    print("\n开始解压模型...")
    if not extract_tarfile(model_filename):
        print("\n❌ 解压失败")
        print("\n请手动解压:")
        print(f"  使用 7-Zip 或其他工具解压 {model_filename}")
        sys.exit(1)
    
    # 清理压缩包
    print("\n清理临时文件...")
    try:
        os.remove(model_filename)
        print(f"✅ 已删除压缩包: {model_filename}")
    except Exception as e:
        print(f"⚠️  删除压缩包失败: {str(e)}")
    
    # 验证模型文件
    print("\n验证模型文件...")
    required_files = ["model.onnx", "lexicon.txt", "tokens.txt"]
    model_dir = Path(model_name)
    
    missing_files = []
    for file_name in required_files:
        file_path = model_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
        else:
            file_size = file_path.stat().st_size
            if file_name == "model.onnx":
                print(f"  ✅ {file_name}: {file_size / 1024 / 1024:.1f} MB")
            else:
                print(f"  ✅ {file_name}: {file_size / 1024:.1f} KB")
    
    if missing_files:
        print(f"\n❌ 缺少以下文件: {', '.join(missing_files)}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ 模型下载和验证完成！")
    print("=" * 70)
    print()
    print(f"模型位置: {os.path.abspath(model_name)}")
    print()
    print("下一步：")
    print("  1. 运行测试脚本: python test_tts.py")
    print("  2. 或查看部署指南: 部署指南.md")
    print()

def extract_only(filename):
    """仅解压已下载的文件"""
    print(f"解压模式: 仅解压 {filename}")
    
    if not os.path.exists(filename):
        print(f"❌ 错误: 文件不存在: {filename}")
        sys.exit(1)
    
    if extract_tarfile(filename):
        print("\n✅ 解压完成！")
        
        # 删除压缩包
        response = input("\n是否删除压缩包? (Y/n): ").strip().lower()
        if response != 'n':
            try:
                os.remove(filename)
                print(f"✅ 已删除: {filename}")
            except Exception as e:
                print(f"⚠️  删除失败: {str(e)}")
    else:
        print("\n❌ 解压失败")
        sys.exit(1)

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--extract" and len(sys.argv) > 2:
            extract_only(sys.argv[2])
        else:
            print("用法:")
            print("  python download_model.py              # 下载并解压模型")
            print("  python download_model.py --extract <文件名>  # 仅解压已下载的文件")
            sys.exit(1)
    else:
        try:
            main()
        except KeyboardInterrupt:
            print("\n\n⚠️  下载被用户中断")
            sys.exit(130)
        except Exception as e:
            print(f"\n\n❌ 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

