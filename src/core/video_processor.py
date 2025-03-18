import ffmpeg
from pathlib import Path
from typing import Tuple, Optional
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

    def get_media_duration(self, input_path: Path) -> float:
        """获取媒体文件时长"""
        try:
            probe = ffmpeg.probe(str(input_path))
            # 获取时长（秒）
            return float(probe['format']['duration'])
        except Exception as e:
            logger.error(f"获取媒体时长失败: {str(e)}")
            raise

    def crop_video(self, 
                  input_path: Path, 
                  output_path: Path, 
                  crop_height: int,
                  audio_mode: str = 'keep',
                  audio_path: Optional[Path] = None) -> None:
        """
        裁切视频并处理音频
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        :param crop_height: 裁切位置（距离顶部的像素数）
        :param audio_mode: 音频处理模式 ('keep', 'remove', 'replace')
        :param audio_path: 替换用的音频文件路径
        """
        try:
            width, height = self.get_video_dimensions(input_path)
            crop_height = min(crop_height, height - self.min_crop_height)
            
            logger.info(f"原始视频尺寸: {width}x{height}")
            logger.info(f"裁切后尺寸: {width}x{crop_height}")
            
            # 基础视频流
            stream = ffmpeg.input(str(input_path))
            video = stream.filter('crop', width, crop_height, 0, 0)
            video_duration = self.get_media_duration(input_path)
            
            # 音频处理
            output_args = {
                'vcodec': VIDEO_CODEC,
                'preset': VIDEO_PRESET,
                'crf': VIDEO_CRF,
                'loglevel': 'error'
            }
            
            if audio_mode == 'keep':
                # 保持原音频
                output_args.update({
                    'acodec': AUDIO_CODEC,
                    'audio_bitrate': AUDIO_BITRATE
                })
                audio = stream.audio
                stream = ffmpeg.output(video, audio, str(output_path), **output_args)
                
            elif audio_mode == 'remove':
                # 删除音频
                output_args['an'] = None
                stream = ffmpeg.output(video, str(output_path), **output_args)
                
            elif audio_mode == 'replace' and audio_path:
                # 替换音频
                audio_duration = self.get_media_duration(audio_path)
                audio = ffmpeg.input(str(audio_path))
                
                if audio_duration < video_duration:
                    # 音频较短，需要循环
                    logger.info(f"音频时长 ({audio_duration:.2f}s) 小于视频时长 ({video_duration:.2f}s)，将循环播放")
                    # 计算需要重复的次数
                    loop_times = int(video_duration / audio_duration) + 1
                    
                    # 创建音频流列表
                    audio_streams = []
                    for _ in range(loop_times):
                        audio_streams.append(audio)
                    
                    # 使用 concat 过滤器连接多个音频流
                    audio = (ffmpeg
                            .concat(*audio_streams, v=0, a=1)
                            .filter('atrim', duration=video_duration)  # 裁切到视频长度
                            .filter('asetpts', 'PTS-STARTPTS'))  # 重置时间戳
                    
                elif audio_duration > video_duration:
                    # 音频较长，需要裁切
                    logger.info(f"音频时长 ({audio_duration:.2f}s) 大于视频时长 ({video_duration:.2f}s)，将被裁切")
                    audio = audio.filter('atrim', duration=video_duration)
                
                stream = ffmpeg.output(video, audio, str(output_path),
                                    acodec=AUDIO_CODEC,
                                    audio_bitrate=AUDIO_BITRATE,
                                    **output_args)
            else:
                # 默认：无音频输出
                stream = ffmpeg.output(video, str(output_path), **output_args)
            
            logger.info(f"开始处理视频，音频模式: {audio_mode}")
            stream.run(capture_stdout=True, capture_stderr=True)
            logger.info(f"视频处理完成: {output_path}")
            
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            raise 