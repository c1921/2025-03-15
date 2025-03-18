from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Web服务器配置
SERVER_HOST = "localhost"
SERVER_PORT = 8000

# 视频处理配置
MIN_CROP_HEIGHT = 100
VIDEO_CODEC = 'h264'
AUDIO_CODEC = 'aac'
AUDIO_BITRATE = '192k'
VIDEO_PRESET = 'slow'
VIDEO_CRF = 18 