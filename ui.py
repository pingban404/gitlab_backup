import time
from tqdm import tqdm
from gitlab_api import start_export, check_export_status, download_export
from file_operations import ensure_output_dir, get_project_info, load_projects_file, save_projects_to_file
from config import OUTPUT_DIR
import os

def show_menu():
    """显示主菜单"""
    print("\n" + "=" * 50)
    print("GitLab 项目工具")
    print("=" * 50)
    print("1. 查询项目列表")
    print("2. 导出项目")
    print("0. 退出")
    print("=" * 50)
    choice = input("\n请选择功能 (0-2): ")
    return choice

def handle_menu_choice(choice):
    """处理菜单选择"""
    if choice == "1":
        from gitlab_api import get_projects
        projects, success = get_projects()
        if success and input("\n是否将项目列表保存到本地文件？(y/n): ").lower() == 'y':
            save_projects_to_file(projects)
    elif choice == "2":
        project_id = select_project()
        if project_id:
            try:
                if export_project(project_id):
                    print("项目导出流程完成")
                else:
                    print("项目导出流程失败")
            except ValueError:
                print("请输入有效的项目ID（数字）")
    elif choice == "0":
        print("退出程序")
        return False
    else:
        print("无效的选择，请重新输入")
    return True

def select_project():
    """从项目列表中选择项目"""
    data = load_projects_file()
    if not data:
        print("\n正在自动获取项目列表...")
        from gitlab_api import get_projects
        projects, success = get_projects(save_automatically=True)
        if not success:
            return None
        from file_operations import save_projects_to_file
        save_projects_to_file(projects)
        data = load_projects_file()
        if not data:
            return None
            
    projects = data['projects']
    print("\n项目列表：")
    print("=" * 80)
    print(f"{'ID':<8} {'项目名称':<30} {'命名空间':<20} {'最后活动时间':<20}")
    print("-" * 80)
    
    for project in projects:
        last_activity = project.get('last_activity_at', '未知')
        if last_activity != '未知':
            last_activity = last_activity.split('T')[0]  # 只显示日期部分
        print(f"{project['id']:<8} {project['name']:<30} {project['namespace']:<20} {last_activity:<20}")
    print("=" * 80)
    
    while True:
        try:
            project_id = input("\n请输入要导出的项目ID (输入0返回): ")
            if project_id == '0':
                return None
                
            project_id = int(project_id)
            # 验证项目ID是否存在
            if any(project['id'] == project_id for project in projects):
                return project_id
            else:
                print("无效的项目ID，请重新输入")
        except ValueError:
            print("请输入有效的项目ID（数字）")

def export_project(project_id):
    """导出项目的完整流程"""
    ensure_output_dir()
    
    if not start_export(project_id):
        return False
    
    print("\n正在等待导出完成...")
    with tqdm(total=100, desc="导出进度") as pbar:
        while True:
            status = check_export_status(project_id)
            if status == "finished":
                pbar.update(100 - pbar.n)
                break
            elif status == "failed":
                print("\n导出失败")
                return False
            elif status == "none":
                print("\n项目未找到或无权访问")
                return False
            
            # 更新进度条（假设导出过程大约需要30秒）
            if pbar.n < 90:  # 保留10%给最后的完成状态
                pbar.update(1)
            time.sleep(0.3)  # 更频繁地更新进度条
    
    project_info = get_project_info(project_id)
    if not project_info:
        print("无法获取项目信息")
        return False
    
    success = download_export(project_id, project_info, OUTPUT_DIR)
    
    # 导出完成后删除项目列表文件
    try:
        from config import GITLAB_URL
        domain = GITLAB_URL.split('://')[1].replace(':', '_')
        filename = f"{domain}.yaml"
        filepath = os.path.join("projects", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"删除项目列表文件时出错: {str(e)}")
    
    return success 