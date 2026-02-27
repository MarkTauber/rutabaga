from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import List, Union


@dataclass(frozen=True)
class TextToken:
    value: str


@dataclass(frozen=True)
class PlaceholderToken:
    name: str


Token = Union[TextToken, PlaceholderToken]

# Any single lowercase letter: $a..$z (built-in n,s,m,l + custom)
_PLACEHOLDER_PATTERN = re.compile(r"\$([a-z])")
_ALLOWED_PLACEHOLDERS = set(string.ascii_lowercase)
RESERVED_PLACEHOLDERS = {"n", "s", "m", "l"}


class MaskError(ValueError):
    """Raised when mask template is invalid."""


def parse_mask(template: str) -> List[Token]:
    """
    Parse mask template into tokens.

    Placeholders: any single lowercase letter $a..$z.
    Built-in: $n (name), $s (surname), $m (patronymic), $l (letter).
    Custom letters get values from -p letter=path (or override n/s/m/l).
    """
    if "$" not in template:
        raise MaskError("Mask must contain at least one placeholder (e.g. $n, $s, $a).")

    parts = _PLACEHOLDER_PATTERN.split(template)
    tokens: List[Token] = []

    for index, part in enumerate(parts):
        if index % 2 == 0:
            if part:
                tokens.append(TextToken(part))
        else:
            name = part
            if name not in _ALLOWED_PLACEHOLDERS:
                raise MaskError(f"Invalid placeholder '${name}' (only $a..$z allowed).")
            tokens.append(PlaceholderToken(name))

    return tokens

