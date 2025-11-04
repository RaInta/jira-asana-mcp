import httpx
from typing import Any, Dict, List, Optional
from .settings import JIRA_BASE, JIRA_EMAIL, JIRA_TOKEN, JIRA_STORY_POINTS_FIELD, JIRA_PARENT_LINK_FIELD

HEADERS = {
    "Authorization": f"Basic {httpx._auth._basic_auth_str(JIRA_EMAIL, JIRA_TOKEN)}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

async def get_issue(key: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=JIRA_BASE) as c:
        r = await c.get(f"/rest/api/3/issue/{key}?expand=names")
        r.raise_for_status()
        return r.json()

async def search_jql(jql: str, fields: Optional[List[str]] = None, max_results: int = 1000) -> List[Dict[str, Any]]:
    params = {"jql": jql, "maxResults": max_results}
    if fields:
        params["fields"] = ",".join(fields)
    async with httpx.AsyncClient(base_url=JIRA_BASE) as c:
        r = await c.get("/rest/api/3/search", params=params, headers=HEADERS)
        r.raise_for_status()
        return r.json().get("issues", [])

async def get_feature_stories(feature_key: str) -> List[Dict[str, Any]]:
    """
    Try two linkage patterns:
      1) parent = FEATURE-123
      2) "Parent Link" = FEATURE-123 (Advanced Roadmaps)
    """
    base_fields = ["summary", "issuetype", "status", "resolutiondate", JIRA_STORY_POINTS_FIELD]
    jql_parent = f'parent = "{feature_key}" AND issuetype in (Story, Task, "User Story")'
    issues = await search_jql(jql_parent, fields=base_fields)
    if not issues:
        jql_link = f'{JIRA_PARENT_LINK_FIELD} = "{feature_key}" AND issuetype in (Story, Task, "User Story")'
        issues = await search_jql(jql_link, fields=base_fields)
    return issues

async def get_epic_features(epic_key: str) -> List[Dict[str, Any]]:
    # Many orgs use Advanced Roadmaps: Features are children of Epics via "Parent Link"
    fields = ["summary", "issuetype", "status", "resolutiondate"]
    jql = f'{JIRA_PARENT_LINK_FIELD} = "{epic_key}" AND issuetype in (Feature)'
    return await search_jql(jql, fields=fields)

