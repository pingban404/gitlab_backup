import os
import yaml
import re
from pathlib import Path
from config import OUTPUT_DIR, GITLAB_URL

def ensure_output_dir():
    """确保输出目录存在"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def clean_filename(filename):
    """清理文件名中的非法字符"""
    # 移除所有非字母、数字、下划线、连字符和点的字符
    return re.sub(r'[^\w\-\.]', '', filename)

def save_projects_to_file(projects):
    """将项目列表保存到本地文件"""
    try:
        # 创建projects目录
        projects_dir = "projects"
        os.makedirs(projects_dir, exist_ok=True)
        
        # 从GitLab URL中提取域名
        domain = GITLAB_URL.split('://')[1].replace(':', '_')
        filename = f"{domain}.yaml"
        filepath = os.path.join(projects_dir, filename)
        
        # 准备要保存的数据
        projects_data = {
            "gitlab_url": GITLAB_URL,
            "projects": [
                {
                    "id": project["id"],
                    "name": project["name"],
                    "path": project["path"],
                    "namespace": project["namespace"]["name"],
                    "last_activity_at": project.get("last_activity_at", "未知")
                }
                for project in projects
            ]
        }
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(projects_data, f, allow_unicode=True, sort_keys=False)
        
        print(f"\n项目列表已保存到: {filepath}")
        return True
    except Exception as e:
        print(f"保存项目列表时出错: {str(e)}")
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

def get_project_info(project_id):
    """获取项目信息"""
    data = load_projects_file()
    if not data:
        return None
        
    for project in data['projects']:
        if project['id'] == project_id:
            return project
    return None 