#!/usr/bin/env bash
# deploy.sh — Interactive installer for the MyAIGame portable AI toolkit
# Deploys skills, instructions, hooks, and config to Claude Code, Codex CLI, and/or OpenCode.
#
# Usage:
#   ./deploy.sh                  # Interactive mode — detect tools, ask what to deploy
#   ./deploy.sh --target claude   # Deploy to Claude Code only
#   ./deploy.sh --target codex    # Deploy to Codex CLI only
#   ./deploy.sh --target opencode # Deploy to OpenCode only
#   ./deploy.sh --target all      # Deploy to all detected tools
#   ./deploy.sh --dry-run         # Show what would be done, change nothing
#   ./deploy.sh --backup-only     # Only create backups, no deployment

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORTABLE_DIR="$SCRIPT_DIR"
BACKUP_SUFFIX="backup-$(date +%Y%m%d-%H%M%S)"
DRY_RUN=false
BACKUP_ONLY=false
TARGET=""
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
FILES_COPIED=0
FILES_SKIPPED=0
BACKUPS_CREATED=0
ERRORS=0

# --- Helpers ---

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_dry()   { echo -e "${CYAN}[DRY-RUN]${NC} Would: $*"; }
log_bold()  { echo -e "${BOLD}$*${NC}"; }

# Safe copy: backup target if it exists, then copy
safe_copy() {
    local src="$1"
    local dst="$2"
    local description="${3:-}"

    if [[ ! -f "$src" ]]; then
        log_error "Source not found: $src"
        ((ERRORS++))
        return 1
    fi

    if $DRY_RUN; then
        if [[ -f "$dst" ]]; then
            log_dry "backup $dst -> ${dst}.${BACKUP_SUFFIX}"
        fi
        log_dry "copy $src -> $dst"
        return 0
    fi

    # Ensure target directory exists
    mkdir -p "$(dirname "$dst")"

    # Backup if target exists and differs
    if [[ -f "$dst" ]]; then
        if ! diff -q "$src" "$dst" &>/dev/null; then
            cp "$dst" "${dst}.${BACKUP_SUFFIX}"
            ((BACKUPS_CREATED++))
            [[ $VERBOSE == true ]] && log_info "Backed up: ${dst}.${BACKUP_SUFFIX}"
        else
            [[ $VERBOSE == true ]] && log_info "Identical, skipping: $dst"
            ((FILES_SKIPPED++))
            return 0
        fi
    fi

    cp "$src" "$dst"
    ((FILES_COPIED++))
    [[ -n "$description" ]] && log_ok "$description"
}

# Safe copy with executable bit preserved
safe_copy_exec() {
    safe_copy "$1" "$2" "$3"
    if ! $DRY_RUN && [[ -f "$2" ]]; then
        chmod +x "$2"
    fi
}

# Copy directory contents
safe_copy_dir() {
    local src_dir="$1"
    local dst_dir="$2"
    local description="${3:-}"

    if [[ ! -d "$src_dir" ]]; then
        log_error "Source directory not found: $src_dir"
        ((ERRORS++))
        return 1
    fi

    if $DRY_RUN; then
        log_dry "copy directory $src_dir/* -> $dst_dir/"
        return 0
    fi

    mkdir -p "$dst_dir"
    for f in "$src_dir"/*; do
        [[ -f "$f" ]] || continue
        local basename
        basename="$(basename "$f")"
        safe_copy "$f" "$dst_dir/$basename" ""
    done
    [[ -n "$description" ]] && log_ok "$description"
}

# --- Detection ---

detect_claude_code() {
    if command -v claude &>/dev/null; then
        echo "installed"
        return 0
    fi
    # Check common locations
    for p in ~/.local/bin/claude /usr/local/bin/claude; do
        if [[ -x "$p" ]]; then
            echo "installed"
            return 0
        fi
    done
    echo "not_found"
    return 1
}

detect_codex() {
    if command -v codex &>/dev/null; then
        echo "installed"
        return 0
    fi
    for p in ~/.local/bin/codex /usr/local/bin/codex ~/.npm-global/bin/codex; do
        if [[ -x "$p" ]]; then
            echo "installed"
            return 0
        fi
    done
    echo "not_found"
    return 1
}

detect_opencode() {
    if command -v opencode &>/dev/null; then
        echo "installed"
        return 0
    fi
    for p in ~/.local/bin/opencode /usr/local/bin/opencode; do
        if [[ -x "$p" ]]; then
            echo "installed"
            return 0
        fi
    done
    echo "not_found"
    return 1
}

# --- Validation ---

validate_portable_dir() {
    local missing=()
    [[ ! -f "$PORTABLE_DIR/SPEC.md" ]] && missing+=("SPEC.md")
    [[ ! -d "$PORTABLE_DIR/instructions" ]] && missing+=("instructions/")
    [[ ! -d "$PORTABLE_DIR/hooks" ]] && missing+=("hooks/")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Portable directory incomplete. Missing: ${missing[*]}"
        log_error "Expected at: $PORTABLE_DIR"
        exit 1
    fi
}

validate_deployment() {
    local target="$1"
    local errors=0

    echo ""
    log_bold "Validating $target deployment..."

    case "$target" in
        claude)
            local claude_dir="$HOME/.claude"
            # Check instructions
            if [[ -f "$claude_dir/CLAUDE.md" ]]; then
                log_ok "CLAUDE.md present"
            else
                log_error "CLAUDE.md missing"; ((errors++))
            fi
            # Check at least some commands
            local cmd_count
            cmd_count=$(ls "$claude_dir/commands/"*.md 2>/dev/null | wc -l)
            if [[ $cmd_count -gt 0 ]]; then
                log_ok "$cmd_count skill commands installed"
            else
                log_error "No commands found in $claude_dir/commands/"; ((errors++))
            fi
            # Check hooks
            if [[ -x "$claude_dir/hooks/gather-context.sh" ]]; then
                log_ok "gather-context.sh present and executable"
            else
                log_warn "gather-context.sh missing or not executable"
            fi
            # Check settings.json syntax
            if [[ -f "$claude_dir/settings.json" ]]; then
                if python3 -c "import json; json.load(open('$claude_dir/settings.json'))" 2>/dev/null; then
                    log_ok "settings.json valid JSON"
                else
                    log_error "settings.json invalid JSON"; ((errors++))
                fi
            fi
            ;;

        codex)
            local codex_dir="$HOME/.codex"
            if [[ -f "$codex_dir/instructions.md" ]]; then
                log_ok "instructions.md present"
            else
                log_error "instructions.md missing"; ((errors++))
            fi
            if [[ -f "$codex_dir/config.toml" ]]; then
                log_ok "config.toml present"
            else
                log_warn "config.toml missing (optional)"
            fi
            local skill_count
            skill_count=$(ls -d "$codex_dir/skills/"*/ 2>/dev/null | wc -l)
            if [[ $skill_count -gt 0 ]]; then
                log_ok "$skill_count skill directories installed"
            else
                log_warn "No skills found in $codex_dir/skills/"
            fi
            ;;

        opencode)
            local oc_dir="$HOME/.opencode"
            if [[ -f "$oc_dir/AGENTS.md" ]] || [[ -f "$oc_dir/instructions.md" ]]; then
                log_ok "Instructions file present"
            else
                log_error "No instructions file found"; ((errors++))
            fi
            if [[ -f "$oc_dir/opencode.json" ]]; then
                if python3 -c "import json; json.load(open('$oc_dir/opencode.json'))" 2>/dev/null; then
                    log_ok "opencode.json valid JSON"
                else
                    log_error "opencode.json invalid JSON"; ((errors++))
                fi
            else
                log_warn "opencode.json missing (optional)"
            fi
            local cmd_count
            cmd_count=$(ls "$oc_dir/commands/"*.md 2>/dev/null | wc -l)
            local skill_count
            skill_count=$(ls -d "$oc_dir/skills/"*/ 2>/dev/null | wc -l)
            local total=$((cmd_count + skill_count))
            if [[ $total -gt 0 ]]; then
                log_ok "$total skills/commands installed"
            else
                log_warn "No skills or commands found"
            fi
            ;;
    esac

    if [[ $errors -eq 0 ]]; then
        log_ok "Validation passed for $target"
    else
        log_error "Validation found $errors error(s) for $target"
    fi
    return $errors
}

# --- Deployment Functions ---

deploy_claude_code() {
    log_bold "=== Deploying to Claude Code ==="
    local claude_dir="$HOME/.claude"

    # 1. Instructions
    log_info "Installing instructions..."
    # Claude Code uses CLAUDE.md at ~/.claude/CLAUDE.md
    # The portable AGENTS.md needs to be adapted to CLAUDE.md format
    safe_copy "$PORTABLE_DIR/instructions/AGENTS.md" "$claude_dir/CLAUDE.md" \
        "CLAUDE.md (system instructions)"

    # Companion files — Claude Code puts them directly in ~/.claude/
    if [[ -d "$PORTABLE_DIR/instructions/companion" ]]; then
        for f in "$PORTABLE_DIR/instructions/companion"/*.md; do
            [[ -f "$f" ]] || continue
            local basename
            basename="$(basename "$f")"
            safe_copy "$f" "$claude_dir/$basename" "  companion: $basename"
        done
    fi

    # 2. Skills (commands)
    log_info "Installing skills as commands..."
    local commands_src="$PORTABLE_DIR/claude-code-commands"
    if [[ -d "$commands_src" ]]; then
        mkdir -p "$claude_dir/commands"
        for f in "$commands_src"/*.md; do
            [[ -f "$f" ]] || continue
            local basename
            basename="$(basename "$f")"
            safe_copy "$f" "$claude_dir/commands/$basename" ""
        done
        log_ok "Skills installed to $claude_dir/commands/"
    else
        # Fallback: copy from original source if available
        local orig_commands="$SCRIPT_DIR/../claude-code/commands"
        if [[ -d "$orig_commands" ]]; then
            mkdir -p "$claude_dir/commands"
            for f in "$orig_commands"/*.md; do
                [[ -f "$f" ]] || continue
                local basename
                basename="$(basename "$f")"
                safe_copy "$f" "$claude_dir/commands/$basename" ""
            done
            log_ok "Skills installed from claude-code/commands/"
        else
            log_warn "No Claude Code commands directory found — skills not deployed"
        fi
    fi

    # 3. Hooks
    log_info "Installing hooks..."
    mkdir -p "$claude_dir/hooks"
    for f in "$PORTABLE_DIR/hooks"/*.sh; do
        [[ -f "$f" ]] || continue
        local basename
        basename="$(basename "$f")"
        safe_copy_exec "$f" "$claude_dir/hooks/$basename" "  hook: $basename"
    done
    for f in "$PORTABLE_DIR/hooks"/*.py; do
        [[ -f "$f" ]] || continue
        local basename
        basename="$(basename "$f")"
        safe_copy "$f" "$claude_dir/hooks/$basename" "  hook: $basename"
    done

    # 4. Hook config (hooks.json goes into settings.json merge — warn user)
    if [[ -f "$PORTABLE_DIR/hooks/hooks.json" ]]; then
        log_warn "hooks.json contains hook bindings for settings.json."
        log_warn "You may need to merge these into ~/.claude/settings.json manually."
        log_warn "The hook scripts are installed; the bindings may need updating."
    fi

    # 5. Config (settings.json) — only copy if no existing one
    local settings_src="$SCRIPT_DIR/../claude-code/settings.json"
    if [[ -f "$settings_src" ]]; then
        if [[ -f "$claude_dir/settings.json" ]]; then
            log_warn "settings.json already exists — backed up but NOT overwritten."
            log_warn "Review and merge manually: diff $claude_dir/settings.json $settings_src"
            if ! $DRY_RUN; then
                cp "$claude_dir/settings.json" "$claude_dir/settings.json.${BACKUP_SUFFIX}"
                ((BACKUPS_CREATED++))
            fi
        else
            safe_copy "$settings_src" "$claude_dir/settings.json" "settings.json (config + MCP servers)"
        fi
    fi

    echo ""
    validate_deployment "claude"
}

deploy_codex() {
    log_bold "=== Deploying to Codex CLI ==="
    local codex_dir="$HOME/.codex"

    # 1. Instructions
    log_info "Installing instructions..."
    safe_copy "$PORTABLE_DIR/instructions/AGENTS.md" "$codex_dir/instructions.md" \
        "instructions.md (system instructions)"

    # Companion files — Codex reads from .codex/ directory
    if [[ -d "$PORTABLE_DIR/instructions/companion" ]]; then
        mkdir -p "$codex_dir/companion"
        for f in "$PORTABLE_DIR/instructions/companion"/*.md; do
            [[ -f "$f" ]] || continue
            local basename
            basename="$(basename "$f")"
            safe_copy "$f" "$codex_dir/companion/$basename" "  companion: $basename"
        done
    fi

    # 2. Config
    if [[ -f "$PORTABLE_DIR/codex/config.toml" ]]; then
        safe_copy "$PORTABLE_DIR/codex/config.toml" "$codex_dir/config.toml" \
            "config.toml (Codex configuration)"
    fi

    # 3. Skills — Codex uses .codex/skills/<name>/SKILL.md
    local skills_src="$PORTABLE_DIR/codex/skills"
    if [[ -d "$skills_src" ]]; then
        log_info "Installing skills..."
        for skill_dir in "$skills_src"/*/; do
            [[ -d "$skill_dir" ]] || continue
            local skill_name
            skill_name="$(basename "$skill_dir")"
            mkdir -p "$codex_dir/skills/$skill_name"
            for f in "$skill_dir"*; do
                [[ -f "$f" ]] || continue
                local basename
                basename="$(basename "$f")"
                safe_copy "$f" "$codex_dir/skills/$skill_name/$basename" ""
            done
            # Copy scripts subdirectory if present
            if [[ -d "$skill_dir/scripts" ]]; then
                safe_copy_dir "$skill_dir/scripts" "$codex_dir/skills/$skill_name/scripts" ""
            fi
        done
        log_ok "Skills installed to $codex_dir/skills/"
    else
        log_warn "No Codex skills directory found — skills not deployed"
        log_info "Skills will be available once Task #3 (Codex porting) completes"
    fi

    # 4. Hooks — Codex uses git hooks as workaround
    log_info "Installing portable hooks..."
    mkdir -p "$codex_dir/hooks"
    for f in "$PORTABLE_DIR/hooks"/gather-context*.sh "$PORTABLE_DIR/hooks"/session-extract.sh; do
        [[ -f "$f" ]] || continue
        local basename
        basename="$(basename "$f")"
        safe_copy_exec "$f" "$codex_dir/hooks/$basename" "  hook: $basename"
    done
    log_info "Note: Codex has no native hook system."
    log_info "Pre-commit hooks can be installed via: cp hooks/pre_commit_tests.py .git/hooks/pre-commit"

    echo ""
    validate_deployment "codex"
}

deploy_opencode() {
    log_bold "=== Deploying to OpenCode ==="
    local oc_dir="$HOME/.opencode"

    # 1. Instructions
    log_info "Installing instructions..."
    safe_copy "$PORTABLE_DIR/instructions/AGENTS.md" "$oc_dir/AGENTS.md" \
        "AGENTS.md (system instructions)"

    # Companion files
    if [[ -d "$PORTABLE_DIR/instructions/companion" ]]; then
        mkdir -p "$oc_dir/companion"
        for f in "$PORTABLE_DIR/instructions/companion"/*.md; do
            [[ -f "$f" ]] || continue
            local basename
            basename="$(basename "$f")"
            safe_copy "$f" "$oc_dir/companion/$basename" "  companion: $basename"
        done
    fi

    # 2. Config
    if [[ -f "$PORTABLE_DIR/opencode/opencode.json" ]]; then
        safe_copy "$PORTABLE_DIR/opencode/opencode.json" "$oc_dir/opencode.json" \
            "opencode.json (configuration + MCP servers)"
    fi

    # 3. Plugins (hook equivalents)
    if [[ -d "$PORTABLE_DIR/opencode/plugins" ]]; then
        log_info "Installing plugins (hook equivalents)..."
        mkdir -p "$oc_dir/plugins"
        for f in "$PORTABLE_DIR/opencode/plugins"/*; do
            [[ -f "$f" ]] || continue
            local basename
            basename="$(basename "$f")"
            safe_copy "$f" "$oc_dir/plugins/$basename" "  plugin: $basename"
        done
    fi

    # 4. Skills — OpenCode uses .opencode/commands/*.md and .opencode/skills/*/SKILL.md
    local commands_src="$PORTABLE_DIR/opencode/commands"
    local skills_src="$PORTABLE_DIR/opencode/skills"

    if [[ -d "$commands_src" ]]; then
        log_info "Installing commands..."
        mkdir -p "$oc_dir/commands"
        for f in "$commands_src"/*.md; do
            [[ -f "$f" ]] || continue
            local basename
            basename="$(basename "$f")"
            safe_copy "$f" "$oc_dir/commands/$basename" ""
        done
        log_ok "Commands installed to $oc_dir/commands/"
    fi

    if [[ -d "$skills_src" ]]; then
        log_info "Installing skills..."
        for skill_dir in "$skills_src"/*/; do
            [[ -d "$skill_dir" ]] || continue
            local skill_name
            skill_name="$(basename "$skill_dir")"
            mkdir -p "$oc_dir/skills/$skill_name"
            for f in "$skill_dir"*; do
                [[ -f "$f" ]] || continue
                local basename
                basename="$(basename "$f")"
                safe_copy "$f" "$oc_dir/skills/$skill_name/$basename" ""
            done
        done
        log_ok "Skills installed to $oc_dir/skills/"
    fi

    if [[ ! -d "$commands_src" ]] && [[ ! -d "$skills_src" ]]; then
        log_warn "No OpenCode skills/commands found — skills not deployed"
        log_info "Skills will be available once Task #4 (OpenCode porting) completes"
    fi

    # 5. Hooks (shell scripts)
    log_info "Installing portable hooks..."
    mkdir -p "$oc_dir/hooks"
    for f in "$PORTABLE_DIR/hooks"/gather-context*.sh "$PORTABLE_DIR/hooks"/session-extract.sh; do
        [[ -f "$f" ]] || continue
        local basename
        basename="$(basename "$f")"
        safe_copy_exec "$f" "$oc_dir/hooks/$basename" "  hook: $basename"
    done

    echo ""
    validate_deployment "opencode"
}

# --- Interactive UI ---

show_banner() {
    echo ""
    log_bold "=========================================="
    log_bold "  MyAIGame Portable Toolkit Installer"
    log_bold "=========================================="
    echo ""
    echo "  Source:  $PORTABLE_DIR"
    echo "  Backup:  *.$BACKUP_SUFFIX"
    if $DRY_RUN; then
        echo -e "  Mode:    ${CYAN}DRY RUN (no changes)${NC}"
    fi
    echo ""
}

detect_tools() {
    log_bold "Detecting installed tools..."
    echo ""

    local claude_status codex_status opencode_status
    claude_status=$(detect_claude_code 2>/dev/null || echo "not_found")
    codex_status=$(detect_codex 2>/dev/null || echo "not_found")
    opencode_status=$(detect_opencode 2>/dev/null || echo "not_found")

    local status_icon
    printf "  %-15s " "Claude Code:"
    if [[ "$claude_status" == "installed" ]]; then
        echo -e "${GREEN}found${NC}"
    else
        echo -e "${YELLOW}not found${NC}"
    fi

    printf "  %-15s " "Codex CLI:"
    if [[ "$codex_status" == "installed" ]]; then
        echo -e "${GREEN}found${NC}"
    else
        echo -e "${YELLOW}not found${NC}"
    fi

    printf "  %-15s " "OpenCode:"
    if [[ "$opencode_status" == "installed" ]]; then
        echo -e "${GREEN}found${NC}"
    else
        echo -e "${YELLOW}not found${NC}"
    fi

    echo ""

    # Return detected tools as space-separated string
    local detected=""
    [[ "$claude_status" == "installed" ]] && detected+="claude "
    [[ "$codex_status" == "installed" ]] && detected+="codex "
    [[ "$opencode_status" == "installed" ]] && detected+="opencode "
    echo "$detected"
}

ask_targets() {
    local detected="$1"

    if [[ -z "$detected" ]]; then
        log_warn "No supported tools detected."
        echo "  You can still deploy — the config files will be placed for when you install the tools."
        echo ""
    fi

    echo "Which target(s) do you want to deploy to?"
    echo ""
    echo "  1) Claude Code   (~/.claude/)"
    echo "  2) Codex CLI     (~/.codex/)"
    echo "  3) OpenCode      (~/.opencode/)"
    echo "  4) All detected  (${detected:-none detected})"
    echo "  5) All three"
    echo "  q) Quit"
    echo ""

    read -rp "  Choose [1-5, or q]: " choice

    case "$choice" in
        1) echo "claude" ;;
        2) echo "codex" ;;
        3) echo "opencode" ;;
        4) echo "$detected" ;;
        5) echo "claude codex opencode" ;;
        q|Q) echo "quit" ;;
        *) echo "invalid" ;;
    esac
}

show_summary() {
    echo ""
    log_bold "=========================================="
    log_bold "  Deployment Summary"
    log_bold "=========================================="
    echo ""
    echo "  Files copied:   $FILES_COPIED"
    echo "  Files skipped:  $FILES_SKIPPED (identical)"
    echo "  Backups created: $BACKUPS_CREATED"
    echo "  Errors:          $ERRORS"
    echo ""

    if [[ $ERRORS -eq 0 ]]; then
        log_ok "Deployment complete."
    else
        log_error "Deployment completed with $ERRORS error(s)."
    fi
    echo ""
}

# --- Argument Parsing ---

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)
                TARGET="$2"
                shift 2
                ;;
            --target=*)
                TARGET="${1#*=}"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --backup-only)
                BACKUP_ONLY=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --target TARGET   Deploy to: claude, codex, opencode, all"
                echo "  --dry-run         Show what would be done, change nothing"
                echo "  --backup-only     Only create backups of existing configs"
                echo "  --verbose, -v     Show detailed file operations"
                echo "  --help, -h        Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Run $0 --help for usage."
                exit 1
                ;;
        esac
    done
}

# --- Main ---

main() {
    parse_args "$@"

    show_banner
    validate_portable_dir

    # Detect tools (capture the last line as the detected tools string)
    local detect_output
    detect_output=$(detect_tools)
    local detected
    detected=$(echo "$detect_output" | tail -1)
    # Print the detection output (all but last line)
    echo "$detect_output" | head -n -1

    if $BACKUP_ONLY; then
        log_info "Backup-only mode — creating backups of existing configs..."
        for dir in "$HOME/.claude" "$HOME/.codex" "$HOME/.opencode"; do
            if [[ -d "$dir" ]]; then
                local backup_dir="${dir}.${BACKUP_SUFFIX}"
                cp -r "$dir" "$backup_dir"
                log_ok "Backed up $dir -> $backup_dir"
            fi
        done
        exit 0
    fi

    # Determine targets
    local targets=""
    if [[ -n "$TARGET" ]]; then
        if [[ "$TARGET" == "all" ]]; then
            targets="claude codex opencode"
        else
            targets="$TARGET"
        fi
    else
        # Interactive mode
        targets=$(ask_targets "$detected")
        if [[ "$targets" == "quit" ]]; then
            log_info "Cancelled."
            exit 0
        fi
        if [[ "$targets" == "invalid" ]]; then
            log_error "Invalid choice."
            exit 1
        fi
    fi

    echo ""
    log_info "Deploying to: $targets"
    echo ""

    # Deploy to each target
    for target in $targets; do
        case "$target" in
            claude)  deploy_claude_code ;;
            codex)   deploy_codex ;;
            opencode) deploy_opencode ;;
            *)
                log_error "Unknown target: $target"
                ((ERRORS++))
                ;;
        esac
        echo ""
    done

    show_summary
    exit $ERRORS
}

main "$@"
