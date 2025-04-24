import requests
import time
from tqdm import tqdm
from config import GITLAB_URL, PRIVATE_TOKEN, MAX_RETRIES, RETRY_DELAY
import os

def get_projects(save_automatically=False):
    """获取所有项目列表"""
    url = f"{GITLAB_URL}/api/v4/projects"
    params = {
        "simple": "true",
        "per_page": 100
    }
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    
    try:
        if not save_automatically:
            print("\n正在获取项目列表...")
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            projects = response.json()
            if not save_automatically:
                print("\n项目列表：")
                print("=" * 80)
                print(f"{'ID':<8} {'项目名称':<30} {'命名空间':<20} {'最后活动时间':<20}")
                print("-" * 80)
                for project in projects:
                    last_activity = project.get('last_activity_at', '未知')
                    if last_activity != '未知':
                        last_activity = last_activity.split('T')[0]  # 只显示日期部分
                    print(f"{project['id']:<8} {project['name']:<30} {project['namespace']['name']:<20} {last_activity:<20}")
                print("=" * 80)
            
            return projects, True
        else:
            print(f"获取项目列表失败: {response.text}")
            return None, False
    except Exception as e:
        print(f"获取项目列表时出错: {str(e)}")
        return None, False

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

def download_export(project_id, project_info, output_dir):
    """下载导出的项目"""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/export/download"
    headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
    
    # 生成文件名
    filename = f"{project_id}_{project_info['name']}.tar.gz"
    filepath = os.path.join(output_dir, filename)
    
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