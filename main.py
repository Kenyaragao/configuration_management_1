# main.py
"""
Entry point for the Stage 1 shell emulator (Variant 27).

Run with:
    python main.py
"""

from shell import Shell


def main() -> None:
    shell = Shell()
    shell.run()


if __name__ == "__main__":
    main()
