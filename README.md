# Whisper 定制化语音转录与深度文本分析 API 服务

本项目提供一个基于 **作者微调的 OpenAI Whisper 模型** 的语音转录 API 服务。它不仅具备高效精准的语音到文本转换能力，还集成了强大的文本分析功能，包括**关键字提取、多维度语义连接词识别、以及智能场景自动判断**，旨在为用户提供从原始音频到结构化、高价值信息的完整解决方案。
本项目还提供一个 **支持用户直接拉取代码训练自己的基于whisper的语音模型**的代码文件，并提供本人训练的数据集（注意：本人未完全训练所有数据，有条件者可尝试）以供用户训练。
## 项目亮点与核心特性

-   **🚀 高度定制化与优化的转录核心**：
    -   **优先使用用户微调的 Whisper 模型**：支持加载在特定数据集上微调过的 `.pt` 模型文件及相应配置，从而在特定领域（如特定口音、专业术语、特定场景噪音环境）实现超越通用模型的转录精度。
    -   **智能模型回退**：若微调模型加载失败或未配置，系统将自动回退至 OpenAI 原始的 Whisper (small) 模型，确保服务的可用性。
    -   **自动硬件加速**：智能检测并优先使用 GPU (NVIDIA CUDA) 进行运算密集型的转录任务，无兼容 GPU 时则平滑切换至 CPU。

-   **💡 深度文本分析与洞察提取**：
    -   **精准关键字匹配**：基于用户在 `app/core/keywords.py` 中定义的词库，高效识别转录文本中的核心关键字。
    -   **多维度语义连接词识别**：不仅识别词汇，更能理解上下文逻辑。系统能够识别并归类文本中的序列、转折、因果、并列、递进、条件、目的、总结、强调、举例等多种语义连接词，帮助用户快速把握文本结构和论证关系。
    -   **智能场景自动判断**：可根据转录文本内容，结合预定义的场景指示词，自动推断音频最可能归属的应用场景（如课堂、会议、备忘录等），并基于此场景应用更具针对性的关键字分析。用户也可在 API 请求中直接指定场景。

-   **🔧 灵活易用与开发者友好**：
    -   **标准化 REST API 接口**：提供易于集成的 `POST /api/v1/transcribe/` 端点，支持 `form-data` 格式上传音频。
    -   **多种音频格式兼容**：广泛支持如 `.mp3`, `.wav`, `.m4a` 等常见音频文件类型，底层依赖 FFmpeg 进行格式处理。
    -   **可配置的分析词库**：关键字、各类语义连接词、场景指示词均在 `app/core/keywords.py` 中通过清晰的 Python 字典结构进行定义，方便用户按需进行自定义和动态扩展。
    -   **本地模型缓存**：无论是原始模型还是微调模型的相关配置（如处理器），都会利用 Hugging Face Transformers 的缓存机制或指定的本地路径，避免不必要的重复下载。

## 项目结构

```
.
├── app/                    # FastAPI 应用核心目录
│   ├── api/                # API 路由定义
│   │   └── v1/
│   │       └── transcribe.py    # /transcribe 端点的实现逻辑
│   ├── core/               # 核心业务逻辑与配置
│   │   ├── config.py           # 应用配置 (模型路径、上传限制、目录结构等)
│   │   ├── keywords.py         # 关键字、语义连接词、场景指示词的词库定义
│   │   └── whisper_handler.py  # Whisper 模型加载、转录处理、文本分析核心实现
│   └── main.py             # FastAPI 应用主入口 (创建 app 实例)
├── ai_model/               # 存放 AI 模型文件
│   ├── small.pt        # 原始 Whisper small 模型 (下载或手动放置)
│   ├── small_finetuned.pt  # 用户微调后的模型权重
│   └── whisper_small_finetuned_config/ (示例) # 微调模型的配置和处理器文件
├── ai_train/               # (可选) 存放模型训练相关脚本和数据集的目录
│   ├── dataset/
│   │   ├── audio/
│   │   └── test.json
│   └── train_whisper_finetune.py (示例)
├── test_data/              # 存放用于测试 API 的示例音频文件
├── uploads/                # 上传音频的临时存储目录 (自动创建和清理)
├── requirements.txt        # Python 项目依赖包列表
├── README.md               # 本文档
├── test_transcribe.py      # 用于测试 /transcribe API 的 Python 脚本示例
└── test_compare_models.py  # 用于对比原始模型和微调模型转录效果的 Python 脚本
```

## 环境与依赖

-   Python 3.8+ (推荐 3.9 或更高版本)
-   **FFmpeg**：必需。需正确安装并将其 `bin` 目录添加到系统 PATH 环境变量。
-   **NVIDIA CUDA Toolkit & cuDNN** (可选，但强烈推荐用于GPU加速)：若要使用 GPU 加速，需安装与 PyTorch 版本兼容的 CUDA 和 cuDNN。

## 安装指南

1.  **安装 FFmpeg**：
    *   访问 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载。
    *   解压并将 `bin` 目录加入系统 PATH。
    *   验证：终端输入 `ffmpeg -version`。

2.  **克隆项目** (如果通过 Git)：
    ```bash
    git clone <your-repository-url>
    cd <project-directory>
    ```

3.  **创建并激活 Python 虚拟环境** (推荐)：
    ```bash
    python -m venv .venv  # 或 venv
    # Windows
    .venv\Scripts\activate
    # Linux/macOS
    source .venv/bin/activate
    ```

4.  **安装 Python 依赖**：
    ```bash
    pip install -r requirements.txt
    ```
    *关键依赖包括：`fastapi`, `uvicorn`, `openai-whisper`, `torch`, `transformers`, `python-multipart`, `librosa`, `soundfile` (推荐，用于改善 librosa 音频读取), `jiwer` (用于训练脚本中的评估)。*

5.  **准备模型文件** (重要)：
    *   **微调模型 (推荐)**：
        *   将您微调好的模型权重文件 (例如 `small_finetuned.pt`) 放入 `ai_model/` 目录下。
        *   将微调模型对应的 Hugging Face Transformers 配置文件和处理器文件夹 (例如 `whisper_small_finetuned_config/`，其中包含 `config.json`, `preprocessor_config.json` 等) 放入 `ai_model/` 目录下。
        *   确保 `app/core/config.py` 中的 `FINETUNED_WHISPER_WEIGHTS_PATH` 和 `FINETUNED_WHISPER_CONFIG_DIR` 正确指向这些文件/文件夹。
    *   **原始 Whisper 模型 (回退选项)**：
        *   如果 `ai_model/small.pt` (或其他在 `config.py` 中定义的原始模型路径) 不存在，`WhisperHandler` 在首次尝试加载原始模型时，会尝试从 OpenAI 或 Hugging Face 下载（取决于 `whisper.load_model` 或 `transformers` 的默认行为）并保存到 `AI_MODEL_DIR`。
        *   您也可以手动下载 `small.pt` 模型文件并放置在 `ai_model/` 目录下。

## 运行服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
参数说明：
-   `--host 0.0.0.0`：允许从任何 IP 地址访问服务（方便局域网测试）。
-   `--port 8000`：指定服务监听端口。
-   `--reload`：开发模式下，代码更改后自动重启服务。生产环境请移除此参数。

服务启动后，API 文档通常可在以下地址访问：
-   Swagger UI: `http://localhost:8000/docs`
-   ReDoc: `http://localhost:8000/redoc`

## API 端点详解

### `POST /api/v1/transcribe/`

接收音频文件，进行语音转录，并执行后续的文本分析。

**请求参数 (Content-Type: `multipart/form-data`)**：

-   `file`: (文件, 必需) 要转录的音频文件 (例如 `.mp3`, `.wav`, `.m4a`)。
-   `return_type`: (字符串, 可选, 默认: `"json"`) 指定响应内容的格式。
    -   `"json"`: 返回包含完整转录结果、分段信息、耗时、模型信息及详细文本分析结果的 JSON 对象。
    -   `"text"`: 仅返回纯粹的转录文本字符串。
-   `scene`: (字符串, 可选, 默认: 自动检测) 指定或辅助判断应用场景。
    -   有效值示例：`"课堂"`, `"会议"`, `"备忘录"`, `"通用"`, `"auto"`。
    -   若提供 `"auto"` 或不传递此参数，系统将基于文本内容尝试自动检测场景。
    -   若自动检测无明显特征或用户指定的场景词库中未定义，则会应用"通用"场景的关键字和语义规则。

**成功响应 (200 OK) - 当 `return_type="json"` (示例)**：

```json
{
    "text": "今天我们讨论一下项目进展，首先回顾上周的任务，然后明确接下来的计划，但是需要注意截止日期。",
    "language": "zh", // 检测到的语言 (微调模型可能固定为 "zh")
    "segments": [ // 音频分段信息 (具体结构取决于所用模型)
        {
            "text": "今天我们讨论一下项目进展，首先回顾上周的任务，然后明确接下来的计划，",
            "start": 0.0,
            "end": 7.5
        },
        {
            "text": "但是需要注意截止日期。",
            "start": 7.5,
            "end": 10.2
        }
    ],
    "processing_time": 5.32, // 转录和分析总耗时 (秒)
    "model_type": "whisper_small_finetuned_config", // 实际加载并用于转录的模型标识
    "device": "cuda", // 执行转录的设备 ("cuda" 或 "cpu")
    "detected_scene": "会议", // 最终采纳的场景 (用户指定或自动检测)
    "found_keywords": ["项目", "任务", "计划", "截止日期"], // 基于场景识别到的关键字
    "found_semantics": { // 按类别组织的语义连接词
        "序列": ["首先", "然后"],
        "转折": ["但是"],
        "因果": [],
        "总结": []
        // ... 其他配置的语义类别
    }
}
```

**成功响应 (200 OK) - 当 `return_type="text"`**：

```json
{
    "text": "今天我们讨论一下项目进展，首先回顾上周的任务，然后明确接下来的计划，但是需要注意截止日期。"
}
```

## 文本分析功能详解

### 1. 关键字提取
-   **配置**：在 `app/core/keywords.py` 文件中，`KEYWORDS_CONFIG` 字典内，为每个场景（如 "会议", "课堂", "通用" 等）定义一个 "关键字" 列表。
-   **逻辑**：API 会根据 `detected_scene`（用户指定或自动判断的场景）加载对应场景的关键字列表，并在转录文本中进行不区分大小写的匹配。

### 2. 语义连接词识别
-   **配置**：在 `app/core/keywords.py` 中，`KEYWORDS_CONFIG` 内的 `"通用"` 场景下（或其他特定场景下），可以定义一个 `"语义连接"` 字典。此字典的键是语义类别（如 "转折", "因果", "并列"），值是对应类别的连接词列表。
-   **逻辑**：API 会加载（通常是"通用"场景下的）所有语义连接词及其分类，并在转录文本中进行不区分大小写的匹配。匹配到的词会按其原始类别组织在响应的 `found_semantics` 字段中。
-   **优势**：帮助用户快速理解文本的逻辑结构、论点间的关系，对于会议纪要、课程笔记等场景的后续整理和摘要非常有价值。

### 3. 场景自动判断
-   **配置**：在 `app/core/keywords.py` 中，`KEYWORDS_CONFIG` 内，为每个希望被自动识别的场景定义一个 `"场景指示词"` 列表。这些词是能较强暗示该场景的特征词。
-   **逻辑**：当用户未指定场景或指定为 `"auto"` 时，系统会用所有场景的指示词去匹配转录文本。通过简单的计数或其他更复杂的评分机制（当前为计数），选择最匹配的场景作为 `detected_scene`。若无明显匹配，则默认为 `"通用"`。

## 自定义与扩展

-   **词库**：如上所述，`app/core/keywords.py` 是进行所有文本分析规则自定义的核心。您可以：
    -   为现有场景增删关键字、场景指示词。
    -   添加全新的场景及其对应的关键字和指示词。
    -   扩展或修改语义连接词的类别和具体词汇。
-   **模型**：
    -   替换 `ai_model/small_finetuned.pt` 和 `ai_model/whisper_small_finetuned_config/` 为您自己训练的其他 Whisper 微调模型（可能需要相应调整 `app/core/config.py` 中的路径配置）。
    -   修改 `app/core/config.py` 中的 `WHISPER_MODEL_NAME` 或 `WHISPER_MODEL_PATH` 来指定不同的原始 Whisper 模型作为回退选项。
-   **上传限制**：在 `app/core/config.py` 中修改 `MAX_AUDIO_SIZE` 和 `ALLOWED_AUDIO_TYPES`。

## 测试

-   **API 测试**：使用 `test_transcribe.py` 脚本。将测试音频放入 `test_data/` 目录，然后运行 `python test_transcribe.py`。
-   **模型对比测试**：使用 `test_compare_models.py` 脚本。确保原始模型和微调模型均已按要求放置在 `ai_model/` 目录，然后运行 `python test_compare_models.py` 来对比它们的转录效果。

## API 调用代码示例

### Python (`requests`)
```python
import requests
import os
import json # 确保导入 json

api_url = "http://localhost:8000/api/v1/transcribe/"
# 确保 test_data 目录和音频文件存在
audio_file_name = "your_audio_sample.mp3" # 替换为您的测试音频文件名
audio_file_path = os.path.join("test_data", audio_file_name)

if not os.path.exists(audio_file_path):
    print(f"测试文件未找到: {audio_file_path}")
else:
    with open(audio_file_path, "rb") as f:
        payload = {
            "return_type": "json",
            "scene": "auto" 
        }
        # audio/mpeg 对应 .mp3, audio/wav 对应 .wav, audio/mp4 或 audio/m4a 对应 .m4a
        mime_type = "audio/mpeg" # 根据您的文件类型调整
        if audio_file_name.lower().endswith(".wav"):
            mime_type = "audio/wav"
        elif audio_file_name.lower().endswith(".m4a"):
            mime_type = "audio/m4a"

        files = {"file": (os.path.basename(audio_file_path), f, mime_type)}
        
        try:
            response = requests.post(api_url, files=files, data=payload)
            response.raise_for_status() # 如果状态码是 4xx 或 5xx，则抛出 HTTPError
            
            result = response.json()
            print(f"--- 转录结果 ({audio_file_name}) ---")
            print(f"检测到的场景: {result.get('detected_scene')}")
            print(f"模型类型: {result.get('model_type')}")
            print(f"转录文本: {result.get('text')}")
            print(f"识别关键字: {result.get('found_keywords')}")
            print(f"识别语义连接: {json.dumps(result.get('found_semantics'), ensure_ascii=False, indent=4)}")

        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                 print(f"错误详情: {e.response.text}")
        except json.JSONDecodeError:
            print(f"无法解析响应的JSON内容: {response.text}")

```

### JavaScript (`fetch`)
```javascript
async function transcribeAudioAPI(audioFile, scene = 'auto', returnType = 'json') {
    const formData = new FormData();
    formData.append('file', audioFile, audioFile.name); // 传入文件名很重要
    formData.append('return_type', returnType);
    if (scene) {
        formData.append('scene', scene);
    }

    try {
        const response = await fetch('http://localhost:8000/api/v1/transcribe/', {
            method: 'POST',
            body: formData
        });

        const responseData = await response.json(); // 尝试解析所有响应为JSON

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: ${responseData.detail || response.statusText}`);
        }
        
        console.log('--- Transcription Result ---');
        console.log('Detected Scene:', responseData.detected_scene);
        console.log('Model Type:', responseData.model_type);
        console.log('Text:', responseData.text);
        console.log('Keywords:', responseData.found_keywords);
        console.log('Semantics:', JSON.stringify(responseData.found_semantics, null, 2));
        return responseData;

    } catch (error) {
        console.error('Transcription API call failed:', error);
        // 如果错误对象中包含 responseData（例如从自定义的错误抛出中），可以打印更多信息
        if (error.responseData) {
            console.error('Server error details:', error.responseData);
        }
    }
}

// 示例：HTML 中有一个 <input type="file" id="audioFileInput">
// document.getElementById('audioFileInput').addEventListener('change', async (event) => {
//     const file = event.target.files[0];
//     if (file) {
//         await transcribeAudioAPI(file, 'auto'); // 自动检测场景
//         // await transcribeAudioAPI(file, '会议'); // 指定会议场景
//     }
// });
```

## 常见问题与错误处理

-   **`500 Internal Server Error`**:
    -   **FFmpeg 未安装或未在 PATH 中**：这是最常见的原因。请确保 FFmpeg 已正确安装并配置。
    -   **模型文件问题**：微调模型 (`.pt` 或 `config` 目录) 路径不正确、文件损坏或不完整。检查 `ai_model/` 目录和 `app/core/config.py` 中的路径配置。
    -   **依赖库问题**：例如 `torch` 与 CUDA 版本不兼容，或某些底层库缺失。检查 FastAPI 应用启动时的控制台日志获取详细错误栈。
    -   **音频文件本身损坏或格式问题**：虽然服务会尝试处理，但极端损坏或 FFmpeg 无法识别的音频可能导致错误。
-   **`400 Bad Request`**:
    -   **文件类型不支持**：上传了 `ALLOWED_AUDIO_TYPES` (在 `config.py` 定义) 之外的文件类型。
    -   **文件过大**：超过了 `MAX_AUDIO_SIZE` (在 `config.py` 定义) 的限制。
-   **转录结果不佳或乱码**：
    -   **原始模型对于特定口音或噪音表现不佳**：考虑使用针对性的数据集进行模型微调。
    -   **微调模型训练不足或数据质量问题**：检查微调过程和数据集。
    -   **音频质量本身差**：噪音过大、声音过小、多人混杂说话等都会严重影响转录效果。

希望这份文档能帮助您更好地理解和使用本项目！ 
