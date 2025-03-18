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
DEFAULT_CROP_HEIGHT = 720  # 默认裁切高度
VIDEO_CODEC = 'h264'      # 视频编码
AUDIO_CODEC = 'aac'       # 音频编码
AUDIO_BITRATE = '192k'    # 音频比特率
VIDEO_PRESET = 'slow'     # 编码预设
VIDEO_CRF = 18           # 视频质量因子