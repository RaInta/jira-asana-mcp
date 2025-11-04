from datetime import date, datetime, timedelta
from dateutil import tz
from typing import Dict, List, Tuple, Any
from .settings import JIRA_STORY_POINTS_FIELD

def default_window(today: date | None = None) -> Tuple[datetime, datetime]:
    """Last full 14-day window ending yesterday (local time)."""
    tzinfo = tz.tzlocal()
    today = today or date.today()
    end = datetime.combine(today, datetime.min.time()).replace(tzinfo=tzinfo)  # midnight today
    end -= timedelta(seconds=1)  # “yesterday 23:59:59”
    start = end - timedelta(days=13)  # inclusive 14 days
    # Normalize to start-of-day:
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=0)
    return start, end

def _sp(issue: Dict[str, Any]) -> float:
    f = issue.get("fields", {})
    val = f.get(JIRA_STORY_POINTS_FIELD)
    try:
        return float(val) if val is not None else 0.0
    except:
        return 0.0

def feature_progress(feature_key: str, stories: List[Dict[str, Any]], start: datetime, end: datetime) -> Dict[str, Any]:
    total_sp = sum(_sp(i) for i in stories)
    done_sp = 0.0
    done_count = 0
    for i in stories:
        fields = i["fields"]
        status_cat = fields.get("status", {}).get("statusCategory", {}).get("name") or fields.get("status", {}).get("statusCategory", {}).get("key")
        res_date = fields.get("resolutiondate")
        sp = _sp(i)
        if status_cat and str(status_cat).lower() in ("done", "complete") and res_date:
            try:
                rdt = datetime.fromisoformat(res_date.replace("Z", "+00:00"))
                if start <= rdt <= end:
                    done_sp += sp
                    done_count += 1
            except Exception:
                pass
    pct = (done_sp / total_sp * 100.0) if total_sp > 0 else 0.0
    return {
        "feature_key": feature_key,
        "stories_total": len(stories),
        "stories_done_in_window": done_count,
        "story_points_total": total_sp,
        "story_points_done_in_window": done_sp,
        "percent_complete_by_sp": pct
    }

def render_project_status_markdown(epic_key: str, window: Tuple[datetime, datetime], feature_rows: List[Dict[str, Any]]) -> Tuple[str, str]:
    start, end = window
    total_sp = sum(r["story_points_total"] for r in feature_rows)
    done_sp = sum(r["story_points_done_in_window"] for r in feature_rows)
    pct = (done_sp / total_sp * 100.0) if total_sp else 0.0

    def fmt(dt: datetime) -> str:
        # ISO-like date without TZ noise
        return dt.strftime("%Y-%m-%d")

    title = f"{epic_key}: {fmt(start)} → {fmt(end)} progress"
    lines = []
    lines.append(f"*Window:* {fmt(start)} to {fmt(end)}")
    lines.append(f"*Epic:* {epic_key}")
    lines.append("")
    lines.append(f"*Story Points done this window:* **{done_sp:.1f} / {total_sp:.1f}** ({pct:.1f}%)")
    lines.append("")
    lines.append("| Feature | Stories (done/total) | SP (done/total) | % complete |")
    lines.append("|---|---:|---:|---:|")
    for r in feature_rows:
        lines.append(f"| {r['feature_key']} | {r['stories_done_in_window']}/{r['stories_total']} | {r['story_points_done_in_window']:.1f}/{r['story_points_total']:.1f} | {r['percent_complete_by_sp']:.1f}% |")
    text = "\n".join(lines)

    color = "green"
    if pct < 20:
        color = "red"
    elif pct < 60:
        color = "yellow"
    return title, text, color

