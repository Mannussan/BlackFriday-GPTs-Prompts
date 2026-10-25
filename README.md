# GPTs Prompts And Jailbreaks

- [2024 May Update](./2024-May-Update.md)
- [Programming](./Programming.md)
- [Marketing](./Marketing.md)
- [Academic](./Academic.md)
- [Job Hunting](./Job-Hunting.md)
- [Game](./Game.md)
- [Creative](./Creative.md)
- [Prompt Engineering](./Prompt-Engineering.md)
- [Business](./Business.md)
- [Productivity & life style](./Productivity-&-life-style.md)
- [Jailbreaks](./Jailbreaks.md)

### Meet [AiDark.net](https://aidark.net/) the world's first fully autonomous AI software engineer. Devin is a tireless, skilled teammate, equally ready to build alongside you or independently complete tasks for you to review.

[![chrome_vbYonNUILv](https://github.com/friuns2/BlackFriday-GPTs-Prompts/assets/16543239/32800aa2-ea2c-4128-9d83-b64e3ce401b9)](https://www.youtube.com/watch?v=P-wWIpqe2CM)

https://github.com/friuns2/BlackFriday-GPTs-Prompts/assets/16543239/81f01fd1-9dca-4730-8d42-8690f83b75be





# All Prompts can be used in [GPTOS](https://play.google.com/store/apps/details?id=gptos.intelligence.assistant)

https://github.com/friuns2/BlackFriday-GPTs-Prompts/assets/16543239/c172af20-9bd6-4fb3-a717-16ff4f822056
# Demo Videos 
**Android self-coding app builder | 01 mobile first try**: https://youtube.com/clip/UgkxNbTCRWGeiOCQUhcm1KNW_izCP_-64-h8

# Chatverläufe unter Windows sortieren

1. Doppelklicke auf **Chatverlaeufe-sortieren.bat** in diesem Ordner.
2. Warte, bis die vollständige Vorschau mit allen Quelldateien und Zielpfaden erscheint.
3. Prüfe die Vorschläge. Nur wenn sie passen, gib exakt **JA** ein und drücke Enter.
4. Nur Enter, jede andere Eingabe oder Strg+C bricht vor dem Verschieben ab.

Ohne Eingabe von JA werden keine Dateien verschoben und keine Sortierordner angelegt.
Das Fenster bleibt nach Abschluss geöffnet, bis du eine Taste drückst.
Es läuft kein automatischer Hintergrunddienst.

## Einen bestimmten Ordner prüfen

Ziehe einen Ordner mit deinen Chat-Exporten auf **Chatverlaeufe-sortieren.bat**.
Dann wird dieser Ordner einschließlich seiner Unterordner geprüft.
Ohne übergebenen Ordner wird der in Windows eingestellte Desktop geprüft,
auch bei einer Umleitung nach OneDrive.

Berücksichtigt werden alle Dateien mit den Endungen .md, .markdown und .pdf.
Das Programm erkennt nicht zuverlässig, ob ein Dokument tatsächlich ein Chat ist.
Die Ähnlichkeit beruht auf gemeinsamen Textpassagen, nicht auf einem KI-Modell.
Die Gruppen sind Vorschläge und müssen vor der Freigabe kontrolliert werden.
Auf einem großen Desktop kann die Prüfung einige Minuten dauern.

## Ergebnis und Schutz vorhandener Dateien

Es werden nur Gruppen mit mindestens zwei ähnlichen Dokumenten verschoben.
Einzelne, leere oder nicht lesbare Dateien bleiben liegen.
Ziel: Chatverlaeufe_sortiert/Geschichte_... innerhalb des geprüften Ordners.
Gleiche Dateinamen erhalten Zusätze wie _2; vorhandene Dateien werden nicht überschrieben.
Der Programmordner, bereits sortierte Dateien und technische Ordner wie .git,
.venv und node_modules werden beim Durchsuchen eines übergeordneten Ordners ausgelassen.
Ordnerverknüpfungen werden nicht verfolgt.

Wenn eine Quelldatei während der Vorschau verändert wird oder ein Ziel inzwischen
belegt ist, bricht das Programm vor dem Verschieben ab. Bei einem späteren Fehler
wird die Anzahl bereits verschobener Dateien angezeigt; es gibt kein automatisches
Zurücksetzen aller bereits abgeschlossenen Verschiebungen.

## Voraussetzungen und PDFs

Erforderlich ist Python ab 3.10. Der Starter sucht py, python und python3.
Das lokale Paket enthält pypdf 6.21.2 im Unterordner _vendor und braucht zum
Sortieren weder Internet noch einen API-Schlüssel. Es lädt keine Dokumente hoch.
Für PDFs muss auswählbarer Text vorhanden sein. Bildscans benötigen vorher OCR.
Dateien, aus denen kein Text gelesen werden kann, werden mit Hinweis übersprungen.
Für einen frischen Download aus GitHub kann die optionale PDF-Bibliothek mit
`python -m pip install --target _vendor -r requirements-chat-sorter.txt`
im Programmordner installiert werden.

## Vorschau im Terminal

`python tools/organize_chat_histories.py "C:\Pfad\zum\Chatordner"`

Mit `--apply` zeigt derselbe Aufruf die Vorschau und fragt anschließend nach JA.
`--threshold 0.45` gruppiert strenger, `--threshold 0.20` lockerer.
Ohne `--apply` gibt es ausschließlich eine Vorschau.
