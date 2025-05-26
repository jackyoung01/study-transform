<template>
	<view class="export-panel">
		<text class="section-title">导出结果</text>
		
		<view class="export-options">
			<view class="export-btn txt-btn" @click="exportAsTxt">
				<text class="export-icon">📄</text>
				<text class="export-label">导出TXT</text>
			</view>
			
			<view class="export-btn word-btn" @click="exportAsWord">
				<text class="export-icon">📝</text>
				<text class="export-label">导出Word</text>
			</view>
			
			<view class="export-btn pdf-btn" @click="exportAsPdf">
				<text class="export-icon">📋</text>
				<text class="export-label">导出PDF</text>
			</view>
		</view>
		
		<view class="export-note">
			<text>导出文件将包含原始转录内容和识别的关键词</text>
		</view>
	</view>
</template>

<script>
export default {
	name: 'ExportPanel',
	props: {
		transcriptText: {
			type: String,
			default: ''
		},
		keywords: {
			type: Array,
			default: () => []
		},
		fileName: {
			type: String,
			default: '转录结果'
		}
	},
	data() {
		return {
			
		}
	},
	methods: {
		// 获取格式化后的导出文本
		getFormattedText() {
			if (!this.transcriptText) {
				return '暂无转录内容';
			}
			
			let formattedText = '转录结果\n';
			formattedText += '='.repeat(20) + '\n\n';
			
			// 添加转录文本
			formattedText += this.transcriptText + '\n\n';
			
			// 添加关键词列表
			if (this.keywords && this.keywords.length > 0) {
				formattedText += '关键词:\n';
				formattedText += '-'.repeat(20) + '\n';
				this.keywords.forEach((keyword, index) => {
					formattedText += `${index + 1}. ${keyword}\n`;
				});
			}
			
			return formattedText;
		},
		
		// 导出为TXT
		exportAsTxt() {
			const content = this.getFormattedText();
			const fileName = `${this.fileName || '转录结果'}.txt`;
			
			this.downloadFile(content, fileName, 'text/plain');
		},
		
		// 导出为Word文档 (实际上是HTML格式，可以导入Word)
		exportAsWord() {
			// #ifdef H5
			try {
				const content = this.getFormattedText();
				const fileName = `${this.fileName || '转录结果'}.doc`;
				
				// 创建HTML内容
				const htmlContent = `
					<html>
					<head>
						<meta charset="utf-8">
						<title>${fileName}</title>
						<style>
							body { font-family: Arial, sans-serif; line-height: 1.6; }
							.transcript { margin: 20px 0; white-space: pre-line; }
							.keywords { margin-top: 20px; }
							.keyword-item { margin: 5px 0; }
						</style>
					</head>
					<body>
						<h1>转录结果</h1>
						<hr>
						<div class="transcript">${this.transcriptText}</div>
						
						${this.keywords && this.keywords.length > 0 ? `
							<div class="keywords">
								<h2>关键词:</h2>
								<hr>
								${this.keywords.map((keyword, index) => `
									<div class="keyword-item">${index + 1}. ${keyword}</div>
								`).join('')}
							</div>
						` : ''}
					</body>
					</html>
				`;
				
				this.downloadFile(htmlContent, fileName, 'application/msword');
			} catch (error) {
				console.error('导出Word文档失败:', error);
				uni.showToast({
					title: '导出Word文档失败',
					icon: 'none'
				});
			}
			// #endif
			
			// #ifndef H5
			uni.showToast({
				title: 'Word导出仅支持H5平台',
				icon: 'none'
			});
			// #endif
		},
		
		// 导出为PDF (仅支持H5)
		exportAsPdf() {
			// #ifdef H5
			uni.showToast({
				title: 'PDF导出功能待实现',
				icon: 'none'
			});
			// #endif
			
			// #ifndef H5
			uni.showToast({
				title: 'PDF导出仅支持H5平台',
				icon: 'none'
			});
			// #endif
		},
		
		// 下载文件 (主要用于H5平台)
		downloadFile(content, fileName, mimeType) {
			// #ifdef H5
			try {
				// 创建Blob对象
				const blob = new Blob([content], { type: mimeType });
				
				// 创建下载链接
				const link = document.createElement('a');
				link.href = URL.createObjectURL(blob);
				link.download = fileName;
				
				// 触发点击事件
				document.body.appendChild(link);
				link.click();
				
				// 清理
				document.body.removeChild(link);
				setTimeout(() => {
					URL.revokeObjectURL(link.href);
				}, 100);
				
				uni.showToast({
					title: '导出成功',
					icon: 'success'
				});
			} catch (error) {
				console.error('下载文件失败:', error);
				uni.showToast({
					title: '导出失败',
					icon: 'none'
				});
			}
			// #endif
			
			// #ifndef H5
			uni.showToast({
				title: '当前平台不支持直接下载',
				icon: 'none'
			});
			// #endif
		}
	}
}
</script>

<style lang="scss" scoped>
.export-panel {
	background-color: #fff;
	border-radius: 8px;
	padding: 15px;
	margin-bottom: 20px;
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
	
	.section-title {
		font-size: 16px;
		font-weight: 500;
		color: #333;
		margin-bottom: 15px;
		display: block;
	}
	
	.export-options {
		display: flex;
		gap: 10px;
		margin-bottom: 15px;
		
		.export-btn {
			flex: 1;
			padding: 15px 10px;
			background-color: #f5f7fa;
			border-radius: 8px;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			cursor: pointer;
			transition: all 0.2s ease;
			
			&:hover {
				transform: translateY(-2px);
				box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
			}
			
			&:active {
				transform: translateY(0);
			}
			
			.export-icon {
				font-size: 24px;
				margin-bottom: 5px;
			}
			
			.export-label {
				font-size: 14px;
				color: #333;
			}
		}
		
		.txt-btn {
			border-top: 3px solid #007AFF;
		}
		
		.word-btn {
			border-top: 3px solid #4CAF50;
		}
		
		.pdf-btn {
			border-top: 3px solid #FF5722;
		}
	}
	
	.export-note {
		font-size: 12px;
		color: #999;
		text-align: center;
	}
}
</style> 