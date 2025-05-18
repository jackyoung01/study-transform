from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import transcribe
import os

app = FastAPI(
    title="Whisper Transcription API",
    description="基于Whisper的语音转录API服务",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加API路由
app.include_router(transcribe.router, prefix="/api/v1", tags=["transcribe"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Whisper Transcription API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 