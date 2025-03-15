import os
from pathlib import Path
import re
import json
import sys
import ffmpeg
import subprocess
from typing import Tuple

def load_config():
    config_path = Path("config.json")
    default_config = {
        "target_directories": [],
        "file_extensions": [".mp4"],
        "skip_existing": True
    }
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("已加载配置文件")
                return config
        else:
            print("未找到配置文件，创建默认配置...")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            return default_config
    except Exception as e:
        print(f"加载配置文件时出错: {str(e)}")
        return default_config

def rename_mp4_files(directory, file_extensions, skip_existing=True):
    target_dir = Path(directory).resolve()
    print(f"\n正在处理目录: {target_dir}")
    
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"错误：目录 '{directory}' 不存在或不是一个有效的目录")
        return
    
    folders = [f for f in target_dir.iterdir() if f.is_dir()]
    if not folders:
        print("警告：目标目录下没有找到子文件夹")
        process_folder(target_dir, file_extensions, skip_existing)
    else:
        for folder in folders:
            process_folder(folder, file_extensions, skip_existing)

def get_next_available_number(folder, folder_name):
    pattern = re.compile(f"{re.escape(folder_name)}_(\d+)\.[^.]+$")
    existing_numbers = set()
    
    for ext in config["file_extensions"]:
        for file in folder.glob(f"*{ext}"):
            match = pattern.match(file.name)
            if match:
                existing_numbers.add(int(match.group(1)))
    
    number = 1
    while number in existing_numbers:
        number += 1
    return number

def remove_audio(input_file: Path, output_file: Path) -> Tuple[bool, str]:
    """
    移除视频文件的音频轨道
    返回: (是否成功, 错误信息)
    """
    try:
        # 构建ffmpeg命令
        cmd = [
            'ffmpeg',
            '-i', str(input_file),  # 输入文件
            '-c:v', 'copy',         # 复制视频流，不重新编码
            '-an',                  # 移除音频
            '-y',                   # 覆盖输出文件
            str(output_file)
        ]
        
        # 执行命令，将输出重定向到PIPE
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)

def process_folder(folder, file_extensions, skip_existing):
    print(f"\n处理文件夹: {folder.name}")
    
    # 获取所有指定扩展名的文件并排序
    media_files = []
    for ext in file_extensions:
        media_files.extend(folder.glob(f"*{ext}"))
    media_files = sorted(media_files)
    
    if not media_files:
        print(f"在文件夹 '{folder.name}' 中没有找到媒体文件")
        return
        
    print(f"找到 {len(media_files)} 个媒体文件")
    
    next_number = get_next_available_number(folder, folder.name)
    
    for file in media_files:
        # 检查文件是否已经符合命名格式
        pattern = f"{folder.name}_\d+\{file.suffix}$"
        if skip_existing and re.match(pattern, file.name):
            print(f"跳过 {file.name} (已经是目标格式)")
            continue
        
        # 构建新文件名，保持原始扩展名
        new_name = f"{folder.name}_{next_number:03d}{file.suffix}"
        new_path = folder / new_name
        
        # 确保文件名不重复
        while new_path.exists():
            next_number += 1
            new_name = f"{folder.name}_{next_number:03d}{file.suffix}"
            new_path = folder / new_name
        
        try:
            print(f"正在处理: {file.name}")
            
            # 创建临时文件路径
            temp_file = folder / f"temp_{new_name}"
            
            # 移除音频
            print("- 移除音频中...")
            success, error = remove_audio(file, temp_file)
            
            if not success:
                print(f"× 移除音频失败: {error}")
                continue
                
            # 如果原文件和目标文件不同，则删除原文件
            if file != new_path:
                file.unlink()
            
            # 将临时文件重命名为目标文件名
            temp_file.rename(new_path)
            print(f"✓ 处理完成: {new_name}")
            next_number += 1
            
        except Exception as e:
            print(f"× 处理失败: {str(e)}")
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()

if __name__ == "__main__":
    # 检查ffmpeg是否可用
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("错误: 未找到ffmpeg。请确保已安装ffmpeg并添加到系统PATH中。")
        sys.exit(1)

    config = load_config()
    
    if not config["target_directories"]:
        target_directory = input("请输入要处理的目录路径: ").strip()
        if not target_directory:
            target_directory = "."
        config["target_directories"] = [target_directory]
    
    for directory in config["target_directories"]:
        rename_mp4_files(
            directory, 
            config["file_extensions"],
            config["skip_existing"]
        )
    
    print("\n所有目录处理完成!") 