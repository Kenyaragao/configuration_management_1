# parser.py
"""
Command line parser for the shell emulator.

Responsibilities:
- Split a raw input line into command and arguments.
- Correctly handle quoted arguments (both single and double quotes).

Implementation detail:
- Uses Python's `shlex.split`, which behaves similarly to a POSIX shell.
"""

import shlex
from typing import List, Tuple


def parse_command_line(line: str) -> Tuple[str, List[str]]:
    """
    Parse a line into (command, args).

    Examples:
        'ls -l "/some path/with spaces"'
        -> command: 'ls'
           args: ['-l', '/some path/with spaces']

    Raises:
        ValueError: if parsing fails (e.g. unmatched quote).
    """
    try:
        tokens: List[str] = shlex.split(line, posix=True)
    except ValueError as e:
        # e.g. "No closing quotation"
        raise ValueError(f"failed to parse command line: {e}") from e

    if not tokens:
        raise ValueError("empty command")

    command = tokens[0]
    args = tokens[1:]
    return command, args
