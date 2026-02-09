"""Template-based narration for common Git/terminal commands."""

from __future__ import annotations

import re
import logging
from typing import Optional

from .providers import BaseNarrator

logger = logging.getLogger("multikanal.narration.providers")


class TemplateNarrator(BaseNarrator):
    """Generate narration using templates for common commands."""

    def __init__(self):
        super().__init__("template")

        self.templates = {
            "git commit": [
                "Ein Git Commit ist wie ein Schnappschuss deines Codes. Du speicherst den aktuellen Stand deiner Arbeit mit einer Nachricht, die beschreibt was du gemacht hast.",
                "Commits sind wie Meilensteine in deinem Projekt. Jeder Commit dokumentiert eine Änderung.",
            ],
            "git branch": [
                "Ein Git Branch ist wie ein paralleler Arbeitszweig. Du kannst neue Features entwickeln, ohne den Hauptcode zu beeinflussen.",
                "Branches ermöglichen es dir, isoliert zu arbeiten und Änderungen später zusammenzuführen.",
            ],
            "git checkout": [
                "Git Checkout wechselt zwischen Branches oder stellt alte Versionen deiner Dateien wieder her.",
                "Mit Checkout kannst du in andere Branches wechseln oder Dateien auf einen früheren Stand zurücksetzen.",
            ],
            "git merge": [
                "Git Merge kombiniert Änderungen von verschiedenen Branches. Die Änderungen vom Feature-Branch werden in den Hauptbranch eingefügt.",
                "Ein Merge fährt die Geschichte verschiedener Branches zusammen.",
            ],
            "git push": [
                "Git Push lädt deine lokalen Commits auf den Remote-Server hoch. Deine Kollegen können jetzt deine Änderungen sehen.",
                "Push synchronisiert deine lokalen Änderungen mit dem Remote-Repository.",
            ],
            "git pull": [
                "Git Pull holt die neuesten Änderungen vom Server und merge sie in deinen lokalen Code.",
                "Pull aktualisiert deinen lokalen Stand mit dem Remote-Repository.",
            ],
            "git status": [
                "Git Status zeigt dir, welche Dateien du geändert hast und welche bereit zum Committen sind.",
                "Status gibt dir einen Überblick über den aktuellen Zustand deines Repositories.",
            ],
            "docker": [
                "Docker Container sind leichte, isolierte Umgebungen die deine Anwendung mit allem was sie braucht verpacken.",
                "Container sind wie Mini-Computer die deine Software überall gleich laufen lassen.",
            ],
            "python": [
                "Python ist eine Programmiersprache die einfach zu lernen und sehr vielseitig ist.",
                "Mit Python kannst du Webanwendungen, Skripte und vieles mehr erstellen.",
            ],
            "test": [
                "Tests überprüfen ob dein Code richtig funktioniert. Sie helfen Fehler früh zu finden.",
                "Unit-Tests prüfen einzelne Funktionen, Integrationstests prüfen das Zusammenspiel.",
            ],
            "error": [
                "Es ist ein Fehler aufgetreten. Das passiert jedem Entwickler. Die Fehlermeldung hilft dir das Problem zu verstehen.",
                "Fehler sind normal beim Programmieren. Die gute Nachricht: der Fehler sagt dir genau was falsch ist.",
            ],
            "file": [
                "Eine Datei speichert Daten auf deinem Computer. Programmcode, Texte und Bilder sind alles Dateien.",
                "Dateien organisiert man in Ordnern um alles wiederzufinden.",
            ],
            "install": [
                "Installation bedeutet ein Programm auf deinem Computer einzurichten. Es wird kopiert und konfiguriert.",
                "Nach der Installation kannst du das Programm nutzen.",
            ],
            "delete": [
                "Löschen entfernt eine Datei oder einen Ordner. Sei vorsichtig - gelöschte Daten sind oft schwer wiederherzustellen.",
                "In manchen Systemen gibt es einen Papierkorb wo gelöschte Dateien zwischengespeichert werden.",
            ],
            "create": [
                "Erstellen bedeutet etwas Neues anlegen. Eine neue Datei, ein neuer Ordner oder ein neuer Branch.",
                "Du beginnst etwas Neues mit dem Erstellen-Befehl.",
            ],
            "npm": [
                "NPM ist der Paketmanager für JavaScript. Er installiert und verwaltet Bibliotheken für dein Projekt.",
                "Mit NPM kannst du fremden Code in dein Projekt einbinden und wiederverwenden.",
            ],
            "docker-compose": [
                "Docker Compose definiert mehrere Container in einer Datei. So startest du ganze Anwendungen mit einem Befehl.",
                "Compose orchestriert deine Container und deren Verbindungen untereinander.",
            ],
            "kubernetes": [
                "Kubernetes orchestriert Container in Clustern. Es automatisiert Skalierung, Deployment und Verwaltung.",
                "K8s, wie Kubernetes oft abgekürzt wird, hält deine Anwendungen am Laufen.",
            ],
            "kubectl": [
                "Kubectl ist das Kommandozeilenwerkzeug für Kubernetes. Damit steuerst du deine Cluster.",
                "Mit kubectl verwaltest du Pods, Services und Deployments in Kubernetes.",
            ],
            "ansible": [
                "Ansible ist ein Automatisierungswerkzeug. Es konfiguriert Server und deployt Anwendungen ohne Agenten.",
                "Mit Ansible schreibst du Playbooks, die deine Infrastruktur als Code beschreiben.",
            ],
            "ssh": [
                "SSH verbindet dich sicher mit entfernten Serern. Es ist wie eine verschlüsselte Konsole.",
                "Mit SSH kannst du von überall auf deine Server zugreifen.",
            ],
            "cron": [
                "Cron ist ein Zeitplaner. Es führt Befehle automatisch zu bestimmten Zeiten aus.",
                "Cronjobs sind wie persönliche Assistenten die wiederkehrende Aufgaben erledigen.",
            ],
            "api": [
                "Eine API ist eine Schnittstelle zwischen Programmen. Sie definiert wie Software miteinander kommuniziert.",
                "APIs ermöglichen es verschiedenen Anwendungen, Daten auszutauschen.",
            ],
            "database": [
                "Eine Datenbank speichert strukturiert Informationen. SQL-Datenbanken wie PostgreSQL nutzen Tabellen.",
                "Datenbanken sind das Gedächtnis deiner Anwendung.",
            ],
            "sql": [
                "SQL ist die Sprache für Datenbanken. SELECT holt Daten, INSERT fügt welche hinzu.",
                "Mit SQL fragst du deine Datenbank gezielt nach Informationen.",
            ],
            "nginx": [
                "Nginx ist ein Webserver und Reverse-Proxy. Er leitet Anfragen an deine Anwendungen weiter.",
                "Nginx kann auch als Load Balancer mehrere Server bedienen.",
            ],
            "aws": [
                "AWS ist Amazons Cloud-Plattform. Sie bietet Rechenkraft, Speicher und viele Dienste.",
                "Mit AWS skalierst du Anwendungen global in Minuten.",
            ],
            "cloud": [
                "Cloud-Computing bedeutet Computing-Ressourcen aus dem Internet zu beziehen. Du bezahlst nur was du nutzt.",
                "Die Cloud macht Infrastruktur elastisch und sofort verfügbar.",
            ],
            "deploy": [
                "Deployment bedeutet deine Anwendung in die Produktion zu bringen. Es wird live geschaltet.",
                "Ein gutes Deployment ist automatisiert und minimiert Ausfallzeiten.",
            ],
            "build": [
                "Build kompiliert deinen Code in ausführbare Form. Bei JavaScript wird ES6 zu älterem Code umgewandelt.",
                "Der Build-Schritt bereitet deine Anwendung für die Ausführung vor.",
            ],
            "debug": [
                "Debugging findet und behebt Fehler im Code. Debugger erlauben schrittweise Ausführung.",
                "Gute Debugging-Tools sind wie ein Mikroskop für deinen Code.",
            ],
            "log": [
                "Logs zeichnen was in deiner Anwendung passiert. Sie sind wichtig für Fehlersuche und Monitoring.",
                "Strukturierte Logs helfen dir, Probleme schnell zu finden.",
            ],
            "config": [
                "Konfiguration steuert wie deine Anwendung läuft. Sie trennt Einstellungen vom Code.",
                "Gute Konfiguration ermöglicht Anpassung ohne Neukompilierung.",
            ],
            "environment": [
                "Umgebungsvariablen speichern Einstellungen außerhalb des Codes. Sie sind perfekt für Geheimnisse.",
                "In verschiedenen Umgebungen wie Entwicklung und Produktion nutzt du unterschiedliche Variablen.",
            ],
            "port": [
                "Ein Port ist ein Endpunkt für Netzwerkverbindungen. HTTP nutzt Port 80, HTTPS Port 443.",
                "Mehrere Anwendungen können gleichzeitig auf einem Computer laufen, jeder an einem anderen Port.",
            ],
            "process": [
                "Ein Prozess ist ein laufendes Programm im Speicher. Jeder Prozess hat seine eigene Umgebung.",
                "Mit ps siehst du alle laufenden Prozesse auf deinem System.",
            ],
            "service": [
                "Ein Service ist ein Hintergrundprozess. Er läuft ständig und wartet auf Anfragen.",
                "Systeme wie systemd verwalten Services und starten sie automatisch nach Abstürzen.",
            ],
            "terminal": [
                "Das Terminal ist deine Kommandozeile. Hier steuerst du den Computer mit Textbefehlen.",
                "Das Terminal ist mächtig und effizient für Entwickler.",
            ],
            "shell": [
                "Die Shell ist dein Kommandointerpreter. Sie versteht Befehle und führt sie aus.",
                "Bash und Zsh sind beliebte Shells unter Linux und macOS.",
            ],
            "path": [
                "Der Pfad zeigt wo eine Datei oder ein Programm liegt. Er ist wie eine Adresse im Dateisystem.",
                "Die PATH-Variable enthält Verzeichnisse, in denen der Computer nach Programmen sucht.",
            ],
            "permission": [
                "Berechtigungen kontrollieren wer was mit einer Datei machen darf. Lesen, Schreiben, Ausführen.",
                "Mit chmod änderst du Dateiberechtigungen unter Unix-Systemen.",
            ],
            "user": [
                "Ein Benutzerkonto repräsentiert eine Person oder einen Dienst. Jedes hat eigene Rechte.",
                "Unter Linux gibt es Benutzer, Gruppen und Others mit unterschiedlichen Zugriffsrechten.",
            ],
            "sudo": [
                "Sudo führt Befehle mit Administratorrechten aus. Es ist wie ein Schlüssel für Systemaktionen.",
                "Sei vorsichtig mit Sudo - es kann viel verändern auf deinem System.",
            ],
            "grep": [
                "Grep durchsucht Dateien nach Textmustern. Es ist das Schweizer Taschenmesser der Textsuche.",
                "Mit regulären Ausdrücken wird Grep noch mächtiger.",
            ],
            "find": [
                "Find sucht Dateien im Dateisystem nach verschiedenen Kriterien wie Name, Größe oder Datum.",
                "Find ist unverzichtbar für die Navigation in großen Projekten.",
            ],
            "curl": [
                "Curl überträgt Daten von oder zu Servern. Es unterstützt viele Protokolle wie HTTP und FTP.",
                "Curl ist perfekt um APIs zu testen oder Dateien herunterzuladen.",
            ],
            "http": [
                "HTTP ist das Protokoll für Webkommunikation. GET holt Seiten, POST sendet Daten.",
                "Statuscodes wie 200 bedeuten Erfolg, 404 bedeutet nicht gefunden.",
            ],
            "https": [
                "HTTPS ist die verschlüsselte Version von HTTP. Es schützt Daten während der Übertragung.",
                "HTTPS nutzt TLS-Zertifikate um die Verbindung zu sichern.",
            ],
            "certificate": [
                "Zertifikate bestätigen die Identität von Servern. Sie ermöglichen verschlüsselte Verbindungen.",
                "Let's Encrypt bietet kostenlose SSL-Zertifikate.",
            ],
            "git": [
                "Git ist ein Versionskontrollsystem. Es verfolgt Änderungen an deinem Code über die Zeit.",
                "Git ermöglicht Zusammenarbeit und macht Experimente sicher.",
            ],
        }

    def generate(self, text: str, system_prompt: str = "", language: str = "") -> str:
        if not text.strip():
            return ""

        text_lower = text.lower()

        for key, narrations in self.templates.items():
            if key in text_lower:
                narration = narrations[0]
                logger.info(f"Template narration for: {key}")
                return narration

        fallback = "Das ist eine technische Ausgabe. Ich erkläre es kurz: "
        words = text.split()[:20]
        fallback += " ".join(words)

        if len(text.split()) > 20:
            fallback += " ..."

        logger.info(f"Fallback narration: {len(fallback)} chars")
        return fallback

    def check_health(self) -> bool:
        return True
