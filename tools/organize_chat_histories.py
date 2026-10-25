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
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".pdf"}
OUTPUT_DIRECTORY = "Chatverlaeufe_sortiert"
STOPWORDS = {
    "aber", "alle", "also", "and", "auf", "aus", "bei", "chatgpt", "dass", "dem", "den", "der", "die", "dies", "ein", "eine", "einer", "eines", "for", "from", "haben", "ich", "ist", "mit", "nicht", "oder", "sich", "sie", "the", "und", "von", "was", "wir", "you", "zur",
}

@dataclass(frozen=True)
class Document:
    path: Path
    text: str
    fingerprint: str
    tokens: frozenset[str]


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf(path: Path) -> str:
    """Extract PDF text with local command-line tools when available."""
    for command in (["pdftotext", "-layout", str(path), "-"], ["python3", "-m", "pypdf", str(path)]):
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
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
    text = read_pdf(path) if path.suffix.casefold() == ".pdf" else read_markdown(path)
    normalized = normalize_text(text)
    fingerprint = hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()
    tokens = token_shingles(tokenize(normalized))
    return Document(path=path, text=text, fingerprint=fingerprint, tokens=tokens)


def similarity(left: Document, right: Document) -> float:
    if left.fingerprint == right.fingerprint:
        return 1.0
    if not left.tokens or not right.tokens:
        return 0.0
    overlap = len(left.tokens & right.tokens)
    return overlap / len(left.tokens | right.tokens)


def find_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and path.suffix.casefold() in SUPPORTED_EXTENSIONS
        and OUTPUT_DIRECTORY not in path.relative_to(root).parts
    )


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


def unique_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def organize(root: Path, threshold: float, apply: bool, assume_yes: bool = False) -> None:
    files = find_files(root)
    documents = [load_document(path) for path in files]
    empty = [doc for doc in documents if not doc.text.strip()]
    documents = [doc for doc in documents if doc.text.strip()]
    groups = build_groups(documents, threshold)

    print(f"Scanned: {len(files)} files under {root}")
    if empty:
        print(f"Skipped unreadable/empty files: {len(empty)}")
    movable_groups = [group for group in groups if len(group) >= 2]
    if not movable_groups:
        print("No groups with at least two similar files were found. Nothing will be moved.")
        return

    if apply and not assume_yes:
        print(f"\nReady to move {sum(map(len, movable_groups))} files into '{OUTPUT_DIRECTORY}'.")
        answer = input("Type JA to continue, or press Enter to cancel: ").strip()
        if answer != "JA":
            print("Cancelled. No files were moved.")
            return

    for group_number, group in enumerate(movable_groups, start=1):
        if len(group) < 2:
            continue
        folder = root / OUTPUT_DIRECTORY / make_group_name(group)
        print(f"\nGroup {group_number}: {folder.name} ({len(group)} files)")
        if apply:
            folder.mkdir(parents=True, exist_ok=True)
        for document in group:
            destination = unique_destination(folder, document.path.name)
            print(f"  {'MOVE' if apply else 'WOULD MOVE'} {document.path} -> {destination}")
            if apply:
                shutil.move(str(document.path), str(destination))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sort Markdown/PDF chat histories into folders by similar story content.")
    parser.add_argument("root", nargs="?", default=str(Path.home() / "Desktop"), help="Desktop folder to scan recursively (default: ~/Desktop)")
    parser.add_argument("--threshold", type=float, default=0.32, help="Similarity threshold from 0.0 to 1.0 (default: 0.32)")
    parser.add_argument("--apply", action="store_true", help="Ask for confirmation, then create folders and move files. Without this, only prints a dry run.")
    parser.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0.0 <= args.threshold <= 1.0:
        raise SystemExit("--threshold must be between 0.0 and 1.0")
    if args.yes and not args.apply:
        raise SystemExit("--yes can only be used together with --apply")
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Folder not found: {root}")
    organize(root, args.threshold, args.apply, args.yes)


if __name__ == "__main__":
    main()
