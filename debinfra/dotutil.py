"""Shared helpers for walking the layered dotfiles tree."""

from pathlib import Path
from typing import Iterator

from debinfra import FILES


GRAPHICAL_TYPES = {"laptop", "vm"}


def layers_for(machine_type: str) -> tuple[str, ...]:
    if machine_type in GRAPHICAL_TYPES:
        return ("common", "graphical", machine_type)
    return ("common", machine_type)


def layered_files(machine_type: str, scope: str) -> Iterator[tuple[Path, Path]]:
    """Yield (source, relative-dest) for scope 'home' or 'root', common layer first
    so more specific layers override earlier ones."""
    seen: dict[Path, Path] = {}
    for layer in layers_for(machine_type):
        base = FILES / "dotfiles" / layer / scope
        if base.is_dir():
            for src in sorted(p for p in base.rglob("*") if p.is_file()):
                seen[src.relative_to(base)] = src
    for rel, src in seen.items():
        yield src, rel
