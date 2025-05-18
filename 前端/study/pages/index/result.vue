<template>
	<view class="container">
		<view class="header">
			<text class="back-icon" @click="goBack">←</text>
			<text class="title">转录结果</text>
		</view>
		
		<view class="main-content">
			<!-- 音频播放器 -->
			<view class="audio-player">
				<view class="audio-info">
					<text class="file-name">{{ audioFileName }}</text>
					<text class="duration">{{ duration }}</text>
				</view>
				<view class="player-controls">
					<slider class="progress-bar" :value="progress" @change="onProgressChange" />
					<view class="controls">
						<text class="control-btn" @click="togglePlay">{{ isPlaying ? '⏸' : '▶' }}</text>
						<text class="time">{{ currentTime }} / {{ duration }}</text>
					</view>
				</view>
			</view>
			
			<!-- 转录文本 -->
			<view class="transcript-container">
				<view class="transcript-header">
					<text class="section-title">转录文本</text>
					<view class="actions">
						<button class="action-btn" @click="copyText">复制</button>
					</view>
				</view>
				<scroll-view class="transcript-content" scroll-y>
					<rich-text :nodes="formattedText"></rich-text>
				</scroll-view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			audioFileName: '未命名音频.mp3',
			audioFile: '',
			duration: '00:00',
			currentTime: '00:00',
			progress: 0,
			isPlaying: false,
			transcriptText: '',
			transcriptInfo: null,
			formattedText: '',
			audioElement: null
		}
	},
	onLoad(options) {
		// 获取转录结果和音频文件信息
		if (options.transcriptResult) {
			this.transcriptInfo = JSON.parse(decodeURIComponent(options.transcriptResult))
		}
		if (options.audioFile) {
			this.audioFile = decodeURIComponent(options.audioFile)
		}
		if (options.audioFileName) {
			this.audioFileName = decodeURIComponent(options.audioFileName)
		}
		
		// 初始化音频播放器
		this.initAudioPlayer()
		// 处理转录结果
		this.processTranscriptResult()
	},
	methods: {
		initAudioPlayer() {
			// 创建音频元素
			this.audioElement = uni.createInnerAudioContext()
			
			// 设置音频源
			if (this.audioFile) {
				this.audioElement.src = this.audioFile
			}
			
			// 监听音频加载完成事件
			this.audioElement.onCanplay(() => {
				// 更新总时长
				this.duration = this.formatTime(this.audioElement.duration)
			})
			
			// 监听播放进度更新
			this.audioElement.onTimeUpdate(() => {
				// 更新当前时间
				this.currentTime = this.formatTime(this.audioElement.currentTime)
				// 更新进度条
				if (this.audioElement.duration > 0) {
					this.progress = (this.audioElement.currentTime / this.audioElement.duration) * 100
				}
			})
			
			// 监听播放结束
			this.audioElement.onEnded(() => {
				this.isPlaying = false
				this.progress = 0
				this.currentTime = '00:00'
			})
			
			// 监听错误
			this.audioElement.onError((res) => {
				console.error('音频播放错误:', res)
				uni.showToast({
					title: '音频播放失败',
					icon: 'none'
				})
			})
		},
		
		processTranscriptResult() {
			if (!this.transcriptInfo) return
			
			console.log('转录结果:', this.transcriptInfo)
			
			// 设置转录文本
			if (typeof this.transcriptInfo === 'string') {
				this.transcriptText = this.transcriptInfo
				this.formattedText = this.transcriptInfo
			} else {
				this.transcriptText = this.transcriptInfo.text || ''
				this.formatTextWithKeywords()
			}
		},
		
		formatTextWithKeywords() {
			if (!this.transcriptInfo || typeof this.transcriptInfo === 'string') {
				this.formattedText = this.transcriptText
				return
			}
			
			let text = this.transcriptText
			console.log('原始文本:', text)
			
			// 收集所有关键词
			let keywords = []
			
			// 处理found_keywords数组
			if (Array.isArray(this.transcriptInfo.found_keywords)) {
				keywords.push(...this.transcriptInfo.found_keywords)
			}
			
			// 处理found_semantics对象中的关键词
			if (this.transcriptInfo.found_semantics) {
				Object.values(this.transcriptInfo.found_semantics).forEach(words => {
					if (Array.isArray(words)) {
						keywords.push(...words)
					}
				})
			}
			
			console.log('识别到的关键词:', keywords)
			
			if (keywords.length === 0) {
				this.formattedText = text
				return
			}
			
			// 过滤并排序关键词
			keywords = keywords
				.filter(keyword => typeof keyword === 'string' && keyword.trim() !== '')
				.sort((a, b) => b.length - a.length)
			
			console.log('处理后的关键词:', keywords)
			
			// 替换关键词为加粗标签
			keywords.forEach(keyword => {
				try {
					// 转义正则表达式特殊字符
					const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
					const regex = new RegExp(escapedKeyword, 'g')
					text = text.replace(regex, `<b style="color: #007AFF; font-weight: bold;">${keyword}</b>`)
				} catch (error) {
					console.error('关键词处理错误:', error)
				}
			})
			
			console.log('格式化后的文本:', text)
			this.formattedText = text
		},
		
		goBack() {
			uni.navigateBack()
		},
		
		togglePlay() {
			if (!this.audioElement || !this.audioFile) {
				uni.showToast({
					title: '无法播放音频',
					icon: 'none'
				})
				return
			}
			
			if (this.isPlaying) {
				this.audioElement.pause()
			} else {
				this.audioElement.play()
			}
			this.isPlaying = !this.isPlaying
		},
		
		onProgressChange(e) {
			if (!this.audioElement || !this.audioFile) return
			
			const value = e.detail.value
			const targetTime = (value / 100) * this.audioElement.duration
			this.audioElement.seek(targetTime)
		},
		
		formatTime(seconds) {
			if (!seconds || isNaN(seconds)) return '00:00'
			const minutes = Math.floor(seconds / 60)
			const remainingSeconds = Math.floor(seconds % 60)
			return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
		},
		
		copyText() {
			uni.setClipboardData({
				data: this.transcriptText,
				success: () => {
					uni.showToast({
						title: '已复制到剪贴板',
						icon: 'success'
					})
				}
			})
		},
		
		// 组件销毁时清理资源
		onUnload() {
			if (this.audioElement) {
				this.audioElement.destroy()
			}
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
	display: flex;
	align-items: center;
	margin-bottom: 30px;
	
	.back-icon {
		font-size: 24px;
		margin-right: 15px;
		cursor: pointer;
	}
	
	.title {
		font-size: 20px;
		font-weight: 500;
	}
}

.main-content {
	background-color: #fff;
	border-radius: 8px;
	padding: 20px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.audio-player {
	margin-bottom: 30px;
	
	.audio-info {
		margin-bottom: 15px;
		
		.file-name {
			font-size: 16px;
			font-weight: 500;
			margin-right: 10px;
		}
		
		.duration {
			color: #666;
			font-size: 14px;
		}
	}
	
	.player-controls {
		.progress-bar {
			margin-bottom: 10px;
		}
		
		.controls {
			display: flex;
			align-items: center;
			
			.control-btn {
				font-size: 24px;
				margin-right: 15px;
				cursor: pointer;
				width: 40px;
				height: 40px;
				display: flex;
				align-items: center;
				justify-content: center;
				border-radius: 50%;
				background-color: #f0f0f0;
				transition: all 0.3s ease;
				
				&:active {
					background-color: #e0e0e0;
				}
			}
			
			.time {
				font-size: 14px;
				color: #666;
			}
		}
	}
}

.transcript-container {
	.transcript-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
		
		.section-title {
			font-size: 18px;
			font-weight: 500;
		}
		
		.actions {
			display: flex;
			gap: 10px;
			
			.action-btn {
				font-size: 14px;
				padding: 5px 15px;
				background-color: #f0f0f0;
				border: none;
				border-radius: 4px;
				
				&::after {
					border: none;
				}
			}
		}
	}
	
	.transcript-content {
		height: 400px;
		border: 1px solid #eee;
		border-radius: 4px;
		padding: 15px;
		
		.transcript-text {
			font-size: 16px;
			line-height: 1.6;
			color: #333;
		}
	}
}
</style> 