/**
 * OpenCode Plugin: Context Injection
 * Equivalent of: gather-context.sh + gather-context-enhanced.sh
 *
 * Uses OpenCode's experimental.chat.system.transform to inject
 * project context into the system prompt before each request.
 *
 * OpenCode plugin API (experimental):
 *   export default function transform(system: string): string
 *   Called before each chat request. Return modified system prompt.
 */

import { execSync } from "child_process";
import { existsSync } from "fs";
import { resolve } from "path";

// Path to the shared gather-context.sh script
const GATHER_CONTEXT = resolve(__dirname, "../../hooks/gather-context.sh");

export default function transform(system: string): string {
  // Only inject if the script exists
  if (!existsSync(GATHER_CONTEXT)) {
    return system;
  }

  try {
    const cwd = process.cwd();
    const context = execSync(`bash "${GATHER_CONTEXT}" "${cwd}" "opencode session"`, {
      timeout: 5000,
      encoding: "utf-8",
      cwd,
    });

    if (context.trim()) {
      return `${system}\n\n<project-context>\n${context.trim()}\n</project-context>`;
    }
  } catch {
    // Never block the agent — return unmodified system prompt
  }

  return system;
}
