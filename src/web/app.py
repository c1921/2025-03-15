import sys
from pathlib import Path
import logging

# 在文件开头添加日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

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

logger = getLogger(__name__)

app = FastAPI(title="视频裁切工具")
video_processor = VideoProcessor()

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
        "DEFAULT_CROP_HEIGHT": DEFAULT_CROP_HEIGHT
    })

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    crop_height: int = Form(...)
):
    """处理视频"""
    if not video.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")
        
    if not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="请上传视频文件")
        
    if crop_height <= 0:
        raise HTTPException(status_code=400, detail="裁切高度必须大于0")

    try:
        output_path = UPLOAD_DIR / f"cropped_{video.filename}"
        output_path = get_unique_filename(output_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=video.filename) as temp_file:
            shutil.copyfileobj(video.file, temp_file)
            temp_path = Path(temp_file.name)
        
        try:
            video_processor.crop_video(temp_path, output_path, crop_height)
            return {
                "status": "success",
                "message": "视频处理完成",
                "output_path": str(output_path)
            }
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"视频处理失败: {str(e)}")
        finally:
            temp_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"处理视频时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """返回前端需要的配置"""
    return {
        "DEFAULT_CROP_HEIGHT": DEFAULT_CROP_HEIGHT
    }

def start_server():
    """启动服务器"""
    ffmpeg_installed, error_msg = check_ffmpeg()
    if not ffmpeg_installed:
        logger.error(f"FFmpeg 未安装: {error_msg}")
        raise SystemExit(1)
    
    logger.info("FFmpeg 检查通过，正在启动服务器...")
    threading.Thread(target=lambda: time.sleep(1) and webbrowser.open(
        f'http://{SERVER_HOST}:{SERVER_PORT}'
    ), daemon=True).start()
    
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)

if __name__ == "__main__":
    start_server() 