const BASE_URL = 'http://localhost:8000'

/**
 * 转录音频文件
 * @param {string} file - 音频文件路径
 * @param {string} [scene] - 应用场景 ("课堂", "会议", "备忘录", "通用", "auto")
 * @param {string} [returnType='json'] - 返回类型 ('json' 或 'text')
 * @param {string} [language='zh'] - 音频语言 ('zh': 中文, 'en': 英文, 'ja': 日语, 'ko': 韩语)
 * @returns {Promise} 上传结果
 */
export const transcribeAudio = (file, scene = null, returnType = 'json', language = 'zh') => {
    const formData = {
        file,
        return_type: returnType,
        language: language
    }
    
    if (scene) {
        formData.scene = scene
    }
    
    return uni.uploadFile({
        url: `${BASE_URL}/api/v1/transcribe/`,
        filePath: file,
        name: 'file',
        formData
    })
}

/**
 * 检查API服务是否可用
 * @returns {Promise} 检查结果
 */
export const checkRoot = () => {
    return uni.request({
        url: `${BASE_URL}/`,
        method: 'GET'
    })
} 