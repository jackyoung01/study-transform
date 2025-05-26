<template>
	<view class="transcript-section">
		<view class="section-header">
			<text class="section-title">转录文本</text>
			<view class="transcript-tools">
				<text class="tool-btn" @click="copyTranscript">📋 复制</text>
				<text class="tool-btn" @click="toggleEditMode">
					{{ isEditing ? '✓ 保存' : '📝 编辑' }}
				</text>
			</view>
		</view>
		<view class="transcript-content">
			<!-- 实时转录中的效果 - 按行显示 -->
			<view v-if="isTranscribing" class="realtime-transcript">
				<!-- 已转录行 -->
				<view v-for="(segment, index) in displayedSegments" :key="index" class="segment-block">
					<view class="segment-header">第{{ index + 1 }}行：</view>
					<view class="segment-content">{{ segment }}</view>
				</view>
				
				<!-- 转录中提示 -->
				<view v-if="isTyping" class="typing-segment">
					<view class="segment-header">转录中</view>
					<view class="typing-indicator">
						<text class="dot"></text>
						<text class="dot"></text>
						<text class="dot"></text>
					</view>
				</view>
				
				<!-- 下一行提示 -->
				<view v-else-if="currentSegmentIndex < fullSegments.length" class="next-segment-hint">
					<text>正在处理第{{ currentSegmentIndex + 1 }}行...</text>
				</view>
			</view>
			
			<!-- 转录完成后的效果 - 编辑模式 -->
			<view v-else-if="isEditing && finalText" class="edit-transcript">
				<textarea 
					class="edit-textarea" 
					v-model="editedText"
					auto-height
					maxlength="-1"
					placeholder="在此编辑转录文本..."
				></textarea>
				<view class="edit-actions">
					<button class="edit-btn cancel-btn" @click="cancelEdit">取消</button>
					<button class="edit-btn save-btn" @click="saveEdit">保存</button>
				</view>
			</view>
			
			<!-- 转录完成后的效果 - 完整文本 -->
			<view v-else-if="finalText" class="final-transcript">
				<view class="final-content" v-html="highlightedText"></view>
			</view>
			
			<!-- 空状态 -->
			<view v-else class="empty-transcript">
				<text>暂无转录内容</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'TranscriptSection',
	props: {
		isTranscribing: {
			type: Boolean,
			default: false
		},
		rawTranscriptText: {
			type: String,
			default: ''
		},
		finalText: {
			type: String,
			default: ''
		},
		keywords: {
			type: Array,
			default: () => []
		}
	},
	data() {
		return {
			displayedSegments: [],
			fullSegments: [],
			currentSegmentIndex: 0,
			isTyping: false,
			typingTimer: null,
			segmentDisplayTimer: null,
			isEditing: false,
			editedText: '',
			originalText: ''
		}
	},
	computed: {
		highlightedText() {
			if (!this.finalText) return '';
			
			// 获取原始文本并处理可能的空格问题
			const originalText = this.finalText;
			// 为了显示，将空格转换为可见空格
			let displayText = originalText.replace(/ /g, ' ');
			
			// 优先处理较长的关键词，避免短词先替换导致的问题
			const sortedKeywords = [...this.keywords].sort((a, b) => b.length - a.length);
			
			// 创建高亮后的HTML标记
			sortedKeywords.forEach(keyword => {
				if (!keyword || !keyword.trim()) return;
				
				// 处理可能的转义字符
				const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
				
				// 创建正则表达式，处理可能的空格
				const regex = new RegExp(escapedKeyword, 'g');
				
				// 尝试在原始文本中查找关键词
				const matches = originalText.match(regex);
				if (matches && matches.length > 0) {
					console.log(`关键词"${keyword}"在原始文本中找到${matches.length}次`);
					
					// 在显示文本中替换关键词为高亮版本
					displayText = displayText.replace(
						new RegExp(escapedKeyword, 'g'), 
						`<span class="highlight-keyword">${keyword}</span>`
					);
				} else {
					// 如果没找到，可能是因为空格问题，尝试移除空格后匹配
					const noSpaceText = originalText.replace(/\s+/g, '');
					const noSpaceKeyword = keyword.replace(/\s+/g, '');
					if (noSpaceText.includes(noSpaceKeyword)) {
						console.log(`关键词"${keyword}"在移除空格后的文本中找到`);
						
						// 创建一个特殊的正则表达式，允许关键词中可能有空格
						const flexibleRegex = new RegExp(
							escapedKeyword.replace(/\s+/g, '\\s*'),
							'g'
						);
						displayText = displayText.replace(
							flexibleRegex,
							`<span class="highlight-keyword">${keyword}</span>`
						);
					} else {
						console.log(`关键词"${keyword}"在文本中未找到`);
					}
				}
			});
			
			return displayText;
		}
	},
	watch: {
		rawTranscriptText: {
			handler(newText) {
				if (newText && this.isTranscribing) {
					this.processTranscriptText(newText);
				}
			},
			immediate: true
		},
		isTranscribing(newVal) {
			if (newVal) {
				// 开始转录，重置状态
				this.resetTranscription();
				// 退出编辑模式
				this.isEditing = false;
			} else {
				// 转录结束，清除计时器
				this.clearTimers();
			}
		},
		finalText: {
			handler(newText) {
				// 当最终文本更新时，更新编辑文本
				if (newText && !this.isEditing) {
					this.editedText = newText;
					this.originalText = newText;
				}
			},
			immediate: true
		}
	},
	methods: {
		processTranscriptText(text) {
			// 将文本分成3段，均匀分配
			this.fullSegments = [];
			const totalLength = text.length;
			const segmentLength = Math.ceil(totalLength / 3);
			
			// 分段
			for (let i = 0; i < text.length; i += segmentLength) {
				const end = Math.min(i + segmentLength, text.length);
				// 尝试在句号、问号、感叹号处断句
				let adjustedEnd = end;
				if (end < text.length) {
					// 向后查找最近的句号、问号或感叹号
					for (let j = end; j < Math.min(end + 30, text.length); j++) {
						if (['.', '。', '!', '！', '?', '？', '，', ','].includes(text[j])) {
							adjustedEnd = j + 1;
							break;
						}
					}
				}
				this.fullSegments.push(text.substring(i, adjustedEnd));
			}
			
			// 确保只有3段
			if (this.fullSegments.length > 3) {
				// 如果分段超过3段，合并最后的段落
				const extraSegments = this.fullSegments.splice(2);
				this.fullSegments[2] = extraSegments.join('');
			} else if (this.fullSegments.length < 3) {
				// 如果不足3段，用空字符串补齐
				while (this.fullSegments.length < 3) {
					this.fullSegments.push('');
				}
			}
			
			console.log(`文本已分成${this.fullSegments.length}段`);
			
			// 开始显示段落
			this.startSegmentDisplay();
		},
		
		startSegmentDisplay() {
			this.clearTimers();
			this.currentSegmentIndex = 0;
			this.displayedSegments = [];
			
			// 开始显示第一段前先显示转录中状态
			this.isTyping = true;
			this.typingTimer = setTimeout(() => {
				this.displayNextSegment();
			}, 1500); // 先显示1.5秒的转录中状态
		},
		
		displayNextSegment() {
			if (this.currentSegmentIndex < this.fullSegments.length) {
				const segment = this.fullSegments[this.currentSegmentIndex];
				
				// 先结束上一个转录中状态
				this.isTyping = false;
				
				// 短暂延迟后再显示本段文本
				setTimeout(() => {
					// 添加这一段文本到显示的段落中
					this.displayedSegments.push(segment);
					
					// 更新当前索引，准备显示下一段
					this.currentSegmentIndex++;
					
					// 如果还有下一段，继续显示转录中状态
					if (this.currentSegmentIndex < this.fullSegments.length) {
						// 延迟一会儿再显示转录中状态
						setTimeout(() => {
							this.isTyping = true;
							
							// 显示一段时间的转录中状态，然后继续下一段
							this.typingTimer = setTimeout(() => {
								this.displayNextSegment();
							}, 2000); // 转录中状态显示2秒
						}, 1000); // 显示完上一段后等待1秒
					} else {
						// 所有段落显示完毕，延迟一会儿再通知完成
						setTimeout(() => {
							this.$emit('transcription-displayed');
						}, 1000);
					}
				}, 500);
			}
		},
		
		resetTranscription() {
			this.clearTimers();
			this.displayedSegments = [];
			this.fullSegments = [];
			this.currentSegmentIndex = 0;
			this.isTyping = false;
		},
		
		clearTimers() {
			if (this.typingTimer) {
				clearTimeout(this.typingTimer);
				this.typingTimer = null;
			}
			if (this.segmentDisplayTimer) {
				clearTimeout(this.segmentDisplayTimer);
				this.segmentDisplayTimer = null;
			}
		},
		
		toggleEditMode() {
			if (this.isEditing) {
				// 如果当前是编辑模式，则保存编辑
				this.saveEdit();
			} else {
				// 否则进入编辑模式
				this.enterEditMode();
			}
		},
		
		enterEditMode() {
			if (!this.finalText) {
				uni.showToast({
					title: '暂无内容可编辑',
					icon: 'none'
				});
				return;
			}
			
			this.isEditing = true;
			this.editedText = this.finalText;
			this.originalText = this.finalText;
		},
		
		saveEdit() {
			// 发送更新后的文本
			this.$emit('update-transcript', this.editedText);
			
			// 退出编辑模式
			this.isEditing = false;
			
			uni.showToast({
				title: '修改已保存',
				icon: 'success'
			});
		},
		
		cancelEdit() {
			// 恢复原始文本
			this.editedText = this.originalText;
			
			// 退出编辑模式
			this.isEditing = false;
			
			uni.showToast({
				title: '已取消编辑',
				icon: 'none'
			});
		},
		
		copyTranscript() {
			let textToCopy = '';
			
			if (this.isTranscribing) {
				// 如果正在转录中，复制已经显示的段落
				textToCopy = this.displayedSegments.join('\n');
			} else if (this.finalText) {
				// 如果已经完成转录，复制最终文本
				textToCopy = this.finalText;
			}
			
			if (!textToCopy) {
				uni.showToast({
					title: '暂无内容可复制',
					icon: 'none'
				});
				return;
			}
			
			// 复制到剪贴板
			uni.setClipboardData({
				data: textToCopy,
				success: () => {
					uni.showToast({
						title: '已复制到剪贴板',
						icon: 'success'
					});
				}
			});
		}
	},
	beforeDestroy() {
		this.clearTimers();
	}
}
</script>

<style lang="scss" scoped>
.transcript-section {
	background-color: #fff;
	border-radius: 8px;
	padding: 15px;
	margin-bottom: 20px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
	max-height: 400px;
	overflow-y: auto;
	
	.section-header {
		margin-bottom: 15px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 10px;
		border-bottom: 1px solid #f0f0f0;
		position: sticky;
		top: 0;
		background-color: #fff;
		z-index: 1;
		
		.section-title {
			font-size: 16px;
			font-weight: 500;
			color: #333;
		}
		
		.transcript-tools {
			display: flex;
			gap: 10px;
			
			.tool-btn {
				font-size: 12px;
				color: #666;
				cursor: pointer;
				
				&:hover {
					color: #007AFF;
				}
			}
		}
	}
	
	.transcript-content {
		.empty-transcript {
			text-align: center;
			padding: 30px 0;
			color: #999;
			font-size: 14px;
		}
		
		.realtime-transcript {
			.segment-block {
				margin-bottom: 15px;
				
				.segment-header {
					font-size: 14px;
					font-weight: 500;
					color: #333;
					margin-bottom: 5px;
				}
				
				.segment-content {
					font-size: 14px;
					line-height: 1.6;
					color: #333;
					background-color: #f0f7ff;
					padding: 10px 15px;
					border-radius: 8px;
					word-break: break-word;
				}
			}
			
			.typing-segment {
				margin-bottom: 15px;
				
				.segment-header {
					font-size: 14px;
					font-weight: 500;
					color: #333;
					margin-bottom: 5px;
				}
			}
			
			.typing-indicator {
				display: flex;
				padding: 10px;
				justify-content: center;
				background-color: #f0f7ff;
				border-radius: 8px;
				
				.dot {
					width: 8px;
					height: 8px;
					border-radius: 50%;
					background-color: #007AFF;
					margin: 0 3px;
					animation: typing 1s infinite ease-in-out;
					
					&:nth-child(1) {
						animation-delay: 0s;
					}
					
					&:nth-child(2) {
						animation-delay: 0.2s;
					}
					
					&:nth-child(3) {
						animation-delay: 0.4s;
					}
				}
			}
			
			.next-segment-hint {
				text-align: center;
				padding: 10px;
				color: #666;
				font-size: 12px;
				font-style: italic;
			}
		}
		
		.edit-transcript {
			.edit-textarea {
				width: 100%;
				min-height: 200px;
				font-size: 14px;
				line-height: 1.6;
				padding: 12px;
				border: 1px solid #e0e0e0;
				border-radius: 8px;
				color: #333;
				background-color: #f8f8f8;
			}
			
			.edit-actions {
				display: flex;
				justify-content: flex-end;
				margin-top: 10px;
				gap: 10px;
				
				.edit-btn {
					font-size: 14px;
					padding: 6px 12px;
					border-radius: 4px;
					border: none;
					cursor: pointer;
				}
				
				.cancel-btn {
					background-color: #f0f0f0;
					color: #666;
				}
				
				.save-btn {
					background-color: #007AFF;
					color: white;
				}
			}
		}
		
		.final-transcript {
			.final-content {
				font-size: 14px;
				line-height: 1.6;
				color: #333;
				background-color: #f0f7ff;
				padding: 15px;
				border-radius: 8px;
				word-break: break-word;
				white-space: pre-line;
			}
		}
	}
}

:deep(.highlight-keyword) {
	background-color: #007AFF;
	color: white;
	padding: 0 2px;
	border-radius: 3px;
}

@keyframes typing {
	0% {
		transform: scale(0.8);
		opacity: 0.6;
	}
	50% {
		transform: scale(1.2);
		opacity: 1;
	}
	100% {
		transform: scale(0.8);
		opacity: 0.6;
	}
}
</style> 