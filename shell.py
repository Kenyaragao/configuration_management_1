# shell.py
"""
Core REPL implementation for the shell emulator.

Requirements covered (Stage 1 / Variant 27):
- Console (CLI) interface.
- Prompt based on real OS data: username@hostname:~$
- Parsing of arguments with quotes (delegated to parser.py).
- Error message on:
    * unknown command
    * invalid arguments for 'exit'
- Stub commands: ls, cd (implemented in commands.py).
- 'exit' command to terminate the shell.
"""

import getpass
import socket
from typing import List, Tuple, Optional

from parser import parse_command_line
import commands as cmd_mod


class Shell:
    """
    Simple interactive shell emulator for Stage 1.
    """

    def __init__(self) -> None:
        # Real OS data
        self.username: str = getpass.getuser()
        self.hostname: str = socket.gethostname()

        # We don't have a real filesystem/VFS yet, so we fake the "current directory".
        # For now it is always '~' (home).
        self.current_dir: str = "~"

        self._running: bool = True

    def build_prompt(self) -> str:
        """
        Build the prompt string, e.g.:

            username@hostname:~$
        """
        return f"{self.username}@{self.hostname}:{self.current_dir}$ "

    def run(self) -> None:
        """
        Run the interactive REPL loop.

        The loop:
        - prints a prompt,
        - reads a line,
        - parses it into command + arguments,
        - executes it or prints an error.
        """
        while self._running:
            try:
                line = input(self.build_prompt())
            except EOFError:
                # Handle Ctrl+D gracefully
                print()
                break

            # Empty line -> just repeat the prompt
            if not line.strip():
                continue

            command, args = self._safe_parse(line)
            if command is None:
                # parse error already printed
                continue

            self._dispatch_command(command, args)

    def _safe_parse(self, line: str) -> Tuple[Optional[str], List[str]]:
        """
        Parse a command line, returning (command, args).

        If parsing fails (e.g. unmatched quotes), print an error
        and return (None, []).
        """
        try:
            command, args = parse_command_line(line)
            return command, args
        except ValueError as e:
            print(f"Error: {e}")
            return None, []

    def _dispatch_command(self, command: str, args: List[str]) -> None:
        """
        Execute one command.

        Known commands in Stage 1:
        - ls  (stub)
        - cd  (stub)
        - exit
        """
        if command == "exit":
            self._handle_exit(args)
        elif command == "ls":
            cmd_mod.cmd_ls(args)
        elif command == "cd":
            cmd_mod.cmd_cd(args)
        else:
            print(f"Error: unknown command '{command}'")

    def _handle_exit(self, args: List[str]) -> None:
        """
        Handle the 'exit' command.

        For Stage 1 we treat any arguments as an error, just to demonstrate
        "invalid arguments" handling.
        """
        if args:
            print("Error: 'exit' does not take any arguments in this emulator.")
            return

        self._running = False
