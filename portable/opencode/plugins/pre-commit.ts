/**
 * OpenCode Plugin: Pre-Commit Test Runner
 * Equivalent of: pre_commit_tests.py
 *
 * Intercepts git commit commands and runs pytest first.
 * Blocks the commit if tests fail.
 *
 * NOTE: OpenCode's plugin API for intercepting tool calls is experimental.
 * If this plugin format is not supported, fall back to:
 *   1. Standard git pre-commit hooks (.git/hooks/pre-commit)
 *   2. The shared pre_commit_tests.py in portable/hooks/
 *
 * OpenCode plugin API (experimental):
 *   export default function preToolUse(event: ToolEvent): ToolDecision
 */

import { execSync } from "child_process";
import { existsSync, readdirSync, statSync } from "fs";
import { join, dirname } from "path";

interface ToolEvent {
  toolName: string;
  toolInput: Record<string, unknown>;
  cwd?: string;
}

interface ToolDecision {
  allow: boolean;
  reason?: string;
}

function isGitCommit(command: string): boolean {
  const cmd = command.trim();
  if (cmd.startsWith("#") || cmd.startsWith("echo ")) return false;

  const parts = cmd.split(/[;&|]+/);
  return parts.some((part) => {
    const p = part.trim();
    return p.startsWith("git commit") || (p.startsWith("git -c") && p.includes("commit"));
  });
}

function findTestFiles(dir: string): boolean {
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.name.startsWith(".") || ["node_modules", "__pycache__", "venv", ".venv"].includes(entry.name)) {
        continue;
      }
      const fullPath = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (findTestFiles(fullPath)) return true;
      } else if (
        (entry.name.startsWith("test_") && entry.name.endsWith(".py")) ||
        entry.name.endsWith("_test.py")
      ) {
        return true;
      }
    }
  } catch {
    /* ignore permission errors */
  }
  return false;
}

function findVenvPython(startDir: string): string {
  let dir = startDir;
  for (let i = 0; i < 5; i++) {
    for (const venvName of [".venv", "venv"]) {
      const candidate = join(dir, venvName, "bin", "python");
      if (existsSync(candidate)) return candidate;
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return "python3";
}

export default function preToolUse(event: ToolEvent): ToolDecision {
  try {
    if (event.toolName !== "Bash") return { allow: true };

    const command = (event.toolInput.command as string) || "";
    if (!isGitCommit(command)) return { allow: true };

    // Find repo root
    let repoDir: string;
    try {
      repoDir = execSync("git rev-parse --show-toplevel", {
        encoding: "utf-8",
        timeout: 5000,
        cwd: event.cwd,
      }).trim();
    } catch {
      return { allow: true }; // Not in a git repo
    }

    if (!findTestFiles(repoDir)) return { allow: true };

    const pythonExe = findVenvPython(repoDir);

    try {
      execSync(`${pythonExe} -m pytest --tb=short -q`, {
        timeout: 120000,
        encoding: "utf-8",
        cwd: repoDir,
      });
    } catch (err: unknown) {
      const error = err as { stdout?: string; stderr?: string; status?: number };
      if (error.status === 5) return { allow: true }; // No tests collected

      const output = ((error.stdout || "") + "\n" + (error.stderr || "")).trim().slice(-800);
      return {
        allow: false,
        reason: `Tests failed! Fix before committing:\n${output}`,
      };
    }

    return { allow: true };
  } catch {
    return { allow: true }; // Iron Rule: never block on plugin errors
  }
}
