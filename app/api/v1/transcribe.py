from fastapi import APIRouter, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from app.core.config import UPLOAD_DIR, ALLOWED_AUDIO_TYPES, MAX_AUDIO_SIZE
from app.core.whisper_handler import whisper_handler
import shutil
from pathlib import Path
import os
import asyncio
from typing import Optional # 导入 Optional

router = APIRouter()

@router.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile,
    return_type: str = Form("json"),
    # scene 参数现在是可选的，如果未提供或为 "auto"，则后端自动判断
    scene: Optional[str] = Form(None) 
):
    """
    上传音频文件并进行转录，可自动判断场景或由用户指定场景。

    参数:
        - file: 音频文件 (必需)
        - return_type: 返回类型 (可选, 'json' 或 'text', 默认 'json')
        - scene: 应用场景 (可选)。
                 可为 "课堂", "会议", "备忘录", "通用"。
                 如果提供 "auto" 或不提供此参数，则系统会尝试自动检测场景。
                 如果自动检测失败或无明显特征，则默认为 "通用"。

    返回:
        - json格式：包含转录文本、识别到的关键字、语义连接词、检测到的场景、时间戳等信息。
        - text格式：只包含转录文本 (不含关键字、语义和场景信息)。
    """
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}. 支持的类型: {ALLOWED_AUDIO_TYPES}"
        )
    
    # 验证文件大小 - 改回使用 await file.read(chunk_size)
    try:
        file_size = 0
        chunk_size = 8192 # 8KB per chunk
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_AUDIO_SIZE:
                await file.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制: {MAX_AUDIO_SIZE/1024/1024:.2f}MB"
                )
        await file.seek(0) # 重置文件指针到开头，以便后续 shutil.copyfileobj 读取
    except HTTPException:
        raise
    except Exception as e:
        await file.close()
        raise HTTPException(status_code=400, detail=f"读取文件大小出错: {str(e)}")
    
    file_id = str(abs(hash(file.filename + str(os.urandom(4)))))
    audio_path = UPLOAD_DIR / f"{file_id}_audio{Path(file.filename).suffix}"
    
    try:
        # 保存上传的文件
        # 确保在 shutil.copyfileobj 之前，文件指针在开头
        await file.seek(0) 
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer) # file.file 是同步文件对象
        
        # 如果 scene 为 None (未提供) 或 "auto"，则传递 None 给 handler，让其自动判断
        scene_to_process = scene if scene and scene.lower() != "auto" else None
        result = whisper_handler.transcribe(audio_path, requested_scene=scene_to_process)
        
        audio_path.unlink(missing_ok=True)
        
        if return_type == "text":
            return {"text": result.get("text", "")}
        else:
            return {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "processing_time": result.get("processing_time", 0.0),
                "model_type": result.get("model_type", "unknown"),
                "device": result.get("device", "unknown"),
                "language": result.get("language", "unknown"),
                "detected_scene": result.get("detected_scene", "通用"),
                "found_keywords": result.get("found_keywords", []),
                "found_semantics": result.get("found_semantics", {})
            }
            
    except Exception as e:
        if audio_path.exists():
            audio_path.unlink(missing_ok=True)
        print(f"API Error during transcription: {e}") 
        raise HTTPException(
            status_code=500,
            detail=f"转录过程中出错: {str(e)}"
        )
    finally:
        await file.close() 