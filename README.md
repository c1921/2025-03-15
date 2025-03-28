# 视频裁切工具 (Video Cropper)

一个简单易用的视频裁切工具，可以通过可视化界面快速裁切视频高度。

## 使用方法

1. 运行程序后，在浏览器中打开 <http://localhost:8000>
2. 点击选择要处理的视频文件
3. 通过以下方式设置裁切位置：
   - 点击"切换裁切模式"按钮或按 `A` 键进入裁切模式
   - 直接点击视频画面设置裁切位置
   - 拖动红色裁切线调整位置
   - 手动输入裁切位置数值
4. 点击"裁切视频"开始处理
5. 处理完成后可在 output 目录找到裁切后的视频

## FFmpeg 安装说明

本工具依赖 FFmpeg 进行视频处理。

Windows 用户：

1. 下载 [ffmpeg-release-full.7z](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z) 并解压
2. 将解压后的 `bin` 目录添加到系统环境变量 PATH 中
3. 打开命令提示符，输入 `ffmpeg -version` 验证安装
