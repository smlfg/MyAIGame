"""CLI entrypoint for MultiKanalAgent."""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multikanal",
        description="MultiKanalAgent — dual-channel CLI assistant (visual + audio)",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # daemon subcommand
    daemon_p = sub.add_parser("daemon", help="Start the narration daemon")
    daemon_p.add_argument(
        "--config", type=str, default=None, help="Path to config YAML"
    )
    daemon_p.add_argument("--port", type=int, default=None, help="Override daemon port")
    daemon_p.add_argument("--host", type=str, default=None, help="Override daemon host")

    # narrate subcommand (one-shot, for testing)
    narrate_p = sub.add_parser("narrate", help="Send text to daemon for narration")
    narrate_p.add_argument(
        "text", nargs="?", default=None, help="Text to narrate (or stdin)"
    )
    narrate_p.add_argument("--source", default="cli", help="Source identifier")

    # health subcommand
    sub.add_parser("health", help="Check daemon health")

    # stop subcommand
    sub.add_parser("stop", help="Stop current audio playback")

    # install-hooks subcommand
    sub.add_parser("install-hooks", help="Install Claude Code hooks for this project")

    # agent subcommand (Codex / others)
    agent_p = sub.add_parser("agent", help="Run an agent backend and narrate output")
    agent_p.add_argument("prompt", nargs="?", default=None, help="Prompt to send (or stdin)")
    agent_p.add_argument(
        "--backend",
        choices=["codex", "opencode"],
        default="codex",
        help="Agent backend to use",
    )

    # codex subcommand
    codex_p = sub.add_parser(
        "codex", help="Run Codex with live audio narration"
    )
    codex_p.add_argument("prompt", nargs="?", default=None, help="Prompt (or stdin)")
    codex_p.add_argument(
        "--one-shot",
        action="store_true",
        help="One-shot mode: narrate only at end (default: live)",
    )
    codex_p.add_argument(
        "--command",
        default="codex",
        help="Path to codex binary (default: codex)",
    )

    # opencode subcommand
    opencode_p = sub.add_parser(
        "opencode", help="Start OpenCode SSE listener with live narration"
    )
    opencode_p.add_argument(
        "--sse-url",
        type=str,
        default="http://localhost:3000/events",
        help="OpenCode SSE URL",
    )
    opencode_p.add_argument(
        "--daemon-url",
        type=str,
        default="http://127.0.0.1:7742",
        help="MultiKanalAgent daemon URL",
    )
    opencode_p.add_argument(
        "--live",
        action="store_true",
        help="Enable live updates (default: final summary only)",
    )

    return parser


def cmd_daemon(args):
    """Start the daemon."""
    import os

    if args.port:
        os.environ["MULTIKANAL_PORT"] = str(args.port)

    from .config import load_config

    cfg = load_config(args.config)
    if args.host:
        cfg["daemon"]["host"] = args.host

    from .daemon import run

    run()


def cmd_narrate(args):
    """Send text to daemon for narration (one-shot)."""
    import httpx

    from .config import load_config

    cfg = load_config()
    port = cfg["daemon"]["port"]

    text = args.text
    if text is None:
        text = sys.stdin.read()

    if not text.strip():
        print("No text provided.", file=sys.stderr)
        sys.exit(1)

    try:
        resp = httpx.post(
            f"http://127.0.0.1:{port}/narrate",
            json={"text": text, "source": args.source},
            timeout=30,
        )
        data = resp.json()
        print(f"Status: {data.get('status')}")
        if data.get("narration"):
            print(f"Narration: {data['narration']}")
        print(f"Duration: {data.get('duration_ms', 0)}ms")
    except httpx.ConnectError:
        print(f"Error: daemon not running on port {port}", file=sys.stderr)
        sys.exit(1)


def cmd_health(args):
    """Check daemon health."""
    import httpx

    from .config import load_config

    cfg = load_config()
    port = cfg["daemon"]["port"]

    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=5)
        data = resp.json()
        print(f"Status:  {data.get('status')}")
        print(f"Uptime:  {data.get('uptime_seconds', 0)}s")
        providers = data.get("providers", {}) or {}
        if providers:
            for name, ok in providers.items():
                print(f"{name.capitalize():8}: {'OK' if ok else 'UNAVAILABLE'}")
        chain = data.get("provider_chain") or []
        if chain:
            print(f"Chain:   {', '.join(chain)}")
        print(f"Piper:   {'OK' if data.get('piper_available') else 'UNAVAILABLE'}")
    except httpx.ConnectError:
        print(f"Error: daemon not running on port {port}", file=sys.stderr)
        sys.exit(1)


def cmd_stop(args):
    """Stop audio playback."""
    import httpx

    from .config import load_config

    cfg = load_config()
    port = cfg["daemon"]["port"]

    try:
        resp = httpx.post(f"http://127.0.0.1:{port}/stop", timeout=5)
        print(resp.json().get("status", "unknown"))
    except httpx.ConnectError:
        print(f"Error: daemon not running on port {port}", file=sys.stderr)
        sys.exit(1)


def cmd_install_hooks(args):
    """Install Claude Code hooks into the current project."""
    from .adapters.claude_hook import install_hooks

    install_hooks()


def cmd_agent(args):
    """Run an agent backend and narrate its output."""
    import sys

    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    if not prompt.strip():
        print("No prompt provided.", file=sys.stderr)
        sys.exit(1)

    if args.backend == "codex":
        from .adapters.codex_wrapper import CodexWrapperAdapter

        adapter = CodexWrapperAdapter()
        adapter.run_and_narrate(prompt)
    elif args.backend == "opencode":
        from .adapters.opencode_sse import OpenCodeSSEAdapter

        adapter = OpenCodeSSEAdapter()
        adapter.run_and_narrate(prompt)
    else:
        print(f"Unsupported backend: {args.backend}", file=sys.stderr)
        sys.exit(1)


def cmd_codex(args):
    """Run Codex with live audio narration."""
    from .adapters.codex_wrapper import CodexWrapperAdapter

    prompt = args.prompt
    if prompt is None:
        prompt = sys.stdin.read()

    if not prompt.strip():
        print("No prompt provided.", file=sys.stderr)
        sys.exit(1)

    adapter = CodexWrapperAdapter(codex_command=args.command)

    if args.one_shot:
        text, _ = adapter.run_and_narrate(prompt)
    else:
        text = adapter.run_live(prompt)

    if not text:
        print("(No output from Codex)", file=sys.stderr)


def cmd_opencode(args):
    """Start OpenCode SSE listener with live narration."""
    from .adapters.opencode_sse import OpenCodeSSEAdapter

    print(f"Connecting to OpenCode SSE at {args.sse_url}")
    print("Press Ctrl+C to stop")
    print("")

    adapter = OpenCodeSSEAdapter(
        daemon_url=args.daemon_url,
        sse_url=args.sse_url,
    )

    if args.live:
        print("Live mode: sending updates immediately")
        import asyncio

        try:
            asyncio.run(adapter.listen_live())
        except KeyboardInterrupt:
            print("\nStopped by user")
    else:
        print("Final mode: waiting for session.idle")
        text = adapter.capture()
        if text:
            print(f"\nAccumulated text ({len(text)} chars)")
            print(text[:500] + "..." if len(text) > 500 else text)


def main():
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "daemon": cmd_daemon,
        "narrate": cmd_narrate,
        "health": cmd_health,
        "stop": cmd_stop,
        "install-hooks": cmd_install_hooks,
        "codex": cmd_codex,
        "opencode": cmd_opencode,
        "agent": cmd_agent,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)
