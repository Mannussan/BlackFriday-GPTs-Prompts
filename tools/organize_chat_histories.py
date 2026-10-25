#!/usr/bin/env python3
"""Group Markdown/PDF chat-history files by similar story content.

The script recursively scans a Desktop folder, extracts text from .md/.markdown/.pdf
files, groups files with similar content, and optionally moves each group into a
new folder named from the shared story/topic.

By default it is a dry run. Add --apply and confirm to move files.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".pdf"}
OUTPUT_DIRECTORY = "Chatverlaeufe_sortiert"
SKIP_DIRECTORIES = {OUTPUT_DIRECTORY.casefold(), ".git", ".venv", "venv", "node_modules", "__pycache__", ".codex", ".agents", "_vendor"}
# Optional PDF dependency bundled in the local Windows download.
VENDOR_DIRECTORY = Path(__file__).resolve().parent.parent / "_vendor"
if VENDOR_DIRECTORY.is_dir():
    sys.path.insert(0, str(VENDOR_DIRECTORY))
STOPWORDS = {
    "aber", "alle", "also", "and", "auf", "aus", "bei", "chatgpt", "dass", "dem", "den", "der", "die", "dies", "ein", "eine", "einer", "eines", "for", "from", "haben", "ich", "ist", "mit", "nicht", "oder", "sich", "sie", "the", "und", "von", "was", "wir", "you", "zur",
}

@dataclass(frozen=True)
class Document:
    path: Path
    text: str
    fingerprint: str
    tokens: frozenset[str]
    signature: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class Move:
    document: Document
    destination: Path


def default_desktop() -> Path:
    """Use the Windows Desktop setting, including redirected OneDrive desktops."""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                desktop, _ = winreg.QueryValueEx(key, "Desktop")
            candidate = Path(os.path.expandvars(desktop))
            if candidate.is_dir():
                return candidate
        except OSError:
            pass
    for base in (Path.home(), *(Path(os.environ[name]) for name in
            ("OneDrive", "OneDriveConsumer", "OneDriveCommercial") if os.environ.get(name))):
        if (base / "Desktop").is_dir():
            return base / "Desktop"
    return Path.home() / "Desktop"


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf(path: Path) -> str:
    """Extract PDF text with local command-line tools when available."""
    try:
        from pypdf import PdfReader
    except ImportError:
        pass
    else:
        try:
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        except Exception as error:
            print(f"Hinweis: PDF nicht lesbar: {path} ({error})")
            return ""
    try:
        result = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=False,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    print(f"Hinweis: PDF uebersprungen: {path}. PDF-Unterstuetzung fehlt oder kein Text auslesbar.")
    return ""


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[\wäöüßÄÖÜ-]{4,}", text.casefold())
    return [word for word in words if word not in STOPWORDS and not word.isdigit()]


def token_shingles(tokens: list[str], size: int = 5) -> frozenset[str]:
    if len(tokens) < size:
        return frozenset(tokens)
    return frozenset(" ".join(tokens[index:index + size]) for index in range(len(tokens) - size + 1))


def load_document(path: Path) -> Document:
    before = path.stat()
    text = read_pdf(path) if path.suffix.casefold() == ".pdf" else read_markdown(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise OSError(f"Datei wurde waehrend des Lesens geaendert: {path}")
    normalized = normalize_text(text)
    fingerprint = hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()
    tokens = token_shingles(tokenize(normalized))
    return Document(path=path, text=text, fingerprint=fingerprint, tokens=tokens,
                    signature=(after.st_size, after.st_mtime_ns))


def similarity(left: Document, right: Document) -> float:
    if left.fingerprint == right.fingerprint:
        return 1.0
    if not left.tokens or not right.tokens:
        return 0.0
    overlap = len(left.tokens & right.tokens)
    return overlap / len(left.tokens | right.tokens)


def find_files(root: Path) -> list[Path]:
    own_directory = Path(__file__).resolve().parent.parent
    files = []
    def report_walk_error(error):
        print(f"Hinweis: Ordner nicht lesbar: {error.filename}")
    for directory, names, filenames in os.walk(root, followlinks=False, onerror=report_walk_error):
        names[:] = sorted(name for name in names
                          if name.casefold() not in SKIP_DIRECTORIES
                          and not (Path(directory) / name).is_symlink()
                          and not (hasattr(Path, "is_junction") and (Path(directory) / name).is_junction())
                          and (Path(directory) / name).resolve() != own_directory)
        for filename in sorted(filenames):
            path = Path(directory) / filename
            if (path.suffix.casefold() in SUPPORTED_EXTENSIONS and path.is_file()
                    and not path.is_symlink()):
                files.append(path)
    return sorted(files)


def build_groups(documents: list[Document], threshold: float) -> list[list[Document]]:
    groups: list[list[Document]] = []
    for document in documents:
        best_group = None
        best_score = 0.0
        for group in groups:
            score = max(similarity(document, existing) for existing in group)
            if score > best_score:
                best_score = score
                best_group = group
        if best_group is not None and best_score >= threshold:
            best_group.append(document)
        else:
            groups.append([document])
    return groups


def make_group_name(group: Iterable[Document]) -> str:
    counter: Counter[str] = Counter()
    for document in group:
        counter.update(tokenize(document.text)[:1000])
    keywords = [word for word, _ in counter.most_common(5)] or ["chatverlauf"]
    name = "Geschichte_" + "_".join(keywords)
    name = re.sub(r"[^\wäöüßÄÖÜ.-]+", "_", name, flags=re.UNICODE).strip("._")
    return name[:90]


def unique_destination(directory: Path, filename: str, reserved: set[Path] | None = None) -> Path:
    reserved = reserved if reserved is not None else set()
    candidate = directory / filename
    if not candidate.exists() and not candidate.is_symlink() and candidate not in reserved:
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists() and not candidate.is_symlink() and candidate not in reserved:
            return candidate
        index += 1


def organize(root: Path, threshold: float, apply: bool) -> None:
    print(f"Suche Markdown- und PDF-Dateien unter: {root}", flush=True)
    files = find_files(root)
    documents = []
    for index, path in enumerate(files, start=1):
        if index == 1 or index % 100 == 0:
            print(f"Lese Datei {index} von {len(files)} ...", flush=True)
        try:
            documents.append(load_document(path))
        except OSError as error:
            print(f"Hinweis: Datei uebersprungen: {path} ({error})")
    empty = [doc for doc in documents if not doc.text.strip()]
    documents = [doc for doc in documents if doc.text.strip()]
    groups = build_groups(documents, threshold)

    print(f"Geprueft: {len(files)} Dateien unter {root}")
    if empty:
        print(f"Leere oder nicht auslesbare Dateien uebersprungen: {len(empty)}")
    movable_groups = [group for group in groups if len(group) >= 2]
    if not movable_groups:
        print("Keine Gruppen mit mindestens zwei aehnlichen Dateien gefunden. Es wird nichts verschoben.")
        return

    plan = []
    reserved = set()
    print("\nVORSCHAU - bisher wurden keine Dateien verschoben oder Sortierordner angelegt.")
    for group_number, group in enumerate(movable_groups, start=1):
        folder = root / OUTPUT_DIRECTORY / make_group_name(group)
        print(f"\nGruppe {group_number}: {folder.name} ({len(group)} Dateien)")
        for document in group:
            destination = unique_destination(folder, document.path.name, reserved)
            reserved.add(destination)
            plan.append(Move(document, destination))
            print(f"  {document.path}\n    -> {destination}")

    print(f"\nVorschlag: {len(plan)} Dateien in {len(movable_groups)} Gruppen.")
    if not apply:
        print("Nur Vorschau. Es wurde nichts verschoben.")
        return
    try:
        answer = input("Erst alle Vorschlaege pruefen. Exakt JA eingeben und Enter druecken zum Verschieben; sonst nur Enter: ")
    except (EOFError, KeyboardInterrupt):
        answer = ""
    if answer != "JA":
        print("\nAbgebrochen. Es wurden keine Dateien verschoben.")
        return

    # Validate the whole plan before creating output directories.
    for move in plan:
        source = move.document.path
        stat = source.stat()
        if source.is_symlink() or (stat.st_size, stat.st_mtime_ns) != move.document.signature:
            raise OSError(f"Datei seit Vorschau geaendert. Bitte neu starten: {source}")
        target_directory = move.destination.parent
        for directory in (target_directory, target_directory.parent):
            if (directory.is_symlink() or (hasattr(Path, "is_junction") and directory.is_junction())
                    or (directory.exists() and not directory.is_dir())):
                raise OSError(f"Unsicherer oder blockierter Zielordner: {directory}")
        if move.destination.exists() or move.destination.is_symlink():
            raise OSError(f"Ziel ist seit Vorschau belegt. Bitte neu starten: {move.destination}")

    completed = 0
    try:
        for move in plan:
            move.destination.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation protects existing files even if another process creates a target.
            created = False
            try:
                with move.document.path.open("rb") as reader, move.destination.open("xb") as writer:
                    created = True
                    shutil.copyfileobj(reader, writer)
                    writer.flush()
                    os.fsync(writer.fileno())
                shutil.copystat(move.document.path, move.destination)
                current = move.document.path.stat()
                if (current.st_size, current.st_mtime_ns) != move.document.signature:
                    raise OSError(f"Quelldatei wurde beim Verschieben geaendert: {move.document.path}")
                move.document.path.unlink()
            except (OSError, KeyboardInterrupt):
                if created and move.document.path.exists():
                    move.destination.unlink(missing_ok=True)
                raise
            completed += 1
            print(f"Verschoben: {move.document.path} -> {move.destination}")
    except (OSError, KeyboardInterrupt):
        print(f"Vorgang gestoppt. Bereits verschoben: {completed} von {len(plan)} Dateien.")
        raise
    print(f"\nFertig. {completed} Dateien wurden nach {root / OUTPUT_DIRECTORY} verschoben.")


class GermanArgumentParser(argparse.ArgumentParser):
    def format_usage(self):
        return super().format_usage().replace("usage: ", "Aufruf: ", 1)

    def format_help(self):
        return super().format_help().replace("usage: ", "Aufruf: ", 1)

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"Fehler bei der Eingabe: {message}\n")


def parse_args() -> argparse.Namespace:
    parser = GermanArgumentParser(description="Markdown- und PDF-Dateien nach aehnlichem Inhalt gruppieren.", add_help=False)
    parser._positionals.title = "Ordner"
    parser._optionals.title = "Optionen"
    parser.add_argument("-h", "--help", action="help", help="Diese Hilfe anzeigen und beenden.")
    parser.add_argument("root", nargs="?", default=str(default_desktop()), help="Zu durchsuchender Ordner samt Unterordnern (Standard: Windows-Desktop)")
    parser.add_argument("--threshold", type=float, default=0.32, help="Aehnlichkeitsschwelle von 0.0 bis 1.0 (Standard: 0.32)")
    parser.add_argument("--apply", action="store_true", help="Vorschau anzeigen und erst nach Eingabe von JA verschieben.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0.0 <= args.threshold <= 1.0:
        raise SystemExit("Fehler: --threshold muss zwischen 0.0 und 1.0 liegen.")
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Fehler: Ordner nicht gefunden: {root}")
    try:
        organize(root, args.threshold, args.apply)
    except OSError as error:
        raise SystemExit(f"Fehler: {error}") from error
    except KeyboardInterrupt:
        raise SystemExit("\nVorgang durch Tastatur abgebrochen.")


if __name__ == "__main__":
    main()

