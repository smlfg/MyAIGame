"""
TUI Event System — unified event bus and plugin framework.

Usage:
    from tui.events import bus, plugin
    from tui.events.types import PostToolUseEvent

    # In a plugin file:
    @plugin.on("post_tool_use")
    def my_handler(event: PostToolUseEvent):
        ...

    # To load all plugins and emit events:
    bus.load_plugins(Path("~/.config/myaigame-tui/plugins").expanduser())
    responses = bus.emit("post_tool_use", event)
"""

from tui.events.bus import EventBus
from tui.events.plugin import PluginRegistry

# Singletons used across the entire TUI process
plugin = PluginRegistry()
bus = EventBus(plugin)

__all__ = ["plugin", "bus"]
