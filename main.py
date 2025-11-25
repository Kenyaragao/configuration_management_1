# main.py
"""
Entry point for the Stage 3 shell emulator (Variant 27).

Command-line parameters:
    --vfs PATH    : physical CSV representation of the VFS
    --log PATH    : XML log file path
    --script PATH : startup script to execute before interactive mode
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config import AppConfig
from shell import Shell


def parse_args() -> AppConfig:
    """
    Parse command-line arguments and build an AppConfig instance.
    """
    parser = argparse.ArgumentParser(
        description="Shell emulator (Stage 3, Variant 27)."
    )

    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        type=Path,
        help="Path to the physical VFS representation on disk (CSV file).",
    )
    parser.add_argument(
        "--log",
        dest="log_path",
        type=Path,
        help="Path to the XML log file for command events.",
    )
    parser.add_argument(
        "--script",
        dest="startup_script",
        type=Path,
        help="Path to the startup script that will be executed before interactive mode.",
    )

    args = parser.parse_args()

    return AppConfig(
        vfs_path=args.vfs_path,
        log_path=args.log_path,
        startup_script=args.startup_script,
    )


def main() -> None:
    config = parse_args()
    shell = Shell(config)
    shell.run()


if __name__ == "__main__":
    main()
