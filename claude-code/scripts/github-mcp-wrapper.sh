#!/bin/bash
# Wrapper to launch GitHub MCP server with dynamic token from gh CLI
export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"
exec npx -y @modelcontextprotocol/server-github "$@"
