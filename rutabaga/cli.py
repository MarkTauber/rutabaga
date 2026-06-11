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
from .output_paths import resolve_normal_output, resolve_validate_outputs
from .validate import (
    DEFAULT_HELO,
    DEFAULT_SENDER,
    DEFAULT_WORKERS,
    normalize_validate_methods,
    validate_stream,
)


ASCII_BANNER = textwrap.dedent(
    """
   __       ___       __        __         _\\|/_ 
  |__) |  |  |   /\\  |__)  /\\  / _`  /\\   (     )
  |  \\ \\__/  |  /~~\\ |__) /~~\\ \\__> /~~\\   '-,-'
  
  Flexible login and email generator and validation (RUTABAGA).
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
        help="Output path: file or directory. Omitted: save to home (~) using -d domain or random ID. "
        "Directory: auto-named file inside. File: use as-is (with --validate: stem_valid/stem_invalid/stem_inconclusive).",
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
        "-V",
        "--verbose",
        action="store_true",
        help="Print generated logins to stdout. By default only banner, settings and status are shown.",
    )
    parser.add_argument(
        "-v",
        "--validate",
        nargs="*",
        choices=["SMTP", "VRFY", "EXPN"],
        metavar="METHOD",
        help="Validate generated emails. Bare -v: SMTP (with STARTTLS). "
        "With METHODs: only those listed (SMTP, VRFY, EXPN). Requires -d/--domain. "
        "Examples: -v, -v SMTP, -v VRFY EXPN, -v SMTP VRFY. "
        "Writes {basename}_valid.txt, {basename}_invalid.txt and {basename}_inconclusive.txt (see -o).",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        metavar="N",
        help=f"Validation worker threads (default {DEFAULT_WORKERS}, used with --validate).",
    )
    parser.add_argument(
        "--sender",
        type=str,
        default=DEFAULT_SENDER,
        metavar="EMAIL",
        help="MAIL FROM address for SMTP validation (used with --validate).",
    )
    parser.add_argument(
        "--helo",
        type=str,
        default=DEFAULT_HELO,
        metavar="HOST",
        help="EHLO/HELO hostname for SMTP validation (used with --validate).",
    )
    parser.add_argument(
        "--mx",
        action="store_true",
        help="On RCPT 5xx, try next MX host before marking address invalid (used with --validate).",
    )
    parser.add_argument(
        "--no-starttls",
        action="store_true",
        help="Do not upgrade SMTP session to TLS even if the server advertises STARTTLS (used with --validate).",
    )

    return parser


def _default_data_root() -> Path:
    return Path(__file__).resolve().parent / "data"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _format_settings(
    args: argparse.Namespace,
    data_root: Path,
    *,
    output_path: Optional[str] = None,
    valid_path: Optional[str] = None,
    invalid_path: Optional[str] = None,
    inconclusive_path: Optional[str] = None,
) -> str:
    lines = [
        "mask: " + args.mask,
        "sex: " + args.sex,
        "data-root: " + str(data_root),
    ]
    if args.domain:
        lines.append("domain: " + args.domain)
    if output_path:
        lines.append("output: " + output_path)
    elif valid_path and invalid_path and inconclusive_path:
        lines.append("output valid: " + valid_path)
        lines.append("output invalid: " + invalid_path)
        lines.append("output inconclusive: " + inconclusive_path)
    if args.letters:
        lines.append("letters: " + args.letters)
    if args.no_unique:
        lines.append("no-unique: true")
    if args.placeholder:
        lines.append("placeholder: " + " ".join(args.placeholder))
    if args.validate is not None:
        methods = normalize_validate_methods(args.validate)
        lines.append("validate: " + ", ".join(sorted(methods)))
        lines.append("workers: " + str(args.workers))
        lines.append("sender: " + args.sender)
        lines.append("helo: " + args.helo)
        if args.mx:
            lines.append("mx: true")
        if args.no_starttls:
            lines.append("starttls: false")
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

    if args.validate is not None and not args.domain:
        parser.error("--validate requires -d/--domain so generated addresses are full emails.")

    if args.validate is not None and args.verbose:
        parser.error("--validate and --verbose cannot be used together.")

    if args.no_starttls and args.validate is None:
        parser.error("--no-starttls requires --validate.")

    write_to_file = args.output is not None or not args.verbose

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

    resolved_output: Optional[Path] = None
    resolved_valid: Optional[Path] = None
    resolved_invalid: Optional[Path] = None
    resolved_inconclusive: Optional[Path] = None

    validate_methods = None
    if args.validate is not None:
        validate_methods = normalize_validate_methods(args.validate)
        resolved_valid, resolved_invalid, resolved_inconclusive = resolve_validate_outputs(
            args.output, args.domain
        )
    elif write_to_file:
        resolved_output = resolve_normal_output(args.output, args.domain)

    if not verbose:
        _log(ASCII_BANNER.rstrip())
        _log("")
        _log("Settings:")
        _log(
            _format_settings(
                args,
                data_root,
                output_path=str(resolved_output) if resolved_output else None,
                valid_path=str(resolved_valid) if resolved_valid else None,
                invalid_path=str(resolved_invalid) if resolved_invalid else None,
                inconclusive_path=str(resolved_inconclusive) if resolved_inconclusive else None,
            )
        )
        _log("")

    if validate_methods is not None:
        valid_path = resolved_valid
        invalid_path = resolved_invalid
        inconclusive_path = resolved_inconclusive
        _log("Validating: " + ", ".join(sorted(validate_methods)))
        _log(f"Valid emails:         {valid_path}")
        _log(f"Invalid emails:       {invalid_path}")
        _log(f"Inconclusive emails:  {inconclusive_path}")
        _log("")

        stats = validate_stream(
            generator,
            valid_path=valid_path,
            invalid_path=invalid_path,
            inconclusive_path=inconclusive_path,
            workers=args.workers,
            sender=args.sender,
            helo=args.helo,
            try_all_mx=args.mx,
            methods=validate_methods,
            use_starttls=not args.no_starttls,
            print_valid=True,
        )

        _log("")
        _log("Validation complete.")
        _log(f"Generated:     {stats['generated']}")
        _log(f"Valid:         {stats['valid']}")
        if stats["invalid"]:
            _log(f"Invalid:       {stats['invalid']}")
        if stats["catch_all"]:
            _log(f"Catch-all:     {stats['catch_all']}")
        if stats["inconclusive"]:
            _log(f"Inconclusive:  {stats['inconclusive']}")
        if stats["unknown"]:
            _log(f"Unknown:       {stats['unknown']}")
        return 0

    if not verbose:
        _log("Generating...")

    out_file_handle = None
    try:
        if write_to_file and resolved_output:
            out_file_handle = open(resolved_output, "w", encoding="utf-8")

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

