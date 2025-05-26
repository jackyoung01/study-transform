<template>
	<view class="upload-section">
		<view class="section-title">音频 / 视频文件</view>
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
				<view class="action-buttons">
					<button class="browse-button" @click="chooseFile">浏览文件</button>
					<button class="record-button" @click="$emit('show-recording')">录制音频</button>
				</view>
			</view>
			<view class="selected-file" v-else>
				<text class="file-icon">📄</text>
				<text class="file-name">{{ audioFileName }}</text>
				<button class="change-file-btn" @click="chooseFile">更换文件</button>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'FileUploader',
	props: {
		audioFile: {
			type: String,
			default: ''
		},
		audioFileName: {
			type: String,
			default: ''
		}
	},
	methods: {
		chooseFile() {
			uni.chooseFile({
				count: 1,
				type: 'all',
				extension: ['.mp3', '.mp4', '.m4a', '.mov', '.aac', '.wav', '.ogg', '.opus', '.mpeg', '.wma', '.wmv'],
				success: (res) => {
					const file = res.tempFilePaths[0];
					const fileName = res.tempFiles[0].name;
					this.$emit('file-selected', {
						file,
						fileName
					});
					
					uni.showToast({
						title: '文件已选择',
						icon: 'success'
					});
				}
			});
		}
	}
}
</script>

<style lang="scss" scoped>
.upload-section {
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

.upload-area {
	margin-bottom: 20px;
}

.upload-box {
	border: 2px dashed #ddd;
	border-radius: 8px;
	padding: 20px;
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
		line-height: 1.6;
	}
}

.divider {
	color: #999;
	margin: 15px 0;
	font-size: 14px;
}

.action-buttons {
	display: flex;
	gap: 10px;
	justify-content: center;
}

.browse-button {
	background-color: #eee;
	border: none;
	padding: 10px 15px;
	border-radius: 4px;
	color: #333;
	font-size: 14px;
	flex: 1;
	max-width: 45%;
}

.record-button {
	background-color: #ff4d4f;
	border: none;
	padding: 10px 15px;
	border-radius: 4px;
	color: #fff;
	font-size: 14px;
	flex: 1;
	max-width: 45%;
}

.selected-file {
	display: flex;
	align-items: center;
	padding: 15px;
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
	}
}
</style> 