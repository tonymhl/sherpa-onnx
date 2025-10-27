#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sherpa-ONNX TTS HTTP API 服务
提供 RESTful API 用于文本转语音
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from waitress import serve
import sherpa_onnx
import soundfile as sf
import numpy as np
import os
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域

# 全局配置
MODEL_DIR = os.getenv('MODEL_DIR', '/app/models/vits-melo-tts-zh_en')
NUM_THREADS = int(os.getenv('NUM_THREADS', '4'))
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '500'))
OUTPUT_DIR = '/app/output'
LOG_DIR = '/app/logs'

# 确保目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 全局 TTS 对象（单例）
_tts_instance = None
_tts_lock = threading.Lock()

def apply_volume_gain(samples, volume=1.0):
    """
    应用音量增益
    
    Args:
        samples: 音频样本数组
        volume: 音量倍数（1.0 = 原音量，2.0 = 两倍音量）
    
    Returns:
        处理后的音频样本
    """
    if volume == 1.0:
        return samples
    
    # 转换为 numpy 数组
    audio_array = np.array(samples, dtype=np.float32)
    
    # 应用增益
    audio_array = audio_array * volume
    
    # 限制在 [-1.0, 1.0] 范围内，防止削波失真
    audio_array = np.clip(audio_array, -1.0, 1.0)
    
    return audio_array

def get_tts():
    """获取或创建 TTS 实例（线程安全）"""
    global _tts_instance
    
    if _tts_instance is None:
        with _tts_lock:
            if _tts_instance is None:
                logger.info("Initializing TTS model...")
                
                model_file = os.path.join(MODEL_DIR, "model.onnx")
                lexicon_file = os.path.join(MODEL_DIR, "lexicon.txt")
                tokens_file = os.path.join(MODEL_DIR, "tokens.txt")
                dict_dir = os.path.join(MODEL_DIR, "dict")
                
                # 检查必要文件
                for file_path, name in [
                    (model_file, "model.onnx"),
                    (lexicon_file, "lexicon.txt"),
                    (tokens_file, "tokens.txt"),
                    (dict_dir, "dict directory"),
                ]:
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Missing {name}: {file_path}")
                
                # 配置规则文件
                rule_fsts = []
                for fst_name in ["phone.fst", "date.fst", "number.fst"]:
                    fst_path = os.path.join(MODEL_DIR, fst_name)
                    if os.path.exists(fst_path):
                        rule_fsts.append(fst_path)
                
                rule_fsts_str = ",".join(rule_fsts)
                
                # 创建配置
                config = sherpa_onnx.OfflineTtsConfig(
                    model=sherpa_onnx.OfflineTtsModelConfig(
                        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                            model=model_file,
                            lexicon=lexicon_file,
                            tokens=tokens_file,
                            dict_dir=dict_dir,
                        ),
                        num_threads=NUM_THREADS,
                        provider="cpu",
                    ),
                    rule_fsts=rule_fsts_str,
                )
                
                if not config.validate():
                    raise ValueError("TTS config validation failed")
                
                start = time.time()
                _tts_instance = sherpa_onnx.OfflineTts(config)
                elapsed = time.time() - start
                
                logger.info(f"TTS model initialized successfully ({elapsed:.2f}s)")
    
    return _tts_instance

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        tts = get_tts()
        return jsonify({
            'status': 'healthy',
            'model': 'vits-melo-tts-zh_en',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/info', methods=['GET'])
def get_info():
    """获取服务信息"""
    return jsonify({
        'service': 'Sherpa-ONNX TTS',
        'model': 'vits-melo-tts-zh_en',
        'version': '1.1.0',
        'capabilities': {
            'languages': ['zh', 'en'],
            'mixed_language': True,
            'max_text_length': MAX_TEXT_LENGTH,
            'speed_range': [0.5, 2.0],
            'volume_range': [0.5, 3.0],
            'default_volume': 1.5,
        },
        'endpoints': {
            '/health': 'GET - Health check',
            '/api/info': 'GET - Service information',
            '/api/tts': 'POST - Generate speech from text',
            '/api/tts/stream': 'POST - Generate and return audio file',
        }
    }), 200

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    文本转语音接口
    
    请求体（JSON）:
    {
        "text": "要转换的文本",
        "speed": 1.0,  # 可选，语速 0.5-2.0
        "volume": 1.5,  # 可选，音量倍数 0.5-3.0，默认 1.5
        "format": "wav"  # 可选，输出格式（目前仅支持 wav）
    }
    
    响应（JSON）:
    {
        "success": true,
        "file_id": "uuid",
        "filename": "output.wav",
        "duration": 3.45,
        "text_length": 20,
        "generation_time": 0.52,
        "rtf": 0.151,
        "download_url": "/api/download/uuid"
    }
    """
    try:
        # 解析请求
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing "text" field'}), 400
        
        text = data['text'].strip()
        speed = float(data.get('speed', 1.0))
        volume = float(data.get('volume', 1.5))  # 默认 1.5 倍音量
        output_format = data.get('format', 'wav').lower()
        
        # 验证参数
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({
                'error': f'Text too long (max {MAX_TEXT_LENGTH} characters)'
            }), 400
        
        if not (0.5 <= speed <= 2.0):
            return jsonify({'error': 'Speed must be between 0.5 and 2.0'}), 400
        
        if not (0.5 <= volume <= 3.0):
            return jsonify({'error': 'Volume must be between 0.5 and 3.0'}), 400
        
        if output_format != 'wav':
            return jsonify({'error': 'Only WAV format is supported'}), 400
        
        # 生成语音
        logger.info(f"Generating TTS for text: {text[:50]}... (speed={speed}, volume={volume})")
        
        tts = get_tts()
        
        start = time.time()
        audio = tts.generate(text, sid=0, speed=speed)
        generation_time = time.time() - start
        
        if len(audio.samples) == 0:
            return jsonify({'error': 'Failed to generate audio'}), 500
        
        # 应用音量增益
        audio_samples = apply_volume_gain(audio.samples, volume)
        
        # 计算指标
        duration = len(audio_samples) / audio.sample_rate
        rtf = generation_time / duration
        
        # 保存音频
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.wav"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        sf.write(filepath, audio_samples, 
                samplerate=audio.sample_rate, 
                subtype="PCM_16")
        
        file_size = os.path.getsize(filepath)
        
        logger.info(
            f"TTS generated successfully: "
            f"duration={duration:.2f}s, "
            f"gen_time={generation_time:.2f}s, "
            f"RTF={rtf:.3f}, "
            f"volume={volume}x"
        )
        
        # 返回结果
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'duration': round(duration, 2),
            'sample_rate': audio.sample_rate,
            'text_length': len(text),
            'generation_time': round(generation_time, 2),
            'rtf': round(rtf, 3),
            'volume': volume,
            'file_size': file_size,
            'download_url': f'/api/download/{file_id}',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tts/stream', methods=['POST'])
def text_to_speech_stream():
    """
    文本转语音并直接返回音频文件
    
    请求体（JSON）:
    {
        "text": "要转换的文本",
        "speed": 1.0,
        "volume": 1.5  # 可选，音量倍数 0.5-3.0，默认 1.5
    }
    
    响应: 音频文件流（WAV格式）
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing "text" field'}), 400
        
        text = data['text'].strip()
        speed = float(data.get('speed', 1.0))
        volume = float(data.get('volume', 1.5))  # 默认 1.5 倍音量
        
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({
                'error': f'Text too long (max {MAX_TEXT_LENGTH} characters)'
            }), 400
        
        # 生成语音
        logger.info(f"Stream TTS: {text[:50]}... (speed={speed}, volume={volume})")
        
        tts = get_tts()
        audio = tts.generate(text, sid=0, speed=speed)
        
        if len(audio.samples) == 0:
            return jsonify({'error': 'Failed to generate audio'}), 500
        
        # 应用音量增益
        audio_samples = apply_volume_gain(audio.samples, volume)
        
        # 临时保存
        temp_id = str(uuid.uuid4())
        temp_file = os.path.join(OUTPUT_DIR, f"{temp_id}.wav")
        
        sf.write(temp_file, audio_samples, 
                samplerate=audio.sample_rate, 
                subtype="PCM_16")
        
        # 返回文件
        return send_file(
            temp_file,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='output.wav'
        )
        
    except Exception as e:
        logger.error(f"TTS stream failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<file_id>', methods=['GET'])
def download_audio(file_id):
    """下载生成的音频文件"""
    try:
        filepath = os.path.join(OUTPUT_DIR, f"{file_id}.wav")
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=f'{file_id}.wav'
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return """
    <html>
    <head><title>Sherpa-ONNX TTS Service</title></head>
    <body>
        <h1>Sherpa-ONNX TTS Service</h1>
        <p>Model: vits-melo-tts-zh_en (Chinese + English)</p>
        <h2>API Endpoints:</h2>
        <ul>
            <li>GET /health - Health check</li>
            <li>GET /api/info - Service information</li>
            <li>POST /api/tts - Generate speech</li>
            <li>POST /api/tts/stream - Generate and download</li>
            <li>GET /api/download/&lt;file_id&gt; - Download audio</li>
        </ul>
        <h2>Example:</h2>
        <pre>
curl -X POST http://localhost:5000/api/tts \\
  -H "Content-Type: application/json" \\
  -d '{"text": "你好世界", "speed": 1.0}'
        </pre>
    </body>
    </html>
    """

def cleanup_old_files():
    """清理旧的音频文件（保留最近1小时）"""
    try:
        now = time.time()
        for filename in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > 3600:  # 1小时
                    os.remove(filepath)
                    logger.info(f"Cleaned up old file: {filename}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

def start_cleanup_thread():
    """启动清理线程"""
    def cleanup_loop():
        while True:
            time.sleep(600)  # 每10分钟清理一次
            cleanup_old_files()
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info("Cleanup thread started")

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("Starting Sherpa-ONNX TTS Service")
    logger.info("=" * 70)
    logger.info(f"Model directory: {MODEL_DIR}")
    logger.info(f"Number of threads: {NUM_THREADS}")
    logger.info(f"Max text length: {MAX_TEXT_LENGTH}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    # 预加载模型
    try:
        get_tts()
        logger.info("Model preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload model: {e}")
        exit(1)
    
    # 启动清理线程
    start_cleanup_thread()
    
    # 启动服务
    logger.info("Starting HTTP server on 0.0.0.0:5000")
    logger.info("=" * 70)
    
    serve(app, host='0.0.0.0', port=5000, threads=4)

