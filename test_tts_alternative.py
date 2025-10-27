#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
替代TTS模型测试脚本
如果 vits-melo-tts-zh_en 遇到问题，使用这个脚本测试其他模型
"""

import sherpa_onnx
import soundfile as sf
import time
import os
import sys

def test_vits_piper_english():
    """测试 vits-piper 英文模型"""
    print("\n" + "=" * 80)
    print("测试 vits-piper 英文模型")
    print("=" * 80)
    
    model_dir = "vits-piper-en_GB-cori-medium"
    
    if not os.path.exists(model_dir):
        print(f"❌ 找不到模型目录: {model_dir}")
        print("\n下载命令：")
        print(f"wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{model_dir}.tar.bz2")
        print(f"tar xvf {model_dir}.tar.bz2")
        return False
    
    try:
        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=f"./{model_dir}/en_GB-cori-medium.onnx",
                    tokens=f"./{model_dir}/tokens.txt",
                    data_dir=f"./{model_dir}/espeak-ng-data",
                ),
                num_threads=4,
                provider="cpu",
            ),
        )
        
        if not config.validate():
            print("❌ 配置验证失败")
            return False
        
        print("✅ 配置验证成功，正在加载模型...")
        start_load = time.time()
        tts = sherpa_onnx.OfflineTts(config)
        load_time = time.time() - start_load
        print(f"✅ 模型加载成功（耗时: {load_time:.2f}秒）")
        
        # 测试
        text = "Hello world! This is a text to speech test."
        print(f"\n生成语音: {text}")
        
        start = time.time()
        audio = tts.generate(text, sid=0, speed=1.0)
        elapsed = time.time() - start
        
        if len(audio.samples) == 0:
            print("❌ 音频生成失败")
            return False
        
        filename = "test_piper_english.wav"
        sf.write(filename, audio.samples, samplerate=audio.sample_rate, subtype="PCM_16")
        
        duration = len(audio.samples) / audio.sample_rate
        rtf = elapsed / duration
        
        print(f"✅ 成功生成: {filename}")
        print(f"   音频时长: {duration:.2f}秒")
        print(f"   生成耗时: {elapsed:.2f}秒")
        print(f"   RTF: {rtf:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_vits_icefall_chinese():
    """测试 vits-icefall 中文模型"""
    print("\n" + "=" * 80)
    print("测试 vits-icefall 中文模型")
    print("=" * 80)
    
    model_dir = "vits-icefall-zh-aishell3"
    
    if not os.path.exists(model_dir):
        print(f"❌ 找不到模型目录: {model_dir}")
        print("\n下载命令：")
        print(f"wget https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{model_dir}.tar.bz2")
        print(f"tar xvf {model_dir}.tar.bz2")
        return False
    
    try:
        # 检查 rule_fsts 文件
        rule_fsts = []
        for fst_name in ["phone.fst", "date.fst", "number.fst"]:
            fst_path = os.path.join(model_dir, fst_name)
            if os.path.exists(fst_path):
                rule_fsts.append(fst_path)
        
        rule_fsts_str = ",".join(rule_fsts) if rule_fsts else ""
        
        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=f"./{model_dir}/model.onnx",
                    lexicon=f"./{model_dir}/lexicon.txt",
                    tokens=f"./{model_dir}/tokens.txt",
                ),
                num_threads=4,
                provider="cpu",
            ),
            rule_fsts=rule_fsts_str,
        )
        
        if not config.validate():
            print("❌ 配置验证失败")
            return False
        
        print("✅ 配置验证成功，正在加载模型...")
        start_load = time.time()
        tts = sherpa_onnx.OfflineTts(config)
        load_time = time.time() - start_load
        print(f"✅ 模型加载成功（耗时: {load_time:.2f}秒）")
        
        # 测试多个说话人
        test_cases = [
            (21, "刘备", "勿以恶小而为之，勿以善小而不为。"),
            (66, "孙尚香", "今天天气真不错。"),
            (10, "女声", "你好世界，这是语音合成测试。"),
        ]
        
        for sid, speaker_name, text in test_cases:
            print(f"\n生成语音（说话人{sid}-{speaker_name}）: {text}")
            
            start = time.time()
            audio = tts.generate(text, sid=sid, speed=1.0)
            elapsed = time.time() - start
            
            if len(audio.samples) == 0:
                print(f"❌ 音频生成失败")
                continue
            
            filename = f"test_icefall_zh_{sid}.wav"
            sf.write(filename, audio.samples, samplerate=audio.sample_rate, subtype="PCM_16")
            
            duration = len(audio.samples) / audio.sample_rate
            rtf = elapsed / duration
            
            print(f"✅ 成功生成: {filename}")
            print(f"   音频时长: {duration:.2f}秒")
            print(f"   生成耗时: {elapsed:.2f}秒")
            print(f"   RTF: {rtf:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 80)
    print("Sherpa-ONNX 替代模型测试工具")
    print("=" * 80)
    print()
    print("如果 vits-melo-tts-zh_en 遇到问题，可以测试以下替代模型：")
    print("  1. vits-piper-en_GB-cori-medium (英文)")
    print("  2. vits-icefall-zh-aishell3 (中文)")
    print()
    print("=" * 80)
    
    # 检查 sherpa-onnx 版本
    try:
        print(f"\nsherpa-onnx 版本: {sherpa_onnx.__version__}")
    except:
        print("\n⚠️  无法获取 sherpa-onnx 版本信息")
    
    # 测试模型
    results = {}
    
    # 测试英文模型
    results['english'] = test_vits_piper_english()
    
    # 测试中文模型
    results['chinese'] = test_vits_icefall_chinese()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    if results.get('english'):
        print("✅ 英文模型测试通过")
    else:
        print("❌ 英文模型测试失败（可能未下载模型）")
    
    if results.get('chinese'):
        print("✅ 中文模型测试通过")
    else:
        print("❌ 中文模型测试失败（可能未下载模型）")
    
    if not any(results.values()):
        print("\n⚠️  所有测试都失败了")
        print("\n建议：")
        print("1. 先下载模型文件")
        print("2. 检查 sherpa-onnx 安装是否正确")
        print("3. 查看详细错误信息")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

