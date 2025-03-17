from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import uvicorn
from video_cropper import crop_video
import tempfile
import webbrowser
import threading
import time

app = FastAPI()

# 创建必要的目录
UPLOAD_DIR = Path("output")
TEMPLATES_DIR = Path("templates")
UPLOAD_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# 设置模板和静态文件
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """返回主页"""
    return templates.TemplateResponse("index.html", {"request": request})

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

def open_browser():
    """延迟一秒后打开浏览器"""
    time.sleep(1)
    webbrowser.open('http://localhost:8000')

if __name__ == "__main__":
    # 创建线程来打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    # 启动服务器
    uvicorn.run(app, host="localhost", port=8000) 