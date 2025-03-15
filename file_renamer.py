import os
from pathlib import Path
import re

def rename_mp4_files(directory):
    # 将输入路径转换为Path对象
    target_dir = Path(directory).resolve()  # 使用resolve()获取绝对路径
    
    print(f"正在处理目录: {target_dir}")
    
    # 确保目录存在
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"错误：目录 '{directory}' 不存在或不是一个有效的目录")
        return
    
    # 遍历目录中的所有文件夹
    folders = [f for f in target_dir.iterdir() if f.is_dir()]
    if not folders:
        print("警告：目标目录下没有找到子文件夹")
        # 直接处理当前目录的MP4文件
        process_folder(target_dir)
    else:
        for folder in folders:
            process_folder(folder)

def get_next_available_number(folder, folder_name):
    # 获取当前文件夹中已存在的序号
    pattern = re.compile(f"{re.escape(folder_name)}_(\d+)\.mp4$")
    existing_numbers = set()
    
    for file in folder.glob("*.mp4"):
        match = pattern.match(file.name)
        if match:
            existing_numbers.add(int(match.group(1)))
    
    # 找到最小的可用序号
    number = 1
    while number in existing_numbers:
        number += 1
    return number

def process_folder(folder):
    print(f"\n处理文件夹: {folder.name}")
    
    # 获取所有mp4文件并排序
    mp4_files = sorted([f for f in folder.glob("*.mp4")])
    
    if not mp4_files:
        print(f"在文件夹 '{folder.name}' 中没有找到MP4文件")
        return
        
    print(f"找到 {len(mp4_files)} 个MP4文件")
    
    # 获取下一个可用序号
    next_number = get_next_available_number(folder, folder.name)
    
    for file in mp4_files:
        # 检查文件是否已经符合命名格式
        pattern = f"{folder.name}_\d+\.mp4$"
        if re.match(pattern, file.name):
            print(f"跳过 {file.name} (已经是目标格式)")
            continue
        
        # 构建新文件名
        new_name = f"{folder.name}_{next_number:03d}.mp4"
        new_path = folder / new_name
        
        # 确保文件名不重复
        while new_path.exists():
            next_number += 1
            new_name = f"{folder.name}_{next_number:03d}.mp4"
            new_path = folder / new_name
        
        try:
            print(f"正在重命名: {file.name} -> {new_name}")
            file.rename(new_path)
            print(f"✓ 重命名成功")
            next_number += 1
        except Exception as e:
            print(f"× 重命名失败: {str(e)}")

if __name__ == "__main__":
    # 获取用户输入的目标目录
    target_directory = input("请输入要处理的目录路径: ").strip()
    if not target_directory:
        target_directory = "."  # 如果没有输入，使用当前目录
    
    rename_mp4_files(target_directory)
    print("\n处理完成!") 