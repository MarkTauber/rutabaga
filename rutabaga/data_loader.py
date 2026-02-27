from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple, Optional


def _read_lines(path: Path) -> List[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_data(
    sex: Optional[str],
    data_root: Path,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Load surnames, names and patronymics for given sex from text files.

    Files layout (under data_root):
        Names_M.txt
        Surnames_M.txt
        Patronymics_M.txt
        Names_F.txt
        Surnames_F.txt
        Patronymics_F.txt

    sex:
        'm'  - male only
        'f'  - female only
        None or 'both' - merge both sets
    """
    data_root = data_root.resolve()

    def files_for(gender_suffix: str) -> Tuple[Path, Path, Path]:
        return (
            data_root / f"Names_{gender_suffix}.txt",
            data_root / f"Surnames_{gender_suffix}.txt",
            data_root / f"Patronymics_{gender_suffix}.txt",
        )

    names: List[str] = []
    surnames: List[str] = []
    patronymics: List[str] = []

    def load_for_suffix(suffix: str) -> None:
        n_path, s_path, p_path = files_for(suffix)
        names.extend(_read_lines(n_path))
        surnames.extend(_read_lines(s_path))
        patronymics.extend(_read_lines(p_path))

    if sex == "m":
        load_for_suffix("M")
    elif sex == "f":
        load_for_suffix("F")
    else:
        # both or None
        load_for_suffix("M")
        load_for_suffix("F")

    return surnames, names, patronymics

