# ADHS-First TUI UX Design

> ADHS-Unterstuetzung ist kein "Nice to Have". Es ist das Fundament.
> Jede Komponente hier wurde mit einem einzigen Ziel designed:
> Das ADHS-Gehirn bleibt im Flow, nicht im Chaos.

---

## Design-Philosophie

**Das ADHS-Gehirn braucht:**
- Einen Anker (Fokus-Ziel immer sichtbar)
- Sofortiges Feedback (Dopamin durch sichtbare Fortschritte)
- Niedrige Einstiegshuerden (Quick Wins gegen Task Paralysis)
- Einen Sicherheitsnet (Distraction Parking statt Rabbit Holes)
- Einen Begleiter (Body Doubling gegen das Alleinsein im Flow)

**Anti-Patterns die wir VERMEIDEN:**
- Information Overload (zu viele Zahlen/Farben/Animationen gleichzeitig)
- Leere Zustande ohne Handlungsaufforderung
- Lange Ladezeiten ohne Feedback
- Abstrakte Fortschrittsanzeigen ("42% fertig" bedeutet nichts)

---

## Komponente 1: Focus Bar (immer sichtbar, ganz oben)

Die Focus Bar ist der Nordstern der Session. Sie ist IMMER sichtbar,
auch wenn alle anderen Panels eingeklappt sind. Sie brennt sich ins
periphere Sehfeld ein. Wenn Samuel abschweift, ist das Ziel noch da.

### Standard-Zustand (alles laeuft gut):

```
+------------------------------------------------------------------------------+
| FOCUS: "Port skills to Codex"           |  23:45 / 25:00  |  Streak: 3  [Park] |
+------------------------------------------------------------------------------+
```

### Erweitert (Farben & Details):

```
+------------------------------------------------------------------------------+
|  FOCUS: "Port skills to Codex"   | [################    ] 23:45/25:00  | x3 | [Park Thought] |
|  /focus aktiv                    |  Pomodoro 2 von 4                   |    |                |
+------------------------------------------------------------------------------+
```

### Warn-Zustand (Drift erkannt — sanfte Bremse):

```
+-- FOCUS CHECK ------------------------------------------------------------------+
|  Warte. Unser Ziel: "Port skills to Codex"                                      |
|  Die letzte Anfrage war: "Wie baut man ein Rust HTTP Server?"                   |
|                                                                                  |
|  Optionen:  [1] Parken & zum Ziel zurueck   [2] Ziel anpassen   [3] 5min Abst. |
+---------------------------------------------------------------------------------+
```

### Pomodoro-Ende (Feier-Moment):

```
+-- POMODORO DONE! ---------------------------------------------------------------+
|  25 Minuten konzentriert. Das war Schritt 3 von 4 heute.                        |
|  Streak: 3  -> 4  [+1]                                                          |
|                                                                                  |
|  [Pause starten - 5min]    [Gleich weitermachen]    [/checkpoint setzen]        |
+---------------------------------------------------------------------------------+
```

### Design-Details:
- Hoehe: 1-2 Zeilen (minimal, nicht ablenkend)
- Farbe: Gruen (normal) -> Gelb (Warnung, 5min vor Ende) -> Rot (Drift erkannt)
- Timer-Animation: Zeichen-basiert `[####    ]`, kein Blinken ausser bei Warnung
- "Park Thought" Button: immer sichtbar, 1-Klick zum Abladen von Gedanken
- Streak-Counter: zeigt nur an, inkrementiert bei jedem abgeschlossenen Pomodoro

---

## Komponente 2: QuickWin Sidebar (einklappbar, rechts)

Gegen Task Paralysis. Wenn Samuel nicht weiss wo anfangen, sind hier
3 sofort startbare Tasks. Kein Nachdenken. Einfach klicken und loslegen.

### Eingeklappt (Standard):

```
                                       +--------+
                                       | QUICK  |
                                       | WINS   |
                                       |   3    |
                                       +--------+
```

### Ausgeklappt (normal):

```
                              +---------------------------+
                              | Quick Wins                |
                              |---------------------------|
                              | 1. Fix typo in README     |
                              |    ~2min  [START]         |
                              |                           |
                              | 2. Add docstring to main()|
                              |    ~5min  [START]         |
                              |                           |
                              | 3. Update .gitignore      |
                              |    ~3min  [START]         |
                              |---------------------------|
                              | [Refresh]  [/quickwin]    |
                              +---------------------------+
```

### Task laeuft (in Bearbeitung):

```
                              +---------------------------+
                              | Quick Wins                |
                              |---------------------------|
                              | 1. Fix typo in README     |
                              |    [###########   ] 1:45  |
                              |    [Done!] [Abbrechen]    |
                              |                           |
                              | 2. Add docstring...       |
                              |    ~5min  (als naechstes) |
                              |                           |
                              | 3. Update .gitignore      |
                              |    ~3min  (als naechstes) |
                              +---------------------------+
```

### Abschluss-Feedback (Dopamin!):

```
                              +---------------------------+
                              |  *** WIN! ***             |
                              |                           |
                              |  "Fix typo in README"     |
                              |  erledigt in 1:52         |
                              |                           |
                              |  * * * * * * * * * *      |
                              |  Streak: 3  +1            |
                              |                           |
                              |  [Naechster Win]          |
                              +---------------------------+
```

### Design-Details:
- Die 3 Tasks kommen von `/quickwin` — automatisch analysiert aus git status + TODOs
- Zeitschaetzung ist prominent (gibt Orientierung: "Das schaffe ich!")
- Abschluss-Animation: ASCII-Sparkle (` * ` Zeichen, die kurz aufleuchten)
- Bei 3/3 Wins: Groessere Celebration mit Streak-Counter
- "Refresh" holt neue Quick Wins falls aktuelle nicht passen

---

## Komponente 3: Checkpoint Celebration (Overlay / Modal)

Sichtbarer Fortschritt ist Treibstoff. Checkpoint Celebration macht
jeden Git-Commit zu einem kleinen Triumph. Das ADHS-Gehirn braucht diese
Anker — sonst fuehlt sich eine 3-Stunden-Session wie "nix geschafft" an.

### Trigger:
- Manuell via `/checkpoint`
- Automatisch alle 25 Minuten (Pomodoro-Ende)
- Automatisch bei `git commit` (Hook)

### Checkpoint-Modal:

```
+====================================================+
|                                                    |
|          CHECKPOINT GESETZT!                       |
|                                                    |
|  Commit: "Add skill parser for Codex format"       |
|                                                    |
|  Was hat sich geaendert:                           |
|  - 3 Dateien geaendert                             |
|  - +127 / -23 Zeilen                               |
|  - 2 neue Tests hinzugefuegt                       |
|                                                    |
|  Ziel-Fortschritt:                                 |
|  "Port skills to Codex"                            |
|  [########################################  ] 80%  |
|                                                    |
|  Session-Streak: x4  (neue Bestleistung heute!)   |
|                                                    |
|  "Du hast den Elefanten angefasst.                 |
|   Die meisten schauen ihn nur an."                 |
|                                                    |
|  [OK, weiter!]   [Pause (5min)]   [Session beenden]|
+====================================================+
```

### Minimal-Version (bei kleinen Commits):

```
+------------------------------------------+
|  Checkpoint! "Fix typo in README"         |
|  1 Datei  |  +1/-1 Zeilen  |  Streak: x4  |
|  [OK]                                     |
+------------------------------------------+
```

### Design-Details:
- Fortschrittsbalken zeigt Fortschritt zum Session-Ziel (geschaetzt durch AI)
- Motivations-Zitat rotiert aus einem Pool (aus `/bigwin` und `/checkpoint` Skills)
- Bei neuem Streak-Rekord: groessere Animation
- Automatisches Schliessen nach 5 Sekunden (kein blockierter Flow)
- Muss NICHT interaktiv bestaetigt werden ausser bei Session-Ende

---

## Komponente 4: Distraction Parking Lot (unten, einklappbar)

Das ADHS-"Aber warte, was ist mit...?"-Problem. Statt den Gedanken zu
vergessen oder ihm nachzujagen, landet er sicher im Parking Lot.
Kein Rabbit Hole. Kein schlechtes Gewissen. Nur: "Notiert, weiter."

### Eingeklappt (Standard):

```
+-- Parking Lot: 3 ideas parked ----------------------------------------[v]--+
```

### Ausgeklappt:

```
+-- Parking Lot (3 geparkte Ideen) ------------------------------------[^]---+
|                                                                             |
|  [+] Neue Idee parken...                                                    |
|                                                                             |
|  1.  "Rust HTTP Server Tutorial lesen"                    [->Task] [Losch]  |
|      Geparkt 14:23  |  Kategorie: Lernen                                    |
|                                                                             |
|  2.  "Was ist der beste TUI-Framework fuer Python?"       [->Task] [Losch]  |
|      Geparkt 14:31  |  Kategorie: Recherche                                 |
|                                                                             |
|  3.  "README mit Badges aufhuebschen"                     [->Task] [Losch]  |
|      Geparkt 14:45  |  Kategorie: Housekeeping                              |
|                                                                             |
|  [Alle als Tasks exportieren]   [Session-Log anhaengen]   [Alle loeschen]  |
+-----------------------------------------------------------------------------+
```

### Quick-Park Dialog (erscheint wenn Drift erkannt):

```
+-- Gedanke parken? --------------------------------------------------+
|                                                                      |
|  Du hast gefragt: "Wie baut man einen Rust HTTP Server?"             |
|                                                                      |
|  Das passt nicht zum Ziel: "Port skills to Codex"                   |
|                                                                      |
|  Idee parkent: [ Rust HTTP Server erkunden           ]  [Parken!]   |
|                                                                      |
|  Oder:  [Ziel aendern]   [5min Abstecher]   [Ignorieren]            |
+----------------------------------------------------------------------+
```

### Session-Ende Export:

```
+-- Parking Lot Export -----------------------------------------------+
|                                                                      |
|  3 geparkte Ideen diese Session:                                     |
|                                                                      |
|  Diese in SESSION_LOG.md unter "Geparkte Ideen" exportieren?        |
|                                                                      |
|  [Ja, exportieren]   [Als neue Tasks anlegen]   [Verwerfen]         |
+----------------------------------------------------------------------+
```

### Design-Details:
- Automatische Kategorisierung: Lernen / Recherche / Feature / Housekeeping / Sonstiges
- Zeitstempel zeigt wann die Idee entstand (hilft beim Priorisieren)
- "->Task" promoted die Idee in die echte Task-Liste
- Integration mit Focus Mode: Drift-Erkennung triggert Quick-Park Angebot
- Farbe: Gedaempft (grau/blau) damit es nicht vom Fokus ablenkt

---

## Komponente 5: Session Dashboard (Startup Screen)

Der erste Eindruck zaehlt. Das Dashboard macht die Session zu einem
bewussten Start statt einem Hineinstolpern. ONE GOAL. Klares Ziel.
Kein "wo war ich nochmal?"

### Startup Screen:

```
+====================================================================+
|                                                                    |
|   Willkommen zurueck, Samuel.                                      |
|                                                                    |
|   Letzte Session: 2026-02-25                                       |
|   "Port skills to Codex — skill parser 80% fertig"                |
|   Offene Punkte: skill_runner.py, Tests fuer edge cases            |
|                                                                    |
|   Dein EINES Ziel heute:                                           |
|   +--------------------------------------------------------------+ |
|   | > _                                                          | |
|   +--------------------------------------------------------------+ |
|   (Ein Satz. Kein "und". Kein "ausserdem". EIN Ding.)             |
|                                                                    |
+====================================================================+
```

### Nach Zieleingabe (Schritt 2):

```
+====================================================================+
|                                                                    |
|   Ziel: "skill_runner.py fertigstellen und testen"                 |
|                                                                    |
|   Wie fuehlt sich deine Energie heute an?                          |
|                                                                    |
|   [Batterie: Voll]   [Batterie: Mittel]   [Batterie: Leer]        |
|      High Energy       Normal Flow          Nur Quick Wins         |
|                                                                    |
+====================================================================+
```

### Energie: Voll (High Energy):

```
+====================================================================+
|   Energie: VOLL  | Ziel: "skill_runner.py fertig"                  |
|                                                                    |
|   Vorgeschlagene Quick Wins zum Warmlaufen:                        |
|   1. Fix TODO in skill_parser.py  ~3min  [START]                   |
|   2. Run test suite, pruefe Status ~2min  [START]                  |
|   3. Update ADHD.md mit Stand      ~2min  [START]                  |
|                                                                    |
|   [Mit Quick Wins starten]   [Direkt zum Ziel]   [/bigwin starten] |
+====================================================================+
```

### Energie: Leer (Low Energy / Schlechter Tag):

```
+====================================================================+
|   Energie: NIEDRIG  | Ziel: "skill_runner.py fertig"               |
|                                                                    |
|   Kein Druck. Heute nur Quick Wins.                                |
|   Drei kleine Dinge erledigen ist mehr als nichts.                 |
|                                                                    |
|   Deine 3 Quick Wins fuer heute:                                   |
|   1. 1 Zeile Code verbessern        ~5min  [START]                 |
|   2. 1 Kommentar schreiben          ~3min  [START]                 |
|   3. Session Log lesen              ~2min  [START]                 |
|                                                                    |
|   [Starten]    [Ich brauche erstmal Kaffee (5min Timer)]           |
+====================================================================+
```

### Design-Details:
- Energie-Selektor bestimmt Task-Schwierigkeit fuer die ganze Session
- Vorherige Session wird automatisch geladen (aus SESSION_LOG.md + /recap)
- Zieleingabe ist ein freies Textfeld — aber Validierung pruefen auf "und"/"ausserdem"
  und schlaegt vor das Ziel aufzuteilen
- "Kaffee-Timer" bei Low Energy: 5min Countdown, dann Session-Start

---

## Komponente 6: Body Doubling Mode (optionaler Overlay)

Der groesste ADHS-Hack: Wenn jemand zuschaut, arbeitet das Gehirn besser.
Body Doubling Mode macht den AI-Agent sichtbar — er "sitzt mit" Samuel zusammen.
Nicht aufdringlich. Nur: "Du bist nicht allein hier."

### Body Doubling Overlay (dezent, Ecke):

```
+-- Ich bin dabei ------+
|  Working on:          |
|  skill_runner.py      |
|                       |
|  Status: Analyzing    |
|  dependencies...      |
|                       |
|  [Minimize]           |
+-----------------------+
```

### Erweiterter Modus (Seitenleiste):

```
                              +---------------------------+
                              | Ich arbeite mit dir       |
                              |---------------------------|
                              | Was ich gerade tue:       |
                              |                           |
                              | Lese skill_parser.py      |
                              | [##########      ] 60%    |
                              |                           |
                              | Naechstes:                |
                              | Tests analysieren         |
                              |                           |
                              |---------------------------|
                              | Laut gedacht:             |
                              | "Die import-Struktur      |
                              |  ist sauber. Gleich bin   |
                              |  ich fertig."             |
                              |                           |
                              | [Stumm]  [Minimieren]     |
                              +---------------------------+
```

### Narrations-Stile:

**Freundlich / Casual:**
```
| Hmm, interessant. Diese Funktion      |
| koennte einfacher sein. Gleich...     |
```

**Professionell / Fokussiert:**
```
| Analysiere: main.py:142-167           |
| Pattern: dependency injection         |
| Status: validiert                     |
```

**Motivierend (fuer Low-Energy-Sessions):**
```
| Du machst das super.                  |
| Dieser Schritt hier ist wichtig.      |
| Gleich haben wir's.                   |
```

### Body Doubling Trigger:
- Manuell via `/bigwin` Schritt 4 ("Body-Doubling aktivieren")
- Automatisch bei Low-Energy Session-Start
- Automatisch wenn keine Aktivitaet fuer 3+ Minuten (sanfter Check-In)

### Check-In nach Inaktivitaet:

```
+-- Hey, alles ok? -----------------------------------------------+
|                                                                  |
|  Ich hab 4 Minuten nichts von dir gehoert.                       |
|                                                                  |
|  [Ich arbeite noch]   [Kurze Pause]   [Gedanke parken]          |
|                                                                  |
|  (Keine Antwort = alles gut, ich warte weiter)                  |
+------------------------------------------------------------------+
```

### Design-Details:
- Kann auf Wunsch stumm geschaltet werden (nur visuell, kein Text)
- Narrations-Stil waehlt Samuel beim Session-Start
- Verschwindet bei Checkpoint-Celebration, kehrt danach zurueck
- Keine Unterbrechungen waehrend Flow — nur dezente Updates
- Position: Ecke unten rechts (Standard), konfigurierbar

---

## Gesamtlayout: Alle Komponenten zusammen

### Standard-Ansicht (normaler Flow):

```
+-- FOCUS: "Port skills to Codex" ----- [####] 18:30/25:00 -- Streak:3 -- [Park] --+
|                                                                                     |
|  +------ MAIN CONTENT AREA ----------------------------------------+  +---------+ |
|  |                                                                  |  | QUICK   | |
|  |  > opencode: Analyzing skill_parser.py...                       |  | WINS  3 | |
|  |                                                                  |  +---------+ |
|  |  > claude: skill_runner.py braucht noch:                        |               |
|  |    1. Error handling fuer missing files                         |               |
|  |    2. Tests fuer edge cases                                     |               |
|  |    3. Integration mit Codex API                                 |               |
|  |                                                                  |               |
|  |  > samuel: lass uns mit error handling anfangen                 |               |
|  |                                                                  |               |
|  |  > opencode: Verstanden. Oeffne skill_runner.py...             |               |
|  |                                                                  |               |
|  +------------------------------------------------------------------+               |
|                                                                                     |
|  +-- INPUT: -----------------------------------------------+  [Send]  [/cmd]  --+ |
|  | > _                                                      |                      |
|  +--------------------------------------------------------+                        |
|                                                                                     |
|  +-- Parking Lot: 2 ideas parked ----------------------------------------[v]----+ |
+-------------------------------------------------------------------------------------+
```

### Checkpoint-Moment (Overlay ueber allem):

```
+====================================================================+
|                   CHECKPOINT!                                      |
|                                                                    |
|  "Add error handling to skill_runner.py"                          |
|  3 Dateien | +47/-5 Zeilen | Tests: 12/12                         |
|                                                                    |
|  Fortschritt: [#####################################     ] 75%     |
|  Streak: x4 (heute!)                                               |
|                                                                    |
|  "Du bist weiter als gestern. Das zaehlt."                        |
|                                                                    |
|  [Weiter]           [Pause]           [Session beenden]           |
+====================================================================+
```

---

## Farbschema

| Zustand | Farbe | Bedeutung |
|---------|-------|-----------|
| Normal / On-Goal | Gruen | Alles laeuft |
| Warnung (5min vor Ende) | Gelb | Bald Pause |
| Drift erkannt | Orange | Sanfte Bremse |
| Blocker | Rot | Aufmerksamkeit noetig |
| Celebration | Cyan/Blau | Dopamin-Hit |
| Parking Lot | Grau | Ruhig, nicht ablenkend |
| Body Doubling | Lila / Indigo | "Ich bin dabei" |

---

## Keyboard Shortcuts (ADHS-optimiert: wenige, einpraegsame)

```
[Space]    = Park current thought (immer verfuegbar)
[Tab]      = Toggle Quick Wins sidebar
[Enter]    = Confirm / Start next quick win
[Esc]      = Close modal / minimize overlay
[F1]       = Focus Mode aktivieren (/focus)
[F5]       = Checkpoint setzen (/checkpoint)
[F12]      = Body Doubling Mode toggle
```

**Design-Prinzip:** Max 8 Shortcuts. Mehr = Kognitiver Overhead = ADHS-Kryptonite.

---

## Technische Implementierungshinweise

### TUI Framework-Optionen:
- **Textual (Python)**: Beste ADHS-UX, CSS-aehnliches Layout, reaktiv
- **Ratatui (Rust)**: Performant, gut fuer Echtzeit-Updates
- **Blessed (Node.js)**: Schneller Einstieg, weniger Features

### State Management:
- Session-Ziel in `session.json` (fluechtiger Speicher)
- Pomodoro-State in Datei (ueberlebt Neustarts)
- Parking Lot in `SESSION_LOG.md` (persistent, lesbar)
- Streak in `.streak` Datei (simpel, robust)

### Integration mit bestehenden Skills:
- `/focus` -> setzt Focus Bar Ziel
- `/quickwin` -> befuellt Quick Wins Sidebar
- `/checkpoint` -> triggert Checkpoint Celebration
- `/recap` -> liest SESSION_LOG.md fuer Startup Dashboard
- `/bigwin` -> aktiviert Body Doubling Mode automatisch

---

## Warum das funktioniert (ADHS-Psychologie)

**Focus Bar:** Externe Repraesentierung des Ziels. Das ADHS-Gehirn vergisst
Ziele wenn sie nicht sichtbar sind. Die Bar ist der Anker der nicht
verschwindet.

**Quick Wins:** Dopamin-Primer. Der erste Schritt ist der schwerste.
3 klare, kleine Tasks senken die Einstiegshuerden auf null.

**Checkpoint Celebration:** Working Memory ist bei ADHS oft schwach.
"Hab ich heute ueberhaupt was geschafft?" ist eine echte Frage.
Der Checkpoint macht Fortschritt unbestreitbar sichtbar.

**Parking Lot:** Verhindert den ADHS-Gedanken-Loop. Statt "ich darf das
nicht vergessen" wird es "ich hab's notiert, kann es loslassen".
Das Gehirn entspannt sich.

**Session Dashboard:** Ritualisierter Start. ADHS-Gehirne brauchen Rituale
als Uebergang in den Arbeitsmodus. "Was ist dein EINES Ziel?" ist dieses Ritual.

**Body Doubling:** Bekanntestes ADHS-Werkzeug. Wenn jemand zuschaut — auch
ein AI-Agent — reduziert das Prokrastination dramatisch. Es ist nicht
Einbildung. Es ist Neurologie.

---

*Erstellt fuer MyAIGame Portable — ADHS-Support als Core Value Proposition*
*Task #16 — Session 2026-02-26*
