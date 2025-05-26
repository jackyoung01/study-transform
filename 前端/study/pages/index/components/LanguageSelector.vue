<template>
	<view class="language-section">
		<text class="section-title">音频语言</text>
		<view class="language-selector">
			<view class="selected-language">简体中文</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'LanguageSelector',
	props: {
		selectedLanguage: {
			type: String,
			default: '简体中文'
		}
	},
	data() {
		return {
			// 只保留中文
			languages: ['简体中文']
		}
	},
	created() {
		// 发送默认语言
		this.$emit('language-change', this.languages[0]);
	},
	methods: {
		// 由于只有一个选项，方法简化
		handleChange() {
			this.$emit('language-change', this.languages[0]);
		}
	}
}
</script>

<style lang="scss" scoped>
.language-section {
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
	
	.language-selector {
		.selected-language {
			width: 100%;
			padding: 10px;
			border: 1px solid #ddd;
			border-radius: 4px;
			background-color: #f5f7fa;
			color: #333;
			text-align: center;
		}
	}
}
</style> 