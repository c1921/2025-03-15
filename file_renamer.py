import os
from pathlib import Path
import re
import json
import sys

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
            print(f"正在重命名: {file.name} -> {new_name}")
            file.rename(new_path)
            print(f"✓ 重命名成功")
            next_number += 1
        except Exception as e:
            print(f"× 重命名失败: {str(e)}")

if __name__ == "__main__":
    config = load_config()
    
    if not config["target_directories"]:
        # 如果配置文件中没有目标目录，则请求用户输入
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