# commands.py
"""
Stub command implementations for Stage 1.

The assignment requires 'ls' and 'cd' to be implemented as stubs
that print their own name and arguments.
"""


from typing import List


def cmd_ls(args: List[str]) -> None:
    """
    Stub implementation of 'ls'.

    For Stage 1 it does not list any real files.
    It simply prints its name and arguments.
    """
    print(f"[ls] arguments: {args}")


def cmd_cd(args: List[str]) -> None:
    """
    Stub implementation of 'cd'.

    For Stage 1 it does not change any real directory.
    It simply prints its name and arguments.
    """
    print(f"[cd] arguments: {args}")
