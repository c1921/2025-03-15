import ffmpeg
from pathlib import Path
from typing import Tuple
from logging import getLogger
from config import *

logger = getLogger(__name__)

class VideoProcessor:
    def __init__(self, min_crop_height: int = 100):
        self.min_crop_height = min_crop_height

    def get_video_dimensions(self, input_path: Path) -> Tuple[int, int]:
        """获取视频尺寸"""
        try:
            probe = ffmpeg.probe(str(input_path))
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            return int(video_info['width']), int(video_info['height'])
        except ffmpeg.Error as e:
            logger.error(f"获取视频信息失败: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"处理视频信息时发生错误: {str(e)}")
            raise

    def crop_video(self, input_path: Path, output_path: Path, crop_height: int) -> None:
        """
        裁切视频
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        :param crop_height: 裁切位置（距离顶部的像素数）
        """
        try:
            width, height = self.get_video_dimensions(input_path)
            crop_height = min(crop_height, height - self.min_crop_height)
            
            logger.info(f"原始视频尺寸: {width}x{height}")
            logger.info(f"裁切后尺寸: {width}x{crop_height}")
            
            stream = (
                ffmpeg
                .input(str(input_path))
                .filter('crop', width, crop_height, 0, 0)
                .output(str(output_path),
                       vcodec=VIDEO_CODEC,
                       preset=VIDEO_PRESET,
                       crf=VIDEO_CRF,
                       acodec=AUDIO_CODEC,
                       audio_bitrate=AUDIO_BITRATE,
                       **{'loglevel': 'error'})
            )
            
            logger.info("开始裁切视频...")
            stream.run(capture_stdout=True, capture_stderr=True)
            logger.info(f"视频裁切完成: {output_path}")
            
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            raise 