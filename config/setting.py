import os
import json
import sys
from pathlib import Path

def find_project_root(current_path: Path, target_files: set) -> Path:
    for parent in current_path.parents:
        if any((parent / target_file).exists() for target_file in target_files):
            return parent
    return current_path

def get_project_root() -> Path:
    current_file_path = Path(__file__).resolve()
    # 假设app.py在项目根目录
    project_root = find_project_root(current_file_path, {"app.py"})
    return project_root

def get_config_path():
    # 获取当前可执行文件的目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用程序
        base_path = sys._MEIPASS
    else:
        # 如果是开发环境
        base_path = get_project_root()

    return os.path.join(base_path, 'config/config.json')

def get_config():
   config_path = get_config_path()
   with open(config_path, 'r') as f:
      return json.load(f)
   


def update_config(new_llm_list=[], new_ocr_process_list=[]):
    """
    更新配置文件中的 default_llm_list 和 default_OCR_process_list 字段内容。
    :param new_llm_list: 用于更新 default_llm_list 的新列表
    :param new_ocr_process_list: 用于更新 default_OCR_process_list 的新列表
    """
    try:
        if len(new_llm_list) == 0 and len(new_ocr_process_list) == 0:
            return
        # 读取原始配置文件内容
        file_path = get_config_path()
        with open(file_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        
        # 更新指定字段
        if "default_llm_list" in config_data:
            if len(new_llm_list):
                config_data["default_llm_list"] = new_llm_list
        if "default_OCR_process_list" in config_data:
            if len(new_ocr_process_list):
                config_data["default_OCR_process_list"] = new_ocr_process_list
        
        # 写回更新后的配置文件
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(config_data, file, indent=4, ensure_ascii=False)
        print("配置文件更新成功！")
    except Exception as e:
        print(f"更新配置文件时发生错误: {e}")


CONFIG = get_config()

