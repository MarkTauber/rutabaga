from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import Optional, Tuple

FILE_EXTENSIONS = frozenset(
    {
        ".txt", 
        ".csv", 
        ".log", 
        ".out", 
        ".lst"
    }
)


def sanitize_domain_for_filename(domain: str) -> str:
    d = domain.strip().lstrip("@")
    return re.sub(r"[^\w.-]", "_", d) or "domain"


def default_basename(domain: Optional[str]) -> str:
    if domain:
        return sanitize_domain_for_filename(domain)
    return f"rutabaga_{secrets.token_hex(4)}"


def is_output_file_path(path: Path) -> bool:
    raw = str(path)
    if raw.endswith(("/", "\\")):
        return False
    if path.exists():
        return path.is_file()
    if path.suffix.lower() in FILE_EXTENSIONS:
        return True
    return False


def _default_output_dir() -> Path:
    return Path.home()


def _ensure_parent_dir(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_normal_output(output: Optional[str], domain: Optional[str]) -> Path:
    basename = default_basename(domain)

    if not output:
        return _ensure_parent_dir(_default_output_dir() / f"{basename}.txt")

    path = Path(output)
    if is_output_file_path(path):
        return _ensure_parent_dir(path)

    path.mkdir(parents=True, exist_ok=True)
    return path / f"{basename}.txt"


def _validate_pair_paths(base_path: Path) -> Tuple[Path, Path]:
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    return (
        parent / f"{stem}_valid{suffix}",
        parent / f"{stem}_invalid{suffix}",
    )


def resolve_validate_outputs(output: Optional[str], domain: str) -> Tuple[Path, Path]:
    basename = default_basename(domain)

    if not output:
        base_dir = _default_output_dir()
        base_dir.mkdir(parents=True, exist_ok=True)
        return _validate_pair_paths(base_dir / f"{basename}.txt")

    path = Path(output)
    if is_output_file_path(path):
        return _validate_pair_paths(_ensure_parent_dir(path))

    path.mkdir(parents=True, exist_ok=True)
    return _validate_pair_paths(path / f"{basename}.txt")
