/**
 * OpenCode Plugin: Post-Response Hook
 * Equivalent of: post_tool_use.py (narration) + syntax_check.py
 *
 * This plugin runs after each agent response/tool use.
 * It handles:
 * 1. Syntax checking Python files that were modified
 * 2. Sending narration to MultiKanalAgent daemon (if running)
 *
 * OpenCode plugin API (experimental):
 *   export default function postResponse(event: ResponseEvent): void
 *   Called after each tool use or response.
 *
 * NOTE: OpenCode's plugin API is experimental and may change.
 * This is a best-effort port. If the API differs, adapt accordingly.
 */

import { execSync } from "child_process";
import * as http from "http";

// Tools that produce noise — skip narration
const SKIP_TOOLS = new Set(["Read", "Glob", "Grep", "WebSearch", "WebFetch"]);

const DAEMON_HOST = "127.0.0.1";
const DAEMON_PORT = 7742;

interface ResponseEvent {
  toolName?: string;
  toolInput?: Record<string, unknown>;
  toolResponse?: string | Record<string, unknown>;
  sessionId?: string;
  error?: string;
}

/**
 * Syntax check: run py_compile on Python files after Edit/Write
 */
function syntaxCheck(filePath: string): void {
  if (!filePath.endsWith(".py")) return;

  try {
    execSync(`python3 -m py_compile "${filePath}"`, {
      timeout: 10000,
      encoding: "utf-8",
    });
  } catch (err: unknown) {
    const error = err as { stderr?: string; stdout?: string };
    const msg = (error.stderr || error.stdout || "").trim().slice(0, 500);
    if (msg) {
      console.error(`Syntax error in ${filePath}:\n${msg}`);
    }
  }
}

/**
 * Send narration text to MultiKanalAgent daemon (fire-and-forget)
 */
function sendNarration(text: string, sessionId: string): void {
  const payload = JSON.stringify({
    text: text.slice(0, 2000),
    source: "opencode",
    session_id: sessionId,
  });

  const req = http.request(
    {
      hostname: DAEMON_HOST,
      port: DAEMON_PORT,
      path: "/narrate",
      method: "POST",
      headers: { "Content-Type": "application/json" },
      timeout: 2000,
    },
    () => {
      /* fire and forget */
    }
  );

  req.on("error", () => {
    /* daemon might not be running */
  });
  req.write(payload);
  req.end();
}

export default function postResponse(event: ResponseEvent): void {
  try {
    const { toolName, toolInput, toolResponse, sessionId } = event;

    // --- Syntax Check ---
    if (toolName === "Edit" || toolName === "Write") {
      const filePath =
        typeof toolInput === "object" ? (toolInput?.file_path as string) : "";
      if (filePath) {
        syntaxCheck(filePath);
      }
    }

    // --- Narration ---
    if (!toolName || SKIP_TOOLS.has(toolName)) return;

    let text = "";
    if (typeof toolResponse === "string") {
      text = toolResponse;
    } else if (typeof toolResponse === "object" && toolResponse) {
      for (const key of ["content", "text", "output", "stdout", "result"]) {
        const val = (toolResponse as Record<string, unknown>)[key];
        if (typeof val === "string" && val.trim()) {
          text = val;
          break;
        }
      }
    }

    if (text.trim()) {
      let context = "";
      if (typeof toolInput === "object" && toolInput) {
        const desc = toolInput.description as string;
        const cmd = toolInput.command as string;
        context = desc || (cmd ? `Command: ${cmd}` : "");
      }

      const narrationInput = context
        ? `${context}\n\nResult:\n${text.slice(0, 2000)}`
        : `Tool '${toolName}' result:\n${text.slice(0, 2000)}`;

      sendNarration(narrationInput, sessionId || "");
    }
  } catch {
    // Iron Rule: never fail, never block the agent
  }
}
