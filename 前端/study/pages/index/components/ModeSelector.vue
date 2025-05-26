<template>
	<view class="mode-section">
		<text class="section-title">应用场景</text>
		<view class="mode-options">
			<view 
				v-for="(mode, index) in modes" 
				:key="index"
				class="mode-card"
				:class="{ selected: selectedMode === index }"
				@click="selectMode(index)"
			>
				<text class="mode-icon">{{ mode.icon }}</text>
				<text class="mode-name">{{ mode.name }}</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'ModeSelector',
	props: {
		selectedMode: {
			type: Number,
			default: 0
		}
	},
	data() {
		return {
			modes: [
				{ icon: '🎓', name: '课堂', desc: '课堂授课场景' },
				{ icon: '👥', name: '会议', desc: '商务会议场景' },
				{ icon: '📝', name: '备忘录', desc: '个人备忘场景' },
				{ icon: '🌐', name: '通用', desc: '通用场景' }
			]
		}
	},
	methods: {
		selectMode(index) {
			this.$emit('mode-selected', index);
		}
	}
}
</script>

<style lang="scss" scoped>
.mode-section {
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

.mode-options {
	display: flex;
	flex-wrap: wrap;
	gap: 10px;
}

.mode-card {
	flex: 1;
	min-width: calc(50% - 5px);
	padding: 10px;
	border: 1px solid #ddd;
	border-radius: 8px;
	text-align: center;
	cursor: pointer;
	transition: all 0.2s ease;
	
	&:hover {
		transform: translateY(-2px);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}
	
	&.selected {
		border-color: #007AFF;
		background-color: #F0F7FF;
	}
	
	.mode-icon {
		font-size: 20px;
		margin-bottom: 5px;
		display: block;
	}
	
	.mode-name {
		font-weight: bold;
		font-size: 14px;
	}
}
</style> 