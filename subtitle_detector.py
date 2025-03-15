import cv2
import numpy as np
from pathlib import Path
import ffmpeg
import matplotlib.pyplot as plt

class SubtitleDetector:
    def __init__(self, sample_interval=1.0, debug=True):
        """
        初始化字幕检测器
        :param sample_interval: 采样间隔（秒）
        :param debug: 是否输出调试图像
        """
        self.sample_interval = sample_interval
        self.debug = debug
        self.debug_dir = Path("debug_output")
        if debug:
            self.debug_dir.mkdir(exist_ok=True)
        
    def save_debug_image(self, image, frame_index, stage):
        """
        保存调试图像
        """
        if not self.debug:
            return
            
        if len(image.shape) == 2:  # 如果是灰度图，转换为RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
        output_path = self.debug_dir / f"frame_{frame_index:03d}_{stage}.jpg"
        cv2.imwrite(str(output_path), image)
        print(f"保存调试图像: {output_path}")
    
    def plot_projection(self, projection, frame_index, height, subtitle_top):
        """
        绘制并保存水平投影图
        """
        if not self.debug:
            return
            
        plt.figure(figsize=(10, 6))
        plt.plot(projection, range(height))
        plt.axhline(y=subtitle_top, color='r', linestyle='--', label='检测到的字幕位置')
        plt.grid(True)
        plt.title(f'帧 {frame_index} 的水平投影')
        plt.xlabel('像素和')
        plt.ylabel('垂直位置')
        plt.legend()
        
        output_path = self.debug_dir / f"frame_{frame_index:03d}_projection.png"
        plt.savefig(output_path)
        plt.close()
        print(f"保存投影图: {output_path}")
    
    def extract_frames(self, video_path: Path):
        """
        从视频中提取帧
        :param video_path: 视频文件路径
        :return: 帧列表
        """
        frames = []
        video = cv2.VideoCapture(str(video_path))
        
        if not video.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
            
        # 获取视频信息
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.sample_interval)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"视频FPS: {fps}")
        print(f"总帧数: {frame_count}")
        print(f"采样间隔: {frame_interval}帧")
        
        current_frame = 0
        while current_frame < frame_count:
            video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = video.read()
            if ret:
                frames.append(frame)
            current_frame += frame_interval
            
        video.release()
        print(f"提取了 {len(frames)} 帧")
        return frames
    
    def detect_subtitle_region(self, frame, frame_index):
        """
        在单帧中检测字幕区域
        """
        # 保存原始帧
        self.save_debug_image(frame, frame_index, "original")
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.save_debug_image(gray, frame_index, "gray")
        
        # 自适应二值化
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # 邻域大小
            2    # 常数差值
        )
        
        # 进行形态学操作
        kernel = np.ones((3,15), np.uint8)  # 横向连接
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        self.save_debug_image(binary, frame_index, "binary")
        
        # 计算水平投影
        height = frame.shape[0]
        horizontal_projection = np.sum(binary, axis=1)
        
        # 使用滑动窗口平滑投影曲线
        window_size = 10
        smoothed_projection = np.convolve(horizontal_projection, 
                                        np.ones(window_size)/window_size, 
                                        mode='valid')
        
        # 计算投影梯度
        gradient = np.gradient(smoothed_projection)
        
        # 从底部向上搜索字幕区域
        bottom_region = height - window_size
        search_range = height // 2  # 只搜索下半部分
        
        # 寻找梯度变化最大的位置
        max_gradient = 0
        subtitle_top = height
        
        for y in range(bottom_region, bottom_region - search_range, -1):
            if y >= len(gradient):
                continue
            current_gradient = abs(gradient[y])
            if current_gradient > max_gradient:
                max_gradient = current_gradient
                subtitle_top = y
        
        # 微调字幕位置
        threshold = np.mean(smoothed_projection) * 1.2
        for y in range(subtitle_top, subtitle_top - 50, -1):
            if y >= len(smoothed_projection) and smoothed_projection[y] < threshold:
                subtitle_top = y
                break
        
        # 在原始帧上标记检测到的字幕区域
        marked_frame = frame.copy()
        cv2.line(marked_frame, (0, subtitle_top), (frame.shape[1], subtitle_top), 
                 (0, 255, 0), 2)
        self.save_debug_image(marked_frame, frame_index, "marked")
        
        # 绘制投影图和梯度
        if self.debug:
            plt.figure(figsize=(12, 8))
            
            # 绘制原始投影
            plt.subplot(211)
            plt.plot(horizontal_projection, range(len(horizontal_projection)), 
                    label='原始投影')
            plt.plot(smoothed_projection, 
                    range(window_size-1, len(horizontal_projection)), 
                    label='平滑后')
            plt.axhline(y=subtitle_top, color='r', linestyle='--', 
                       label='检测到的字幕位置')
            plt.grid(True)
            plt.title(f'帧 {frame_index} 的水平投影')
            plt.xlabel('像素和')
            plt.ylabel('垂直位置')
            plt.legend()
            
            # 绘制梯度
            plt.subplot(212)
            plt.plot(gradient, range(window_size-1, len(horizontal_projection)), 
                    label='梯度')
            plt.axhline(y=subtitle_top, color='r', linestyle='--', 
                       label='检测到的字幕位置')
            plt.grid(True)
            plt.title('投影梯度')
            plt.xlabel('梯度值')
            plt.ylabel('垂直位置')
            plt.legend()
            
            plt.tight_layout()
            output_path = self.debug_dir / f"frame_{frame_index:03d}_analysis.png"
            plt.savefig(output_path)
            plt.close()
        
        return subtitle_top
    
    def detect_subtitle_height(self, video_path: Path):
        """
        检测视频中字幕的位置
        :param video_path: 视频文件路径
        :return: 建议的裁剪位置
        """
        # 提取帧
        frames = self.extract_frames(video_path)
        if not frames:
            raise ValueError("未能提取到视频帧")
            
        # 检测每一帧中的字幕位置
        subtitle_positions = []
        for i, frame in enumerate(frames):
            position = self.detect_subtitle_region(frame, i)
            subtitle_positions.append(position)
            print(f"帧 {i+1}: 检测到字幕位置在 {position}")
        
        # 统计分析检测结果
        positions = np.array(subtitle_positions)
        
        # 1. 使用四分位数方法去除异常值
        Q1 = np.percentile(positions, 25)
        Q3 = np.percentile(positions, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # 过滤掉异常值
        filtered_positions = positions[(positions >= lower_bound) & (positions <= upper_bound)]
        
        # 2. 使用直方图找到最频繁的位置区间
        hist, bin_edges = np.histogram(filtered_positions, bins='auto')
        most_common_bin = np.argmax(hist)
        start_pos = bin_edges[most_common_bin]
        end_pos = bin_edges[most_common_bin + 1]
        
        # 3. 在最频繁区间内取一个保守的位置（靠上的位置）
        final_positions = filtered_positions[
            (filtered_positions >= start_pos) & 
            (filtered_positions <= end_pos)
        ]
        
        if len(final_positions) == 0:
            print("警告：未能找到稳定的字幕位置")
            crop_position = int(np.mean(filtered_positions))
        else:
            crop_position = int(np.min(final_positions))
        
        # 可视化检测结果
        if self.debug:
            plt.figure(figsize=(12, 8))
            
            # 绘制原始检测位置
            plt.subplot(211)
            plt.plot(positions, 'b.', label='原始检测位置')
            plt.axhline(y=crop_position, color='r', linestyle='--', label='最终裁剪位置')
            plt.axhline(y=lower_bound, color='g', linestyle=':', label='异常值边界')
            plt.axhline(y=upper_bound, color='g', linestyle=':')
            plt.grid(True)
            plt.title('字幕位置检测结果')
            plt.xlabel('帧序号')
            plt.ylabel('垂直位置')
            plt.legend()
            
            # 绘制位置分布直方图
            plt.subplot(212)
            plt.hist(filtered_positions, bins='auto', alpha=0.7, color='b', label='位置分布')
            plt.axvline(x=crop_position, color='r', linestyle='--', label='最终裁剪位置')
            plt.axvline(x=start_pos, color='g', linestyle=':', label='最频繁区间')
            plt.axvline(x=end_pos, color='g', linestyle=':')
            plt.grid(True)
            plt.title('字幕位置分布')
            plt.xlabel('垂直位置')
            plt.ylabel('频次')
            plt.legend()
            
            plt.tight_layout()
            plt.savefig(self.debug_dir / "detection_statistics.png")
            plt.close()
            
            # 保存检测数据
            stats = {
                "原始检测位置": positions.tolist(),
                "过滤后位置": filtered_positions.tolist(),
                "异常值边界": [lower_bound, upper_bound],
                "最频繁区间": [start_pos, end_pos],
                "最终裁剪位置": crop_position
            }
            
            import json
            with open(self.debug_dir / "detection_stats.json", 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return crop_position

    def crop_video(self, input_path: Path, output_path: Path, crop_height: int):
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
                       # 使用高质量编码设置
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

    def process_video(self, input_path: Path):
        """
        处理单个视频：检测字幕位置并裁切
        :param input_path: 输入视频路径
        """
        try:
            # 检测字幕位置
            print(f"\n处理视频: {input_path}")
            crop_height = self.detect_subtitle_height(input_path)
            print(f"检测到字幕位置: 距离顶部 {crop_height} 像素")
            
            # 构建输出文件路径
            output_path = input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"
            
            # 裁切视频
            self.crop_video(input_path, output_path, crop_height)
            
        except Exception as e:
            print(f"处理视频 {input_path} 时出错: {str(e)}")
            raise

def test_detector():
    """
    测试函数
    """
    detector = SubtitleDetector(sample_interval=1.0, debug=True)
    video_path = Path("海蜇2_021.mp4")
    
    try:
        detector.process_video(video_path)
        print(f"\n处理完成！调试图像已保存到 {detector.debug_dir} 目录")
        
    except Exception as e:
        print(f"处理出错: {str(e)}")

if __name__ == "__main__":
    test_detector() 