# test_compare_models.py
import torch
import whisper # For original model
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperConfig # For finetuned model
import librosa
import json
from pathlib import Path

# --- 配置路径 ---
# 项目根目录 (假设此脚本放在项目根目录下)
ROOT_DIR = Path(__file__).parent
AI_MODEL_DIR = ROOT_DIR / "ai_model"
AI_TRAIN_DIR = ROOT_DIR / "ai_train"

# 原始 Whisper 模型配置
ORIGINAL_WHISPER_MODEL_NAME = "small"
ORIGINAL_WHISPER_MODEL_PATH = AI_MODEL_DIR / f"{ORIGINAL_WHISPER_MODEL_NAME}.pt" # 本地预训练模型路径

# 微调模型配置
FINETUNED_MODEL_WEIGHTS = AI_MODEL_DIR / "small_finetuned.pt"
FINETUNED_MODEL_CONFIG_DIR = AI_MODEL_DIR / "whisper_small_finetuned_config"

# 测试数据集
TEST_JSON_PATH = AI_TRAIN_DIR / "dataset/test.json"
# AUDIO_BASE_DIR = AI_TRAIN_DIR / "dataset" # test.json中的audio path是相对于此目录的

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SAMPLING_RATE = 16000

# --- 模型加载函数 ---

def load_original_model():
    print(f"\nLoading original Whisper model: {ORIGINAL_WHISPER_MODEL_NAME}...")
    try:
        # 优先从本地路径加载，如果不存在则从网络下载 (如果 download_root 设置了)
        model_path_to_load = str(ORIGINAL_WHISPER_MODEL_PATH) \
            if ORIGINAL_WHISPER_MODEL_PATH.exists() \
            else ORIGINAL_WHISPER_MODEL_NAME
        
        model = whisper.load_model(model_path_to_load, download_root=str(AI_MODEL_DIR))
        model = model.to(DEVICE)
        print("Original Whisper model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading original Whisper model: {e}")
        return None

def load_finetuned_model():
    print(f"\nLoading finetuned Whisper model from {FINETUNED_MODEL_CONFIG_DIR}...")
    if not FINETUNED_MODEL_CONFIG_DIR.exists() or not FINETUNED_MODEL_WEIGHTS.exists():
        print("Finetuned model config directory or weights file does not exist.")
        return None, None
    try:
        processor = WhisperProcessor.from_pretrained(str(FINETUNED_MODEL_CONFIG_DIR))
        config = WhisperConfig.from_pretrained(str(FINETUNED_MODEL_CONFIG_DIR))
        model = WhisperForConditionalGeneration(config=config)
        model.load_state_dict(torch.load(str(FINETUNED_MODEL_WEIGHTS), map_location=DEVICE))
        model = model.to(DEVICE)
        model.eval()
        print("Finetuned Whisper model and processor loaded successfully.")
        return model, processor
    except Exception as e:
        print(f"Error loading finetuned model: {e}")
        return None, None

# --- 转录函数 ---

def transcribe_with_original(model, audio_file_path):
    if model is None:
        return "Original model not loaded."
    try:
        result = model.transcribe(str(audio_file_path), fp16=torch.cuda.is_available())
        return result.get("text", "Transcription error")
    except Exception as e:
        return f"Error during original transcription: {e}"

def transcribe_with_finetuned(model, processor, audio_file_path):
    if model is None or processor is None:
        return "Finetuned model or processor not loaded."
    try:
        speech_array, sr = librosa.load(str(audio_file_path), sr=SAMPLING_RATE)
        input_features = processor(speech_array, sampling_rate=sr, return_tensors="pt").input_features.to(DEVICE)
        
        # 获取强制解码ID (对于中文微调模型很重要)
        forced_decoder_ids = processor.get_decoder_prompt_ids(language="zh", task="transcribe")
        
        predicted_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
        return transcription[0] if transcription else "Transcription error"
    except Exception as e:
        return f"Error during finetuned transcription: {e}"

# --- 主测试逻辑 ---
def main():
    print(f"Using device: {DEVICE}")

    original_model = load_original_model()
    finetuned_model, finetuned_processor = load_finetuned_model()

    if not TEST_JSON_PATH.exists():
        print(f"Test JSON file not found: {TEST_JSON_PATH}")
        return

    with open(TEST_JSON_PATH, 'r', encoding='utf-8') as f:
        test_samples = [json.loads(line) for line in f if line.strip()]

    num_samples_to_test = min(5, len(test_samples)) # 测试前N个样本，可调整
    print(f"\n--- Starting Transcription Comparison for {num_samples_to_test} samples ---")

    for i, sample in enumerate(test_samples[:num_samples_to_test]):
        # test.json 中的 "audio": {"path": "audio/xxx.wav"} 是相对于 `DST_LABEL_DIR` (即 `dataset/`) 的
        # 所以正确的路径拼接应该是：
        audio_full_path = (AI_TRAIN_DIR / "dataset" / sample['audio']['path']).resolve()
        
        reference_text = sample['sentence']

        print(f"\n--- Sample {i+1}/{num_samples_to_test} ---")
        print(f"Audio File: {audio_full_path}")
        print(f"Reference Text:    {reference_text}")

        if original_model:
            original_transcription = transcribe_with_original(original_model, audio_full_path)
            print(f"Original Model:    {original_transcription}")
        else:
            print("Original Model:    Not loaded, skipping.")

        if finetuned_model and finetuned_processor:
            finetuned_transcription = transcribe_with_finetuned(finetuned_model, finetuned_processor, audio_full_path)
            print(f"Finetuned Model:   {finetuned_transcription}")
        else:
            print("Finetuned Model:   Not loaded or processor missing, skipping.")
        
        print("-" * 40)

if __name__ == "__main__":
    # 设置Hugging Face Transformers使用镜像（如果需要且不在全局环境变量中设置）
    # import os
    # os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    main() 