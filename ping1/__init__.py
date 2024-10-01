import logging
import os

from rich.logging import RichHandler
import yaml


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO, handlers=[RichHandler()])
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)


def config(key):
    yaml_file_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            config = yaml.safe_load(file)
        
        return config.get(key) if config else None
    except FileNotFoundError:
        print(f"Config file not found at {yaml_file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    

token = config("token")