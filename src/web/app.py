import sys
from pathlib import Path
import logging
import os
import socket

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from version.version import VERSION_STR, APP_NAME, COMPANY, DESCRIPTION, COPYRIGHT

# 在文件开头添加日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import tempfile
import shutil
import webbrowser
import threading
import time
from pathlib import Path
from logging import getLogger
from src.core.video_processor import VideoProcessor
from src.utils.ffmpeg_utils import check_ffmpeg, get_unique_filename
from config import *
import uvicorn

logger = getLogger(__name__)

app = FastAPI(title="视频裁切工具")
video_processor = VideoProcessor()

# 动态设置 UPLOAD_DIR 为可执行文件所在目录的 output 子目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    base_dir = Path(sys.executable).parent
else:
    # 如果是直接运行的脚本
    base_dir = Path(__file__).resolve().parent.parent

UPLOAD_DIR = base_dir / "output"

# 初始化所有必要的目录
for directory in [UPLOAD_DIR, TEMPLATES_DIR, STATIC_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# 设置模板和静态文件
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """返回主页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "DEFAULT_CROP_HEIGHT": DEFAULT_CROP_HEIGHT,
        "version": VERSION_STR,
        "app_name": APP_NAME,
        "company": COMPANY,
        "description": DESCRIPTION,
        "copyright": COPYRIGHT
    })

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    crop_height: int = Form(...),
    audio_mode: str = Form('keep'),
    audio_file: UploadFile = File(None)
):
    """处理视频"""
    if not video.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")
        
    if not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="请上传视频文件")
        
    if crop_height <= 0:
        raise HTTPException(status_code=400, detail="裁切高度必须大于0")
        
    if audio_mode not in AUDIO_MODES:
        raise HTTPException(status_code=400, detail="无效的音频处理模式")
        
    if audio_mode == 'replace' and not audio_file:
        raise HTTPException(status_code=400, detail="请选择替换用的音频文件")

    try:
        # 确保 output 目录存在
        UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        
        output_path = UPLOAD_DIR / f"cropped_{video.filename}"
        output_path = get_unique_filename(output_path)
        
        # 保存临时文件
        temp_files = []
        with tempfile.NamedTemporaryFile(delete=False, suffix=video.filename) as temp_file:
            shutil.copyfileobj(video.file, temp_file)
            video_path = Path(temp_file.name)
            temp_files.append(video_path)
            
        # 如果有音频文件，也保存为临时文件
        audio_path = None
        if audio_file and audio_mode == 'replace':
            with tempfile.NamedTemporaryFile(delete=False, suffix=audio_file.filename) as temp_audio:
                shutil.copyfileobj(audio_file.file, temp_audio)
                audio_path = Path(temp_audio.name)
                temp_files.append(audio_path)
        
        try:
            video_processor.crop_video(
                video_path, 
                output_path, 
                crop_height,
                audio_mode=audio_mode,
                audio_path=audio_path
            )
            return {
                "status": "success",
                "message": "视频处理完成",
                "output_path": str(output_path)
            }
        finally:
            # 清理所有临时文件
            for temp_file in temp_files:
                temp_file.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"处理视频时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """返回前端需要的配置"""
    return {
        "DEFAULT_CROP_HEIGHT": DEFAULT_CROP_HEIGHT
    }

def find_free_port(start_port=8080, max_tries=100):
    """查找可用的端口号"""
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError('无法找到可用的端口')

def start_server():
    """启动服务器"""
    ffmpeg_installed, error_msg = check_ffmpeg()
    if not ffmpeg_installed:
        logger.error(f"FFmpeg 未安装: {error_msg}")
        raise SystemExit(1)
    
    logger.info("FFmpeg 检查通过，正在启动服务器...")

    # 查找可用的端口
    port = find_free_port(SERVER_PORT)
    
    # 使用线程在服务器启动后打开浏览器
    threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(
        f'http://{SERVER_HOST}:{port}'
    )), daemon=True).start()
    
    # 使用 uvicorn 启动服务器
    uvicorn.run(app, host=SERVER_HOST, port=port)

if __name__ == "__main__":
    start_server() 