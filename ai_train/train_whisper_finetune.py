import os
# 必须在 import transformers 之前设置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" #解决中国huggingface.co无法访问问题
os.environ['HF_HOME'] = os.path.abspath('hf_cache')
os.environ['TRANSFORMERS_CACHE'] = os.path.abspath('hf_cache/transformers')
os.environ['HUGGINGFACE_HUB_CACHE'] = os.path.abspath('hf_cache/hub')
os.environ['HF_DATASETS_CACHE'] = os.path.abspath('hf_cache/datasets')
import json
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperFeatureExtractor, WhisperTokenizer
import librosa
import numpy as np
from tqdm import tqdm
import jiwer

# 配置参数
# MODEL_PATH = "../ai_model/small.pt"  # 不再使用本地pt权重
FINETUNED_MODEL_SAVE_PATH = "small_finetuned.pt"
MODEL_CONFIG_SAVE_DIR = "whisper_small_finetuned_config"
AUDIO_DIR = "dataset/audio"
TRAIN_JSON = "dataset/train.json"
TEST_JSON = "dataset/test.json"
LEARNING_RATE = 5e-6
BATCH_SIZE = 2
NUM_EPOCHS = 2
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SAMPLING_RATE = 16000

print(f"Using device: {DEVICE}")
print(f"Audio dir: {AUDIO_DIR}")
print(f"Train json: {TRAIN_JSON}")
print(f"Test json: {TEST_JSON}")
print(f"Huggingface cache dir: {os.environ['HF_HOME']}")

# 数据集类
def load_jsonlines(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

class AudioTranscriptionDataset(Dataset):
    def __init__(self, json_path, audio_dir, feature_extractor, tokenizer, sampling_rate=SAMPLING_RATE):
        self.samples = load_jsonlines(json_path)
        self.audio_dir = audio_dir
        self.feature_extractor = feature_extractor
        self.tokenizer = tokenizer
        self.sampling_rate = sampling_rate
        print(f"Loaded {len(self.samples)} samples from {json_path}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        audio_path = sample['audio']['path']
        if not os.path.isabs(audio_path):
            audio_path = os.path.join(self.audio_dir, os.path.basename(audio_path))
        text = sample['sentence']
        try:
            speech_array, sr = librosa.load(audio_path, sr=self.sampling_rate)
        except Exception as e:
            print(f"Error loading audio file {audio_path}: {e}. Skipping.")
            return None
        input_features = self.feature_extractor(speech_array, sampling_rate=self.sampling_rate, return_tensors="pt").input_features
        labels = self.tokenizer(text, return_tensors="pt").input_ids
        return {
            "input_features": input_features.squeeze(0),
            "labels": labels.squeeze(0)
        }

def dynamic_collate_fn(batch):
    batch = [item for item in batch if item is not None]
    if not batch:
        return None
    input_features = [item["input_features"] for item in batch]
    labels = [item["labels"] for item in batch]
    padded_input_features = torch.nn.utils.rnn.pad_sequence(input_features, batch_first=True, padding_value=0.0)
    pad_token_id = 50257
    padded_labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=pad_token_id)
    return {
        "input_features": padded_input_features,
        "labels": padded_labels
    }

def evaluate_on_testset(model, processor, test_json_path, audio_dir, device):
    print(f"Evaluating on test set: {test_json_path}")
    refs, hyps = [], []
    samples = load_jsonlines(test_json_path)
    for sample in tqdm(samples, desc="Evaluating"):
        audio_path = sample['audio']['path']
        if not os.path.isabs(audio_path):
            audio_path = os.path.join(audio_dir, os.path.basename(audio_path))
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            continue
        speech_array, sr = librosa.load(audio_path, sr=SAMPLING_RATE)
        input_features = processor.feature_extractor(speech_array, sampling_rate=SAMPLING_RATE, return_tensors="pt").input_features.to(device)
        with torch.no_grad():
            predicted_ids = model.generate(
                input_features,
                forced_decoder_ids=processor.get_decoder_prompt_ids(language="zh", task="transcribe")
            )
            transcription = processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        refs.append(sample['sentence'])
        hyps.append(transcription)
        print(f"REF: {sample['sentence']}")
        print(f"HYP: {transcription}")
        print('-' * 30)
    cer = jiwer.cer(refs, hyps)
    wer = jiwer.wer(refs, hyps)
    print(f"Test CER: {cer:.4f}")
    print(f"Test WER: {wer:.4f}")

def main():
    # 直接用 transformers 官方权重和配置
    feature_extractor = WhisperFeatureExtractor.from_pretrained("openai/whisper-small")
    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-small", language="Chinese", task="transcribe")
    processor = WhisperProcessor.from_pretrained("openai/whisper-small")
    pad_token_id = processor.tokenizer.pad_token_id

    train_dataset = AudioTranscriptionDataset(TRAIN_JSON, AUDIO_DIR, feature_extractor, tokenizer)
    dataloader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=dynamic_collate_fn)

    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
    model.to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    print("Starting training...")
    model.train()
    for epoch in range(NUM_EPOCHS):
        print(f"--- Epoch {epoch+1}/{NUM_EPOCHS} ---")
        total_loss = 0
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}")
        for batch in progress_bar:
            if batch is None:
                continue
            input_features = batch["input_features"].to(DEVICE)
            labels = batch["labels"].to(DEVICE)
            labels[labels == pad_token_id] = -100
            optimizer.zero_grad()
            outputs = model(input_features=input_features, labels=labels)
            loss = outputs.loss
            if loss is None:
                continue
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            progress_bar.set_postfix({"loss": f"{loss.item():.4f}"})
        avg_loss = total_loss / (len(dataloader) or 1)
        print(f"Epoch {epoch+1} - Avg Loss: {avg_loss:.4f}")

    print("Training finished. Saving model...")
    torch.save(model.state_dict(), FINETUNED_MODEL_SAVE_PATH)
    if not os.path.exists(MODEL_CONFIG_SAVE_DIR):
        os.makedirs(MODEL_CONFIG_SAVE_DIR)
    model.config.save_pretrained(MODEL_CONFIG_SAVE_DIR)
    processor.save_pretrained(MODEL_CONFIG_SAVE_DIR)
    print(f"Model and processor configs saved to {MODEL_CONFIG_SAVE_DIR}")

    # 自动评测
    if os.path.exists(TEST_JSON):
        evaluate_on_testset(model, processor, TEST_JSON, AUDIO_DIR, DEVICE)
    else:
        print(f"Test set {TEST_JSON} not found, skipping evaluation.")

if __name__ == "__main__":
    main()
