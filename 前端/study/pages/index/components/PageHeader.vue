<template>
	<view class="header">
		<view class="home-icon">🏠</view>
		<text class="title">{{ title }}</text>
		<view class="header-actions">
			<view class="search-btn">🔍 搜索</view>
			<view class="share-btn">👥 协作</view>
			<view class="more-btn">📝 分享</view>
			<view class="download-btn">⬇️ 下载</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'PageHeader',
	props: {
		title: {
			type: String,
			default: '基于whisper综合语音转录分析'
		}
	}
}
</script>

<style lang="scss" scoped>
.header {
	display: flex;
	align-items: center;
	padding: 15px 20px;
	background-color: #fff;
	border-bottom: 1px solid #e9e9e9;
	
	.home-icon {
		font-size: 20px;
		margin-right: 10px;
	}
	
	.title {
		font-size: 16px;
		color: #333;
		font-weight: 500;
		flex: 1;
	}
	
	.header-actions {
		display: flex;
		align-items: center;
		gap: 15px;
		
		.search-btn, .share-btn, .more-btn, .download-btn {
			font-size: 14px;
			color: #666;
		}
	}
}
</style> 