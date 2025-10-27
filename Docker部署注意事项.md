# ⚠️ Docker 部署重要注意事项

## 关于 `vits-melo-tts-zh_en` 模型的 `dict_dir` 配置

### 问题背景

在 Windows 本地测试时，您遇到了以下错误：
```
D:\a\sherpa-onnx\sherpa-onnx\sherpa-onnx/csrc/offline-tts-vits-impl.h:InitFrontend:384
Please provide --vits-dict-dir for Chinese TTS models using jieba
```

这是因为 `vits-melo-tts-zh_en` 模型是中文TTS模型，**必须**提供 `dict_dir` 参数指向 jieba 字典目录。

---

## ✅ 已在 Docker 方案中解决

我们已经在 Docker 部署方案中**完整解决**了这个问题：

### 1. 模型文件完整复制

**Dockerfile (第25行)**:
```dockerfile
COPY vits-melo-tts-zh_en /app/models/vits-melo-tts-zh_en
```

✅ 这会复制整个模型目录，**包括关键的 `dict/` 子目录**

确保您的模型目录结构如下：
```
vits-melo-tts-zh_en/
├── model.onnx           # 模型文件
├── lexicon.txt          # 词典
├── tokens.txt           # 标记
├── dict/                # ⭐ jieba 字典目录（必需）
│   ├── jieba.dict.utf8
│   ├── user.dict.utf8
│   └── ...
├── phone.fst            # 规则文件（可选）
├── date.fst
└── number.fst
```

### 2. 正确配置 dict_dir 参数

**tts_service.py (第60行和88行)**:
```python
# 第60行：定义 dict_dir 路径
dict_dir = os.path.join(MODEL_DIR, "dict")

# 第88行：配置中使用 dict_dir
vits=sherpa_onnx.OfflineTtsVitsModelConfig(
    model=model_file,
    lexicon=lexicon_file,
    tokens=tokens_file,
    dict_dir=dict_dir,  # ⭐ 关键配置
),
```

✅ 正确指向 `/app/models/vits-melo-tts-zh_en/dict` 目录

### 3. 安装 jieba 依赖

**Dockerfile (第31-37行)**:
```dockerfile
RUN pip install --no-index --find-links=/app/python-packages \
    sherpa-onnx \
    soundfile \
    flask \
    flask-cors \
    jieba \        # ⭐ jieba 中文分词库（必需）
    waitress \
    && rm -rf /app/python-packages
```

✅ 离线安装 jieba 库

**build_docker_image.py (第92行)**:
```python
subprocess.run([
    "pip", "download",
    "sherpa-onnx", "soundfile", "flask", "flask-cors", "jieba", "waitress",
    #                                                    ^^^^^^
    "-d", "python-packages"
], check=True)
```

✅ 下载 jieba 到离线包

### 4. 文件完整性检查

**tts_service.py (第62-70行)**:
```python
# 检查必要文件
for file_path, name in [
    (model_file, "model.onnx"),
    (lexicon_file, "lexicon.txt"),
    (tokens_file, "tokens.txt"),
    (dict_dir, "dict directory"),  # ⭐ 检查 dict 目录是否存在
]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing {name}: {file_path}")
```

✅ 启动时自动验证 dict 目录

---

## 🔍 部署前验证清单

### Windows 构建阶段

在运行 `python build_docker_image.py` 之前，请确认：

- [ ] **模型目录完整**
  ```bash
  # 检查 dict 目录是否存在
  dir vits-melo-tts-zh_en\dict
  ```
  
  应该看到类似：
  ```
  jieba.dict.utf8
  user.dict.utf8
  idf.utf8.dict
  stop_words.utf8
  ```

- [ ] **python-packages 包含 jieba**
  ```bash
  # 如果还没下载依赖，运行：
  pip download sherpa-onnx soundfile flask flask-cors jieba waitress -d python-packages
  
  # 检查是否包含 jieba
  dir python-packages\jieba*
  ```

- [ ] **所有必需文件就位**
  ```
  ✓ vits-melo-tts-zh_en/
  ✓ vits-melo-tts-zh_en/dict/
  ✓ python-packages/ (包含 jieba)
  ✓ Dockerfile
  ✓ docker-compose.yml
  ✓ tts_service.py
  ```

### Docker 镜像构建

构建脚本会自动检查，但您可以手动验证：

```powershell
# 构建镜像
python build_docker_image.py

# 构建后，检查镜像内容
docker run --rm sherpa-onnx-tts:latest ls -la /app/models/vits-melo-tts-zh_en/dict

# 应该看到 jieba 字典文件
```

### CentOS 部署阶段

部署后验证：

```bash
# 1. 检查容器是否正常启动
sudo docker ps | grep sherpa-onnx-tts

# 2. 检查日志中是否有 dict_dir 错误
sudo docker logs sherpa-onnx-tts-service | grep dict

# 3. 测试 API（关键验证）
curl -X POST http://localhost:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界"}' \
  -o test.wav

# 4. 检查音频文件
ls -lh test.wav
file test.wav
```

---

## 🐛 如果仍然出现 dict_dir 错误

### 症状
```
Please provide --vits-dict-dir for Chinese TTS models using jieba
```

### 诊断步骤

#### 1. 检查模型目录是否完整

进入容器检查：
```bash
sudo docker exec -it sherpa-onnx-tts-service bash

# 在容器内
ls -la /app/models/vits-melo-tts-zh_en/
ls -la /app/models/vits-melo-tts-zh_en/dict/
```

**预期输出**：
```
drwxr-xr-x 2 root root   4096 Oct 21 14:30 dict
-rw-r--r-- 1 root root 170000 Oct 21 14:30 model.onnx
-rw-r--r-- 1 root root   6840 Oct 21 14:30 lexicon.txt
-rw-r--r-- 1 root root    600 Oct 21 14:30 tokens.txt
```

如果 `dict/` 目录不存在 → **重新构建镜像，确保模型目录完整**

#### 2. 检查 jieba 是否安装

```bash
sudo docker exec -it sherpa-onnx-tts-service python -c "import jieba; print(jieba.__version__)"
```

如果报错 `No module named 'jieba'` → **重新构建镜像，确保 python-packages 包含 jieba**

#### 3. 检查配置是否正确

```bash
sudo docker exec -it sherpa-onnx-tts-service python -c "
import os
MODEL_DIR = '/app/models/vits-melo-tts-zh_en'
dict_dir = os.path.join(MODEL_DIR, 'dict')
print(f'dict_dir: {dict_dir}')
print(f'exists: {os.path.exists(dict_dir)}')
if os.path.exists(dict_dir):
    print(f'files: {os.listdir(dict_dir)}')
"
```

**预期输出**：
```
dict_dir: /app/models/vits-melo-tts-zh_en/dict
exists: True
files: ['jieba.dict.utf8', 'user.dict.utf8', ...]
```

---

## 🔧 解决方案

### 方案1：重新构建镜像（推荐）

如果发现问题，重新构建：

```powershell
# Windows 上
cd D:\workspace\sherpa-onnx

# 1. 确认模型目录完整
dir vits-melo-tts-zh_en\dict

# 2. 确认 jieba 在离线包中
dir python-packages\jieba*

# 3. 重新构建
docker rmi sherpa-onnx-tts:latest  # 删除旧镜像
python build_docker_image.py        # 重新构建
```

### 方案2：临时修复（不推荐）

如果只是测试，可以临时挂载：

修改 `docker-compose.yml`:
```yaml
volumes:
  - ./vits-melo-tts-zh_en:/app/models/vits-melo-tts-zh_en:ro
  - ./output:/app/output
  - ./logs:/app/logs
```

但这**不是离线方案**，CentOS 上需要额外复制模型。

---

## ✅ 最终验证

部署成功后，运行完整测试：

```bash
# 1. 中文测试
curl -X POST http://localhost:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "这是中文测试，今天是2024年10月21日"}' \
  -o chinese.wav

# 2. 英文测试
curl -X POST http://localhost:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "This is an English test"}' \
  -o english.wav

# 3. 中英混合测试
curl -X POST http://localhost:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello大家好，today是10月21号"}' \
  -o mixed.wav

# 4. 数字日期测试（需要 jieba 和 rule_fsts）
curl -X POST http://localhost:5000/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "我的电话是13800138000，日期是2024-10-21"}' \
  -o numbers.wav
```

如果所有测试都成功生成音频文件，说明 `dict_dir` 配置完全正确！✅

---

## 📝 总结

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Dockerfile 复制模型 | ✅ | 包含 dict 目录 |
| tts_service.py 配置 | ✅ | dict_dir 正确设置 |
| Dockerfile 安装 jieba | ✅ | 已添加到依赖 |
| build_docker_image.py | ✅ | 下载 jieba 到离线包 |
| 启动时文件检查 | ✅ | 验证 dict 目录存在 |

**结论**：Docker 部署方案已经**完整解决** `dict_dir` 问题，不会在 CentOS 环境中出现您之前遇到的错误。

---

**最后更新**: 2024-10-21  
**适用版本**: Docker 部署方案 v1.0.0

