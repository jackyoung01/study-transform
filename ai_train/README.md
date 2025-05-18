# Whisper 微调训练与数据准备说明（ai_train 目录）

本说明适用于在本地微调 Whisper small 语音识别模型，适配 thchs30 数据集（或类似结构的数据）。

---

## 1. 目录结构

请确保您的工作区目录结构如下：

```
<项目根目录>/
├── ai_model/
│   └── small.pt                  # 预训练 Whisper small 模型
│
├── ai_train/
│   ├── data_thchs30/             # 原始数据集目录（需手动下载解压）
│   │   └── data/                 # 包含 .wav 和 .trn 文件
│   ├── dataset/
│   │   ├── audio/                # 训练用音频文件（自动生成）
│   │   ├── train.json            # 训练集标注（自动生成）
│   │   └── test.json             # 测试集标注（自动生成）
│   ├── prepare_thchs30_json.py   # 数据准备脚本
│   ├── train_whisper_finetune.py # 训练与评测脚本
│   ├── small_finetuned.pt        # 微调后模型（训练后生成）
│   └── whisper_small_finetuned_config/ # 微调后模型配置（训练后生成）
│
└── ...
```

---

## 2. 数据准备流程

1. **确保 `data_thchs30/data/` 下有 .wav 和 .trn 文件。**
2. 在 `ai_train` 目录下运行：
   ```bash
   cd <项目根目录>/ai_train
   python prepare_thchs30_json.py
   ```
3. 脚本会自动：
   - 复制 100 条音频到 `dataset/audio/`
   - 生成 `dataset/train.json` 和 `dataset/test.json`

**注意：**
- 必须在 `ai_train` 目录下运行，否则会找不到数据目录。
- 如需更多样本，可修改脚本中的 `wav_files = wav_files[:100]`。

---

## 3. 训练与评测流程

1. 确保 `ai_model/small.pt` 存在。
2. 在 `ai_train` 目录下运行：
   ```bash
   python train_whisper_finetune.py
   ```
3. 训练完成后会自动在测试集上评测，并输出 CER/WER。
4. 训练后生成：
   - `small_finetuned.pt`（微调模型权重）
   - `whisper_small_finetuned_config/`（模型和分词器配置）

---

## 4. 常见错误与解决办法

### 1. 路径找不到/数据集未找到
- **报错：FileNotFoundError: ... 'data_thchs30/data'**
  - 解决：请确保在 `ai_train` 目录下运行脚本。
  - 检查 `SRC_DIR` 路径是否与实际目录一致。

### 2. 依赖未安装
- **报错：无法导入 soundfile/librosa/torch/transformers/jiwer 等**
  - 解决：安装依赖
    ```bash
    pip install torch transformers librosa tqdm jiwer numpy
    ```

### 3. 编辑器启动按钮导致路径错误
- 解决：请用终端 `cd ai_train` 后再运行脚本。

---

## 5. 推理/集成简要说明

训练完成后，可用如下代码加载微调模型进行推理：

```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch, librosa

config_dir = "ai_train/whisper_small_finetuned_config"
model_weights = "ai_train/small_finetuned.pt"
device = "cuda" if torch.cuda.is_available() else "cpu"

processor = WhisperProcessor.from_pretrained(config_dir)
model = WhisperForConditionalGeneration.from_pretrained(config_dir)
model.load_state_dict(torch.load(model_weights, map_location=device))
model.to(device)
model.eval()

# 推理示例
audio_path = "your_audio.wav"
speech_array, sr = librosa.load(audio_path, sr=16000)
input_features = processor.feature_extractor(speech_array, sampling_rate=16000, return_tensors="pt").input_features.to(device)
with torch.no_grad():
    predicted_ids = model.generate(
        input_features,
        forced_decoder_ids=processor.get_decoder_prompt_ids(language="zh", task="transcribe")
    )
    transcription = processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True)[0]
print("识别结果：", transcription)
```

---

## 6. 依赖安装说明

建议在虚拟环境中安装：
```bash
pip install torch transformers librosa tqdm jiwer numpy
```

---

如有问题，建议先检查路径和依赖，再查阅本说明。如需进一步帮助，欢迎随时提问！ 