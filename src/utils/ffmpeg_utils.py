import subprocess
from typing import Tuple
from pathlib import Path

def check_ffmpeg() -> Tuple[bool, str]:
    """
    检查 FFmpeg 是否已安装
    :return: (是否安装, 错误信息)
    """
    try:
        subprocess.run(['ffmpeg', '-version'], 
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE,
                     check=True)
        return True, ""
    except FileNotFoundError:
        return False, (
            "未检测到 FFmpeg，请按照以下步骤安装：\n\n"
            "1. 下载 FFmpeg: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z\n"
            "2. 解压下载的文件\n"
            "3. 将解压后的 bin 目录添加到系统环境变量 PATH 中\n"
            "4. 重启程序\n"
        )
    except subprocess.CalledProcessError as e:
        return False, f"FFmpeg 运行出错: {e.stderr.decode()}"
    except Exception as e:
        return False, f"检查 FFmpeg 时发生错误: {str(e)}"

def get_unique_filename(path: Path) -> Path:
    """
    生成唯一的文件名
    :param path: 原始文件路径
    :return: 唯一的文件路径
    """
    if not path.exists():
        return path
        
    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1 