import os
import json
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperConfig
import librosa
from tqdm import tqdm
import jiwer

# 配置
CONFIG_DIR = "whisper_small_finetuned_config"
MODEL_WEIGHTS = "small_finetuned.pt"
TEST_JSON = "dataset/test.json"
AUDIO_DIR = "dataset/audio"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SAMPLING_RATE = 16000

def load_jsonlines(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def main():
    processor = WhisperProcessor.from_pretrained(CONFIG_DIR)
    config = WhisperConfig.from_pretrained(CONFIG_DIR)
    model = WhisperForConditionalGeneration(config)
    model.load_state_dict(torch.load(MODEL_WEIGHTS, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    samples = load_jsonlines(TEST_JSON)
    refs, hyps = [], []

    for sample in tqdm(samples, desc="Evaluating"):
        audio_path = sample['audio']['path']
        if not os.path.isabs(audio_path):
            audio_path = os.path.join(AUDIO_DIR, os.path.basename(audio_path))
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            continue
        speech_array, sr = librosa.load(audio_path, sr=SAMPLING_RATE)
        input_features = processor.feature_extractor(speech_array, sampling_rate=SAMPLING_RATE, return_tensors="pt").input_features.to(DEVICE)
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

if __name__ == "__main__":
    main()