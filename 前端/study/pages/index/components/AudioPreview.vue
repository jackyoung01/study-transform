<template>
	<view class="preview-player-section" v-if="audioSrc">
		<text class="section-title">音频预览</text>
		<view class="preview-player">
			<view class="mini-player-controls">
				<view class="play-button" @click="togglePlay">
					<text class="play-icon">{{ isPlaying ? '⏸' : '▶' }}</text>
				</view>
				<view class="progress-container">
					<view class="progress-bar" @tap="handleProgressTap">
						<view class="progress-inner" :style="{ width: progress + '%' }"></view>
					</view>
					<view class="time-display">
						<text class="current-time">{{ currentTime }}</text>
						<text class="total-time">{{ duration }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'AudioPreview',
	props: {
		audioSrc: {
			type: String,
			default: ''
		}
	},
	data() {
		return {
			isPlaying: false,
			currentTime: '00:00',
			duration: '00:00',
			progress: 0,
			audioElement: null
		}
	},
	watch: {
		audioSrc: {
			handler(newValue) {
				if (newValue) {
					this.initAudioPlayer();
				}
			},
			immediate: true
		}
	},
	methods: {
		initAudioPlayer() {
			// 销毁已有的播放器
			if (this.audioElement) {
				this.audioElement.destroy();
			}
			
			// 创建音频元素
			this.audioElement = uni.createInnerAudioContext();
			
			// 设置新的音频源
			this.audioElement.src = this.audioSrc;
			
			// 监听音频加载完成事件
			this.audioElement.onCanplay(() => {
				// 更新总时长
				this.duration = this.formatTime(this.audioElement.duration);
			});
			
			// 监听播放进度更新
			this.audioElement.onTimeUpdate(() => {
				// 更新当前时间
				this.currentTime = this.formatTime(this.audioElement.currentTime);
				// 更新进度条
				if (this.audioElement.duration > 0) {
					this.progress = (this.audioElement.currentTime / this.audioElement.duration) * 100;
				}
			});
			
			// 监听播放结束
			this.audioElement.onEnded(() => {
				this.isPlaying = false;
				this.progress = 0;
				this.currentTime = '00:00';
			});
			
			// 监听错误
			this.audioElement.onError((res) => {
				console.error('音频播放错误:', res);
				uni.showToast({
					title: '音频播放失败',
					icon: 'none'
				});
			});
		},
		
		togglePlay() {
			if (!this.audioElement) return;
			
			this.isPlaying = !this.isPlaying;
			
			if (this.isPlaying) {
				this.audioElement.play();
			} else {
				this.audioElement.pause();
			}
			
			this.$emit('toggle-play', this.isPlaying);
		},
		
		// 使用uni-app兼容的方式处理进度条点击
		handleProgressTap(e) {
			if (!this.audioElement || !this.audioElement.duration) return;
			
			try {
				// 获取点击位置相对信息
				const { x, width } = e.target;
				const position = e.detail.x ? (e.detail.x - x) / width : 0.5;
				
				// 确保position在0-1范围内
				const normalizedPosition = Math.max(0, Math.min(1, position));
				
				// 更新进度
				this.progress = normalizedPosition * 100;
				
				// 设置音频位置
				const seekTime = normalizedPosition * this.audioElement.duration;
				this.audioElement.seek(seekTime);
				
				this.$emit('seek', normalizedPosition);
			} catch (error) {
				console.error('处理进度条点击出错:', error);
				// 备用方案：使用50%位置
				this.seekToPercent(0.5);
			}
		},
		
		// 备用方法：按百分比设置进度
		seekToPercent(percent) {
			if (!this.audioElement || !this.audioElement.duration) return;
			
			// 确保percent在0-1范围内
			const normalizedPercent = Math.max(0, Math.min(1, percent));
			
			// 更新进度
			this.progress = normalizedPercent * 100;
			
			// 设置音频位置
			const seekTime = normalizedPercent * this.audioElement.duration;
			this.audioElement.seek(seekTime);
			
			this.$emit('seek', normalizedPercent);
		},
		
		formatTime(seconds) {
			if (!seconds || isNaN(seconds)) {
				return '00:00';
			}
			
			const minutes = Math.floor(seconds / 60);
			const remainingSeconds = Math.floor(seconds % 60);
			return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
		}
	},
	beforeDestroy() {
		// 销毁音频播放器
		if (this.audioElement) {
			this.audioElement.destroy();
		}
	}
}
</script>

<style lang="scss" scoped>
.preview-player-section {
	background-color: #fff;
	border-radius: 8px;
	padding: 20px;
	margin-bottom: 20px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
	
	.section-title {
		font-size: 18px;
		color: #333;
		font-weight: 500;
		margin-bottom: 15px;
	}
}

.preview-player {
	margin-top: 10px;
}

.mini-player-controls {
	display: flex;
	align-items: center;
	gap: 10px;
	
	.play-button {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background-color: #1890ff;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		
		.play-icon {
			color: #fff;
			font-size: 16px;
		}
	}
	
	.progress-container {
		flex: 1;
		
		.progress-bar {
			height: 4px;
			background-color: #e9e9e9;
			border-radius: 2px;
			position: relative;
			margin-bottom: 5px;
			cursor: pointer;
			
			.progress-inner {
				position: absolute;
				left: 0;
				top: 0;
				height: 100%;
				width: 20%;
				background-color: #1890ff;
				border-radius: 2px;
			}
		}
		
		.time-display {
			display: flex;
			justify-content: space-between;
			font-size: 12px;
			color: #999;
		}
	}
}
</style> 