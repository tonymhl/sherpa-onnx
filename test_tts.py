#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sherpa-ONNX TTS 测试脚本
支持 vits-melo-tts-zh_en 模型的中英文混合语音合成
"""

import sherpa_onnx
import soundfile as sf
import time
import os
import sys

def test_tts_zh_en():
    """测试中英文混合TTS"""
    
    # 自动检测模型路径
    model_paths = [
        "./vits-melo-tts-zh_en",  # 当前目录
        "../models/vits-melo-tts-zh_en",  # 上级目录的models文件夹
        "./models/vits-melo-tts-zh_en",  # 同级models文件夹
    ]
    
    model_dir = None
    for path in model_paths:
        if os.path.exists(path) and os.path.isdir(path):
            model_dir = path
            break
    
    if model_dir is None:
        print("❌ 错误：找不到模型目录 'vits-melo-tts-zh_en'")
        print("\n请确保模型文件位于以下任一位置：")
        for path in model_paths:
            print(f"  - {os.path.abspath(path)}")
        sys.exit(1)
    
    print(f"✅ 找到模型目录: {os.path.abspath(model_dir)}")
    
    # 配置模型路径
    model_file = os.path.join(model_dir, "model.onnx")
    lexicon_file = os.path.join(model_dir, "lexicon.txt")
    tokens_file = os.path.join(model_dir, "tokens.txt")
    
    # 检查必要文件
    missing_files = []
    for file_path, file_name in [
        (model_file, "model.onnx"),
        (lexicon_file, "lexicon.txt"),
        (tokens_file, "tokens.txt")
    ]:
        if not os.path.exists(file_path):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ 错误：缺少以下文件：{', '.join(missing_files)}")
        sys.exit(1)
    
    print(f"✅ 模型文件检查完成")
    print(f"   - model.onnx: {os.path.getsize(model_file) / 1024 / 1024:.1f} MB")
    print(f"   - lexicon.txt: {os.path.getsize(lexicon_file) / 1024:.1f} KB")
    print(f"   - tokens.txt: {os.path.getsize(tokens_file) / 1024:.1f} KB")
    
    # 创建 TTS 配置
    # vits-melo-tts-zh_en 模型配置
    print("\n正在加载模型...")
    
    # 检查 dict 目录（jieba 字典）
    dict_dir = os.path.join(model_dir, "dict")
    if not os.path.exists(dict_dir):
        print(f"⚠️  警告：找不到 dict 目录，jieba 功能可能不可用")
        dict_dir = ""
    else:
        print(f"✅ 找到 jieba 字典目录: {dict_dir}")
    
    # 检查 rule_fsts 文件（用于数字、日期等的转换）
    rule_fsts = []
    for fst_name in ["phone.fst", "date.fst", "number.fst"]:
        fst_path = os.path.join(model_dir, fst_name)
        if os.path.exists(fst_path):
            rule_fsts.append(fst_path)
    
    rule_fsts_str = ",".join(rule_fsts) if rule_fsts else ""
    if rule_fsts_str:
        print(f"✅ 找到规则文件: {len(rule_fsts)} 个")
    
    # 配置 VITS 模型（包含 dict_dir）
    vits_config = sherpa_onnx.OfflineTtsVitsModelConfig(
        model=model_file,
        lexicon=lexicon_file,
        tokens=tokens_file,
        dict_dir=dict_dir,  # 关键：指定 jieba 字典目录
    )
    
    tts_config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=vits_config,
            num_threads=4,  # 根据您的CPU核心数调整
            debug=False,
            provider="cpu",
        ),
        rule_fsts=rule_fsts_str,  # 添加规则文件
        max_num_sentences=1,
    )
    
    # 验证配置
    if not tts_config.validate():
        print("❌ 错误：配置验证失败，请检查模型文件")
        sys.exit(1)
    
    # 创建 TTS 对象
    start_load = time.time()
    tts = sherpa_onnx.OfflineTts(tts_config)
    load_time = time.time() - start_load
    print(f"✅ 模型加载成功（耗时: {load_time:.2f}秒）")
    
    # 测试用例
    test_cases = [
        ("纯中文测试：你好世界，这是一个语音合成测试。", "test_chinese.wav"),
        ("English test: Hello world, this is a text to speech test.", "test_english.wav"),
        ("中英混合：Hello大家好，today我们测试TTS功能。", "test_mixed.wav"),
        ("数字测试：今天是2024年10月21日，电话号码是13812345678。", "test_numbers.wav"),
        ("长句测试：当夜幕降临，星光点点，伴随着微风拂面，我在静谧中感受着时光的流转。", "test_long.wav"),
    ]
    
    print("\n" + "=" * 80)
    print("开始测试 vits-melo-tts-zh_en 模型")
    print("=" * 80)
    
    success_count = 0
    total_audio_duration = 0
    total_generation_time = 0
    
    for i, (text, filename) in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 测试文本: {text}")
        
        try:
            start_time = time.time()
            audio = tts.generate(text, sid=0, speed=1.0)
            end_time = time.time()
            
            if len(audio.samples) == 0:
                print(f"❌ 错误：音频生成失败")
                continue
            
            # 保存音频
            sf.write(
                filename,
                audio.samples,
                samplerate=audio.sample_rate,
                subtype="PCM_16",
            )
            
            # 计算性能指标
            elapsed_seconds = end_time - start_time
            audio_duration = len(audio.samples) / audio.sample_rate
            rtf = elapsed_seconds / audio_duration
            
            total_audio_duration += audio_duration
            total_generation_time += elapsed_seconds
            success_count += 1
            
            print(f"✅ 成功保存到: {filename}")
            print(f"   音频时长: {audio_duration:.2f}秒")
            print(f"   生成耗时: {elapsed_seconds:.2f}秒")
            print(f"   RTF (实时率): {rtf:.3f}")
            print(f"   文件大小: {os.path.getsize(filename) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print(f"成功生成: {success_count}/{len(test_cases)} 个音频文件")
    
    if success_count > 0:
        avg_rtf = total_generation_time / total_audio_duration
        print(f"总音频时长: {total_audio_duration:.2f}秒")
        print(f"总生成耗时: {total_generation_time:.2f}秒")
        print(f"平均 RTF: {avg_rtf:.3f}")
        
        # 性能评估
        if avg_rtf < 0.1:
            performance = "优秀 🚀"
        elif avg_rtf < 0.3:
            performance = "良好 ✅"
        elif avg_rtf < 1.0:
            performance = "合格 ✔️"
        else:
            performance = "较慢 ⚠️"
        
        print(f"性能评估: {performance}")
        print("\n提示：")
        print("  - RTF < 1.0 表示可以实时合成")
        print("  - 可以通过调整 num_threads 参数优化性能")
        print("  - 首次合成可能较慢，后续会更快")
    
    print("\n生成的音频文件：")
    for _, filename in test_cases:
        if os.path.exists(filename):
            print(f"  - {filename}")

def test_speed_variations():
    """测试不同语速"""
    print("\n" + "=" * 80)
    print("测试不同语速")
    print("=" * 80)
    
    # 简化的快速测试（不重新加载模型）
    text = "这是语速测试。"
    
    try:
        # 重用已加载的TTS对象需要在函数外部定义
        # 这里仅作演示，实际使用时可以调整
        print("\n提示：语速参数 speed 可以设置为 0.5-2.0 之间的值")
        print("  - speed=0.8: 慢速")
        print("  - speed=1.0: 正常速度")
        print("  - speed=1.2: 快速")
        print("  - speed=1.5: 很快")
        
    except Exception as e:
        print(f"语速测试跳过: {str(e)}")

if __name__ == "__main__":
    try:
        test_tts_zh_en()
        test_speed_variations()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试完成！")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

