#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版 TTS 测试脚本（避免 Windows 控制台编码问题）
"""

import sherpa_onnx
import soundfile as sf
import time
import os
import sys

def main():
    print("=" * 70)
    print("Sherpa-ONNX TTS Test (Simplified)")
    print("Model: vits-melo-tts-zh_en")
    print("=" * 70)
    print()
    
    # 检查模型目录
    model_dir = "vits-melo-tts-zh_en"
    if not os.path.exists(model_dir):
        print(f"ERROR: Model directory not found: {model_dir}")
        print("\nPlease download the model first:")
        print("  python download_model.py")
        return False
    
    print(f"[OK] Found model directory: {model_dir}")
    
    # 检查必要文件
    model_file = os.path.join(model_dir, "model.onnx")
    lexicon_file = os.path.join(model_dir, "lexicon.txt")
    tokens_file = os.path.join(model_dir, "tokens.txt")
    dict_dir = os.path.join(model_dir, "dict")
    
    for file_path, name in [
        (model_file, "model.onnx"),
        (lexicon_file, "lexicon.txt"),
        (tokens_file, "tokens.txt"),
        (dict_dir, "dict directory"),
    ]:
        if not os.path.exists(file_path):
            print(f"ERROR: Missing {name}")
            return False
        print(f"[OK] Found {name}")
    
    print()
    print("Loading model...")
    
    # 配置模型
    try:
        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=model_file,
                    lexicon=lexicon_file,
                    tokens=tokens_file,
                    dict_dir=dict_dir,  # KEY: jieba dictionary
                ),
                num_threads=4,
                provider="cpu",
            ),
            rule_fsts=f"{model_dir}/phone.fst,{model_dir}/date.fst,{model_dir}/number.fst",
        )
        
        if not config.validate():
            print("ERROR: Config validation failed")
            return False
        
        start_load = time.time()
        tts = sherpa_onnx.OfflineTts(config)
        load_time = time.time() - start_load
        
        print(f"[OK] Model loaded successfully ({load_time:.2f} seconds)")
        print()
        
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试用例
    test_cases = [
        ("test_chinese.wav", "你好世界，这是一个语音合成测试。"),
        ("test_english.wav", "Hello world, this is a text to speech test."),
        ("test_mixed.wav", "Hello大家好，today我们测试TTS功能。"),
        ("test_numbers.wav", "今天是2024年10月21日，电话号码是13812345678。"),
    ]
    
    print("Starting TTS tests...")
    print("=" * 70)
    
    success_count = 0
    total_audio_time = 0
    total_gen_time = 0
    
    for i, (filename, text) in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Generating: {filename}")
        print(f"Text: {text}")
        
        try:
            start = time.time()
            audio = tts.generate(text, sid=0, speed=1.0)
            elapsed = time.time() - start
            
            if len(audio.samples) == 0:
                print("ERROR: Generated audio is empty")
                continue
            
            # 保存音频
            sf.write(filename, audio.samples, 
                    samplerate=audio.sample_rate, 
                    subtype="PCM_16")
            
            # 计算指标
            duration = len(audio.samples) / audio.sample_rate
            rtf = elapsed / duration
            
            total_audio_time += duration
            total_gen_time += elapsed
            success_count += 1
            
            print(f"[OK] Saved to: {filename}")
            print(f"     Duration: {duration:.2f}s")
            print(f"     Gen time: {elapsed:.2f}s")
            print(f"     RTF: {rtf:.3f}")
            print(f"     Size: {os.path.getsize(filename) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Success: {success_count}/{len(test_cases)}")
    
    if success_count > 0:
        avg_rtf = total_gen_time / total_audio_time
        print(f"Total audio duration: {total_audio_time:.2f}s")
        print(f"Total generation time: {total_gen_time:.2f}s")
        print(f"Average RTF: {avg_rtf:.3f}")
        
        if avg_rtf < 0.1:
            performance = "Excellent"
        elif avg_rtf < 0.3:
            performance = "Good"
        elif avg_rtf < 1.0:
            performance = "Acceptable"
        else:
            performance = "Slow"
        
        print(f"Performance: {performance}")
    
    print()
    print("Generated files:")
    for filename, _ in test_cases:
        if os.path.exists(filename):
            print(f"  - {filename}")
    
    print()
    print("=" * 70)
    print("Test completed successfully!" if success_count == len(test_cases) else "Some tests failed")
    print("=" * 70)
    
    return success_count == len(test_cases)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

