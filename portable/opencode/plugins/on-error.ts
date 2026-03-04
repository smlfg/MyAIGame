/**
 * OpenCode Plugin: Error Handler
 * Equivalent of: codex_advisor.py (second opinion on errors)
 *
 * This plugin runs when a tool call fails or produces error output.
 * Since OpenCode cannot call Codex CLI internally (that would be recursive),
 * this plugin:
 * 1. Logs errors to a state file (same format as codex_advisor.py)
 * 2. Provides additional context back to the agent
 * 3. Detects soft errors in Bash/Task output
 *
 * NOTE: The "second opinion from another AI" aspect is NOT portable.
 * In Claude Code, codex_advisor.py calls Codex CLI for analysis.
 * In OpenCode, the agent itself must handle error recovery.
 * This plugin provides structured error tracking to aid that.
 *
 * OpenCode plugin API (experimental):
 *   export default function onError(event: ErrorEvent): ErrorResponse | void
 */

import { existsSync, readFileSync, writeFileSync, mkdtempSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";

// Soft error patterns (same as codex_advisor.py)
const SOFT_ERROR_PATTERNS = [
  "Traceback (most recent call last)",
  "Error:",
  "FAILED",
  "SyntaxError",
  "TypeError",
  "NameError",
  "ValueError",
  "AttributeError",
  "ImportError",
  "ModuleNotFoundError",
  "KeyError",
  "IndexError",
  "RuntimeError",
  "fatal:",
  "panic:",
  "Exception:",
  "Uncaught",
  "segfault",
  "core dumped",
];

// Trivial errors that don't need special handling
const TRIVIAL_PATTERNS = [
  "file not found",
  "no such file",
  "permission denied",
  "not unique in the file",
  "empty file",
  "command not found",
  "is a directory",
  "not a directory",
];

const ERROR_THRESHOLD = 2;

interface ErrorEvent {
  toolName?: string;
  toolInput?: Record<string, unknown>;
  error?: string;
  toolResponse?: string | Record<string, unknown>;
  sessionId?: string;
  cwd?: string;
}

interface ErrorState {
  errors: Array<{ tool: string; error: string; ts: number }>;
  count: number;
}

interface ErrorResponse {
  additionalContext?: string;
}

function getStateFile(sessionId: string): string {
  return join(tmpdir(), `opencode-errors-${sessionId}.json`);
}

function loadState(sessionId: string): ErrorState {
  const path = getStateFile(sessionId);
  try {
    if (existsSync(path)) {
      return JSON.parse(readFileSync(path, "utf-8"));
    }
  } catch {
    /* ignore */
  }
  return { errors: [], count: 0 };
}

function saveState(sessionId: string, state: ErrorState): void {
  try {
    writeFileSync(getStateFile(sessionId), JSON.stringify(state));
  } catch {
    /* ignore */
  }
}

function logError(sessionId: string, tool: string, error: string): void {
  if (!sessionId) return;
  const state = loadState(sessionId);
  state.errors.push({ tool, error: error.slice(0, 200), ts: Date.now() });
  state.count = state.errors.length;
  saveState(sessionId, state);
}

function isTrivial(error: string): boolean {
  const lower = error.toLowerCase();
  return TRIVIAL_PATTERNS.some((p) => lower.includes(p));
}

function hasSoftError(text: string): boolean {
  return SOFT_ERROR_PATTERNS.some((p) => text.includes(p));
}

function extractResponseText(response: unknown): string {
  if (typeof response === "string") return response;
  if (typeof response === "object" && response) {
    const parts: string[] = [];
    for (const key of ["stdout", "stderr", "output", "content", "text", "result"]) {
      const val = (response as Record<string, unknown>)[key];
      if (typeof val === "string" && val.trim()) {
        parts.push(val);
      }
    }
    return parts.join("\n");
  }
  return "";
}

export default function onError(event: ErrorEvent): ErrorResponse | void {
  try {
    const { toolName = "unknown", error, toolResponse, sessionId = "" } = event;

    // --- Hard error ---
    if (error) {
      if (isTrivial(error)) return;
      logError(sessionId, toolName, error);

      // Check if we've hit the threshold for a session review warning
      const state = loadState(sessionId);
      if (state.count > ERROR_THRESHOLD) {
        const errorList = state.errors
          .slice(-10)
          .map((e, i) => `${i + 1}. [${e.tool}] ${e.error}`)
          .join("\n");

        return {
          additionalContext:
            `[ERROR PATTERN DETECTED — ${state.count} errors in this session]\n\n` +
            `Recent errors:\n${errorList}\n\n` +
            `Consider: Is there a recurring pattern? Should the approach be reconsidered?`,
        };
      }

      return {
        additionalContext:
          `[Error logged: ${toolName}] ${error.slice(0, 300)}\n` +
          `Errors in session: ${state.count}. Consider the root cause before retrying.`,
      };
    }

    // --- Soft error detection (Bash/Task output) ---
    if (toolName !== "Bash" && toolName !== "Task") return;

    const responseText = extractResponseText(toolResponse);
    if (!responseText || !hasSoftError(responseText)) return;

    const matched = SOFT_ERROR_PATTERNS.filter((p) => responseText.includes(p));
    logError(sessionId, toolName, `soft-error: ${matched.slice(0, 3).join(", ")}`);

    return {
      additionalContext:
        `[Soft error detected in ${toolName} output]\n` +
        `Patterns found: ${matched.slice(0, 5).join(", ")}\n` +
        `Review the output carefully before proceeding.`,
    };
  } catch {
    // Iron Rule: never fail
  }
}
