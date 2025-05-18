import os
import json
import random
import shutil

# 源数据目录
SRC_DIR = "data_thchs30/data"
# 目标音频目录
DST_AUDIO_DIR = "dataset/audio"
# 目标标注目录
DST_LABEL_DIR = "dataset"
os.makedirs(DST_AUDIO_DIR, exist_ok=True)
os.makedirs(DST_LABEL_DIR, exist_ok=True)

# 收集所有.wav文件
wav_files = [f for f in os.listdir(SRC_DIR) if f.endswith('.wav')]
wav_files = sorted(wav_files)  # 保证顺序一致
random.seed(42)
random.shuffle(wav_files)
wav_files = wav_files[:500]  # 修改点：只取500条

samples = []
for wav in wav_files:
    wav_path = os.path.join(SRC_DIR, wav)
    trn_path = wav_path + ".trn"
    if not os.path.exists(trn_path):
        print(f"缺少标注文件，跳过: {trn_path}")
        continue
    # 读取标注文件的第一行
    with open(trn_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if not lines:
            print(f"标注文件为空，跳过: {trn_path}")
            continue
        sentence = lines[0].strip()
    # 复制音频到目标目录
    dst_wav_path = os.path.join(DST_AUDIO_DIR, wav)
    if not os.path.exists(dst_wav_path):
        shutil.copy(wav_path, dst_wav_path)
    # 构造样本
    samples.append({
        "audio": {"path": f"audio/{wav}"},
        "sentence": sentence
    })

# 划分训练/测试（90/10）
random.shuffle(samples)
n_train = int(len(samples) * 0.9)
train_samples = samples[:n_train]
test_samples = samples[n_train:]

with open(os.path.join(DST_LABEL_DIR, "train.json"), "w", encoding="utf-8") as f:
    for s in train_samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
with open(os.path.join(DST_LABEL_DIR, "test.json"), "w", encoding="utf-8") as f:
    for s in test_samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"已生成 {len(train_samples)} 条训练数据，{len(test_samples)} 条测试数据。")
print("数据已准备好，可直接用于 train_whisper_finetune.py 训练。")