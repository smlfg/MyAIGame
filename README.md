# MAS Live-Dashboard

Real-time monitoring dashboard for Multi-Agent Systems. Watch your AI agents work — track costs, tokens, timelines, and delegation flows as they happen.

Built with **Streamlit** + **Plotly**. Reads session data from **Claude Code** and **OpenCode** automatically.

## Views

### War Room
Live status board with one card per agent (Opus, Sonnet, Haiku, Flash, MiniMax). Shows active/idle state, per-agent costs, token counts, and last action — updates in real-time.

### Timeline
Swimlane chart showing agent activity over time. Each event is a bar on its agent's lane with hover details (tokens, cost, tool called). Scrollable event list below.

### Cost Analysis
Three tabs:
- **Sankey Diagram** — Token flow from User to Agents
- **Cumulative Cost** — Stacked area chart of spend over time per agent
- **Heatmap** — Cost intensity in 5-minute buckets per agent

### Storyboard
Narrative markdown view of the session — what happened, when, and at what cost. Generates a Mermaid sequence diagram of the delegation flow. Exportable as Markdown.

## Supported Agents & Pricing

| Agent | Input $/1M tokens | Output $/1M tokens |
|-------|-------------------:|--------------------:|
| Opus | $15.00 | $75.00 |
| Sonnet | $3.00 | $15.00 |
| Haiku | $0.25 | $1.25 |
| Flash (Gemini) | $0.075 | $0.30 |
| MiniMax | $0.10 | $0.30 |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The dashboard auto-detects active Claude Code and OpenCode sessions. Use the sidebar to select specific sessions or enable auto-refresh.

## Data Sources

- **Claude Code** — Parses JSONL session files from `~/.claude/projects/`
- **OpenCode** — Polls session data via OpenCode's local storage

No API keys needed. All data is read locally from your existing coding sessions.

## Project Structure

```
app.py                   # Streamlit entry point + routing
data/
  models.py              # AgentEvent dataclass
  pricing.py             # Per-model token pricing
  claude_watcher.py      # Claude Code JSONL parser
  opencode_poller.py     # OpenCode session reader
  loader.py              # Unified event loader + session discovery
views/
  warroom.py             # Live agent status cards
  timeline.py            # Plotly swimlane timeline
  sankey_costs.py        # Sankey + cumulative cost + heatmap
  storyboard.py          # Narrative + Mermaid export
components/
  shared.py              # Session picker, formatters, color map
```

## Requirements

- Python 3.11+
- Streamlit >= 1.40
- Plotly >= 5.24
- pandas >= 2.2

## License

Part of [MyAIGame](https://github.com/smlfg/MyAIGame).
