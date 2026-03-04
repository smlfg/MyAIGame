# TUI Provider Abstraction Layer

> Python interfaces that let the TUI talk to Claude Code, Codex, and OpenCode
> through a single, unified API — regardless of which backend is running.

---

## Design Philosophy

The TUI knows nothing about Claude Code internals. It only knows:
- "Send this prompt, stream the response"
- "Can this backend spawn sub-agents?"
- "How much will this cost?"
- "Is this backend healthy?"

Every backend implements the same contract. The TUI picks one at startup and
never changes its call sites. Swapping backends is a config change, not a code change.

---

## 1. Core Data Types

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Any
import asyncio


class HealthStatus(Enum):
    OK = "ok"
    DEGRADED = "degraded"      # Running but slower than expected
    UNAVAILABLE = "unavailable"  # Cannot connect at all
    UNKNOWN = "unknown"


class CostTier(Enum):
    FREE = "free"
    MINIMAL = "minimal"   # < $0.05
    LOW = "low"           # $0.05 - $0.30
    MEDIUM = "medium"     # $0.30 - $1.00
    HIGH = "high"         # $1.00 - $5.00
    VARIABLE = "variable" # Scales with input


@dataclass
class ProviderCapabilities:
    """What a backend can and cannot do. Used by the skill router."""
    # Core features
    supports_streaming: bool = True
    supports_subagents: bool = False
    supports_sandbox: bool = False      # Isolated execution environment
    supports_hooks: bool = False        # Pre/post execution hooks
    supports_mcp: bool = False          # Can call MCP servers

    # Skill-relevant capabilities (maps to SPEC.md tool abstractions)
    supports_delegate_code: bool = True
    supports_delegate_code_async: bool = False
    supports_research: bool = False     # Built-in web search / Gemini
    supports_voice: bool = False

    # Resource limits
    max_context_tokens: int = 200_000
    max_output_tokens: int = 8_000
    max_concurrent_sessions: int = 1

    # Pricing (per 1M tokens, USD)
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0


@dataclass
class CostEstimate:
    """Best-effort cost estimate before sending a prompt."""
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_usd: float
    tier: CostTier
    confidence: float  # 0.0 - 1.0; low confidence = wide variance possible
    note: str = ""    # Human-readable caveat (e.g. "subagents add cost")


@dataclass
class AgentConfig:
    """Configuration for spawning a sub-agent."""
    role: str                          # e.g. "researcher", "executor"
    model: str | None = None           # Override default model
    prompt: str = ""
    working_directory: str | None = None
    max_tokens: int | None = None
    background: bool = True            # Non-blocking spawn?
    tools: list[str] = field(default_factory=list)  # Allowed tool names


@dataclass
class AgentHandle:
    """Reference to a running sub-agent. Backend-specific ID is opaque."""
    agent_id: str
    role: str
    is_background: bool
    provider_metadata: dict[str, Any] = field(default_factory=dict)

    async def wait(self) -> str:
        """Block until agent completes. Returns final output."""
        raise NotImplementedError

    async def get_status(self) -> str:
        """Non-blocking status check. Returns human-readable status string."""
        raise NotImplementedError


@dataclass
class ToolResult:
    """Result of executing an abstract tool call."""
    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    duration_ms: int = 0
```

---

## 2. AgentProvider — The Abstract Base

```python
class AgentProvider(ABC):
    """
    Base interface all AI coding backends must implement.

    A provider wraps one backend (Claude Code CLI, Codex CLI, or OpenCode MCP)
    and exposes a unified async interface to the TUI. Streaming is the default
    for all text responses — the TUI renders tokens as they arrive.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name. e.g. 'Claude Code', 'Codex', 'OpenCode'"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Detected version string of the underlying CLI/server."""
        ...

    # ------------------------------------------------------------------
    # Core interaction
    # ------------------------------------------------------------------

    @abstractmethod
    async def send_prompt(
        self,
        prompt: str,
        context: dict[str, Any],
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Send a prompt and stream the response token by token.

        Args:
            prompt: The user's input or skill-generated prompt.
            context: Arbitrary context dict (working_dir, skill_name, etc.)
            session_id: Continue an existing conversation if provided.

        Yields:
            Text chunks as they arrive from the backend.

        Raises:
            ProviderUnavailableError: Backend is not reachable.
            ProviderTimeoutError: Response stalled > timeout threshold.
        """
        ...

    @abstractmethod
    async def spawn_agent(self, config: AgentConfig) -> AgentHandle:
        """
        Spawn a sub-agent with its own context.

        The returned AgentHandle is opaque — callers use .wait() or
        .get_status() without knowing backend internals.

        Raises:
            CapabilityNotSupportedError: If supports_subagents is False.
        """
        ...

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
    ) -> ToolResult:
        """
        Execute an abstract tool by name (maps to SPEC.md tool abstractions).

        tool_name matches the abstract tool table in SPEC.md Section 4.2:
        'delegate_code', 'research', 'shell', 'read_file', etc.

        The provider maps tool_name to its backend-specific implementation.
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """
        Return what this backend can do. Called at startup by the skill router
        to determine which skills are available.

        Should be fast and synchronous — no network calls.
        """
        ...

    @abstractmethod
    async def get_cost_estimate(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> CostEstimate:
        """
        Estimate cost before sending. Used by the TUI cost dashboard.

        Implementations may use local token counting (tiktoken) for speed.
        No network call required.
        """
        ...

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """
        Quick liveness check. Should complete in < 2 seconds.

        The TUI polls this every 30s to show backend status in the header.
        """
        ...

    # ------------------------------------------------------------------
    # Session management (optional override)
    # ------------------------------------------------------------------

    async def create_session(self, title: str = "") -> str:
        """
        Create a new named conversation session.

        Returns:
            session_id: Opaque string identifying this session.

        Default implementation: returns a UUID (stateless providers).
        Stateful backends override this.
        """
        import uuid
        return str(uuid.uuid4())

    async def end_session(self, session_id: str) -> None:
        """
        Clean up a session. Default: no-op for stateless backends.
        """
        pass

    async def list_sessions(self) -> list[dict[str, Any]]:
        """
        List active sessions with metadata.
        Returns empty list if sessions are not supported.
        """
        return []
```

---

## 3. Three Concrete Implementations

### 3.1 ClaudeCodeProvider — Wraps the `claude` CLI

```python
import subprocess
import asyncio
import json
import tiktoken
from pathlib import Path


class ClaudeCodeProvider(AgentProvider):
    """
    Wraps the `claude` CLI via subprocess with stdin/stdout streaming.

    Claude Code runs as a persistent process. We communicate via:
    - stdin: JSON-encoded messages
    - stdout: Streaming token chunks (Server-Sent Events format)

    Sessions map to Claude Code's conversation history (in-process).
    """

    def __init__(self, claude_bin: str = "~/.local/bin/claude"):
        self._claude_bin = Path(claude_bin).expanduser()
        self._sessions: dict[str, subprocess.Popen] = {}  # session_id -> process
        self._encoder = tiktoken.get_encoding("cl100k_base")

    @property
    def name(self) -> str:
        return "Claude Code"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run(
                [str(self._claude_bin), "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    async def send_prompt(
        self,
        prompt: str,
        context: dict[str, Any],
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream response from claude CLI via subprocess."""
        cmd = [
            str(self._claude_bin),
            "--print",            # Non-interactive mode
            "--output-format", "stream-json",
        ]

        working_dir = context.get("working_directory", str(Path.home()))
        if session_id and session_id in self._sessions:
            # Continue existing session by passing conversation file
            cmd += ["--resume", session_id]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )

        # Write prompt to stdin
        proc.stdin.write(prompt.encode())
        await proc.stdin.drain()
        proc.stdin.close()

        # Stream stdout line by line, parse SSE JSON
        async for line in proc.stdout:
            line = line.decode().strip()
            if not line or line.startswith(":"):
                continue
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                    if chunk := event.get("content", ""):
                        yield chunk
                except json.JSONDecodeError:
                    yield line  # Fallback: yield raw

        await proc.wait()

    async def spawn_agent(self, config: AgentConfig) -> AgentHandle:
        """Spawn via Task tool (Haiku model) — maps to SPEC.md 'subagent' engine."""
        # Claude Code spawns sub-agents via its Task tool internally.
        # We trigger this by sending a special prompt that invokes the Task tool.
        prompt = f"""Use the Task tool to spawn a background sub-agent:
- Role: {config.role}
- Model: {config.model or 'claude-haiku-4-5-20251001'}
- Task: {config.prompt}
- Working dir: {config.working_directory or '.'}
- Background: {config.background}

Return the task ID on completion."""

        session_id = await self.create_session(f"subagent-{config.role}")
        agent_id = f"claude-subagent-{session_id}"

        # Fire the spawn asynchronously
        asyncio.create_task(
            self._consume_stream(
                self.send_prompt(prompt, {"working_directory": config.working_directory})
            )
        )

        return ClaudeCodeAgentHandle(
            agent_id=agent_id,
            role=config.role,
            is_background=config.background,
            provider=self,
        )

    async def execute_tool(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """Map abstract tool names (SPEC.md Section 4.2) to Claude Code equivalents."""
        tool_map = {
            "shell": self._exec_shell,
            "read_file": self._exec_read_file,
            "write_file": self._exec_write_file,
            "search_files": self._exec_search_files,
            "research": self._exec_research,
            "delegate_code": self._exec_delegate_code,
        }

        handler = tool_map.get(tool_name)
        if not handler:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Unknown tool: {tool_name}",
            )

        try:
            output = await handler(params)
            return ToolResult(tool_name=tool_name, success=True, output=output)
        except Exception as e:
            return ToolResult(tool_name=tool_name, success=False, output=None, error=str(e))

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            supports_subagents=True,       # Via Task tool
            supports_sandbox=False,
            supports_hooks=True,           # CLAUDE.md hooks system
            supports_mcp=True,             # Full MCP support
            supports_delegate_code=True,
            supports_delegate_code_async=True,
            supports_research=True,        # Via Gemini MCP
            supports_voice=True,           # Via voicemode MCP
            max_context_tokens=200_000,
            max_concurrent_sessions=5,
            cost_per_1m_input=15.0,        # Opus 4.6 pricing
            cost_per_1m_output=75.0,
        )

    async def get_cost_estimate(self, prompt: str, context: dict | None = None) -> CostEstimate:
        tokens = len(self._encoder.encode(prompt))
        caps = self.get_capabilities()
        estimated_output = min(tokens * 2, caps.max_output_tokens)
        cost = (
            tokens / 1_000_000 * caps.cost_per_1m_input +
            estimated_output / 1_000_000 * caps.cost_per_1m_output
        )
        return CostEstimate(
            estimated_input_tokens=tokens,
            estimated_output_tokens=estimated_output,
            estimated_usd=round(cost, 4),
            tier=CostTier.HIGH,
            confidence=0.6,
            note="Opus 4.6 pricing. Sub-agents add cost.",
        )

    async def health_check(self) -> HealthStatus:
        try:
            result = subprocess.run(
                [str(self._claude_bin), "--version"],
                capture_output=True, timeout=3
            )
            return HealthStatus.OK if result.returncode == 0 else HealthStatus.DEGRADED
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return HealthStatus.UNAVAILABLE

    # -- Private helpers --

    async def _consume_stream(self, stream: AsyncIterator[str]) -> str:
        """Drain an async stream, return full text."""
        result = []
        async for chunk in stream:
            result.append(chunk)
        return "".join(result)

    async def _exec_shell(self, params: dict) -> str:
        cmd = params["command"]
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode() or stderr.decode()

    async def _exec_read_file(self, params: dict) -> str:
        return Path(params["path"]).read_text()

    async def _exec_write_file(self, params: dict) -> str:
        Path(params["path"]).write_text(params["content"])
        return f"Written: {params['path']}"

    async def _exec_search_files(self, params: dict) -> list[str]:
        import subprocess
        result = subprocess.run(
            ["rg", "--files-with-matches", params["pattern"], params.get("path", ".")],
            capture_output=True, text=True
        )
        return result.stdout.strip().splitlines()

    async def _exec_research(self, params: dict) -> str:
        # Delegates to Gemini MCP — in Claude Code this is a tool call
        # Here we simulate by sending a research prompt
        query = params["query"]
        return f"[Research result for: {query}]"  # TUI replaces with real MCP call

    async def _exec_delegate_code(self, params: dict) -> str:
        prompt = params["prompt"]
        directory = params.get("dir", ".")
        chunks = []
        async for chunk in self.send_prompt(prompt, {"working_directory": directory}):
            chunks.append(chunk)
        return "".join(chunks)


class ClaudeCodeAgentHandle(AgentHandle):
    def __init__(self, provider: ClaudeCodeProvider, **kwargs):
        super().__init__(**kwargs)
        self._provider = provider
        self._result: str | None = None

    async def wait(self) -> str:
        while self._result is None:
            await asyncio.sleep(0.5)
        return self._result

    async def get_status(self) -> str:
        return "running" if self._result is None else "completed"
```

---

### 3.2 CodexProvider — Wraps `codex` CLI or SDK

```python
class CodexProvider(AgentProvider):
    """
    Wraps the Codex CLI (OpenAI's coding agent).

    Codex runs as a subprocess. Unlike Claude Code, Codex is stateless
    per invocation — sessions are emulated by prepending history to prompts.

    Communication: stdin prompt -> stdout stream (plain text or JSON lines)
    """

    def __init__(self, codex_bin: str = "codex", model: str = "o3"):
        self._codex_bin = codex_bin
        self._model = model
        self._session_histories: dict[str, list[dict]] = {}
        try:
            import tiktoken
            self._encoder = tiktoken.get_encoding("o200k_base")
        except ImportError:
            self._encoder = None

    @property
    def name(self) -> str:
        return "Codex"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run(
                [self._codex_bin, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    async def send_prompt(
        self,
        prompt: str,
        context: dict[str, Any],
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream from codex CLI. Codex uses SSE or plain newline-delimited output."""
        working_dir = context.get("working_directory", ".")

        # Build conversation: prepend history if session exists
        full_prompt = prompt
        if session_id and session_id in self._session_histories:
            history = self._session_histories[session_id]
            history_text = "\n".join(
                f"[{m['role']}]: {m['content']}" for m in history
            )
            full_prompt = f"{history_text}\n\n[user]: {prompt}"

        cmd = [
            self._codex_bin,
            "--model", self._model,
            "--quiet",              # Machine-readable output
            "--full-auto",          # Non-interactive
            full_prompt,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )

        full_response = []
        async for line in proc.stdout:
            chunk = line.decode()
            full_response.append(chunk)
            yield chunk

        # Save to session history
        if session_id is not None:
            if session_id not in self._session_histories:
                self._session_histories[session_id] = []
            self._session_histories[session_id].append(
                {"role": "user", "content": prompt}
            )
            self._session_histories[session_id].append(
                {"role": "assistant", "content": "".join(full_response)}
            )

        await proc.wait()

    async def spawn_agent(self, config: AgentConfig) -> AgentHandle:
        """Spawn Codex as a background subprocess."""
        if not self.get_capabilities().supports_subagents:
            raise CapabilityNotSupportedError("Codex subagents require separate process")

        cmd = [
            self._codex_bin,
            "--model", config.model or self._model,
            "--full-auto",
            "--quiet",
            config.prompt,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=config.working_directory or ".",
        )

        agent_id = f"codex-{id(proc)}"
        return CodexAgentHandle(
            agent_id=agent_id,
            role=config.role,
            is_background=config.background,
            process=proc,
        )

    async def execute_tool(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """Codex has native file/shell tools. Map abstract names to Codex equivalents."""
        # Codex can execute tools natively in --full-auto mode.
        # We invoke the relevant Codex command for each abstract tool.
        try:
            if tool_name == "shell":
                output = await self._exec_shell(params["command"])
            elif tool_name == "read_file":
                output = Path(params["path"]).read_text()
            elif tool_name == "write_file":
                Path(params["path"]).write_text(params["content"])
                output = f"Written: {params['path']}"
            elif tool_name == "delegate_code":
                chunks = []
                async for chunk in self.send_prompt(params["prompt"], {"working_directory": params.get("dir", ".")}):
                    chunks.append(chunk)
                output = "".join(chunks)
            else:
                return ToolResult(tool_name=tool_name, success=False, output=None,
                                  error=f"Tool not supported by Codex: {tool_name}")
            return ToolResult(tool_name=tool_name, success=True, output=output)
        except Exception as e:
            return ToolResult(tool_name=tool_name, success=False, output=None, error=str(e))

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,       # Via stdout line-by-line
            supports_subagents=True,       # Via separate subprocess
            supports_sandbox=True,         # Codex has sandbox mode
            supports_hooks=False,          # No hooks system
            supports_mcp=False,            # No native MCP support
            supports_delegate_code=True,
            supports_delegate_code_async=True,
            supports_research=True,        # Built-in web search
            supports_voice=False,
            max_context_tokens=128_000,    # o3 context window
            max_concurrent_sessions=10,   # Each is a subprocess
            cost_per_1m_input=2.0,         # o4-mini approximate
            cost_per_1m_output=8.0,
        )

    async def get_cost_estimate(self, prompt: str, context: dict | None = None) -> CostEstimate:
        tokens = len(prompt) // 4  # Rough estimate without tiktoken
        if self._encoder:
            tokens = len(self._encoder.encode(prompt))
        caps = self.get_capabilities()
        estimated_output = min(tokens * 3, 16_000)
        cost = (
            tokens / 1_000_000 * caps.cost_per_1m_input +
            estimated_output / 1_000_000 * caps.cost_per_1m_output
        )
        return CostEstimate(
            estimated_input_tokens=tokens,
            estimated_output_tokens=estimated_output,
            estimated_usd=round(cost, 4),
            tier=CostTier.LOW,
            confidence=0.5,
            note="Codex pricing varies by model. Using o4-mini estimate.",
        )

    async def health_check(self) -> HealthStatus:
        try:
            result = subprocess.run(
                [self._codex_bin, "--version"],
                capture_output=True, timeout=3
            )
            return HealthStatus.OK if result.returncode == 0 else HealthStatus.DEGRADED
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return HealthStatus.UNAVAILABLE

    async def _exec_shell(self, command: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode() or stderr.decode()


class CodexAgentHandle(AgentHandle):
    def __init__(self, process: asyncio.subprocess.Process, **kwargs):
        super().__init__(**kwargs)
        self._process = process
        self._output: str | None = None

    async def wait(self) -> str:
        if self._output is None:
            stdout, _ = await self._process.communicate()
            self._output = stdout.decode()
        return self._output

    async def get_status(self) -> str:
        if self._process.returncode is None:
            return "running"
        return "completed" if self._process.returncode == 0 else "failed"
```

---

### 3.3 OpenCodeProvider — Wraps the OpenCode MCP Server

```python
class OpenCodeProvider(AgentProvider):
    """
    Wraps the OpenCode MCP server (already running locally).

    OpenCode is a first-class MCP server — we call it via HTTP/stdio MCP protocol.
    Sessions are native OpenCode sessions (persistent, resumable).

    Key advantage: OpenCode already has full session management, streaming,
    sub-agents, and file operations — we just map our abstract interface to it.

    The MCP server is typically running at the default port or via stdio.
    """

    def __init__(
        self,
        provider_id: str = "anthropic",
        model_id: str = "claude-sonnet-4-6",
        opencode_url: str | None = None,  # None = use stdio MCP
    ):
        self._provider_id = provider_id
        self._model_id = model_id
        self._opencode_url = opencode_url
        self._active_sessions: dict[str, dict[str, Any]] = {}
        # In production, this would be the MCP client instance
        # For now we use subprocess calls to opencode CLI as fallback
        self._opencode_bin = "opencode"

    @property
    def name(self) -> str:
        return "OpenCode"

    @property
    def version(self) -> str:
        try:
            result = subprocess.run(
                [self._opencode_bin, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    async def send_prompt(
        self,
        prompt: str,
        context: dict[str, Any],
        session_id: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Use opencode_message_send_async + poll for streaming.

        OpenCode's native streaming is via SSE events. We poll the conversation
        and yield new tokens as they arrive (simulated streaming via polling).
        """
        working_dir = context.get("working_directory")

        # Create session if needed
        if session_id is None:
            session_id = await self.create_session(
                title=context.get("skill_name", "TUI Session")
            )

        # In production: call mcp__opencode__opencode_message_send_async
        # Here we show the structure with placeholder MCP calls
        session_info = self._active_sessions.get(session_id, {})
        oc_session_id = session_info.get("opencode_session_id", session_id)

        # Send message async (non-blocking)
        message_id = await self._send_message_async(oc_session_id, prompt, working_dir)

        # Poll for completion, yielding content deltas
        last_content_len = 0
        poll_interval = 0.3  # seconds

        for _ in range(200):  # max ~60s polling
            await asyncio.sleep(poll_interval)
            content = await self._get_message_content(oc_session_id, message_id)

            if content and len(content) > last_content_len:
                new_chunk = content[last_content_len:]
                last_content_len = len(content)
                yield new_chunk

            if await self._is_message_complete(oc_session_id, message_id):
                break

    async def spawn_agent(self, config: AgentConfig) -> AgentHandle:
        """
        Spawn via opencode_session_create + opencode_message_send_async.

        Each sub-agent gets its own OpenCode session — completely isolated,
        resumable, and trackable via the OpenCode session system.
        """
        new_session_id = await self.create_session(title=f"agent-{config.role}")
        oc_session_id = self._active_sessions[new_session_id]["opencode_session_id"]

        # Fire the prompt async
        message_id = await self._send_message_async(
            oc_session_id,
            config.prompt,
            config.working_directory,
        )

        return OpenCodeAgentHandle(
            agent_id=new_session_id,
            role=config.role,
            is_background=config.background,
            provider=self,
            opencode_session_id=oc_session_id,
            message_id=message_id,
        )

    async def execute_tool(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """
        OpenCode has native equivalents for all abstract tools in SPEC.md.
        These map 1:1 to MCP tool calls.
        """
        # Tool name -> MCP tool name mapping (from SPEC.md Section 4.2)
        mcp_tool_map = {
            "delegate_code": "opencode_ask",
            "delegate_code_async": "opencode_message_send_async",
            "delegate_code_run": "opencode_run",
            "shell": "opencode_shell_execute",
            "read_file": "opencode_file_read",
            "search_files": "opencode_find_text",
            "glob_files": "opencode_find_file",
            "check_session": "opencode_check",
            "review_changes": "opencode_review_changes",
            "revert_session": "opencode_session_revert",
        }

        mcp_name = mcp_tool_map.get(tool_name)
        if not mcp_name:
            return ToolResult(
                tool_name=tool_name, success=False, output=None,
                error=f"No OpenCode mapping for abstract tool: {tool_name}"
            )

        try:
            # In production: call the MCP tool directly via MCP client
            output = await self._call_mcp_tool(mcp_name, params)
            return ToolResult(tool_name=tool_name, success=True, output=output)
        except Exception as e:
            return ToolResult(tool_name=tool_name, success=False, output=None, error=str(e))

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,        # Native SSE streaming
            supports_subagents=True,        # Each session = isolated agent
            supports_sandbox=False,         # No explicit sandbox
            supports_hooks=False,           # No hooks system
            supports_mcp=True,              # IS an MCP server
            supports_delegate_code=True,
            supports_delegate_code_async=True,
            supports_research=True,         # Via built-in web search
            supports_voice=False,
            max_context_tokens=200_000,     # Depends on underlying model
            max_concurrent_sessions=50,     # OpenCode manages many sessions
            cost_per_1m_input=3.0,          # Sonnet 4.6 default
            cost_per_1m_output=15.0,
        )

    async def get_cost_estimate(self, prompt: str, context: dict | None = None) -> CostEstimate:
        # Use OpenCode's native cost estimation if available
        tokens = len(prompt) // 4
        caps = self.get_capabilities()
        estimated_output = min(tokens * 2, 8_000)
        cost = (
            tokens / 1_000_000 * caps.cost_per_1m_input +
            estimated_output / 1_000_000 * caps.cost_per_1m_output
        )
        return CostEstimate(
            estimated_input_tokens=tokens,
            estimated_output_tokens=estimated_output,
            estimated_usd=round(cost, 4),
            tier=CostTier.MEDIUM,
            confidence=0.7,
            note=f"Using {self._provider_id}/{self._model_id} pricing.",
        )

    async def health_check(self) -> HealthStatus:
        """Ping OpenCode MCP server via opencode_health tool."""
        try:
            result = await self._call_mcp_tool("opencode_health", {})
            return HealthStatus.OK if result else HealthStatus.DEGRADED
        except Exception:
            return HealthStatus.UNAVAILABLE

    async def create_session(self, title: str = "") -> str:
        """Create an OpenCode session and track it."""
        import uuid
        local_id = str(uuid.uuid4())
        # In production: oc_session_id = await mcp_client.opencode_session_create(title=title)
        oc_session_id = f"ses_{local_id[:8]}"
        self._active_sessions[local_id] = {
            "opencode_session_id": oc_session_id,
            "title": title,
        }
        return local_id

    async def end_session(self, session_id: str) -> None:
        """Delete the underlying OpenCode session."""
        if session_id in self._active_sessions:
            oc_id = self._active_sessions[session_id]["opencode_session_id"]
            await self._call_mcp_tool("opencode_session_delete", {"sessionId": oc_id})
            del self._active_sessions[session_id]

    async def list_sessions(self) -> list[dict[str, Any]]:
        """List active sessions from OpenCode."""
        return list(self._active_sessions.values())

    # -- Private MCP bridge --

    async def _call_mcp_tool(self, tool_name: str, params: dict) -> Any:
        """
        Call an OpenCode MCP tool.

        In production this is replaced by the actual MCP client call.
        The MCP client is injected at construction time or resolved from
        the running MCP server connection.
        """
        # Placeholder — replaced by real MCP client in TUI runtime
        raise NotImplementedError(f"MCP client not injected for tool: {tool_name}")

    async def _send_message_async(
        self, session_id: str, prompt: str, working_dir: str | None
    ) -> str:
        """Send a message to an OpenCode session asynchronously."""
        params = {
            "sessionID": session_id,
            "providerID": self._provider_id,
            "modelID": self._model_id,
            "parts": [{"type": "text", "text": prompt}],
        }
        if working_dir:
            params["directory"] = working_dir
        result = await self._call_mcp_tool("opencode_message_send_async", params)
        return result.get("messageID", "")

    async def _get_message_content(self, session_id: str, message_id: str) -> str:
        """Get current content of a message (for polling-based streaming)."""
        result = await self._call_mcp_tool(
            "opencode_message_get",
            {"sessionID": session_id, "messageID": message_id}
        )
        return result.get("content", "")

    async def _is_message_complete(self, session_id: str, message_id: str) -> bool:
        """Check if a message has finished generating."""
        result = await self._call_mcp_tool(
            "opencode_session_status",
            {"sessionID": session_id}
        )
        return result.get("status") in ("idle", "error")


class OpenCodeAgentHandle(AgentHandle):
    def __init__(
        self,
        provider: OpenCodeProvider,
        opencode_session_id: str,
        message_id: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._provider = provider
        self._opencode_session_id = opencode_session_id
        self._message_id = message_id

    async def wait(self) -> str:
        """Block until OpenCode session goes idle."""
        for _ in range(400):  # max ~2 minutes
            if await self._provider._is_message_complete(
                self._opencode_session_id, self._message_id
            ):
                return await self._provider._get_message_content(
                    self._opencode_session_id, self._message_id
                )
            await asyncio.sleep(0.3)
        return "[timeout waiting for OpenCode agent]"

    async def get_status(self) -> str:
        """Non-blocking status check via opencode_check."""
        try:
            result = await self._provider._call_mcp_tool(
                "opencode_check",
                {"sessionId": self._opencode_session_id}
            )
            return result.get("status", "unknown")
        except Exception:
            return "unknown"
```

---

## 4. Custom Exceptions

```python
class ProviderError(Exception):
    """Base for all provider errors."""

class ProviderUnavailableError(ProviderError):
    """Backend is not reachable (CLI not found, server down)."""

class ProviderTimeoutError(ProviderError):
    """Response stalled past the 60s threshold (see SPEC.md Section 9.3)."""

class CapabilityNotSupportedError(ProviderError):
    """Called a method the backend doesn't support (e.g. spawn_agent on Codex)."""
    def __init__(self, message: str, capability: str = ""):
        super().__init__(message)
        self.capability = capability
```

---

## 5. Session Management Strategy

Each provider handles state differently. The TUI uses a unified `SessionManager`
that talks only to `AgentProvider` and never to backends directly.

```python
@dataclass
class SessionState:
    """TUI-level session state. Backend-agnostic."""
    session_id: str
    title: str
    provider_name: str
    created_at: float
    last_active: float
    message_count: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0


class SessionManager:
    """
    Manages conversation sessions across TUI lifetime.

    One SessionManager per TUI instance. Multiple sessions can exist
    (tabbed interface), but only one is "active" at a time.
    """

    def __init__(self, provider: AgentProvider):
        self._provider = provider
        self._sessions: dict[str, SessionState] = {}
        self._active_session_id: str | None = None

    async def new_session(self, title: str = "") -> str:
        import time
        session_id = await self._provider.create_session(title)
        now = time.time()
        self._sessions[session_id] = SessionState(
            session_id=session_id,
            title=title or f"Session {len(self._sessions) + 1}",
            provider_name=self._provider.name,
            created_at=now,
            last_active=now,
        )
        self._active_session_id = session_id
        return session_id

    async def send(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Send prompt in active session, update cost tracking."""
        if not self._active_session_id:
            await self.new_session()

        context = context or {}
        estimate = await self._provider.get_cost_estimate(prompt, context)

        async for chunk in self._provider.send_prompt(
            prompt, context, session_id=self._active_session_id
        ):
            yield chunk

        # Update session cost tracking
        state = self._sessions[self._active_session_id]
        state.total_cost_usd += estimate.estimated_usd
        state.message_count += 1
        import time
        state.last_active = time.time()

    async def switch_to(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise KeyError(f"Unknown session: {session_id}")
        self._active_session_id = session_id

    async def close_session(self, session_id: str) -> None:
        await self._provider.end_session(session_id)
        del self._sessions[session_id]
        if self._active_session_id == session_id:
            self._active_session_id = (
                next(iter(self._sessions), None)
            )

    def get_all_sessions(self) -> list[SessionState]:
        return list(self._sessions.values())

    def get_active_session(self) -> SessionState | None:
        if self._active_session_id:
            return self._sessions.get(self._active_session_id)
        return None
```

**How each backend handles state:**

| Concern | ClaudeCodeProvider | CodexProvider | OpenCodeProvider |
|---|---|---|---|
| Session storage | In-process history (--resume flag) | In-memory dict, prepended to prompts | OpenCode native sessions (persistent) |
| Resume across restarts | No (process dies) | No (in-memory only) | Yes (OpenCode sessions survive) |
| Max sessions | ~5 (process-limited) | Unlimited (subprocess) | 50+ (server-managed) |
| Session cost tracking | Manual token counting | Manual token counting | Via opencode_check |

---

## 6. Provider Registry and Auto-Detection

```python
class ProviderRegistry:
    """
    Auto-detects available backends at startup and picks the best one.

    Priority order (based on cost and capability):
    1. OpenCode (already running, cheapest, most capable)
    2. ClaudeCode (powerful, supports MCP)
    3. Codex (sandboxed, good for untrusted code)
    """

    _providers: dict[str, type[AgentProvider]] = {
        "opencode": OpenCodeProvider,
        "claude-code": ClaudeCodeProvider,
        "codex": CodexProvider,
    }

    @classmethod
    async def auto_detect(cls) -> AgentProvider:
        """Probe backends in priority order, return first healthy one."""
        priority = ["opencode", "claude-code", "codex"]

        for name in priority:
            provider_cls = cls._providers[name]
            provider = provider_cls()
            status = await provider.health_check()
            if status == HealthStatus.OK:
                return provider

        raise ProviderUnavailableError(
            "No AI coding backend found. Install claude, codex, or start opencode."
        )

    @classmethod
    async def get_all_healthy(cls) -> dict[str, AgentProvider]:
        """Return all healthy providers (for capability comparison UI)."""
        results = {}
        for name, provider_cls in cls._providers.items():
            provider = provider_cls()
            status = await provider.health_check()
            if status != HealthStatus.UNAVAILABLE:
                results[name] = provider
        return results
```

---

## 7. Key Design Decisions

**Why async generators for streaming?**
The TUI renders tokens as they arrive. Synchronous calls would block the event
loop and freeze the UI. `AsyncIterator[str]` lets the TUI `async for chunk in stream`
and update the widget on each yield without blocking.

**Why abstract tool names instead of direct MCP calls?**
Mirrors SPEC.md's tool abstraction layer. The TUI calls `execute_tool("shell", ...)`
and never knows if that becomes `Bash()`, `codex shell_exec`, or `opencode_shell_execute`.
Swapping backends requires zero TUI code changes.

**Why polling for OpenCode streaming?**
OpenCode's MCP interface is request/response, not push. True SSE streaming would
require a direct WebSocket or SSE connection bypassing MCP. Polling at 300ms
gives adequate perceived responsiveness for a TUI context.

**Session state ownership:**
OpenCode owns its sessions on disk. Claude Code and Codex lose state on process
exit. The TUI's `SessionManager` tracks metadata (cost, message count) for all
backends, and delegates actual state to the provider.

---

*Generated: 2026-02-26 | Part of MyAIGame TUI architecture series*
