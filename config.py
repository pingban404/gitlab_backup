import os
import yaml

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