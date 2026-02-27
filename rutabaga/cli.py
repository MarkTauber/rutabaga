from __future__ import annotations

import argparse
import string
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

from .mask import parse_mask, MaskError, PlaceholderToken, RESERVED_PLACEHOLDERS
from .data_loader import load_data
from .generator import generate_logins


ASCII_BANNER = textwrap.dedent(
    """
   __       ___       __        __         _\\|/_ 
  |__) |  |  |   /\\  |__)  /\\  / _`  /\\   (     )
  |  \\ \\__/  |  /~~\\ |__) /~~\\ \\__> /~~\\   '-,-'
  
  Flexible login and email generator (RUTABAGA).
"""
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=ASCII_BANNER
        + textwrap.dedent(
            """
Mask examples:
  $n.$s$l@corp.local
  $s_$l$l$l

Placeholders: $a..$z (one letter per placeholder).
  Built-in: $n name, $s surname, $m patronymic, $l letter.
  Custom: e.g. $a, $b via -p a=file.txt -p b=file2.txt (overrides $n/$s/$m/$l if used).

Quick examples:
  -m '$n.$s' -d corp.local -o logins.txt
  -m '$n.$s_$l' -d example.com --data-root rutabaga/data_gost --sex m -o users.txt
  -m '$s$l' -L abc -o out.txt
"""
        ),
    )

    parser.add_argument(
        "-p",
        "--placeholder",
        action="append",
        default=[],
        metavar="LETTER=PATH",
        help="Custom placeholder: letter=path (e.g. a=./text.txt). Multiple files: a=./t1.txt,./t2.txt or repeat -p a=...",
    )
    parser.add_argument(
        "-m",
        "--mask",
        type=str,
        required=True,
        help="Mask template, e.g. '$n.$s_$l$l'. On Windows/PowerShell use single quotes: -m '$n.$s_$l'",
    )
    parser.add_argument(
        "-d",
        "--domain",
        type=str,
        required=False,
        metavar="DOMAIN",
        help="Optional domain to append, e.g. 'corp.local' (turned into '@corp.local').",
    )
    parser.add_argument(
        "-s",
        "--sex",
        type=str,
        choices=["m", "f", "both"],
        default="both",
        help="Gender to use for data files: m, f or both (default).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=False,
        metavar="PATH",
        help="Output file path (required without -v). With -v, optional; logins go to stdout.",
    )
    parser.add_argument(
        "--data-root",
        type=str,
        required=False,
        metavar="PATH",
        help="Directory with data files (Names_*.txt, Surnames_*.txt, Patronymics_*.txt). "
        "If not set, built-in 'rutabaga/data' is used.",
    )
    parser.add_argument(
        "-L",
        "--letters",
        type=str,
        required=False,
        metavar="LETTERS",
        help="Alphabet for $l placeholder, e.g. 'abcxyz'. Default: ascii lowercase a-z.",
    )
    parser.add_argument(
        "--no-unique",
        action="store_true",
        help="Do not filter duplicates between different data sets.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print generated logins to stdout. By default only banner, settings and status are shown.",
    )

    return parser


def _default_data_root() -> Path:
    return Path(__file__).resolve().parent / "data"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _format_settings(args: argparse.Namespace, data_root: Path) -> str:
    lines = [
        "mask: " + args.mask,
        "sex: " + args.sex,
        "data-root: " + str(data_root),
    ]
    if args.domain:
        lines.append("domain: " + args.domain)
    if args.output:
        lines.append("output: " + args.output)
    if args.letters:
        lines.append("letters: " + args.letters)
    if args.no_unique:
        lines.append("no-unique: true")
    if args.placeholder:
        lines.append("placeholder: " + " ".join(args.placeholder))
    return "\n".join(lines)


def _build_domain_suffix(domain: Optional[str]) -> str:
    if not domain:
        return ""
    d = domain.strip()
    if d and "@" not in d:
        d = "@" + d
    return d


def _read_file_lines(path: Path) -> List[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_placeholder_args(
    placeholder_args: Optional[List[str]],
    parser: argparse.ArgumentParser,
) -> Dict[str, List[str]]:
    custom_map: Dict[str, List[str]] = {}
    for arg in placeholder_args or []:
        if "=" not in arg:
            parser.error(f"Invalid -p value: expected LETTER=PATH, got '{arg}'")
        eq_idx = arg.index("=")
        letter = arg[:eq_idx].strip().lower()
        paths_str = arg[eq_idx + 1 :].strip()
        if len(letter) != 1 or letter not in string.ascii_lowercase:
            parser.error(f"Invalid -p letter: must be one letter a-z, got '{letter}'")
        paths = [p.strip() for p in paths_str.split(",") if p.strip()]
        if not paths:
            parser.error(f"Invalid -p: no path(s) for ${letter}")
        for p in paths:
            path = Path(p)
            if not path.is_absolute():
                path = Path.cwd() / path
            try:
                lines = _read_file_lines(path)
            except FileNotFoundError as e:
                parser.error(str(e))
            except OSError as e:
                parser.error(f"Cannot read {path}: {e}")
            custom_map.setdefault(letter, []).extend(lines)
    return custom_map


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.verbose and not args.output:
        parser.error(
            "Output file is required when -v is not set. Use -o PATH or -v to print to stdout."
        )

    try:
        tokens = parse_mask(args.mask)
    except MaskError as exc:
        parser.error(str(exc))

    custom_map = parse_placeholder_args(args.placeholder, parser)

    data_root = Path(args.data_root) if args.data_root else _default_data_root()

    try:
        surnames, names, patronymics = load_data(
            sex=None if args.sex == "both" else args.sex, data_root=data_root
        )
    except FileNotFoundError as e:
        parser.error(str(e))

    letters = list(args.letters) if args.letters else [chr(c) for c in range(ord("a"), ord("z") + 1)]

    base_map = {
        "n": names,
        "s": surnames,
        "m": patronymics,
        "l": letters,
    }
    placeholder_map = dict(base_map)
    for letter, values in custom_map.items():
        placeholder_map[letter] = values

    used_letters = {t.name for t in tokens if isinstance(t, PlaceholderToken)}
    for letter in used_letters:
        values = placeholder_map.get(letter)
        if not values:
            if letter in RESERVED_PLACEHOLDERS:
                parser.error(
                    f"No data for ${letter} (use -p {letter}=path or ensure --data-root contains {letter} data)."
                )
            parser.error(f"Placeholder ${letter} is not defined (use -p {letter}=path).")

    domain_suffix = _build_domain_suffix(args.domain)

    generator = generate_logins(
        tokens=tokens,
        placeholder_map=placeholder_map,
        domain_suffix=domain_suffix,
        unique=not args.no_unique,
    )

    verbose = args.verbose
    if not verbose:
        _log(ASCII_BANNER.rstrip())
        _log("")
        _log("Settings:")
        _log(_format_settings(args, data_root))
        _log("")
        _log("Generating...")

    out_file_handle = None
    try:
        if args.output:
            out_file_handle = open(args.output, "w", encoding="utf-8")

        count = 0
        for login in generator:
            count += 1
            if verbose:
                print(login)
            if out_file_handle:
                out_file_handle.write(login + "\n")

        if not verbose:
            _log("")
            _log(f"Done. {count} logins.")
    finally:
        if out_file_handle:
            out_file_handle.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

