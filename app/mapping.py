import yaml, os
from typing import Optional
from .settings import EPIC_ASANA_MAP_PATH

def asana_project_for_epic(epic_key: str) -> Optional[str]:
    if not os.path.exists(EPIC_ASANA_MAP_PATH):
        return None
    with open(EPIC_ASANA_MAP_PATH, "r") as f:
        data = yaml.safe_load(f) or {}
    return data.get(epic_key)

