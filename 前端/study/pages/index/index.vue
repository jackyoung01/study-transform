<template>
	<view class="container">
		<page-header title="基于whisper综合语音转录分析"></page-header>
		
		<view class="main-content">
			<view class="split-layout">
				<!-- 左侧：转录功能区域 -->
				<view class="left-panel">
					<!-- 文件上传区域 -->
					<file-uploader 
						:audio-file="audioFile" 
						:audio-file-name="audioFileName"
						@file-selected="handleFileSelected"
						@show-recording="showRecordingModal"
					></file-uploader>
					
					<!-- 语言选择 -->
					<language-selector 
						:selected-language="selectedLanguage"
						@language-change="handleLanguageChange"
					></language-selector>
					
					<!-- 预览音频播放器 -->
					<audio-preview 
						v-if="audioFile"
						:audio-src="audioFile"
						@toggle-play="handleTogglePlay"
						@seek="handleSeek"
					></audio-preview>
					
					<!-- 转录模式 -->
					<mode-selector 
						:selected-mode="selectedMode"
						@mode-selected="handleModeSelected"
					></mode-selector>
					
					<!-- 转录按钮 -->
					<button class="convert-button" type="primary" @click="handleTranscribe" :disabled="isTranscribing">
						{{ isTranscribing ? '转录中...' : '转录' }}
					</button>
				</view>
				
				<!-- 右侧：转录结果区域 -->
				<view class="right-panel">
					<!-- 原文区域 - 实时转录效果 -->
					<transcript-section 
						:is-transcribing="isTranscribing"
						:raw-transcript-text="rawTranscriptText"
						:final-text="finalText"
						:keywords="keywords"
						@transcription-displayed="handleTranscriptionDisplayed"
						@update-transcript="handleUpdateTranscript"
					></transcript-section>
					
					<!-- 导出面板 - 仅在有转录结果时显示 -->
					<export-panel 
						v-if="finalText"
						:transcript-text="finalText"
						:keywords="keywords"
						:file-name="audioFileName ? audioFileName.split('.')[0] + '_转录结果' : '转录结果'"
					></export-panel>
					
					<!-- 空白提示 -->
					<view v-if="!isTranscribing && !finalText" class="empty-state">
						<view class="empty-icon">🔊</view>
						<view class="empty-text">请上传音频并点击转录按钮</view>
						<view class="supported-formats">
							支持格式：MP3, MP4, M4A, MOV, AAC, WAV, OGG, OPUS, MPEG, WMA, WMV
						</view>
					</view>
				</view>
			</view>
		</view>
		
		<!-- 录音弹窗 -->
		<view class="modal-overlay" v-if="showRecordingPopup" @click.self="closeRecordingModal">
			<view class="record-popup">
				<view class="popup-header">
					<text class="popup-title">录制音频</text>
					<text class="close-icon" @click="closeRecordingModal">✕</text>
				</view>
				<view class="recording-content">
					<view class="recording-visual">
						<view class="mic-icon" :class="{ recording: isRecording }">🎤</view>
						<text class="recording-time">{{ formatTime(recordingTime) }}</text>
					</view>
					<view class="recording-status" v-if="!recordingFinished">
						<text>{{ isRecording ? '正在录音...' : '准备录音' }}</text>
					</view>
					<view class="recording-status" v-else>
						<text>录音已完成</text>
					</view>
				</view>
				<view class="recording-controls">
					<button class="record-control-btn" 
						:class="{ recording: isRecording }" 
						@click="handleRecordBtn">
						{{ isRecording ? '停止录音' : '开始录音' }}
					</button>
					<button class="confirm-btn" 
						:disabled="!recordingFinished" 
						:class="{ disabled: !recordingFinished }"
						@click="handleRecordingComplete">
						使用录音
					</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { transcribeAudio, checkRoot } from '@/utils/api'
import PageHeader from './components/PageHeader.vue'
import TranscriptSection from './components/TranscriptSection.vue'
import FileUploader from './components/FileUploader.vue'
import AudioPreview from './components/AudioPreview.vue'
import ModeSelector from './components/ModeSelector.vue'
import LanguageSelector from './components/LanguageSelector.vue'
import ExportPanel from './components/ExportPanel.vue'

export default {
	components: {
		PageHeader,
		TranscriptSection,
		FileUploader,
		AudioPreview,
		ModeSelector,
		LanguageSelector,
		ExportPanel
	},
	data() {
		return {
			// 文件上传相关
			audioFile: null,
			audioFileName: '',
			
			// 语言选择
			selectedLanguage: '简体中文',
			
			// 转录模式
			selectedMode: 0,
			
			// 转录结果相关
			isTranscribing: false,
			rawTranscriptText: '',
			finalText: '',
			keywords: [], // 存储检测到的关键词
			
			// 录音相关
			showRecordingPopup: false,
			isRecording: false,
			recordingTime: 0,
			recordingFinished: false,
			tempRecordingFile: null,
			timer: null,
			recorderManager: null,
			
			// H5录音相关
			mediaRecorder: null,
			audioChunks: [],
			stream: null,
			previousObjectUrl: null,
		}
	},
	onLoad() {
		// 检查API健康状态
		this.checkApiHealth();
		// 初始化录音管理器
		this.initRecorder();
	},
	methods: {
		async checkApiHealth() {
			try {
				const res = await checkRoot()
				if (res.statusCode !== 200) {
					uni.showToast({
						title: 'API服务不可用',
						icon: 'none'
					})
				}
			} catch (error) {
				uni.showToast({
					title: 'API服务连接失败',
					icon: 'none'
				})
			}
		},
		
		// 初始化录音管理器
		initRecorder() {
			// #ifdef APP-PLUS || MP
			this.initUniRecorder();
			// #endif
		},
		
		// 初始化 uni 录音管理器（APP 和小程序平台）
		initUniRecorder() {
			this.recorderManager = uni.getRecorderManager();
			this.recorderManager.onStart(() => {
				this.isRecording = true;
				this.startTimer();
				console.log('录音开始');
			});
			this.recorderManager.onStop((res) => {
				this.isRecording = false;
				this.stopTimer();
				this.tempRecordingFile = res.tempFilePath;
				this.recordingFinished = true;
				console.log('录音结束', res.tempFilePath);
			});
			this.recorderManager.onError((res) => {
				console.error('录音错误:', res);
				uni.showToast({
					title: '录音失败',
					icon: 'none'
				});
			});
		},
		
		// 初始化 Web 录音（H5平台）
		async initWebRecorder() {
			try {
				// 请求麦克风权限
				const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
				this.stream = stream;
				return true;
			} catch (err) {
				console.error('获取麦克风权限失败:', err);
				uni.showToast({
					title: '无法访问麦克风',
					icon: 'none'
				});
				return false;
			}
		},
		
		// 文件选择处理
		handleFileSelected(data) {
			this.audioFile = data.file;
			this.audioFileName = data.fileName;
		},
		
		// 录音弹窗相关
		async showRecordingModal() {
			this.cleanupRecordingResources();
			this.showRecordingPopup = true;
			
			// 初始化录音
			// #ifdef H5
			await this.initWebRecorder();
			// #endif
		},
		
		// 清理录音资源
		cleanupRecordingResources() {
			// #ifdef H5
			// 停止所有轨道
			if (this.stream) {
				this.stream.getTracks().forEach(track => track.stop());
				this.stream = null;
			}
			
			// 释放之前的对象URL
			if (this.previousObjectUrl) {
				URL.revokeObjectURL(this.previousObjectUrl);
				this.previousObjectUrl = null;
			}
			// #endif
			
			// 重置状态
			this.mediaRecorder = null;
			this.audioChunks = [];
			this.recordingTime = 0;
			this.isRecording = false;
			this.recordingFinished = false;
			this.tempRecordingFile = null;
			
			// 停止计时器
			this.stopTimer();
		},
		
		closeRecordingModal() {
			if (this.isRecording) {
				this.stopRecording();
			}
			this.showRecordingPopup = false;
			this.cleanupRecordingResources();
		},
		
		// 处理录音按钮点击
		handleRecordBtn() {
			if (!this.isRecording) {
				this.startRecording();
			} else {
				this.stopRecording();
			}
		},
		
		// 开始录音
		async startRecording() {
			this.recordingTime = 0;
			this.startTimer();
			this.recordingFinished = false;
			this.audioChunks = [];
			
			// #ifdef APP-PLUS || MP
			if (this.recorderManager) {
				this.recorderManager.start({
					duration: 600000, // 最长录音时间，单位ms
					sampleRate: 44100,
					numberOfChannels: 1,
					encodeBitRate: 192000,
					format: 'mp3'
				});
			}
			// #endif
			
			// #ifdef H5
			if (this.stream) {
				try {
					this.mediaRecorder = new MediaRecorder(this.stream);
					this.mediaRecorder.ondataavailable = (event) => {
						if (event.data.size > 0) {
							this.audioChunks.push(event.data);
						}
					};
					this.mediaRecorder.onstart = () => {
						this.isRecording = true;
						console.log('Web录音开始');
					};
					this.mediaRecorder.onstop = () => {
						this.isRecording = false;
						this.stopTimer();
						this.recordingFinished = true;
						
						// 创建音频文件
						const audioBlob = new Blob(this.audioChunks, { type: 'audio/mp3' });
						// 释放之前的URL
						if (this.previousObjectUrl) {
							URL.revokeObjectURL(this.previousObjectUrl);
						}
						// 创建新的URL
						this.tempRecordingFile = URL.createObjectURL(audioBlob);
						this.previousObjectUrl = this.tempRecordingFile;
						console.log('Web录音结束', this.tempRecordingFile);
					};
					this.mediaRecorder.start();
				} catch (err) {
					console.error('初始化录音失败:', err);
					uni.showToast({
						title: '录音初始化失败',
						icon: 'none'
					});
				}
			} else {
				// 如果没有stream，尝试重新初始化
				const initialized = await this.initWebRecorder();
				if (initialized) {
					this.startRecording();
				} else {
					uni.showToast({
						title: '录音初始化失败',
						icon: 'none'
					});
				}
			}
			// #endif
		},
		
		// 停止录音
		stopRecording() {
			// #ifdef APP-PLUS || MP
			if (this.recorderManager) {
				this.recorderManager.stop();
			}
			// #endif
			
			// #ifdef H5
			if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
				try {
					this.mediaRecorder.stop();
				} catch (err) {
					console.error('停止录音失败:', err);
				}
			}
			// #endif
		},
		
		// 开始计时器
		startTimer() {
			if (this.timer) {
				clearInterval(this.timer);
			}
			this.recordingTime = 0;
			this.timer = setInterval(() => {
				this.recordingTime++;
			}, 1000);
		},
		
		// 停止计时器
		stopTimer() {
			if (this.timer) {
				clearInterval(this.timer);
				this.timer = null;
			}
		},
		
		// 处理录音完成
		handleRecordingComplete() {
			if (!this.tempRecordingFile) {
				uni.showToast({
					title: '没有录音文件',
					icon: 'none'
				});
				return;
			}
			
			this.audioFile = this.tempRecordingFile;
			this.audioFileName = `录音_${new Date().toLocaleString()}.mp3`;
			
			// 关闭弹窗
			this.showRecordingPopup = false;
			
			uni.showToast({
				title: '录音已设置',
				icon: 'success'
			});
		},
		
		// 语言选择处理
		handleLanguageChange(language) {
			this.selectedLanguage = language;
			console.log('语言已切换为:', language);
		},
		
		// 转录模式选择处理
		handleModeSelected(index) {
			this.selectedMode = index;
			console.log('模式已切换为:', index);
		},
		
		// 处理转录
		async handleTranscribe() {
			if (!this.audioFile) {
				uni.showToast({
					title: '请先选择文件',
					icon: 'none'
				})
				return
			}
			
			// 开始转录，显示实时转录效果
			this.isTranscribing = true;
			this.rawTranscriptText = '';
			this.finalText = ''; // 清除之前的转录结果
			this.keywords = []; // 清除之前的关键词
			
			uni.showLoading({
				title: '转录中...'
			})
			
			try {
				const scene = this.selectedMode;
				// 设置固定的中文语言参数
				const lang = 'zh'; // 使用中文语言代码
				const res = await transcribeAudio(this.audioFile, scene, 'json', lang)
				if (res.statusCode === 200) {
					console.log('API返回原始数据:', res.data);
					let result;
					
					// 处理返回的数据，确保是JSON对象
					if (typeof res.data === 'string') {
						try {
							result = JSON.parse(res.data);
						} catch (e) {
							console.error('解析JSON失败:', e);
							result = { text: res.data };
						}
					} else {
						result = res.data;
					}
					
					// 处理转录结果
					this.processTranscriptResult(result);
				} else {
					throw new Error('转录失败')
				}
			} catch (error) {
				// 转录失败
				console.error('转录请求失败:', error);
				uni.showToast({
					title: '转录失败，请重试',
					icon: 'none'
				});
				this.isTranscribing = false;
			} finally {
				uni.hideLoading()
			}
		},
		
		// 处理转录结果
		processTranscriptResult(result) {
			console.log('处理转录结果:', result);
			
			// 保存转录文本
			if (result && result.text) {
				// 一次性提供完整文本给TranscriptSection组件
				// 该组件会自动将文本分成3行并逐行显示
				this.rawTranscriptText = result.text;
				
				// 转录完成后延迟结束转录状态
				// 这个延迟需要足够长，让TranscriptSection组件有时间显示所有3行
				// TranscriptSection组件会在完成显示后触发'transcription-displayed'事件
				// 我们在该事件的处理函数中会关闭转录状态
				
				// 初始化关键词数组
				this.keywords = [];
				
				// 从found_keywords中提取关键词
				if (result && result.found_keywords && Array.isArray(result.found_keywords)) {
					this.keywords = [...result.found_keywords];
					console.log('从found_keywords提取的关键词:', this.keywords);
				}
				
				// 从found_semantics中提取词语
				if (result && result.found_semantics && typeof result.found_semantics === 'object') {
					// 遍历所有语义类别
					for (const category in result.found_semantics) {
						const words = result.found_semantics[category];
						if (Array.isArray(words)) {
							// 将所有语义词添加到关键词数组中
							words.forEach(word => {
								if (word && !this.keywords.includes(word)) {
									this.keywords.push(word);
								}
							});
						}
					}
					console.log('添加语义词后的关键词:', this.keywords);
				}
			} else {
				console.error('未找到转录文本');
				uni.showToast({
					title: '未获取到转录结果',
					icon: 'none'
				});
				this.isTranscribing = false;
				return;
			}
		},
		
		// 转录显示完成
		handleTranscriptionDisplayed() {
			console.log('所有转录行已显示完毕');
			
			// 等待一小段时间后结束转录状态
			setTimeout(() => {
				// 转录动画显示完毕
				this.isTranscribing = false;
				
				// 设置最终的转录文本
				this.finalText = this.rawTranscriptText;
				
				// 显示转录完成提示
				uni.showToast({
					title: '转录完成',
					icon: 'success'
				});
			}, 1000);
		},
		
		// 音频播放相关方法
		handleTogglePlay(isPlaying) {
			console.log('播放状态:', isPlaying)
		},
		
		handleSeek(position) {
			console.log('seek位置:', position)
		},
		
		// 处理转录文本更新
		handleUpdateTranscript(updatedText) {
			console.log('接收到更新的转录文本:', updatedText);
			
			// 更新最终文本
			this.finalText = updatedText;
			
			// 重新识别关键词，或者保留原有关键词
			// 如果有需要，可以重新调用API进行关键词识别
			
			// 保存编辑后的文本（这里可以添加保存到服务器的逻辑）
			uni.showToast({
				title: '文本已更新',
				icon: 'success'
			});
		},
		
		// 格式化时间
		formatTime(seconds) {
			const minutes = Math.floor(seconds / 60);
			const remainingSeconds = Math.floor(seconds % 60);
			return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
		}
	}
}
</script>

<style lang="scss">
.container {
	padding: 0;
	background-color: #f5f7fa;
	min-height: 100vh;
}

.main-content {
	padding: 20px;
}

/* 左右分栏布局 */
.split-layout {
	display: flex;
	gap: 20px;
	min-height: calc(100vh - 110px); /* 减去header和padding的高度 */
}

/* 左侧面板 */
.left-panel {
	flex: 1;
	max-width: 48%;
}

/* 右侧面板 */
.right-panel {
	flex: 1;
	max-width: 48%;
	background-color: #fff;
	border-radius: 8px;
	padding: 20px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.convert-button {
	width: 100%;
	padding: 15px;
	font-size: 16px;
	background-color: #007AFF;
	color: #fff;
	cursor: pointer;
	transition: all 0.2s ease;
	
	&:hover {
		background-color: #40a9ff;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
	}
	
	&:active {
		transform: translateY(0);
	}
	
	&:disabled {
		background-color: #cccccc;
		cursor: not-allowed;
		transform: none;
		box-shadow: none;
	}
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60px 20px;
	text-align: center;
	
	.empty-icon {
		font-size: 48px;
		color: #ccc;
		margin-bottom: 15px;
	}
	
	.empty-text {
		font-size: 16px;
		color: #999;
		margin-bottom: 10px;
	}
	
	.supported-formats {
		font-size: 12px;
		color: #aaa;
		max-width: 300px;
		line-height: 1.5;
	}
}

.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 1000;
}

.record-popup {
	background-color: #fff;
	padding: 20px;
	border-radius: 8px;
	max-width: 80%;
	width: 400px;
}

.popup-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.popup-title {
	font-size: 18px;
	font-weight: bold;
}

.close-icon {
	font-size: 24px;
	cursor: pointer;
}

.recording-content {
	text-align: center;
	margin-bottom: 20px;
}

.recording-visual {
	margin-bottom: 10px;
}

.mic-icon {
	font-size: 48px;
	color: #ccc;
	transition: color 0.2s ease;
	
	&.recording {
		color: #007AFF;
	}
}

.recording-time {
	font-size: 14px;
	color: #999;
}

.recording-status {
	font-size: 14px;
	color: #333;
}

.recording-controls {
	display: flex;
	justify-content: center;
	gap: 10px;
}

.record-control-btn {
	padding: 12px 20px;
	font-size: 16px;
	background-color: #007AFF;
	color: #fff;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.2s ease;
	
	&.recording {
		background-color: #40a9ff;
	}
	
	&:hover {
		background-color: #40a9ff;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
	}
	
	&:active {
		transform: translateY(0);
	}
}

.confirm-btn {
	padding: 12px 20px;
	font-size: 16px;
	background-color: #007AFF;
	color: #fff;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.2s ease;
	
	&.disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}
	
	&:hover {
		background-color: #40a9ff;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
	}
	
	&:active {
		transform: translateY(0);
	}
}
</style>
