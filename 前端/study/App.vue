<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
	page {
		background-color: #f5f7fa;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
	}
	
	/* 重置默认样式 */
	view, text, button, input, textarea, scroll-view {
		box-sizing: border-box;
	}
	
	button::after {
		border: none;
	}
	
	/* 全局颜色变量 */
	:root {
		--primary-color: #1890ff;
		--background-color: #f5f7fa;
		--text-color: #333;
		--text-color-secondary: #666;
		--text-color-light: #999;
		--border-color: #e9e9e9;
		--card-background: #fff;
		--box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
	}
</style>
