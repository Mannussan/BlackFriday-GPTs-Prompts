@echo off
setlocal
title Chatverlaeufe sortieren - Vorschau und Bestaetigung
set "PYTHONUTF8=1"
set "SORTER=%~dp0tools\organize_chat_histories.py"
if not exist "%SORTER%" goto missing_script
echo Chatverlaeufe sortieren
echo Zuerst erscheint eine Vorschau. Erst nach Ihrer Eingabe JA wird verschoben.
echo Der gesamte Desktop samt Unterordnern wird nach Markdown und PDF durchsucht.
echo Sie koennen alternativ einen Ordner auf diese BAT-Datei ziehen.
echo.
py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto run_py
python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto run_python
python3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto run_python3
echo FEHLER: Python ab Version 3.10 wurde nicht gefunden.
echo Bitte Python installieren und den Starter erneut oeffnen.
set "SORT_EXIT=1"
goto finish
:run_py
py -3 "%SORTER%" --apply %*
set "SORT_EXIT=%ERRORLEVEL%"
goto finish
:run_python
python "%SORTER%" --apply %*
set "SORT_EXIT=%ERRORLEVEL%"
goto finish
:run_python3
python3 "%SORTER%" --apply %*
set "SORT_EXIT=%ERRORLEVEL%"
goto finish
:missing_script
echo FEHLER: Das Programm tools\organize_chat_histories.py fehlt.
echo Bitte den vollstaendigen Programmordner entpacken.
set "SORT_EXIT=1"
:finish
echo.
if not "%SORT_EXIT%"=="0" echo Das Programm meldet einen Fehler. Bitte den Text oben lesen.
echo Zum Schliessen eine Taste druecken.
pause >nul
exit /b %SORT_EXIT%
