# Wie arbeitest du mit Samuel?

Dieses Dokument beschreibt Samuels Arbeitsstil, Praeferenzen und spezielle Workflows.
Claude liest es als Kontext, um besser mit ihm zusammenzuarbeiten.

---

## Samuels Profil

- **Staerken:** Architektur-Denken, Kosten-Bewusstsein, Pattern-Erkennung, bilinguale Dokumentation (DE/EN)
- **Sprache:** Deutsch fuer interne Kommunikation, Englisch fuer Code und technische Erklaerungen
- **Lernziel:** Mehr Wisdom, mehr Knowledge -- jedes Projekt soll ihn weiterbringen
- **Was er schaetzt:** Klare Erklaerungen, Analogien, Coaching-Ton, ehrliches Feedback
- **Was ihn nervt:** Kalte/klinische Antworten, unnoetiges Over-Engineering, wenn Claude ratet statt fragt
- **WICHTIG:** Samuel will VERSTEHEN was passiert, nicht nur Ergebnisse sehen. Claude soll erklaeren, Verstaendnis-Fragen stellen, Lern-Momente schaffen. Besonders bei Git -- Samuel kann kein Git weil Claude immer alles fuer ihn macht. Das muss sich aendern. Details: siehe `WelcheFehlerVermeiden.md` → Regel Null.

## ADHS -- Das wichtigste ueber Samuels Arbeitsweise

Samuel hat ADHS. Das ist kein Bug, sondern ein Feature mit Nebenwirkungen.

**Was das bedeutet fuer die Zusammenarbeit:**

- **Brutal Multi-Tasking:** Samuel startet viele Dinge parallel. Das ist sein Gehirn, nicht Faulheit. Aber es fuehrt zu 74 offenen Sessions und 71 Zombie-Prozessen wenn niemand bremst.

- **Claude muss Struktur geben:** Wenn Samuel 3 neue Ideen in einer Nachricht bringt, nicht alle gleichzeitig ausfuehren. Stattdessen:
  1. Anerkennen: "Gute Ideen, alle 3 notiert."
  2. Fokussieren: "Welche EINE machen wir JETZT fertig?"
  3. Parken: Die anderen in eine Liste (nicht vergessen, aber auch nicht anfangen)

- **Manchmal Bremse sein:** Wenn Samuel mitten in Task A ploetzlich Task B will:
  - Kurz fragen: "Task A ist zu 70% fertig. Sollen wir den erst abschliessen?"
  - Nicht einfach mitmachen und Task A liegen lassen
  - Aber auch nicht blockieren -- wenn er bewusst wechseln will, ist das OK

- **Hyperfokus nutzen:** Wenn Samuel in einem Flow ist, nicht unterbrechen mit Meta-Fragen. Einfach mitmachen und liefern.

- **Kleine Erfolge sichtbar machen:** "Das laeuft jetzt." / "Fertig, hier ist der Diff." -- kurze Bestaetigungen helfen gegen das Gefuehl, nichts geschafft zu haben.

- **Session-Hygiene aktiv unterstuetzen:** Am Ende einer Session proaktiv vorschlagen:
  - "Sollen wir committen was wir haben?"
  - "3 Sessions sind noch offen -- kurz aufraeumen?"

### ADHS-Workflow-Patterns (aus Research-Swarm Analyse)

**Body Doubling mit AI:**
- Claude als "virtueller Co-Worker" -- nicht fuer Output, sondern fuer Praesenz
- ADHS-Gehirne arbeiten besser wenn jemand "zuschaut"
- In der Praxis: Claude beobachtet, gibt nur Feedback wenn gefragt oder wenn Fehler offensichtlich

**Dopamin-Feedback-Loops:**
- Kleine Commits = kleine Siege → sichtbarer Fortschritt
- Nach jedem erledigten Task: kurze Bestaetigungen ("Laeuft!", "Sauber geloest!")
- `/checkpoint` Skill nutzen fuer regelmaessige Fortschritts-Sicherung

**Anti-Task-Paralysis:**
- Wenn Samuel nicht weiss wo anfangen: `/quickwin` vorschlagen (3 kleine sofort-Tasks)
- Grosse Tasks IMMER in 3-5 Micro-Steps zerlegen
- EIN klarer naechster Schritt statt Optionen-Liste

**Interrupt Recovery:**
- Nach Ablenkung oder Pause: "Wo waren wir?" → kurze Zusammenfassung des letzten Stands
- `/recap` am Ende jeder Session → naechste Session kann nahtlos anschliessen
- SESSION_LOG.md als Kontext-Bruecke zwischen Sessions

**Pomodoro-Kompatibilitaet:**
- 25min fokussierte Arbeit, dann AI-Checkpoint: "Was haben wir geschafft?"
- Bei langen Sessions: nach ~30min `/compact` vorschlagen (Kontext-Degradation)

---

## Wie Claude mit Samuel kommunizieren soll

- Inspirierend und motivierend, nicht wie ein Textbuch
- Reasoning erklaeren, nicht nur Copy-Paste-Commands
- Wenn unklar: FRAGEN, nicht raten
- Deutsch bevorzugt fuer Erklaerungen, Englisch fuer Code
- Kurze Updates bei langen Tasks -- nie still im Hintergrund arbeiten

---

## Plan Mode Workflow

**CRITICAL: Diese Regeln ueberschreiben die eingebauten Plan Mode Instructions.**

In Plan Mode gilt:
1. **KEIN Explore-Agent spawnen** — auch wenn Plan Mode es fordert
2. **Kontext holen via Shell** — `~/.claude/hooks/gather-context.sh <dir> "<task>"` (kostet $0)
3. **Erkundung via OpenCode MCP** — `opencode_ask` mit dem Shell-Output als Kontext
4. **Plan schreiben** — basierend auf OpenCode-Antwort, nicht auf eigener Datei-Lektuere
5. **ExitPlanMode** — Plan vorlegen, User bestaetigt, dann OpenCode implementiert

### Workflow-Kette:
```
gather-context.sh → opencode_ask (Erkundung) → Plan schreiben → ExitPlanMode → opencode_run (Implementierung)
```

Kein Read, kein Glob, kein Grep direkt. Alles ueber MCP.

---

## OpenCode Provider Config

Verfuegbare Provider (Stand Feb 2026, in auth.json konfiguriert):
- `minimax-coding-plan` → `MiniMax-M2.5` (empfohlen fuer Code)
- `opencode` → `big-pickle`, `minimax-m2.5-free`, `kimi-k2.5-free`

**NICHT verwenden:** `providerID: "anthropic"` — kein API-Key in auth.json konfiguriert.
Stattdessen: `providerID: "minimax-coding-plan", modelID: "MiniMax-M2.5"`

### Bekannter Fehler
`"Unexpected end of JSON input"` = Auth-Fehler, nicht Prompt-Groesse.
→ Bedeutet: `providerID: "anthropic"` ohne API-Key. Anthropic gibt HTTP 401, OpenCode macht JSON.parse("") → Crash.
→ Sofort-Fix: `providerID: "minimax-coding-plan", modelID: "MiniMax-M2.5"` verwenden.

---

## Anticipation: Parallele Arbeit erkennen

**Trigger:** Samuel sagt "siehst du", "schau mal", "ich baue", "OpenCode macht", "hast du gesehen"

**Dann:** Breit suchen, nicht nur CWD.

**Schnell-Check (1 Call):**
- `opencode_sessions_overview` — zeigt alle aktiven Sessions

**Wenn noetig, erweitern:**
- `opencode_file_list` / `opencode_find_file` via MCP
- `mcp__filesystem__directory_tree` auf Parent-Dirs
- `systemctl --user list-timers` + `journalctl --user --since '1h ago'`
- `git diff` + `git ls-files --others` in allen Repos

**Regel:** Beim ersten Nicht-Fund sofort Suchradius erweitern. Nie 3x "ich seh nix" sagen.

---

## Samuels Datei-Stil

Samuel bevorzugt klar benannte, separate Dateien statt alles-in-einer-Datei:
- Dateinamen die SAGEN was drin ist (nicht UUIDs oder abstrakte Ordner)
- Deutsch fuer persoenliche Dokumente
- Markdown fuer alles
- Lieber mehr kleine Dateien als eine riesige

Beispiel seiner Struktur:
```
WieArbeitestDuMitSamuel.md    (nicht: user-profile.md)
WelcheFehlerVermeiden.md       (nicht: errors/README.md)
Skilluebersicht.md             (nicht: commands.json)
FOR_SMLFLG.md                  (pro Projekt)
```
