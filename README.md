# Jira to Asana MCP Bridge

Do you manage projects using **Jira** but need to keep stakeholders updated in **Asana**?

If so, then I completely feel your pain! This is a lightweight **Model Context Protocol (MCP)** server (HTTP variant) that synchronizes **Jira** feature progress with **Asana** project status updates.  

Designed for enterprise environments running **VS Code**, and **GitHub**, this bridge lets development or PMO teams keep portfolio visibility in Asana while maintaining Jira as the single source of truth.

---

## Features

- **Read-only integration from Jira to Asana**
  - Computes two-week progress snapshots at the *Feature* level (based on User Story completion and Story Points).
  - Rolls up multiple Features under a single *Epic* (this may depend on how your organization models work items in Jira).
- **Automatic Asana project status updates**
  - Posts clean, markdown-formatted summaries with color-coded status (green / yellow / red).
  - Optionally logs updates to a “Progress Log” task in the Asana project.
- **HTTP MCP-compatible**
  - Exposes both *resources* (for read-only queries) and *tools* (for controlled writes) over REST.
  - Can be called directly from VS Code’s MCP client or an LLM agent.
- **Secure and auditable**
  - Jira and Asana tokens passed via environment variables or Azure Key Vault.
  - Read-only by design; no writes to Jira.
  - Easily containerized and deployed to Azure Container Apps or AKS.

---

## Architecture Overview

```text
                ┌──────────────────────────┐
                │  VS Code / MCP Client    │
                └─────────────┬────────────┘
                              │ HTTP (JSON)
                ┌─────────────▼────────────┐
                │    jira-asana-mcp        │
                │  (FastAPI + MCP facade)  │
                └──────┬────────┬──────────┘
                       │        │
           ┌───────────▼───┐ ┌──▼────────────┐
           │ Jira Cloud API│ │ Asana REST API│
           └───────────────┘ └───────────────┘
```

  * Resources
    /resources/jira/feature/{feature_key}/progress

    /resources/jira/epic/{epic_key}/rollup

  * Tools

    /tools/post_asana_project_status

    /tools/sync_one_feature

```bash
jira-asana-mcp/
├─ app/
│  ├─ server.py              # FastAPI + MCP HTTP layer
│  ├─ jira_client.py         # Jira REST wrapper
│  ├─ asana_client.py        # Asana REST wrapper
│  ├─ logic.py               # Story-point math, markdown rendering
│  ├─ mapping.py             # Epic-to-Project map utilities
│  └─ settings.py            # Env configuration
├─ mappings/
│  └─ epic_asana_map.yaml    # Optional static mapping
├─ Dockerfile
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Quick Start (Local)

```bash
git clone https://github.com/RaInta/jira-asana-mcp.git
cd jira-asana-mcp
cp .env.example .env
```

Edit `.env` to add your Jira and Asana tokens. Make sure `.env` is in your `.gitignore`! This is set up by default in this repo.

```bash
JIRA_BASE=https://yourcompany.atlassian.net
JIRA_EMAIL=svc-jira@yourcompany.com
JIRA_TOKEN=***************
ASANA_TOKEN=1/***************
JIRA_STORY_POINTS_FIELD=customfield_10016
JIRA_PARENT_LINK_FIELD="Parent Link"
```

Build and run in Docker:

```bash
docker build -t jira-asana-mcp:local .
docker run --env-file .env -p 8080:8080 jira-asana-mcp:local
```

Server listens on port 8080.

## Usage

Get progress for one Feature

```bash
curl http://localhost:8080/resources/jira/feature/FEATURE-123/progress
```

Roll up all Features under an Epic

```bash
curl http://localhost:8080/resources/jira/epic/EPIC-456/rollup
``` 

Post a two-week Asana status update

```bash
curl -X POST "http://localhost:8080/tools/post_asana_project_status" \
  -H "Content-Type: application/json" \
  -d '{
        "epic_key": "EPIC-123",
        "asana_project_gid": "12001234567890"
      }'
```

The tool will:
  * Collect all Features under EPIC-123.
  * Count completed Story Points within the last 14 days.
  * Compute percentage complete and render markdown.
  * Post a new Project Status in Asana.

## VS Code MCP Integration

1. Install the [MCP Client extension](https://marketplace.visualstudio.com/items?itemName=rainta.mcp-client) in VS Code.

Add this block to your .vscode/settings.json:

```json
{
  "mcpServers": {
    "jira-asana-bridge": {
      "type": "http",
      "baseUrl": "http://localhost:8080",
      "tools": {
        "post_asana_project_status": { "path": "/tools/post_asana_project_status", "method": "POST" },
        "sync_one_feature": { "path": "/tools/sync_one_feature", "method": "POST" }
      },
      "resources": {
        "jira-feature-progress": { "path": "/resources/jira/feature/{feature_key}/progress" },
        "jira-epic-rollup": { "path": "/resources/jira/epic/{epic_key}/rollup" }
      }
    }
  }
}
```

Then you can query or trigger tools directly through the MCP interface.

## Deployment (Azure Container Apps)

```bash
az acr create -g my-rg -n myacr --sku Basic
docker tag jira-asana-mcp:local myacr.azurecr.io/jira-asana-mcp:v1
docker push myacr.azurecr.io/jira-asana-mcp:v1

az containerapp create \
  -g my-rg -n jira-asana-mcp \
  --environment my-env \
  --image myacr.azurecr.io/jira-asana-mcp:v1 \
  --target-port 8080 --ingress internal \
  --env-vars-file .env
```

  * Set ingress to **internal** for security.
  * Use Azure Key Vault to inject `JIRA_TOKEN` and `ASANA_TOKEN`.

## Configuration Options

| Variable                       | Description                                     |
| ------------------------------ | ----------------------------------------------- |
| `JIRA_BASE`                    | Jira Cloud base URL                             |
| `JIRA_EMAIL`                   | Jira service account email                      |
| `JIRA_TOKEN`                   | Jira API token                                  |
| `ASANA_TOKEN`                  | Asana personal access token                     |
| `JIRA_STORY_POINTS_FIELD`      | Custom field ID for Story Points                |
| `JIRA_PARENT_LINK_FIELD`       | Field name for parent (usually `"Parent Link"`) |
| `EPIC_ASANA_MAP_PATH`          | YAML mapping file for Epic → Asana project      |
| `ASANA_PROGRESS_LOG_TASK_NAME` | Optional task name for logging updates          |

## Security & Governance

  * Read-only Jira access — no write operations.
  * Scoped Asana PAT limited to posting project status updates.
  * Auditability — all tool calls logged; pair with your standard observability stack.
  * Deployment options — run locally, in Azure Container Apps, or on AKS behind an internal ingress.

## Status Logic

  1. Collect stories under each Feature.
  1. Compute totals:
       *  Total story points.
       *  Story points completed in the two-week window.
  1. Aggregate across all Features under an Epic.
  1. Render markdown table and post Asana Project Status:
     *  🟢 Green ≥ 60 %
     *  🟡 Yellow 20–59 %
     *  🔴 Red < 20 %

## Automation

You can run this automatically e.g. every second Friday via GitHub Actions:

```yaml
name: Post Asana Status
on:
  schedule:
    - cron: '0 22 * * 5'   # 22:00 UTC ≈ 16:00 CT
jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - name: Post fortnightly Asana status
        run: |
          curl -X POST "$MCP_BASE/tools/post_asana_project_status" \
            -H "Content-Type: application/json" \
            -d "{\"epic_key\":\"EPIC-123\",\"asana_project_gid\":\"12001234567890\"}"
        env:
          MCP_BASE: https://internal-gateway/jira-asana-mcp
```

## Future Enhancements

  * Support for additional Jira work item types (e.g. Initiatives).
  * More granular progress
  * Sprint-aware window detection (use latest closed Jira Sprint dates).
  * Idempotent updates (update existing Asana status entries instead of creating duplicates).
  * Dynamic Asana project lookup by `jira_epic_key` custom field.
  * Integration with internal Alana agent for conversational reporting. But that seems to suck at the moment, so maybe not.

## License

Apache 2.0 License. See LICENSE file in repo.

---

## Appendix: Getting Developer API Keys (Enterprise SSO)

This is largely because I keep forgetting how to do this myself!

### Jira Cloud API Token (Atlassian)
1. Go to **https://id.atlassian.com/manage-profile/security/api-tokens**  
   (You may need to open this in a private window if SSO is enforced.)
2. Click **Create API Token**. Give it a name like `jira-asana-mcp`.
3. Copy the token.
4. In `.env`, set:
```bash
JIRA_EMAIL=<your Atlassian user email>
JIRA_TOKEN=<copied token>
```
5. Confirm your service account has read access to the Jira Projects and Epics being queried.

> If your organization restricts personal tokens via SSO (Okta/AzureAD), ask your Jira admin to create a service account with API token and limited “read-only” permissions.

### Asana Personal Access Token (PAT)

  1. Navigate to `https://app.asana.com/0/developer-console`  (You may need to be an Asana Admin or Workspace Owner.)
  1. Under "Personal Access Tokens", click `Create new token`.
  1. Give it a descriptive name, e.g. `jira-asana-mcp`.
  1. Copy the generated token and add to `.env`:
```bash
  ASANA_TOKEN=1/<your token here>
```
  1. Ensure the PAT has sufficient scopes to post Project Status updates (at least `Edit Project Status` permission).

> For enterprise SSO-managed accounts, Asana may require token creation through an admin-controlled service account. Request one via your Asana admin panel if token creation is disabled.

### Recommended Practice

  * Store tokens in Azure Key Vault and inject at runtime (instead of committing to `.env` files).
  * Rotate both Jira and Asana tokens every 90 days (or less, if you're sufficiently paranoid).
  * Keep all service accounts documented in your internal access registry.

---



