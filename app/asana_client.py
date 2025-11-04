import httpx
from typing import Any, Dict, List, Optional
from .settings import ASANA_BASE, ASANA_TOKEN, ASANA_PROGRESS_LOG_TASK_NAME

HEADERS = {"Authorization": f"Bearer {ASANA_TOKEN}"}

async def get_project(gid: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=ASANA_BASE, headers=HEADERS) as c:
        r = await c.get(f"/projects/{gid}")
        r.raise_for_status()
        return r.json()["data"]

async def list_project_sections(project_gid: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(base_url=ASANA_BASE, headers=HEADERS) as c:
        r = await c.get(f"/projects/{project_gid}/sections")
        r.raise_for_status()
        return r.json()["data"]

async def create_project_status(project_gid: str, title: str, text: str, color: str = "green") -> Dict[str, Any]:
    # color one of: green, yellow, red
    payload = {"data": {"title": title, "text": text, "color": color}}
    async with httpx.AsyncClient(base_url=ASANA_BASE, headers=HEADERS) as c:
        r = await c.post(f"/projects/{project_gid}/project_statuses", json=payload)
        r.raise_for_status()
        return r.json()["data"]

async def search_tasks(project_gid: str, text: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    params = {"project": project_gid, "limit": limit}
    if text:
        params["text"] = text
    async with httpx.AsyncClient(base_url=ASANA_BASE, headers=HEADERS) as c:
        r = await c.get("/tasks", params=params)
        r.raise_for_status()
        return r.json().get("data", [])

async def ensure_progress_log_task(project_gid: str) -> Optional[str]:
    tasks = await search_tasks(project_gid, text=ASANA_PROGRESS_LOG_TASK_NAME, limit=25)
    if tasks:
        return tasks[0]["gid"]
    # create one (optional)
    payload = {"data": {"name": ASANA_PROGRESS_LOG_TASK_NAME, "projects": [project_gid]}}
    async with httpx.AsyncClient(base_url=ASANA_BASE, headers=HEADERS) as c:
        r = await c.post("/tasks", json=payload)
        r.raise_for_status()
        return r.json()["data"]["gid"]

async def add_task_comment(task_gid: str, text: str) -> Dict[str, Any]:
    payload = {"data": {"text": text}}
    async with httpx.AsyncClient(baseURL=ASANA_BASE, headers=HEADERS) as c:
        r = await c.post(f"/tasks/{task_gid}/stories", json=payload)
        r.raise_for_status()
        return r.json()["data"]
