import whisper
import torch
from pathlib import Path
from typing import Union, Dict, Any, List, Tuple
from app.core.config import (
    WHISPER_MODEL_NAME,
    WHISPER_MODEL_PATH,
    AI_MODEL_DIR,
    FINETUNED_WHISPER_WEIGHTS_PATH,
    FINETUNED_WHISPER_CONFIG_DIR
)
from app.core.keywords import (
    get_keywords_by_scene,
    get_all_semantic_keywords_with_category,
    get_scene_indicator_words,
    KEYWORDS_CONFIG
)
import time
import re
from collections import Counter

from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperConfig

class WhisperHandler:
    def __init__(self):
        self._model = None
        self._processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name_loaded = "original_whisper"

    def _load_finetuned_model(self):
        """尝试加载微调后的模型和处理器"""
        print(f"Attempting to load finetuned model from: {FINETUNED_WHISPER_CONFIG_DIR} and weights from: {FINETUNED_WHISPER_WEIGHTS_PATH}")
        if FINETUNED_WHISPER_CONFIG_DIR.exists() and FINETUNED_WHISPER_WEIGHTS_PATH.exists():
            try:
                self._processor = WhisperProcessor.from_pretrained(str(FINETUNED_WHISPER_CONFIG_DIR))
                
                model_config = WhisperConfig.from_pretrained(str(FINETUNED_WHISPER_CONFIG_DIR))
                self._model = WhisperForConditionalGeneration(config=model_config)
                self._model.load_state_dict(torch.load(str(FINETUNED_WHISPER_WEIGHTS_PATH), map_location=self.device))
                
                self._model = self._model.to(self.device)
                self._model.eval()
                self.model_name_loaded = FINETUNED_WHISPER_CONFIG_DIR.name
                print(f"Successfully loaded finetuned model '{self.model_name_loaded}' and processor from local files.")
                return True
            except Exception as e:
                print(f"Error loading finetuned model: {e}. Will attempt to load original whisper model.")
                self._model = None
                self._processor = None
                return False
        else:
            print("Finetuned model config or weights path does not exist. Will attempt to load original whisper model.")
            return False

    def _load_original_whisper_model(self):
        """加载原始的 OpenAI Whisper 模型"""
        print(f"Attempting to load original OpenAI Whisper model: {WHISPER_MODEL_NAME}")
        try:
            self._model = whisper.load_model(
                WHISPER_MODEL_NAME if not WHISPER_MODEL_PATH.exists() else str(WHISPER_MODEL_PATH),
                download_root=str(AI_MODEL_DIR)
            )
            self._model = self._model.to(self.device)
            self.model_name_loaded = f"original_whisper_{WHISPER_MODEL_NAME}"
            print(f"Successfully loaded original OpenAI Whisper model: {self.model_name_loaded}")
            return True
        except Exception as e:
            print(f"Error loading original OpenAI Whisper model: {e}")
            self._model = None
            return False

    @property
    def model(self):
        if self._model is None:
            if not self._load_finetuned_model():
                self._load_original_whisper_model()
        return self._model
    
    @property
    def processor(self):
        if self._processor is None:
            _ = self.model
            if self._processor is None and self.model_name_loaded.startswith("original_whisper"):
                print("Original whisper model does not have a separate Hugging Face processor. Operations will use model's internal methods.")
        return self._processor

    def _find_keywords_and_semantics(self, text: str, keywords_to_check: List[str], semantic_keywords_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """在文本中查找指定的关键字和语义连接词 (不区分大小写)"""
        lower_text = text.lower()
        
        found_plain_keywords = set()
        for kw in keywords_to_check:
            # 对于普通关键字，简单包含检查
            if kw.lower() in lower_text:
                found_plain_keywords.add(kw) 
                
        found_semantic_keywords: Dict[str, List[str]] = {}
        for category, kws in semantic_keywords_map.items():
            current_category_found = []
            for kw in kws:
                if kw.lower() in lower_text: # 简单包含检查
                    current_category_found.append(kw)
            if current_category_found:
                found_semantic_keywords[category] = list(set(current_category_found)) # 去重
                
        return {
            "keywords": list(found_plain_keywords),
            "semantics": found_semantic_keywords
        }

    def _auto_detect_scene(self, text: str) -> str:
        """根据文本内容自动判断场景"""
        lower_text = text.lower()
        scene_scores: Dict[str, int] = Counter()
        indicator_map = get_scene_indicator_words()

        for scene, indicators in indicator_map.items():
            for indicator in indicators:
                if indicator in lower_text:
                    scene_scores[scene] += 1
        
        if scene_scores:
            return scene_scores.most_common(1)[0][0]
        return "通用"

    def transcribe(self, audio_path: Union[str, Path], requested_scene: str = None) -> Dict[str, Any]:
        start_time = time.time() # 记录开始时间
        
        current_model = self.model
        if current_model is None:
            raise Exception("Whisper model could not be loaded.")

        transcribed_text = ""
        detected_language = "unknown"
        segments = []
        _processing_time_value = 0.0 

        try:
            if self.model_name_loaded.startswith("original_whisper"):
                result = current_model.transcribe(str(audio_path), fp16=torch.cuda.is_available())
                transcribed_text = result.get("text", "")
                detected_language = result.get("language", "unknown")
                segments = result.get("segments", [])
            elif self._processor and isinstance(current_model, WhisperForConditionalGeneration):
                import librosa
                
                speech_array = librosa.load(str(audio_path), sr=self._processor.feature_extractor.sampling_rate)[0]
                
                processed_input = self._processor(
                    speech_array,
                    sampling_rate=self._processor.feature_extractor.sampling_rate, 
                    return_tensors="pt",
                )
                input_features = processed_input["input_features"].to(self.device) # 使用字典访问
                
                if "attention_mask" in processed_input:
                    attention_mask = processed_input["attention_mask"].to(self.device)
                else:
                    print("WARNING: 'attention_mask' not found in processor output. Passing None to model.generate.")
                    attention_mask = None 

                forced_decoder_ids = self._processor.get_decoder_prompt_ids(language="zh", task="transcribe")
                
                generate_args = {
                    "input_features": input_features,
                    "forced_decoder_ids": forced_decoder_ids
                }
                if attention_mask is not None: # 只有当 attention_mask 存在时才传递
                    generate_args["attention_mask"] = attention_mask
                
                predicted_ids = current_model.generate(**generate_args)
                
                transcription_result = self._processor.batch_decode(predicted_ids, skip_special_tokens=True)
                transcribed_text = transcription_result[0] if transcription_result else ""
                
                if hasattr(current_model.config, "forced_decoder_ids"):
                    lang_code = "zh"
                else:
                    lang_code = "zh"
                detected_language = lang_code
                
                segments = [{"text": transcribed_text, "start": 0, "end": 0}]
            else:
                raise Exception(f"Model '{self.model_name_loaded}' is not a recognized type for transcription.")
            
            _processing_time_value = time.time() - start_time

        except Exception as e:
            _processing_time_value = time.time() - start_time 
            if "ffmpeg" in str(e).lower():
                print("FFMPEG related error suspected. Please ensure FFmpeg is installed and in system PATH.")
            
            import traceback
            print(f"Error during transcription with model {self.model_name_loaded}:")
            print(f"Exception Type: {type(e)}")
            print(f"Exception Details: {str(e)}")
            print("Traceback:")
            traceback.print_exc()

            raise
        
        if requested_scene and requested_scene != "auto":
            final_scene = requested_scene
        else:
            final_scene = self._auto_detect_scene(transcribed_text)
        
        current_scene_keywords_config = KEYWORDS_CONFIG.get(final_scene, {})
        scene_specific_plain_keywords = [kw.lower() for kw in current_scene_keywords_config.get("关键字", [])]
        all_semantic_keywords_map = get_all_semantic_keywords_with_category()
        analysis_result = self._find_keywords_and_semantics(transcribed_text, scene_specific_plain_keywords, all_semantic_keywords_map)

        output = {
            "text": transcribed_text,
            "language": detected_language,
            "segments": segments,
            "processing_time": _processing_time_value,
            "model_type": self.model_name_loaded,
            "device": self.device,
            "detected_scene": final_scene,
            "found_keywords": analysis_result["keywords"],
            "found_semantics": analysis_result["semantics"]
        }
        
        return output

whisper_handler = WhisperHandler() 