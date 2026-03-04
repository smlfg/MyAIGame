"""Main Textual application — MyAIGame Portable TUI."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
    Tree,
)
from textual.reactive import reactive
from textual import events

from tui.widgets.focus_bar import FocusBar
from tui.widgets.cost_ticker import CostTicker
from tui.widgets.agent_status import AgentStatus
from tui.providers.claude import ClaudeCodeProvider
from tui.providers.opencode import OpenCodeProvider
from tui.providers.codex import CodexProvider
from tui.skills.engine import SkillEngine
from tui.screens.control_board import ControlBoardScreen


APP_CSS = """
Screen {
    background: #0d1117;
}

/* Focus bar at the top */
FocusBar {
    height: 3;
    background: #161b22;
    border-bottom: solid #30363d;
    padding: 0 2;
    color: #58a6ff;
}

/* Main layout: left chat + right panel */
#main-layout {
    height: 1fr;
}

/* Left: chat area */
#chat-panel {
    width: 2fr;
    border-right: solid #30363d;
}

#chat-log {
    height: 1fr;
    padding: 1 2;
    background: #0d1117;
    scrollbar-color: #30363d #0d1117;
}

/* Right: agent status + file tree */
#right-panel {
    width: 1fr;
    background: #161b22;
}

#right-panel-header {
    height: 3;
    background: #21262d;
    border-bottom: solid #30363d;
    padding: 0 2;
    color: #8b949e;
    content-align: center middle;
}

AgentStatus {
    height: auto;
    min-height: 8;
    border-bottom: solid #30363d;
    padding: 1 2;
}

#file-tree-header {
    height: 2;
    background: #21262d;
    padding: 0 2;
    color: #8b949e;
    border-bottom: solid #30363d;
}

#file-tree {
    height: 1fr;
    padding: 1;
    scrollbar-color: #30363d #161b22;
}

/* Input bar at bottom of chat */
#input-bar {
    height: 3;
    background: #161b22;
    border-top: solid #30363d;
    padding: 0 1;
}

#skill-hint {
    height: 3;
    width: 20;
    color: #484f58;
    content-align: center middle;
    padding: 0 1;
}

#chat-input {
    width: 1fr;
    background: #21262d;
    border: solid #30363d;
    color: #e6edf3;
}

#chat-input:focus {
    border: solid #58a6ff;
}

/* Cost ticker at the very bottom */
#status-bar {
    height: 1;
    background: #21262d;
    border-top: solid #30363d;
}

CostTicker {
    width: 1fr;
    height: 1;
    color: #3fb950;
    background: #21262d;
    padding: 0 2;
}

/* Welcome message styling */
.welcome {
    color: #58a6ff;
}

.system-msg {
    color: #8b949e;
}

.user-msg {
    color: #e6edf3;
}

.assistant-msg {
    color: #7ee787;
}

.error-msg {
    color: #f85149;
}

/* Tree styling */
Tree {
    background: #161b22;
    color: #8b949e;
}

Tree > .tree--cursor {
    background: #1f6feb;
    color: #ffffff;
}
"""


class ChatPanel(Container):
    """Left panel: scrollable chat/conversation area."""

    def compose(self) -> ComposeResult:
        yield RichLog(id="chat-log", markup=True, highlight=True, wrap=True)
        yield Horizontal(
            Static("/ skill", id="skill-hint"),
            Input(placeholder="Message the agent... (/ for skills)", id="chat-input"),
            id="input-bar",
        )


class FileTree(Container):
    """Collapsible file tree in the right panel."""

    def compose(self) -> ComposeResult:
        yield Static(" Files", id="file-tree-header")
        tree = Tree("~/Projekte/MyAIGame", id="file-tree")
        tree.root.expand()
        portable = tree.root.add("portable/")
        portable.add_leaf("SPEC.md")
        portable.add_leaf("deploy.sh")
        skills_node = portable.add("skills/")
        for skill in ["chef", "chef-async", "focus", "research", "test"]:
            skills_node.add_leaf(f"{skill}/SKILL.md")
        codex_node = portable.add("codex/")
        codex_node.add_leaf("config.yaml")
        opencode_node = portable.add("opencode/")
        opencode_node.add_leaf("opencode.json")
        tui_node = tree.root.add("tui/")
        tui_node.add_leaf("app.py")
        tui_node.add_leaf("providers/")
        tui_node.add_leaf("skills/")
        tui_node.add_leaf("widgets/")
        yield tree


class RightPanel(Container):
    """Right panel: agent status + file tree."""

    def compose(self) -> ComposeResult:
        yield Static(" Agents & Files", id="right-panel-header")
        yield AgentStatus()
        yield FileTree()


class MyAIGameApp(App):
    """MyAIGame Portable TUI — Universal AI Coding Assistant."""

    CSS = APP_CSS
    TITLE = "MyAIGame TUI"
    SUB_TITLE = "Universal AI Coding Assistant"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "toggle_right_panel", "Toggle Panel"),
        Binding("ctrl+b", "toggle_control_board", "Control Board"),
        Binding("ctrl+f", "set_focus_goal", "Set Focus"),
        Binding("ctrl+l", "clear_chat", "Clear Chat"),
        Binding("escape", "blur_input", "Blur Input"),
        Binding("tab", "cycle_providers", "Cycle Provider"),
        Binding("f1", "show_help", "Help"),
    ]

    right_panel_visible: reactive[bool] = reactive(True)
    current_provider: reactive[str] = reactive("claude-code")

    def __init__(self):
        super().__init__()
        self.providers = {
            "claude-code": ClaudeCodeProvider(),
            "opencode": OpenCodeProvider(),
            "codex": CodexProvider(),
        }
        self.skill_engine = SkillEngine()
        self.skill_engine.discover_skills()
        self._message_count = 0

    def compose(self) -> ComposeResult:
        yield FocusBar()
        yield Horizontal(
            ChatPanel(id="chat-panel"),
            RightPanel(id="right-panel"),
            id="main-layout",
        )
        yield Horizontal(
            CostTicker(),
            id="status-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Show welcome message on startup."""
        log = self.query_one("#chat-log", RichLog)
        log.write("[bold cyan]MyAIGame Portable TUI v0.1.0[/bold cyan]")
        log.write("[dim]Universal AI Coding Assistant — Claude Code / OpenCode / Codex[/dim]")
        log.write("")
        log.write("[dim]Providers:[/dim]")
        for name, provider in self.providers.items():
            status = provider.health_check()
            icon = "[green]●[/green]" if status["healthy"] else "[red]○[/red]"
            log.write(f"  {icon} [bold]{name}[/bold] — {status['model']}")
        log.write("")

        skills = self.skill_engine.list_skills()
        log.write(f"[dim]Skills loaded:[/dim] [cyan]{len(skills)}[/cyan] skills discovered")
        if skills:
            skill_names = ", ".join(f"[yellow]/{s}[/yellow]" for s in list(skills.keys())[:5])
            log.write(f"  {skill_names}...")
        log.write("")
        log.write("[dim]Type a message or [bold]/skill-name[/bold] to invoke a skill.[/dim]")
        log.write("[dim]Ctrl+F to set focus goal, Ctrl+P to toggle panel.[/dim]")
        log.write("")

        # Focus the input
        self.query_one("#chat-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        if event.input.id != "chat-input":
            return

        text = event.value.strip()
        if not text:
            return

        event.input.value = ""
        log = self.query_one("#chat-log", RichLog)
        self._message_count += 1

        # Display user message
        log.write(f"[bold white]You:[/bold white] {text}")

        # Check for skill invocation
        if text.startswith("/"):
            self._handle_skill(text, log)
        else:
            self._handle_chat(text, log)

        # Update cost ticker
        self.query_one(CostTicker).add_cost(0.002)

    def _handle_skill(self, text: str, log: RichLog) -> None:
        """Handle /skill invocations."""
        parts = text[1:].split(" ", 1)
        skill_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        skill = self.skill_engine.get_skill(skill_name)
        if skill:
            log.write(f"[cyan]Skill:[/cyan] [bold]{skill_name}[/bold] — {skill.get('description', '')}")
            if skill.get("cost_tier"):
                log.write(f"[dim]  Cost tier: {skill['cost_tier']} | Category: {skill.get('category', 'unknown')}[/dim]")
            if args:
                log.write(f"[dim]  Arguments: {args}[/dim]")

            provider = self.providers[self.current_provider]
            response = provider.send_prompt(
                f"[SKILL: {skill_name}] {args or skill.get('description', '')}"
            )
            log.write(f"[green]Agent:[/green] {response['content']}")
        else:
            available = ", ".join(f"/{s}" for s in list(self.skill_engine.list_skills().keys())[:8])
            log.write(f"[red]Unknown skill:[/red] /{skill_name}")
            log.write(f"[dim]Available: {available}[/dim]")

        log.write("")

    def _handle_chat(self, text: str, log: RichLog) -> None:
        """Handle regular chat messages."""
        provider = self.providers[self.current_provider]
        response = provider.send_prompt(text)
        log.write(f"[green]Agent[/green] [dim]({self.current_provider})[/dim]: {response['content']}")
        log.write(f"[dim]  Tokens: {response.get('tokens', 0)} | Cost: ${response.get('cost', 0):.4f}[/dim]")
        log.write("")

    def action_toggle_right_panel(self) -> None:
        """Toggle the right panel visibility."""
        right = self.query_one("#right-panel")
        self.right_panel_visible = not self.right_panel_visible
        right.display = self.right_panel_visible

    def action_set_focus_goal(self) -> None:
        """Set a new focus goal."""
        focus_bar = self.query_one(FocusBar)
        focus_bar.prompt_new_goal()

    def action_clear_chat(self) -> None:
        """Clear the chat log."""
        log = self.query_one("#chat-log", RichLog)
        log.clear()
        log.write("[dim]Chat cleared.[/dim]")
        log.write("")

    def action_blur_input(self) -> None:
        """Blur the input field."""
        self.query_one("#chat-input", Input).blur()

    def action_cycle_providers(self) -> None:
        """Cycle through available providers."""
        provider_list = list(self.providers.keys())
        current_idx = provider_list.index(self.current_provider)
        next_idx = (current_idx + 1) % len(provider_list)
        self.current_provider = provider_list[next_idx]

        log = self.query_one("#chat-log", RichLog)
        log.write(f"[cyan]Provider switched to:[/cyan] [bold]{self.current_provider}[/bold]")
        log.write("")

        agent_status = self.query_one(AgentStatus)
        agent_status.set_active_provider(self.current_provider)

    def action_show_help(self) -> None:
        """Show help in chat."""
        log = self.query_one("#chat-log", RichLog)
        log.write("[bold cyan]Keybindings:[/bold cyan]")
        log.write("  [bold]Ctrl+Q[/bold]  Quit")
        log.write("  [bold]Ctrl+P[/bold]  Toggle right panel")
        log.write("  [bold]Ctrl+F[/bold]  Set focus goal")
        log.write("  [bold]Ctrl+L[/bold]  Clear chat")
        log.write("  [bold]Tab[/bold]     Cycle providers")
        log.write("  [bold]F1[/bold]      Show this help")
        log.write("")
        log.write("[bold cyan]Skill syntax:[/bold cyan]")
        log.write("  [yellow]/chef[/yellow] [dim]<task>[/dim]         Delegate to OpenCode")
        log.write("  [yellow]/research[/yellow] [dim]<query>[/dim]    Web research via Gemini")
        log.write("  [yellow]/focus[/yellow] [dim]<goal>[/dim]        Set focus session goal")
        log.write("  [yellow]/test[/yellow] [dim]<scope>[/dim]        Run test crew")
        log.write("  [yellow]/swarm[/yellow] [dim]<task>[/dim]        Multi-agent swarm")
        log.write("")

    def action_toggle_control_board(self) -> None:
        """Toggle the Control Board overlay screen."""
        if isinstance(self.screen, ControlBoardScreen):
            self.pop_screen()
        else:
            self.push_screen(ControlBoardScreen())
