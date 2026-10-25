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




## Chatverläufe auf dem Desktop sortieren

Mit `tools/organize_chat_histories.py` können Markdown- und PDF-Chatverläufe rekursiv unter dem Desktop gescannt und nach ähnlichem Geschichten-/Themeninhalt gruppiert werden. Standardmäßig läuft das Werkzeug als Trockenlauf und verschiebt noch nichts:

**Es läuft nichts im Hintergrund.** Nach dem Herunterladen oder Zusammenführen muss das Werkzeug bewusst in einem Terminal gestartet werden. Der erste Befehl ist nur eine Vorschau; dabei werden weder Dateien verschoben noch Ordner angelegt:

```bash
python3 tools/organize_chat_histories.py ~/Desktop
```

Wenn die vorgeschlagenen Gruppen passen, kann derselbe Befehl mit `--apply` gestartet werden:

```bash
python3 tools/organize_chat_histories.py ~/Desktop --apply
```

Das Werkzeug zeigt dann die Anzahl der betroffenen Dateien und wartet auf eine letzte Bestätigung. Nur wenn exakt `JA` eingegeben und mit der Eingabetaste bestätigt wird, werden die Dateien verschoben. Jede andere Eingabe bricht ohne Änderungen ab. Die sortierten Dateien landen gesammelt unter `Desktop/Chatverlaeufe_sortiert/Geschichte_...`; vorhandene Originalnamen werden beibehalten und Namenskollisionen sicher nummeriert.

Kurz gesagt:

1. Terminal öffnen.
2. Den ersten Befehl **ohne** `--apply` ausführen und die Vorschau lesen.
3. Nur bei passenden Vorschlägen den zweiten Befehl **mit** `--apply` ausführen.
4. Erst nach der angezeigten Rückfrage `JA` eingeben. Bis dahin wurde nichts verschoben.

Falls zu viele oder zu wenige Dateien zusammengefasst werden, kann die Ähnlichkeitsschwelle angepasst werden, zum Beispiel strenger mit `--threshold 0.45` oder lockerer mit `--threshold 0.20`.
