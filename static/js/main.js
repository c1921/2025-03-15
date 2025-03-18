const BUTTON_STYLES = {
    INACTIVE: 'btn-secondary',  // 非裁切模式样式
    ACTIVE: 'btn-danger'               // 裁切模式样式
};

const videoInput = document.getElementById('videoInput');
const videoPreview = document.getElementById('videoPreview');
const cropLine = document.getElementById('cropLine');
const cropInfo = document.getElementById('cropInfo');
const cropHeight = document.getElementById('cropHeight');
const processBtn = document.getElementById('processBtn');
const progress = document.getElementById('progress');
const result = document.getElementById('result');
const toggleMode = document.getElementById('toggleMode');
const videoContainer = document.querySelector('.video-container');
const audioMode = document.getElementById('audioMode');
const audioInputGroup = document.getElementById('audioInputGroup');
const audioInput = document.getElementById('audioInput');
let cropMode = false;
let isDragging = false;
let DEFAULT_CROP_HEIGHT = 720;  // 默认值

// 获取服务器配置
fetch('/config')
    .then(response => response.json())
    .then(config => {
        DEFAULT_CROP_HEIGHT = config.DEFAULT_CROP_HEIGHT;
    });

// 切换裁切模式
function toggleCropMode() {
    cropMode = !cropMode;
    videoContainer.classList.toggle('crop-mode', cropMode);
    toggleMode.textContent = cropMode ? '退出裁切模式' : '切换裁切模式';
    toggleMode.classList.toggle(BUTTON_STYLES.INACTIVE, !cropMode);
    toggleMode.classList.toggle(BUTTON_STYLES.ACTIVE, cropMode);

    // 在裁切模式下暂停视频
    if (cropMode) {
        videoPreview.pause();
    }
}

// 点击按钮切换模式
toggleMode.onclick = toggleCropMode;

// 修改键盘事件监听
document.addEventListener('keydown', (e) => {
    // 只在输入数字的输入框上禁用快捷键
    if (e.code === 'KeyA' && document.activeElement.type !== 'number') {
        e.preventDefault();
        toggleCropMode();
    }
});

// 修改裁切线事件处理
cropLine.addEventListener('mousedown', (e) => {
    if (!cropMode) return;
    isDragging = true;
    e.preventDefault();  // 防止选中文本
});

// 修改拖动事件处理
document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    const containerRect = videoContainer.getBoundingClientRect();
    // 使用相对于容器的坐标
    let y = e.clientY - containerRect.top;
    
    // 计算实际的视频显示区域
    const videoHeight = videoPreview.videoHeight;
    const videoWidth = videoPreview.videoWidth;
    const containerHeight = videoContainer.clientHeight;
    
    let displayHeight;
    if (videoWidth / videoHeight > videoContainer.clientWidth / containerHeight) {
        displayHeight = (videoHeight * videoContainer.clientWidth) / videoWidth;
    } else {
        displayHeight = containerHeight;
    }
    
    // 计算视频在容器中的偏移
    const topOffset = (containerHeight - displayHeight) / 2;
    
    // 限制在视频区域内
    y = Math.max(topOffset, Math.min(y, topOffset + displayHeight));
    
    // 计算实际裁切位置
    const ratio = videoHeight / displayHeight;
    const cropPos = Math.round((y - topOffset) * ratio);
    
    // 确保值在有效范围内
    const validPos = Math.min(Math.max(cropPos, 1), videoHeight);
    cropHeight.value = validPos;
    updateCropLine(validPos);
});

document.addEventListener('mouseup', () => {
    isDragging = false;
});

// 修改点击事件处理
videoContainer.onclick = (e) => {
    if (!cropMode || isDragging) return;

    const containerRect = videoContainer.getBoundingClientRect();
    // 使用相对于容器的坐标
    const y = e.clientY - containerRect.top;
    
    // 计算实际的视频显示区域
    const videoHeight = videoPreview.videoHeight;
    const videoWidth = videoPreview.videoWidth;
    const containerHeight = videoContainer.clientHeight;
    
    let displayHeight;
    if (videoWidth / videoHeight > videoContainer.clientWidth / containerHeight) {
        displayHeight = (videoHeight * videoContainer.clientWidth) / videoWidth;
    } else {
        displayHeight = containerHeight;
    }
    
    // 计算视频在容器中的偏移
    const topOffset = (containerHeight - displayHeight) / 2;
    
    // 只在视频区域内响应点击
    if (y < topOffset || y > topOffset + displayHeight) return;
    
    // 计算实际裁切位置
    const ratio = videoHeight / displayHeight;
    const cropPos = Math.round((y - topOffset) * ratio);
    
    // 确保值在有效范围内
    const validPos = Math.min(Math.max(cropPos, 1), videoHeight);
    cropHeight.value = validPos;
    updateCropLine(validPos);
};

// 视频预览
videoInput.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
        const url = URL.createObjectURL(file);
        videoPreview.src = url;
        processBtn.disabled = true;  // 初始时禁用按钮
        cropMode = false;
        videoContainer.classList.remove('crop-mode');
        toggleMode.classList.add(BUTTON_STYLES.INACTIVE);
        toggleMode.classList.remove(BUTTON_STYLES.ACTIVE);
        toggleMode.textContent = '切换裁切模式';

        // 加载视频后显示裁切线
        videoPreview.onloadedmetadata = () => {
            cropLine.style.display = 'block';
            
            // 根据视频实际高度设置默认裁切高度
            const videoHeight = videoPreview.videoHeight;
            let defaultHeight;
            
            if (videoHeight <= DEFAULT_CROP_HEIGHT) {
                // 如果视频高度小于默认值，使用视频高度的一半
                defaultHeight = Math.floor(videoHeight / 2);
            } else {
                // 否则使用默认值
                defaultHeight = DEFAULT_CROP_HEIGHT;
            }
            
            cropHeight.value = defaultHeight;
            updateCropLine(defaultHeight);
        };
    }
};

// 更新裁切线位置
function updateCropLine(pos) {
    const videoElement = videoPreview;
    const containerHeight = videoContainer.clientHeight;
    const videoHeight = videoElement.videoHeight;
    const videoWidth = videoElement.videoWidth;
    
    // 计算视频在容器中的实际显示尺寸
    let displayHeight;
    let displayWidth;
    
    if (videoWidth / videoHeight > videoContainer.clientWidth / containerHeight) {
        // 视频比容器更宽，以宽度为准
        displayWidth = videoContainer.clientWidth;
        displayHeight = (videoHeight * displayWidth) / videoWidth;
    } else {
        // 视频比容器更高，以高度为准
        displayHeight = containerHeight;
        displayWidth = (videoWidth * displayHeight) / videoHeight;
    }
    
    // 计算视频在容器中的偏移
    const topOffset = (containerHeight - displayHeight) / 2;
    
    // 计算裁切线位置
    const ratio = displayHeight / videoHeight;
    const linePos = pos * ratio + topOffset;
    
    cropLine.style.top = `${linePos}px`;
    cropInfo.style.top = `${linePos - 20}px`;
    cropInfo.textContent = `裁切位置: ${pos}px`;
    
    // 更新裁切按钮状态
    processBtn.disabled = !pos || !videoInput.files[0];
}

// 修改裁切高度输入框的验证
cropHeight.addEventListener('input', (e) => {
    const value = parseInt(e.target.value);
    const maxHeight = videoPreview.videoHeight;
    
    if (!isNaN(value) && value >= 1 && value <= maxHeight) {
        cropHeight.classList.remove('is-invalid');
        updateCropLine(value);
    } else {
        cropHeight.classList.add('is-invalid');
        processBtn.disabled = true;
        
        // 添加错误提示
        if (value > maxHeight) {
            cropHeight.title = `裁切高度不能超过视频高度 ${maxHeight}px`;
        } else if (value < 1) {
            cropHeight.title = '裁切高度必须大于0';
        } else {
            cropHeight.title = '请输入有效的数字';
        }
    }
});

// 音频模式切换处理
document.querySelectorAll('input[name="audioMode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        audioInputGroup.classList.toggle('d-none', e.target.value !== 'replace');
        if (e.target.value !== 'replace') {
            audioInput.value = '';  // 清空已选择的文件
        }
    });
});

// 修改处理视频的代码
processBtn.onclick = async () => {
    if (!videoInput.files[0]) return;

    const cropValue = parseInt(cropHeight.value);
    const maxHeight = videoPreview.videoHeight;
    
    if (isNaN(cropValue) || cropValue < 1 || cropValue > maxHeight) {
        result.innerHTML = `
            <div class="alert alert-danger">
                <h5>错误</h5>
                <p class="mb-0">裁切高度必须在 1 到 ${maxHeight} 像素之间</p>
            </div>
        `;
        return;
    }

    // 禁用按钮
    processBtn.disabled = true;
    progress.classList.remove('d-none');
    result.innerHTML = '';

    const formData = new FormData();
    formData.append('video', videoInput.files[0]);
    formData.append('crop_height', cropValue);
    // 获取选中的音频模式
    const audioMode = document.querySelector('input[name="audioMode"]:checked').value;
    formData.append('audio_mode', audioMode);
    
    if (audioMode === 'replace' && audioInput.files[0]) {
        formData.append('audio_file', audioInput.files[0]);
    }

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (response.ok) {
            result.innerHTML = `
                <div class="alert alert-success">
                    <h5>✓ ${data.message}</h5>
                    <p class="mb-0">输出文件：${data.output_path}</p>
                </div>
            `;
        } else {
            result.innerHTML = `
                <div class="alert alert-danger">
                    <h5>处理失败</h5>
                    <p class="mb-0">${data.detail || data.error || '未知错误'}</p>
                </div>
            `;
        }
    } catch (error) {
        result.innerHTML = `
            <div class="alert alert-danger">
                <h5>处理出错</h5>
                <p class="mb-0">${error.message || '未知错误'}</p>
            </div>
        `;
    }
    // 重新启用按钮
    processBtn.disabled = false;
    progress.classList.add('d-none');
};