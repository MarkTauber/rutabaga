from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, Iterator, List, Set

from .mask import Token, TextToken, PlaceholderToken


def generate_logins(
    tokens: List[Token],
    placeholder_map: Dict[str, Iterable[str]],
    domain_suffix: str = "",
    unique: bool = True,
) -> Iterator[str]:
    """
    Generate logins/emails according to parsed tokens and placeholder values.

    placeholder_map keys:
        'n' -> iterable of first names
        's' -> iterable of surnames
        'm' -> iterable of patronymics
        'l' -> iterable of letters
    """
    variants: List[List[str]] = []

    for token in tokens:
        if isinstance(token, TextToken):
            variants.append([token.value])
        elif isinstance(token, PlaceholderToken):
            values = list(placeholder_map.get(token.name, []))
            if not values:
                # if no values for placeholder, generation is meaningless
                continue
            variants.append(values)
        else:
            continue

    seen: Set[str] = set()

    for combo in product(*variants):
        login = "".join(combo) + domain_suffix
        if not unique:
            yield login
        else:
            if login in seen:
                continue
            seen.add(login)
            yield login

