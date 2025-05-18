<template>
	<view class="container">
		<view class="header">
			<text class="cloud-icon">☁</text>
			<text class="title">转录文件</text>
		</view>
		
		<view class="main-content">
			<!-- 文件类型区域 -->
			<view class="file-type">
				<text class="section-title">音频 / 视频文件</text>
				<view class="controls">
					<button class="icon-btn" @click="showRecordingModal">
						<text class="iconfont">🎤</text>
					</button>
					<button class="icon-btn"><text class="iconfont">🔗</text></button>
				</view>
			</view>
			
			<!-- 上传区域 -->
			<view class="upload-area">
				<view class="upload-box" v-if="!audioFile">
					<view class="file-formats">
						<text class="drag-text">拖放</text>
						<text class="format-text">MP3、MP4、M4A、MOV、AAC、</text>
						<text class="format-text">WAV、OGG、OPUS、MPEG、WMA、</text>
						<text class="format-text">WMV</text>
					</view>
					<view class="divider">
						<text>— 或 —</text>
					</view>
					<button class="browse-button" @click="chooseFile">浏览文件</button>
				</view>
				<view class="selected-file" v-else>
					<text class="file-icon">📄</text>
					<text class="file-name">{{ audioFileName }}</text>
					<button class="change-file-btn" @click="chooseFile">更换文件</button>
				</view>
			</view>

			<!-- 语言选择 -->
			<view class="language-section">
				<text class="section-title">音频语言</text>
				<view class="language-selector">
					<picker mode="selector" :range="['简体中文 CN']" :value="0">
						<view class="uni-input">简体中文 CN</view>
					</picker>
				</view>
			</view>

			<!-- 转录模式 -->
			<view class="mode-section">
				<text class="section-title">应用场景</text>
				<view class="mode-options">
					<view 
						v-for="(mode, index) in modes" 
						:key="index"
						class="mode-card"
						:class="{ selected: selectedMode === index }"
						@click="selectedMode = index"
					>
						<text class="mode-icon">{{ mode.icon }}</text>
						<text class="mode-name">{{ mode.name }}</text>
						<text class="mode-desc">{{ mode.desc }}</text>
					</view>
				</view>
			</view>

			<!-- 说话人识别设置 -->
			<button class="speaker-button">
				<text class="speaker-icon">👤</text>
				<text>说话人识别及更多设置</text>
				<text class="arrow-down">▼</text>
			</button>

			<!-- 转录按钮 -->
			<button class="convert-button" type="primary" @click="handleTranscribe">转录</button>
		</view>
		
		<!-- 录音弹窗 -->
		<view class="recording-modal" v-if="showModal">
			<view class="modal-content">
				<view class="modal-header">
					<text class="modal-title">录音</text>
					<button class="close-btn" @click="closeModal">×</button>
				</view>
				<view class="modal-body">
					<view class="recording-status">
						<text class="recording-icon" :class="{ 'recording': isRecording }">🎤</text>
						<text class="recording-time">{{ formatTime(recordingTime) }}</text>
					</view>
					<view class="recording-controls">
						<button 
							class="record-btn" 
							:class="{ 'recording': isRecording }" 
							@click="handleRecordBtn"
							v-if="!recordingFinished"
						>
							{{ isRecording ? '结束录制' : '开始录制' }}
						</button>
						<button 
							class="complete-btn" 
							@click="handleComplete"
							v-if="recordingFinished"
						>
							完成
						</button>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { transcribeAudio, checkRoot } from '@/utils/api'

export default {
	data() {
		return {
			title: 'Hello',
			selectedMode: 0,
			modes: [
				{ icon: '🎓', name: '课堂', desc: '课堂授课场景' },
				{ icon: '👥', name: '会议', desc: '商务会议场景' },
				{ icon: '📝', name: '备忘录', desc: '个人备忘场景' },
				{ icon: '🌐', name: '通用', desc: '通用场景' }
			],
			audioFile: null,
			audioFileName: '',
			isRecording: false,
			recorderManager: null,
			recordingTime: 0,
			timer: null,
			showModal: false,
			recordingFinished: false,
			tempRecordingFile: null,
			mediaRecorder: null,
			audioChunks: [],
			stream: null,
			previousObjectUrl: null
		}
	},
	onLoad() {
		// 检查API健康状态
		this.checkApiHealth()
		
		// 根据平台初始化不同的录音管理器
		// #ifdef APP-PLUS || MP
		this.initUniRecorder()
		// #endif
		
		// #ifdef H5
		this.initWebRecorder()
		// #endif
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
		
		// 选择文件
		chooseFile() {
			uni.chooseFile({
				count: 1,
				type: 'all',
				extension: ['.mp3', '.mp4', '.m4a', '.mov', '.aac', '.wav', '.ogg', '.opus', '.mpeg', '.wma', '.wmv'],
				success: (res) => {
					this.audioFile = res.tempFilePaths[0]
					this.audioFileName = res.tempFiles[0].name
					uni.showToast({
						title: '文件已选择',
						icon: 'success'
					})
				}
			})
		},
		
		// 清理资源的方法
		cleanupResources() {
			// 停止所有轨道
			if (this.stream) {
				this.stream.getTracks().forEach(track => track.stop())
				this.stream = null
			}
			
			// 释放之前的对象URL
			if (this.previousObjectUrl) {
				URL.revokeObjectURL(this.previousObjectUrl)
				this.previousObjectUrl = null
			}
			
			// 重置状态
			this.mediaRecorder = null
			this.audioChunks = []
			this.recordingTime = 0
			this.isRecording = false
			this.recordingFinished = false
		},
		
		// 修改：显示录音弹窗方法
		async showRecordingModal() {
			// 清理之前的资源
			this.cleanupResources()
			
			// 重新初始化录音
			await this.initWebRecorder()
			this.showModal = true
		},
		
		// 修改：关闭弹窗方法
		closeModal() {
			if (this.isRecording) {
				this.stopRecording()
			}
			this.showModal = false
			this.cleanupResources()
		},
		
		// 录音弹窗按钮逻辑
		handleRecordBtn() {
			if (!this.isRecording) {
				this.startRecording()
			} else {
				this.stopRecording()
			}
		},
		
		// 初始化 uni 录音管理器（APP 和小程序平台）
		initUniRecorder() {
			this.recorderManager = uni.getRecorderManager()
			this.recorderManager.onStart(() => {
				this.isRecording = true
				console.log('录音开始')
			})
			this.recorderManager.onStop((res) => {
				this.isRecording = false
				this.stopTimer()
				this.tempRecordingFile = res.tempFilePath
				this.recordingFinished = true
				console.log('录音结束', res.tempFilePath)
			})
			this.recorderManager.onError((res) => {
				console.error('录音错误:', res)
				uni.showToast({
					title: '录音失败',
					icon: 'none'
				})
			})
		},
		
		// 初始化 Web 录音（H5平台）
		async initWebRecorder() {
			try {
				// 请求麦克风权限
				const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
				this.stream = stream
			} catch (err) {
				console.error('获取麦克风权限失败:', err)
				uni.showToast({
					title: '无法访问麦克风',
					icon: 'none'
				})
			}
		},
		
		// 修改：开始录音方法
		async startRecording() {
			this.recordingTime = 0
			this.startTimer()
			this.recordingFinished = false
			this.audioChunks = []
			
			// #ifdef APP-PLUS || MP
			if (this.recorderManager) {
				this.recorderManager.start({
					duration: 600000,
					sampleRate: 44100,
					numberOfChannels: 1,
					encodeBitRate: 192000,
					format: 'mp3'
				})
			}
			// #endif
			
			// #ifdef H5
			if (this.stream) {
				this.mediaRecorder = new MediaRecorder(this.stream)
				this.mediaRecorder.ondataavailable = (event) => {
					if (event.data.size > 0) {
						this.audioChunks.push(event.data)
					}
				}
				this.mediaRecorder.onstart = () => {
					this.isRecording = true
					console.log('Web录音开始')
				}
				this.mediaRecorder.onstop = () => {
					this.isRecording = false
					this.stopTimer()
					this.recordingFinished = true
					
					// 创建音频文件
					const audioBlob = new Blob(this.audioChunks, { type: 'audio/mp3' })
					// 释放之前的URL
					if (this.previousObjectUrl) {
						URL.revokeObjectURL(this.previousObjectUrl)
					}
					// 创建新的URL
					this.tempRecordingFile = URL.createObjectURL(audioBlob)
					this.previousObjectUrl = this.tempRecordingFile
					console.log('Web录音结束', this.tempRecordingFile)
				}
				this.mediaRecorder.start()
			} else {
				uni.showToast({
					title: '录音初始化失败',
					icon: 'none'
				})
			}
			// #endif
		},
		
		// 停止录音
		stopRecording() {
			// #ifdef APP-PLUS || MP
			if (this.recorderManager) {
				this.recorderManager.stop()
			}
			// #endif
			
			// #ifdef H5
			if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
				this.mediaRecorder.stop()
			}
			// #endif
		},
		
		// 开始计时器
		startTimer() {
			if (this.timer) {
				clearInterval(this.timer)
			}
			this.recordingTime = 0
			this.timer = setInterval(() => {
				this.recordingTime++
			}, 1000)
		},
		
		// 停止计时器
		stopTimer() {
			if (this.timer) {
				clearInterval(this.timer)
				this.timer = null
			}
		},
		
		// 修改：处理完成按钮点击
		handleComplete() {
			if (this.tempRecordingFile) {
				this.audioFile = this.tempRecordingFile
				this.audioFileName = `录音_${new Date().toLocaleString()}.mp3`
				
				this.showModal = false
				this.recordingFinished = false
				
				// 注意：这里不清理tempRecordingFile，因为它现在被用作audioFile
				
				uni.showToast({
					title: '录音已设置',
					icon: 'success'
				})
			}
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
			
			uni.showLoading({
				title: '转录中...'
			})
			
			try {
				const scene = this.modes[this.selectedMode].name
				const res = await transcribeAudio(this.audioFile, scene, 'json')
				if (res.statusCode === 200) {
					const result = JSON.parse(res.data)
					// 跳转到结果页面，传递转录结果和音频文件信息
					uni.navigateTo({
						url: `/pages/index/result?transcriptResult=${encodeURIComponent(JSON.stringify(result))}&audioFile=${encodeURIComponent(this.audioFile)}&audioFileName=${encodeURIComponent(this.audioFileName)}`
					})
				} else {
					throw new Error('转录失败')
				}
			} catch (error) {
				uni.showToast({
					title: '转录失败，请重试',
					icon: 'none'
				})
			} finally {
				uni.hideLoading()
			}
		},
		
		// 格式化时间
		formatTime(seconds) {
			const minutes = Math.floor(seconds / 60)
			const remainingSeconds = seconds % 60
			return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
		}
	}
}
</script>

<style lang="scss">
	.container {
		padding: 20px;
		background-color: #f5f5f5;
		min-height: 100vh;
	}

	.header {
		text-align: center;
		margin-bottom: 30px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		
		.cloud-icon {
			font-size: 28px;
		}
		
		.title {
			font-size: 24px;
			color: #333;
		}
	}

	.main-content {
		background-color: #fff;
		border-radius: 8px;
		padding: 20px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.file-type {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.section-title {
		font-size: 18px;
		color: #333;
		font-weight: 500;
	}

	.controls {
		display: flex;
		align-items: center;
		gap: 10px;
		
		.icon-btn {
			background: none;
			border: none;
			font-size: 20px;
			padding: 5px;
			line-height: 1;
			transition: all 0.3s ease;
			
			&.recording {
				animation: pulse 1.5s infinite;
			}
			
			&::after {
				border: none;
			}
		}
		
		.recording-time {
			color: #ff4d4f;
			font-size: 14px;
			font-weight: 500;
		}
	}

	@keyframes pulse {
		0% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.1);
		}
		100% {
			transform: scale(1);
		}
	}

	.upload-area {
		margin-bottom: 30px;
	}

	.upload-box {
		border: 2px dashed #ddd;
		border-radius: 8px;
		padding: 30px;
		text-align: center;
		background-color: #f8f8f8;
	}

	.file-formats {
		margin-bottom: 20px;
		
		.drag-text {
			font-size: 16px;
			color: #333;
			margin-bottom: 10px;
			display: block;
		}
		
		.format-text {
			color: #666;
			font-size: 14px;
			display: block;
			line-height: 1.8;
		}
	}

	.divider {
		color: #999;
		margin: 20px 0;
		font-size: 14px;
	}

	.browse-button {
		background-color: #eee;
		border: none;
		padding: 10px 20px;
		border-radius: 4px;
		color: #333;
		font-size: 14px;
		
		&::after {
			border: none;
		}
	}

	.language-section {
		margin-bottom: 30px;
		
		.language-selector {
			margin-top: 10px;
			
			.uni-input {
				width: 100%;
				padding: 10px;
				border: 1px solid #ddd;
				border-radius: 4px;
				background-color: white;
			}
		}
	}

	.mode-section {
		margin-bottom: 30px;
	}

	.mode-options {
		display: flex;
		gap: 20px;
		margin-top: 10px;
	}

	.mode-card {
		flex: 1;
		padding: 15px;
		border: 1px solid #ddd;
		border-radius: 8px;
		text-align: center;
		
		&.selected {
			border-color: #007AFF;
			background-color: #F0F7FF;
		}
		
		.mode-icon {
			font-size: 24px;
			margin-bottom: 5px;
			display: block;
		}
		
		.mode-name {
			font-weight: bold;
			margin-bottom: 5px;
			display: block;
		}
		
		.mode-desc {
			font-size: 12px;
			color: #666;
			display: block;
		}
	}

	.speaker-button {
		width: 100%;
		padding: 10px;
		background: none;
		border: 1px solid #ddd;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		margin-bottom: 20px;
		
		&::after {
			border: none;
		}
		
		.speaker-icon {
			font-size: 16px;
		}
		
		.arrow-down {
			font-size: 12px;
			color: #666;
		}
	}

	.convert-button {
		width: 100%;
		padding: 15px;
		font-size: 16px;
		background-color: #007AFF;
		
		&::after {
			border: none;
		}
	}

	.selected-file {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 20px;
		background-color: #f8f8f8;
		border-radius: 8px;
		border: 1px solid #ddd;
		
		.file-icon {
			font-size: 24px;
			margin-right: 10px;
		}
		
		.file-name {
			flex: 1;
			font-size: 14px;
			color: #333;
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
		}
		
		.change-file-btn {
			margin-left: 10px;
			padding: 5px 10px;
			background-color: #eee;
			border: none;
			border-radius: 4px;
			font-size: 12px;
			color: #333;
			
			&::after {
				border: none;
			}
		}
	}

	.recording-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 999;
		
		.modal-content {
			width: 80%;
			max-width: 400px;
			background-color: #fff;
			border-radius: 12px;
			overflow: hidden;
			
			.modal-header {
				display: flex;
				align-items: center;
				border-bottom: 1px solid #eee;
				padding: 15px;
				position: relative;
				
				.modal-title {
					flex: 1;
					text-align: center;
					font-size: 18px;
					font-weight: 500;
					color: #333;
				}
				
				.close-btn {
					position: absolute;
					right: 15px;
					top: 50%;
					transform: translateY(-50%);
					font-size: 24px;
					background: none;
					border: none;
					padding: 0;
					line-height: 1;
				}
			}
			
			.modal-body {
				padding: 30px;
				text-align: center;
				
				.recording-status {
					margin-bottom: 30px;
					
					.recording-icon {
						font-size: 48px;
						display: block;
						margin-bottom: 10px;
						
						&.recording {
							animation: pulse 1.5s infinite;
						}
					}
					
					.recording-time {
						font-size: 24px;
						color: #ff4d4f;
						font-weight: 500;
					}
				}
				
				.recording-controls {
					.record-btn, .complete-btn {
						width: 100%;
						padding: 15px;
						font-size: 16px;
						border: none;
						border-radius: 8px;
						transition: all 0.3s ease;
						
						&::after {
							border: none;
						}
					}
					
					.record-btn {
						background-color: #007AFF;
						color: #fff;
						
						&.recording {
							background-color: #ff4d4f;
						}
					}
					
					.complete-btn {
						background-color: #67C23A;
						color: #fff;
						
						&:active {
							background-color: #529b2e;
						}
					}
				}
			}
		}
	}
</style>
