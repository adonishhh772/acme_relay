# Runbook: agent tool failures

## Symptoms

- Chat answers lack facts / groundedness fails
- `GET /api/mcp/status` shows `reachable=false` or `agent_tools_loaded=false`
- Langfuse shows tool spans with errors

## Checks

1. `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/mcp/status`
2. `docker compose ps mcp-domain mcp-filesystem mcp-postgres`
3. API logs for `MCP tool load failed`
4. Confirm `ENABLE_MCP_AGENT_TOOLS=true` and MCP URLs resolve inside the API container

## Mitigations

- Restart MCP sidecars; API warm-up retries 3 times on load
- Disable MCP temporarily: `ENABLE_MCP_AGENT_TOOLS=false` (native tools still work)
- For Postgres MCP failures, verify SELECT-only queries and DB connectivity
