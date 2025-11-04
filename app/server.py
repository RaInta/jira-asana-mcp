# FastAPI server + MCP adapter

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok"}

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dateutil import parser as dateparser

from .jira_client import get_epic_features, get_feature_stories
from .asana_client import create_project_status, ensure_progress_log_task, add_task_comment
from .logic import default_window, feature_progress, render_project_status_markdown
from .mapping import asana_project_for_epic

app = FastAPI(title="jira-asana-bridge")

class WindowArgs(BaseModel):
    window_start: Optional[str] = None
    window_end: Optional[str] = None

def parse_window(window_start: Optional[str], window_end: Optional[str]) -> Tuple[datetime, datetime]:
    if window_start and window_end:
        s = dateparser.parse(window_start)
        e = dateparser.parse(window_end)
        if e < s:
            raise HTTPException(400, "window_end must be >= window_start")
        return s, e
    return default_window()

# ---- RESOURCES ----

@app.get("/resources/jira/feature/{feature_key}/progress")
async def resource_feature_progress(feature_key: str, window_start: Optional[str] = None, window_end: Optional[str] = None):
    start, end = parse_window(window_start, window_end)
    stories = await get_feature_stories(feature_key)
    snap = feature_progress(feature_key, stories, start, end)
    return {"data": snap, "window": {"start": start.isoformat(), "end": end.isoformat()}}

@app.get("/resources/jira/epic/{epic_key}/rollup")
async def resource_epic_rollup(epic_key: str, window_start: Optional[str] = None, window_end: Optional[str] = None):
    start, end = parse_window(window_start, window_end)
    features = await get_epic_features(epic_key)
    rows = []
    for f in features:
        fkey = f["key"]
        stories = await get_feature_stories(fkey)
        rows.append(feature_progress(fkey, stories, start, end))
    return {"data": rows, "window": {"start": start.isoformat(), "end": end.isoformat()}}

# ---- TOOLS ----

class PostStatusArgs(BaseModel):
    epic_key: str
    asana_project_gid: Optional[str] = None
    window_start: Optional[str] = None
    window_end: Optional[str] = None

@app.post("/tools/post_asana_project_status")
async def post_asana_project_status(args: PostStatusArgs):
    start, end = parse_window(args.window_start, args.window_end)
    project_gid = args.asana_project_gid or asana_project_for_epic(args.epic_key)
    if not project_gid:
        raise HTTPException(400, "Asana project GID not provided and no mapping found.")

    features = await get_epic_features(args.epic_key)
    if not features:
        raise HTTPException(404, f"No Features found under Epic {args.epic_key}")

    rows = []
    for f in features:
        fkey = f["key"]
        stories = await get_feature_stories(fkey)
        rows.append(feature_progress(fkey, stories, start, end))

    title, text, color = render_project_status_markdown(args.epic_key, (start, end), rows)
    status = await create_project_status(project_gid, title, text, color=color)

    # Optional: also drop a line into a “Progress Log” task
    try:
        log_task = await ensure_progress_log_task(project_gid)
        await add_task_comment(log_task, f"Posted status **{title}**\n\n{text}")
    except Exception:
        pass

    return {"ok": True, "project_gid": project_gid, "status_id": status["gid"], "color": color}

class SyncFeatureArgs(BaseModel):
    feature_key: str
    asana_project_gid: str
    window_start: Optional[str] = None
    window_end: Optional[str] = None

@app.post("/tools/sync_one_feature")
async def sync_one_feature(args: SyncFeatureArgs):
    start, end = parse_window(args.window_start, args.window_end)
    stories = await get_feature_stories(args.feature_key)
    snap = feature_progress(args.feature_key, stories, start, end)
    log_task = await ensure_progress_log_task(args.asana_project_gid)
    text = (f"Feature {args.feature_key} — {start.date()} → {end.date()}\n\n"
            f"Stories done/total: {snap['stories_done_in_window']}/{snap['stories_total']}\n"
            f"SP done/total: {snap['story_points_done_in_window']:.1f}/{snap['story_points_total']:.1f}\n"
            f"% complete: {snap['percent_complete_by_sp']:.1f}%")
    await add_task_comment(log_task, text)
    return {"ok": True, "feature": snap}
