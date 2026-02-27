"""
Rutabaga - flexible login and email generator based on name templates.

This package provides:
- mask parsing with placeholders ($n, $s, $m, $l)
- combinatorial generator of logins/emails
- CLI entrypoint (see rutabaga.cli)
"""

from .mask import parse_mask  # noqa: F401
from .generator import generate_logins  # noqa: F401

