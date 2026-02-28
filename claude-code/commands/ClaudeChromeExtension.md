---
description: Chrome Extension Status prüfen, Architektur-Referenz und Troubleshooting
---

Prüfe den Status der Claude Code <-> Chrome Browser Extension.

## System-Check

Führe diese Checks parallel aus:

1. `cat ~/.config/google-chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json`
2. `ls -la ~/.claude/chrome/chrome-native-host`
3. `cat ~/.claude/chrome/chrome-native-host`
4. `claude --version`
5. `pgrep -a chrome | head -3`

## Auswertung

Zeige eine Status-Tabelle basierend auf den Ergebnissen:

| Komponente | Status | Details |
|---|---|---|
| NM Host JSON | OK/FEHLER | Pfad existiert, allowed_origins korrekt |
| Wrapper Script | OK/FEHLER | Existiert + executable |
| Chrome läuft | OK/FEHLER | Anzahl Chrome-Prozesse |
| Version-Match | OK/FEHLER | Version im Wrapper vs. `claude --version` |

## Bei Fehlern automatisch Lösung vorschlagen

- **Version-Mismatch** -> Wrapper-Script mit aktueller Version updaten
- **Script nicht executable** -> `chmod +x ~/.claude/chrome/chrome-native-host`
- **NM Host JSON fehlt** -> `claude --chrome` ausführen
- **Chrome nicht gestartet** -> Hinweis: Chrome neustarten, Extension prüfen

## Schnellreferenz

| Befehl | Was es tut |
|--------|-----------|
| `/chrome` | Verbindung aktivieren / Status prüfen |
| `claude --chrome` | Chrome-Modus starten (erstellt NM Host + Wrapper) |
| Extension Popup | Zeigt Verbindungsstatus zur CLI |

## Architektur (Kurzfassung)

```
Chrome Extension <--Native Messaging--> Wrapper Script <--stdin/stdout--> Claude CLI
```

- Extension kommuniziert über Chrome Native Messaging Protocol
- Wrapper Script in `~/.claude/chrome/` leitet JSON-Messages weiter
- NM Host JSON registriert den Wrapper bei Chrome (allowed_origins = Extension ID)
