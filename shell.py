# shell.py
"""
Core REPL implementation for the shell emulator (Stage 2, Variant 27).

New in Stage 2:
- Support configuration via command-line arguments:
    * VFS physical path
    * Log file path
    * Startup script path
- Print all configuration parameters at startup (debug output).
- Log command events to an XML file:
    * username
    * date and time
- Support a startup script:
    * Supports comments using Python-style syntax ('# ...').
    * During execution, both input (command line) and output are shown,
      simulating an interactive session.
    * Errors during script execution are reported.
"""

from __future__ import annotations

import getpass
import socket
from pathlib import Path
from typing import List, Tuple, Optional

from parser import parse_command_line
import commands as cmd_mod
from config import AppConfig
from logger_xml import CommandLogger


class Shell:
    """
    Simple interactive shell emulator for Stage 2.
    """

    def __init__(self, config: AppConfig) -> None:
        # Configuration passed from main()
        self.config = config

        # Real OS data
        self.username: str = getpass.getuser()
        self.hostname: str = socket.gethostname()

        # We don't have a real filesystem/VFS yet, so we fake the "current directory".
        self.current_dir: str = "~"

        self._running: bool = True

        # XML logger for command events
        self.logger = CommandLogger(config.log_path, self.username)

        # Print debug info about configuration
        self._print_debug_config()

    def _print_debug_config(self) -> None:
        """
        Print all configuration parameters for debugging purposes.
        """
        print("=== Shell Emulator Configuration ===")
        print(f"VFS path       : {self._path_or_none(self.config.vfs_path)}")
        print(f"Log file path  : {self._path_or_none(self.config.log_path)}")
        print(f"Startup script : {self._path_or_none(self.config.startup_script)}")
        print("====================================")

    @staticmethod
    def _path_or_none(path: Optional[Path]) -> str:
        return str(path) if path is not None else "(none)"

    def build_prompt(self) -> str:
        """
        Build the prompt string, e.g.:

            username@hostname:~$
        """
        return f"{self.username}@{self.hostname}:{self.current_dir}$ "

    def run(self) -> None:
        """
        Run the shell:
        - Execute the startup script if configured.
        - Enter the interactive REPL loop.
        """
        # 1) Run startup script if provided
        if self.config.startup_script is not None:
            self._run_startup_script(self.config.startup_script)

        # 2) Interactive REPL
        self._run_interactive_loop()

    def _run_interactive_loop(self) -> None:
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

            self._process_line(line, from_script=False)

    def _run_startup_script(self, script_path: Path) -> None:
        """
        Execute a startup script line by line.

        - Lines starting with '#' (after stripping leading spaces) are comments and ignored.
        - Empty lines are ignored.
        - Each command line is printed with a prompt to imitate user input.
        - Errors during script execution are reported.
        """
        if not script_path.exists():
            print(f"Error: startup script '{script_path}' not found.")
            return

        print(f"Running startup script: {script_path}")

        try:
            content = script_path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error: could not read startup script '{script_path}': {e}")
            return

        for line_no, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.rstrip("\n")

            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                # Comment or empty line - just skip
                continue

            # Show the command as if the user typed it
            print(self.build_prompt() + line)

            # Process the line; any errors will be printed by the parser/dispatcher
            self._process_line(line, from_script=True, script_line_no=line_no)

    def _process_line(
        self,
        line: str,
        from_script: bool,
        script_line_no: Optional[int] = None,
    ) -> None:
        """
        Process a single line of input (either from the user or from a script).
        This includes parsing, dispatching the command, logging, and error handling.
        """
        command: Optional[str]
        args: List[str]

        # 1) Parse
        try:
            command, args = parse_command_line(line)
        except ValueError as e:
            error_msg = f"{e}"
            if from_script and script_line_no is not None:
                print(f"Error in startup script line {script_line_no}: {error_msg}")
            else:
                print(f"Error: {error_msg}")
            # Log parse failure with a pseudo-command name
            self.logger.log(
                command="(parse-error)",
                args=[line],
                success=False,
                error_message=error_msg,
            )
            return

        # 2) Dispatch command
        self._dispatch_command(command, args)

    def _dispatch_command(self, command: str, args: List[str]) -> None:
        """
        Execute one command.

        Known commands in Stage 2:
        - ls  (stub)
        - cd  (stub)
        - exit
        """
        success = True
        error_message: Optional[str] = None

        if command == "exit":
            success, error_message = self._handle_exit(args)
        elif command == "ls":
            cmd_mod.cmd_ls(args)
        elif command == "cd":
            cmd_mod.cmd_cd(args)
        else:
            error_message = f"unknown command '{command}'"
            print(f"Error: {error_message}")
            success = False

        # Log the command (including failures)
        self.logger.log(
            command=command,
            args=args,
            success=success,
            error_message=error_message,
        )

    def _handle_exit(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Handle the 'exit' command.

        For Stage 2 we still treat any arguments as an error,
        just to demonstrate "invalid arguments" handling.
        """
        if args:
            msg = "Error: 'exit' does not take any arguments in this emulator."
            print(msg)
            return False, "exit called with arguments"

        self._running = False
        return True, None
