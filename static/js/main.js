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
let cropMode = false;
let isDragging = false;

// 切换裁切模式
function toggleCropMode() {
    cropMode = !cropMode;
    videoContainer.classList.toggle('crop-mode', cropMode);
    toggleMode.textContent = cropMode ? '退出裁切模式' : '切换裁切模式';
    toggleMode.classList.toggle('btn-outline-primary', !cropMode);
    toggleMode.classList.toggle('btn-primary', cropMode);

    // 在裁切模式下暂停视频
    if (cropMode) {
        videoPreview.pause();
    }
}

// 点击按钮切换模式
toggleMode.onclick = toggleCropMode;

// 修改键盘事件监听
document.addEventListener('keydown', (e) => {
    if (e.code === 'KeyA' && document.activeElement.tagName !== 'INPUT') {
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

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    const rect = videoPreview.getBoundingClientRect();
    let y = e.clientY - rect.top;

    // 限制在视频区域内
    y = Math.max(0, Math.min(y, videoPreview.offsetHeight));

    // 计算实际裁切位置
    const height = videoPreview.offsetHeight;
    const realHeight = videoPreview.videoHeight;
    const ratio = realHeight / height;

    const cropPos = Math.round(y * ratio);
    cropHeight.value = cropPos;
    updateCropLine(cropPos);
});

document.addEventListener('mouseup', () => {
    isDragging = false;
});

// 修改点击事件，支持直接点击设置位置
videoContainer.onclick = (e) => {
    if (!cropMode || isDragging) return;

    const rect = videoPreview.getBoundingClientRect();
    const y = e.clientY - rect.top;

    if (Math.abs(y - cropLine.offsetTop) < 20) return;  // 如果点击太靠近裁切线，忽略

    const height = videoPreview.offsetHeight;
    const realHeight = videoPreview.videoHeight;
    const ratio = realHeight / height;

    const cropPos = Math.round(y * ratio);
    cropHeight.value = cropPos;
    updateCropLine(cropPos);
};

// 视频预览
videoInput.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
        const url = URL.createObjectURL(file);
        videoPreview.src = url;
        processBtn.disabled = false;
        cropMode = false;
        videoContainer.classList.remove('crop-mode');
        toggleMode.classList.add('btn-outline-primary');
        toggleMode.classList.remove('btn-primary');
        toggleMode.textContent = '切换裁切模式';

        // 加载视频后显示裁切线
        videoPreview.onloadedmetadata = () => {
            cropLine.style.display = 'block';
            updateCropLine(720); // 默认位置
        };
    }
};

// 更新裁切线位置
function updateCropLine(pos) {
    const height = videoPreview.offsetHeight;
    const realHeight = videoPreview.videoHeight;
    const ratio = height / realHeight;

    const linePos = pos * ratio;
    cropLine.style.top = `${linePos}px`;
    cropInfo.style.top = `${linePos - 20}px`;
    cropInfo.textContent = `裁切位置: ${pos}px`;
}

// 处理视频
processBtn.onclick = async () => {
    if (!videoInput.files[0]) return;

    progress.classList.remove('d-none');
    result.innerHTML = '';

    const formData = new FormData();
    formData.append('video', videoInput.files[0]);
    formData.append('crop_height', cropHeight.value);

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
                    <p class="mb-0">${data.error || '未知错误'}</p>
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
    progress.classList.add('d-none');
};