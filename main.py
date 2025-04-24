import requests
import os
import time
import yaml
from pathlib import Path
import re
from tqdm import tqdm
import signal
import sys
from ui import show_menu, select_project, export_project, handle_menu_choice
from gitlab_api import get_projects
from file_operations import save_projects_to_file
from utils import setup_signal_handler

def signal_handler(sig, frame):
    """处理中断信号"""
    print("\n程序已中断")
    sys.exit(0)

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 加载配置
config = load_config()
GITLAB_URL = config['gitlab']['url']
PRIVATE_TOKEN = config['gitlab']['private_token']
OUTPUT_DIR = config['output']['dir']
MAX_RETRIES = config['download']['max_retries']
RETRY_DELAY = config['download']['retry_delay']

# 注册中断信号处理
signal.signal(signal.SIGINT, signal_handler)

def ensure_output_dir():
    """确保输出目录存在"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def start_export(project_id):
    """开始导出项目"""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/export"
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    
    response = requests.post(url, headers=headers)
    if response.status_code == 202:
        print(f"项目 {project_id} 导出已开始")
        return True
    else:
        print(f"启动导出失败: {response.text}")
        return False

def check_export_status(project_id):
    """检查导出状态"""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/export"
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("export_status")
    return None

def clean_filename(filename):
    """清理文件名中的非法字符"""
    # 移除所有非字母、数字、下划线、连字符和点的字符
    return re.sub(r'[^\w\-\.]', '', filename)

def get_project_info(project_id):
    """获取项目信息"""
    data = load_projects_file()
    if not data:
        return None
        
    for project in data['projects']:
        if project['id'] == project_id:
            return project
    return None

def download_export(project_id):
    """下载导出的项目"""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/export/download"
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    
    # 获取项目信息
    project_info = get_project_info(project_id)
    if not project_info:
        print("无法获取项目信息")
        return False
    
    # 生成文件名
    filename = f"{project_id}_{project_info['name']}.tar.gz"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                
                with open(filepath, 'wb') as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="下载进度") as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                
                print(f"\n项目已成功导出到: {filepath}")
                return True
            elif response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    print(f"请求过于频繁，等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
            else:
                print(f"下载失败: {response.text}")
                return False
        except Exception as e:
            print(f"下载出错: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
                continue
            return False
    
    return False


def load_projects_file():
    """加载项目列表文件"""
    projects_dir = "projects"
    domain = GITLAB_URL.split('://')[1].replace(':', '_')
    filename = f"{domain}.yaml"
    filepath = os.path.join(projects_dir, filename)
    
    try:
        if not os.path.exists(filepath):
            print(f"未找到项目列表文件: {filepath}")
            print("请先使用功能1查询项目列表")
            return None
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data
    except Exception as e:
        print(f"读取项目列表文件时出错: {str(e)}")
        return None

def main():
    setup_signal_handler()
    
    while True:
        choice = show_menu()
        if not handle_menu_choice(choice):
            break

if __name__ == "__main__":
    main()
