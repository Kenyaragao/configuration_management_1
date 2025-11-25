# shell.py
"""
Core REPL implementation for the shell emulator (Stage 3, Variant 27).

Stage 1:
- Basic REPL, stub commands (ls, cd), exit.

Stage 2:
- Configuration via command-line arguments.
- XML logging of command invocations.
- Startup script with comments, input+output echo, error reporting.

Stage 3:
- In-memory Virtual File System (VFS) loaded from a CSV file.
- All VFS operations are in memory only.
- Report errors when loading VFS (file not found, invalid format).
- Implement command: vfs-save <path> to save the current VFS state to disk.
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
from vfs import Vfs, VfsLoadError, VfsSaveError


class Shell:
    """
    Shell emulator for Stage 3.
    """

    def __init__(self, config: AppConfig) -> None:
        # Configuration passed from main()
        self.config = config

        # Real OS data
        self.username: str = getpass.getuser()
        self.hostname: str = socket.gethostname()

        # Logical "current directory" within the VFS
        self.current_dir: str = "~"  # will be replaced with VFS-aware path in Stage 4

        self._running: bool = True

        # XML logger for command events
        self.logger = CommandLogger(config.log_path, self.username)

        # In-memory VFS (initially empty)
        self.vfs: Vfs = Vfs()

        # Print debug info about configuration
        self._print_debug_config()

        # Load VFS from disk if path provided
        if self.config.vfs_path is not None:
            self._load_vfs(self.config.vfs_path)

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

    def _load_vfs(self, vfs_path: Path) -> None:
        """
        Try to load the VFS from the given CSV file.
        Print an error if anything goes wrong.
        """
        try:
            self.vfs = Vfs.from_csv(vfs_path)
            print(f"VFS loaded successfully from: {vfs_path}")
        except VfsLoadError as e:
            print(f"Error: failed to load VFS from '{vfs_path}': {e}")

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

        Known commands in Stage 3:
        - ls        (stub)
        - cd        (stub)
        - exit
        - vfs-save  (save current VFS to CSV)
        """
        success = True
        error_message: Optional[str] = None

        if command == "exit":
            success, error_message = self._handle_exit(args)
        elif command == "ls":
            cmd_mod.cmd_ls(args)
        elif command == "cd":
            cmd_mod.cmd_cd(args)
        elif command == "vfs-save":
            success, error_message = self._handle_vfs_save(args)
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

        For now we still treat any arguments as an error,
        just to demonstrate "invalid arguments" handling.
        """
        if args:
            msg = "Error: 'exit' does not take any arguments in this emulator."
            print(msg)
            return False, "exit called with arguments"

        self._running = False
        return True, None

    def _handle_vfs_save(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Handle the 'vfs-save <path>' command.

        Saves the current in-memory VFS to the given CSV file.
        """
        if len(args) != 1:
            msg = "Usage: vfs-save <path-to-csv>"
            print(msg)
            return False, "vfs-save called with wrong number of arguments"

        dest_path = Path(args[0])

        try:
            self.vfs.to_csv(dest_path)
            print(f"VFS saved successfully to: {dest_path}")
            return True, None
        except VfsSaveError as e:
            print(f"Error: failed to save VFS: {e}")
            return False, str(e)
