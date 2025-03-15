import ffmpeg
from pathlib import Path

def crop_video(input_path: Path, output_path: Path, crop_height: int):
    """
    裁切视频
    :param input_path: 输入视频路径
    :param output_path: 输出视频路径
    :param crop_height: 裁切位置（距离顶部的像素数）
    """
    try:
        # 获取视频信息
        probe = ffmpeg.probe(str(input_path))
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])
        
        # 计算裁切参数
        crop_height = min(crop_height, height - 100)  # 确保至少保留100像素
        new_height = crop_height
        
        print(f"原始视频尺寸: {width}x{height}")
        print(f"裁切后尺寸: {width}x{new_height}")
        
        # 构建ffmpeg命令
        stream = (
            ffmpeg
            .input(str(input_path))
            .filter('crop', width, new_height, 0, 0)  # crop=w:h:x:y
            .output(str(output_path),
                   vcodec='h264',              # 使用h264编码器
                   preset='slow',              # 较慢的编码速度，更好的质量
                   crf=18,                     # 恒定质量因子（0-51，越小质量越好）
                   acodec='aac',               # 音频编码器
                   audio_bitrate='192k',       # 音频比特率
                   **{'loglevel': 'error'})    # 只显示错误信息
        )
        
        # 执行ffmpeg命令
        print("开始裁切视频...")
        stream.run(capture_stdout=True, capture_stderr=True)
        print(f"视频裁切完成: {output_path}")
        
    except ffmpeg.Error as e:
        print(f"处理视频时出错: {e.stderr.decode()}")
        raise
    except Exception as e:
        print(f"发生错误: {str(e)}")
        raise

def test_cropper():
    """
    测试函数
    """
    input_path = Path("test.mp4")
    output_path = input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"
    crop_height = 720  # 示例裁切高度
    
    try:
        crop_video(input_path, output_path, crop_height)
    except Exception as e:
        print(f"处理出错: {str(e)}")

if __name__ == "__main__":
    test_cropper() 