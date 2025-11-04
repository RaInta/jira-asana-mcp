import os

JIRA_BASE = os.getenv("JIRA_BASE")                 # e.g. https://yourcompany.atlassian.net
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")               # Jira PAT or OAuth token

ASANA_BASE = "https://app.asana.com/api/1.0"
ASANA_TOKEN = os.getenv("ASANA_TOKEN")

# Jira story points custom field (commonly customfield_10016, but varies)
JIRA_STORY_POINTS_FIELD = os.getenv("JIRA_STORY_POINTS_FIELD", "customfield_10016")

# Parent linkage: try both "parent = FEATURE-123" and "Parent Link" advanced-roadmaps field
JIRA_PARENT_LINK_FIELD = os.getenv("JIRA_PARENT_LINK_FIELD", '"Parent Link"')

# Optional YAML mapping for Epic→Asana project fallback
EPIC_ASANA_MAP_PATH = os.getenv("EPIC_ASANA_MAP_PATH", "mappings/epic_asana_map.yaml")

# A designated “Progress Log” task name inside each Asana project (optional)
ASANA_PROGRESS_LOG_TASK_NAME = os.getenv("ASANA_PROGRESS_LOG_TASK_NAME", "Progress Log")

