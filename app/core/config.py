from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# AI模型存储目录
AI_MODEL_DIR = ROOT_DIR / "ai_model"
AI_MODEL_DIR.mkdir(exist_ok=True)

# 临时文件存储目录
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Whisper模型配置
WHISPER_MODEL_NAME = "small"
# WHISPER_MODEL_PATH 原本指向一个子目录，现在直接指向模型文件
WHISPER_MODEL_PATH = AI_MODEL_DIR / f"{WHISPER_MODEL_NAME}.pt" # 例如 ai_model/small.pt

# 新增：微调模型的配置
FINETUNED_WHISPER_MODEL_NAME = "small_finetuned"
FINETUNED_WHISPER_WEIGHTS_PATH = AI_MODEL_DIR / f"{FINETUNED_WHISPER_MODEL_NAME}.pt" # 指向 ai_model/small_finetuned.pt
FINETUNED_WHISPER_CONFIG_DIR = AI_MODEL_DIR / "whisper_small_finetuned_config"    # 指向 ai_model/whisper_small_finetuned_config/

# 文件上传配置
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_AUDIO_TYPES = [
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/x-m4a",
    "audio/m4a",
] 