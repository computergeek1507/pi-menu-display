import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def load_config() -> dict:
    config_path = BASE_DIR / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
