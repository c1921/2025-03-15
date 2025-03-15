from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import uvicorn
from video_cropper import crop_video
import tempfile

app = FastAPI()

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    """返回主页HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>视频裁切工具</title>
        <style>
            body { max-width: 1000px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
            .form-group { margin: 15px 0; }
            .progress { display: none; margin: 10px 0; color: #666; }
            .video-container { position: relative; margin: 20px 0; }
            #videoPreview { max-width: 100%; }
            #cropLine {
                position: absolute;
                left: 0;
                width: 100%;
                height: 20px;  /* 交互区域高度 */
                cursor: row-resize;
                pointer-events: auto;
                margin-top: -10px;
            }
            
            /* 实际显示的细线 */
            #cropLine::after {
                content: '';
                position: absolute;
                left: 0;
                top: 50%;
                width: 100%;
                height: 2px;
                background: rgba(255, 0, 0, 0.7);
                transform: translateY(-50%);
                transition: background-color 0.2s;
            }
            
            /* 悬停时细线加亮 */
            #cropLine:hover::after {
                background: rgba(255, 50, 50, 1);
                box-shadow: 0 0 4px rgba(255, 0, 0, 0.5);
            }
            
            .video-container.crop-mode #cropLine {
                pointer-events: auto;
            }
            .controls { margin: 10px 0; }
            button { padding: 8px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; margin-right: 10px; }
            button:hover { background: #45a049; }
            #cropHeight { width: 100px; padding: 5px; }
            .crop-info {
                position: absolute;
                left: 0;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px;
                font-size: 12px;
            }
            .mode-switch {
                margin: 10px 0;
            }
            .video-container.crop-mode {
                cursor: crosshair;
            }
            .video-container.crop-mode video {
                pointer-events: none;
            }
            .controls-overlay {
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.7);
                padding: 5px 10px;
                border-radius: 5px;
                color: white;
                display: none;
            }
            .video-container.crop-mode .controls-overlay {
                display: block;
            }
        </style>
    </head>
    <body>
        <h1>视频裁切工具</h1>
        <div class="form-group">
            <input type="file" id="videoInput" accept="video/*" required>
        </div>
        
        <div class="mode-switch">
            <button id="toggleMode" type="button">切换裁切模式</button>
        </div>
        
        <div class="video-container">
            <video id="videoPreview" controls>
                您的浏览器不支持 HTML5 视频。
            </video>
            <div id="cropLine"></div>
            <div id="cropInfo" class="crop-info"></div>
            <div class="controls-overlay">
                点击视频设置裁切位置 (按A键切换模式)
            </div>
        </div>
        
        <div class="controls">
            <input type="number" id="cropHeight" min="100" placeholder="裁切位置">
            <button id="processBtn" disabled>裁切视频</button>
        </div>
        
        <div id="progress" class="progress">处理中...</div>
        <div id="result"></div>
        
        <script>
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
            
            progress.style.display = 'block';
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
                result.innerHTML = `
                    <p style="color: green">✓ ${data.message}</p>
                    <p>输出文件：${data.output_path}</p>
                `;
            } catch (error) {
                result.innerHTML = `<p style="color: red">处理出错: ${error}</p>`;
            }
            progress.style.display = 'none';
        };
        </script>
    </body>
    </html>
    """

def ensure_dir(path: Path) -> None:
    """
    确保目录存在，如果不存在则创建
    :param path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)

def get_unique_filename(base_path: Path) -> Path:
    """
    生成唯一的文件名，并确保父目录存在
    :param base_path: 基础文件路径
    :return: 唯一的文件路径
    """
    # 确保父目录存在
    ensure_dir(base_path.parent)
    
    if not base_path.exists():
        return base_path
        
    counter = 1
    while True:
        new_path = base_path.parent / f"{base_path.stem}_{counter}{base_path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    crop_height: int = Form(...)
):
    """处理视频"""
    try:
        # 确保输出目录存在
        ensure_dir(UPLOAD_DIR)
        
        # 构建输出路径
        output_path = UPLOAD_DIR / f"cropped_{video.filename}"
        output_path = get_unique_filename(output_path)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=video.filename) as temp_file:
            shutil.copyfileobj(video.file, temp_file)
            temp_path = Path(temp_file.name)
        
        try:
            # 裁切视频
            crop_video(temp_path, output_path, crop_height)
        finally:
            # 清理临时文件
            temp_path.unlink()
        
        return {
            "message": "视频处理完成",
            "output_path": str(output_path)
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 