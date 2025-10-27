# 📡 Sherpa-ONNX TTS API 使用示例

## 目录

- [基础使用](#基础使用)
- [Python 客户端](#python-客户端)
- [JavaScript 客户端](#javascript-客户端)
- [Bash 脚本](#bash-脚本)
- [高级功能](#高级功能)

---

## 基础使用

### 1. 健康检查

```bash
curl http://server-ip:5000/health
```

**响应**:
```json
{
  "status": "healthy",
  "model": "vits-melo-tts-zh_en",
  "timestamp": "2024-10-21T14:30:45"
}
```

### 2. 获取服务信息

```bash
curl http://server-ip:5000/api/info
```

### 3. 生成中文语音

```bash
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界，这是语音合成测试。"}' \
  -o chinese.wav
```

### 4. 生成英文语音

```bash
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world, this is a text to speech test."}' \
  -o english.wav
```

### 5. 中英混合

```bash
curl -X POST http://server-ip:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello大家好，today我们测试TTS功能。"}' \
  -o mixed.wav
```

---

## Python 客户端

### 简单示例

```python
import requests

BASE_URL = "http://server-ip:5000"

# 生成语音（流式下载）
response = requests.post(
    f"{BASE_URL}/api/tts/stream",
    json={"text": "你好世界", "speed": 1.0}
)

with open("output.wav", "wb") as f:
    f.write(response.content)

print("音频已保存")
```

### 完整客户端类

```python
import requests
from pathlib import Path

class TTSClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_info(self):
        """获取服务信息"""
        response = self.session.get(f"{self.base_url}/api/info")
        return response.json()
    
    def generate_speech(self, text, speed=1.0, output_file="output.wav"):
        """生成语音"""
        response = self.session.post(
            f"{self.base_url}/api/tts/stream",
            json={"text": text, "speed": speed},
            stream=True
        )
        
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return output_file
        else:
            raise Exception(f"TTS failed: {response.text}")
    
    def generate_speech_async(self, text, speed=1.0):
        """异步生成语音（返回文件ID）"""
        response = self.session.post(
            f"{self.base_url}/api/tts",
            json={"text": text, "speed": speed}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"TTS failed: {response.text}")
    
    def download_audio(self, file_id, output_file="output.wav"):
        """下载音频文件"""
        response = self.session.get(
            f"{self.base_url}/api/download/{file_id}",
            stream=True
        )
        
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_file

# 使用示例
if __name__ == "__main__":
    client = TTSClient("http://server-ip:5000")
    
    # 健康检查
    health = client.health_check()
    print(f"服务状态: {health['status']}")
    
    # 生成语音
    client.generate_speech("你好世界", speed=1.0, output_file="test.wav")
    print("语音生成完成")
```

### 批量生成

```python
import concurrent.futures

def batch_generate(texts, output_dir="outputs"):
    client = TTSClient()
    Path(output_dir).mkdir(exist_ok=True)
    
    def generate_one(item):
        index, text = item
        filename = f"{output_dir}/audio_{index:03d}.wav"
        client.generate_speech(text, output_file=filename)
        return filename
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(generate_one, item) 
                   for item in enumerate(texts)]
        
        results = [future.result() for future in futures]
    
    return results

# 使用
texts = [
    "第一句话",
    "第二句话",
    "第三句话",
]

files = batch_generate(texts)
print(f"生成了 {len(files)} 个音频文件")
```

---

## JavaScript 客户端

### Node.js 示例

```javascript
const axios = require('axios');
const fs = require('fs');

const BASE_URL = 'http://server-ip:5000';

// 生成语音
async function generateSpeech(text, outputFile = 'output.wav') {
    try {
        const response = await axios.post(
            `${BASE_URL}/api/tts/stream`,
            { text, speed: 1.0 },
            { responseType: 'arraybuffer' }
        );
        
        fs.writeFileSync(outputFile, response.data);
        console.log(`音频已保存到 ${outputFile}`);
        
    } catch (error) {
        console.error('生成失败:', error.message);
    }
}

// 使用
generateSpeech('你好世界', 'chinese.wav');
```

### 浏览器示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>TTS 测试</title>
</head>
<body>
    <h1>语音合成测试</h1>
    
    <textarea id="text" rows="5" cols="50">
你好世界，这是语音合成测试。
    </textarea>
    <br>
    
    <label>语速:
        <input type="range" id="speed" min="0.5" max="2.0" step="0.1" value="1.0">
        <span id="speed-value">1.0</span>
    </label>
    <br>
    
    <button onclick="generateSpeech()">生成语音</button>
    <br>
    
    <audio id="audio" controls></audio>
    
    <script>
        const BASE_URL = 'http://server-ip:5000';
        
        // 更新语速显示
        document.getElementById('speed').addEventListener('input', function() {
            document.getElementById('speed-value').textContent = this.value;
        });
        
        // 生成语音
        async function generateSpeech() {
            const text = document.getElementById('text').value;
            const speed = parseFloat(document.getElementById('speed').value);
            
            if (!text.trim()) {
                alert('请输入文本');
                return;
            }
            
            try {
                const response = await fetch(`${BASE_URL}/api/tts/stream`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text, speed })
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    
                    const audio = document.getElementById('audio');
                    audio.src = url;
                    audio.play();
                    
                    console.log('语音生成成功');
                } else {
                    const error = await response.json();
                    alert('生成失败: ' + error.error);
                }
                
            } catch (error) {
                alert('请求失败: ' + error.message);
            }
        }
    </script>
</body>
</html>
```

---

## Bash 脚本

### 批量生成脚本

```bash
#!/bin/bash

# 批量生成语音
# 用法: ./batch_tts.sh input.txt output_dir

INPUT_FILE=$1
OUTPUT_DIR=${2:-outputs}
BASE_URL="http://localhost:5000"

# 检查参数
if [ -z "$INPUT_FILE" ]; then
    echo "用法: $0 <input_file> [output_dir]"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 计数器
counter=0

# 读取文件并生成
while IFS= read -r line; do
    # 跳过空行
    if [ -z "$line" ]; then
        continue
    fi
    
    counter=$((counter + 1))
    output_file="$OUTPUT_DIR/audio_$(printf '%03d' $counter).wav"
    
    echo "[$counter] 生成: $line"
    
    curl -X POST "$BASE_URL/api/tts/stream" \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"$line\"}" \
        -o "$output_file" \
        -s
    
    if [ $? -eq 0 ]; then
        echo "    保存到: $output_file"
    else
        echo "    失败"
    fi
done < "$INPUT_FILE"

echo "完成！共生成 $counter 个音频文件"
```

使用:
```bash
# 创建文本文件
cat > texts.txt <<EOF
你好世界
Hello World
中英混合测试
EOF

# 批量生成
chmod +x batch_tts.sh
./batch_tts.sh texts.txt outputs/
```

---

## 高级功能

### 1. 带进度条的下载

```python
import requests
from tqdm import tqdm

def download_with_progress(url, output_file):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_file, 'wb') as f, \
         tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))
```

### 2. 重试机制

```python
import time

def generate_with_retry(text, max_retries=3):
    client = TTSClient()
    
    for attempt in range(max_retries):
        try:
            return client.generate_speech(text)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"重试 ({attempt + 1}/{max_retries})，等待 {wait_time}秒...")
                time.sleep(wait_time)
            else:
                raise
```

### 3. 异步处理

```python
import asyncio
import aiohttp

async def async_generate(session, text, output_file):
    async with session.post(
        f"{BASE_URL}/api/tts/stream",
        json={"text": text}
    ) as response:
        with open(output_file, 'wb') as f:
            async for chunk in response.content.iter_chunked(8192):
                f.write(chunk)
        return output_file

async def batch_generate_async(texts):
    async with aiohttp.ClientSession() as session:
        tasks = [
            async_generate(session, text, f"output_{i}.wav")
            for i, text in enumerate(texts)
        ]
        return await asyncio.gather(*tasks)

# 使用
texts = ["文本1", "文本2", "文本3"]
asyncio.run(batch_generate_async(texts))
```

### 4. 错误处理

```python
class TTSError(Exception):
    pass

def generate_safe(text):
    try:
        client = TTSClient()
        return client.generate_speech(text)
    except requests.exceptions.ConnectionError:
        raise TTSError("无法连接到服务器")
    except requests.exceptions.Timeout:
        raise TTSError("请求超时")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            raise TTSError("文本格式错误")
        elif e.response.status_code == 503:
            raise TTSError("服务不可用")
        else:
            raise TTSError(f"HTTP错误: {e.response.status_code}")
    except Exception as e:
        raise TTSError(f"未知错误: {str(e)}")
```

---

## 完整示例项目

### Python CLI 工具

```python
#!/usr/bin/env python3
"""
TTS 命令行工具
"""

import argparse
import sys
from tts_client import TTSClient

def main():
    parser = argparse.ArgumentParser(description='TTS 命令行工具')
    parser.add_argument('text', help='要转换的文本')
    parser.add_argument('-o', '--output', default='output.wav', help='输出文件名')
    parser.add_argument('-s', '--speed', type=float, default=1.0, help='语速 (0.5-2.0)')
    parser.add_argument('-u', '--url', default='http://localhost:5000', help='服务地址')
    
    args = parser.parse_args()
    
    try:
        client = TTSClient(args.url)
        output_file = client.generate_speech(
            args.text, 
            speed=args.speed,
            output_file=args.output
        )
        print(f"✓ 语音已生成: {output_file}")
        
    except Exception as e:
        print(f"✗ 错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

使用:
```bash
python tts_cli.py "你好世界" -o hello.wav -s 1.2
```

---

**文档版本**: 1.0.0  
**最后更新**: 2024-10-21

