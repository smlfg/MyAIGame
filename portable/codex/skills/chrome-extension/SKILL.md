---
name: chrome-extension
description: "Chrome Extension Status pruefen, Architektur-Referenz und Troubleshooting"
category: utility
cost-tier: free
dependencies:
  tools: [shell, file_read]
tags: [chrome, extension, troubleshooting]
---

# /chrome-extension -- Chrome Extension Status

Pruefe den Status der Claude Code <-> Chrome Browser Extension.

## System-Check

Fuehre diese Checks aus:

1. {{read_file("~/.config/google-chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json")}}
2. {{shell("ls -la ~/.claude/chrome/chrome-native-host")}}
3. {{read_file("~/.claude/chrome/chrome-native-host")}}
4. {{shell("claude --version")}}
5. {{shell("pgrep -a chrome | head -3")}}

## Auswertung

Zeige eine Status-Tabelle:

| Komponente | Status | Details |
|---|---|---|
| NM Host JSON | OK/FEHLER | Pfad existiert, allowed_origins korrekt |
| Wrapper Script | OK/FEHLER | Existiert + executable |
| Chrome laeuft | OK/FEHLER | Anzahl Chrome-Prozesse |
| Version-Match | OK/FEHLER | Version im Wrapper vs. claude --version |

## Bei Fehlern automatisch Loesung vorschlagen

- **Version-Mismatch** -> Wrapper-Script mit aktueller Version updaten
- **Script nicht executable** -> {{shell("chmod +x ~/.claude/chrome/chrome-native-host")}}
- **NM Host JSON fehlt** -> {{shell("claude --chrome")}} ausfuehren
- **Chrome nicht gestartet** -> Hinweis: Chrome neustarten, Extension pruefen

## Codex Limitation
This skill is specific to Claude Code's Chrome extension integration. Codex CLI does not have a Chrome extension. This skill is NOT portable to Codex -- it only applies to Claude Code environments.
