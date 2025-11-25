# shell.py
"""
Shell emulator for Stage 4 (Variant 27).

Stage 1:
    - Basic REPL, stub commands (ls, cd), exit.

Stage 2:
    - Configuration via command-line arguments.
    - XML logging of command invocations.
    - Startup script with comments, input+output echo, error reporting.

Stage 3:
    - In-memory Virtual File System (VFS) loaded from a CSV file.
    - Command: vfs-save <path> to save VFS back to CSV.

Stage 4:
    - Real logic for commands: ls, cd (working on the VFS).
    - New commands:
        * clear  – clear the console screen.
        * uniq   – print unique lines of a file (remove adjacent duplicates).
        * du     – compute disk usage in bytes for a path or current directory.
"""

from __future__ import annotations

import getpass
import socket
from pathlib import Path
from typing import List, Tuple, Optional

from parser import parse_command_line
from config import AppConfig
from logger_xml import CommandLogger
from vfs import Vfs, VfsLoadError, VfsSaveError


class Shell:
    """
    Shell emulator for Stage 4.
    """

    def __init__(self, config: AppConfig) -> None:
        # Configuration passed from main()
        self.config = config

        # Real OS data
        self.username: str = getpass.getuser()
        self.hostname: str = socket.gethostname()

        # Logical "current directory" within the VFS (absolute path)
        self.current_dir: str = "/"  # will be shown as '~' in the prompt

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

    # ------------- Initialization helpers -------------

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

    # ------------- Prompt & main loop -------------

    def build_prompt(self) -> str:
        """
        Build the prompt string, e.g.:

            username@hostname:~$

        We display '/' as '~' to mimic a typical Unix home directory prompt.
        """
        if self.current_dir == "/":
            path_display = "~"
        else:
            path_display = self.current_dir
        return f"{self.username}@{self.hostname}:{path_display}$ "

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

    # ------------- Startup script -------------

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

    # ------------- Command processing -------------

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

        Known commands in Stage 4:
        - ls        : list directory contents (VFS)
        - cd        : change current directory (VFS)
        - clear     : clear the screen
        - uniq      : print unique lines of a file
        - du        : disk usage (in bytes) for a path or current dir
        - vfs-save  : save current VFS to CSV
        - exit      : terminate the shell
        """
        success = True
        error_message: Optional[str] = None

        if command == "exit":
            success, error_message = self._handle_exit(args)
        elif command == "ls":
            success, error_message = self._handle_ls(args)
        elif command == "cd":
            success, error_message = self._handle_cd(args)
        elif command == "clear":
            success, error_message = self._handle_clear(args)
        elif command == "uniq":
            success, error_message = self._handle_uniq(args)
        elif command == "du":
            success, error_message = self._handle_du(args)
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

    # ------------- Command handlers -------------

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

    # --- ls ---

    def _handle_ls(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        List directory contents.

        Usage:
            ls              -> list current directory
            ls <path>       -> list given path (absolute or relative)
        """
        if len(args) > 1:
            msg = "Usage: ls [path]"
            print(msg)
            return False, "ls called with too many arguments"

        # Determine target path
        if args:
            target = args[0]
        else:
            target = self.current_dir

        abs_path = self._make_abs_path(target)

        # Try to list directory or print file name
        try:
            from vfs import VfsNode  # local import to avoid circular hints

            node = self.vfs.find_node(abs_path)
            if node is None:
                print(f"Error: path not found: {abs_path}")
                return False, f"path not found: {abs_path}"

            if node.is_dir:
                entries = self.vfs.list_dir(abs_path)
                for entry in entries:
                    suffix = "/" if entry.is_dir else ""
                    print(entry.name + suffix)
            else:
                # If it's a file, just print its name
                print(node.name)
            return True, None
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"Error: {e}")
            return False, str(e)

    # --- cd ---

    def _handle_cd(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Change current directory.

        Usage:
            cd <path>       (absolute or relative)
        """
        if len(args) != 1:
            msg = "Usage: cd <path>"
            print(msg)
            return False, "cd called with wrong number of arguments"

        target = args[0]
        abs_path = self._make_abs_path(target)

        node = self.vfs.find_node(abs_path)
        if node is None:
            msg = f"Error: directory not found: {abs_path}"
            print(msg)
            return False, f"directory not found: {abs_path}"

        if not node.is_dir:
            msg = f"Error: not a directory: {abs_path}"
            print(msg)
            return False, f"not a directory: {abs_path}"

        self.current_dir = abs_path
        return True, None

    # --- clear ---

    def _handle_clear(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Clear the console screen.

        Usage:
            clear
        """
        if args:
            msg = "Usage: clear"
            print(msg)
            return False, "clear called with arguments"

        # ANSI escape sequence to clear screen and move cursor to top-left.
        # Works in most modern terminals.
        print("\033[2J\033[H", end="")
        return True, None

    # --- uniq ---

    def _handle_uniq(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Print unique lines from a file (remove adjacent duplicates).

        Usage:
            uniq <file-path>

        The file path is interpreted within the VFS.
        """
        if len(args) != 1:
            msg = "Usage: uniq <file-path>"
            print(msg)
            return False, "uniq called with wrong number of arguments"

        target = args[0]
        abs_path = self._make_abs_path(target)

        node = self.vfs.find_node(abs_path)
        if node is None:
            msg = f"Error: file not found: {abs_path}"
            print(msg)
            return False, f"file not found: {abs_path}"

        if node.is_dir:
            msg = f"Error: not a file: {abs_path}"
            print(msg)
            return False, f"not a file: {abs_path}"

        # Decode file content as text, best-effort
        text = node.content.decode("utf-8", errors="replace")
        lines = text.splitlines()

        last_line: Optional[str] = None
        for line in lines:
            if line != last_line:
                print(line)
                last_line = line

        return True, None

    # --- du ---

    def _handle_du(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Disk usage (in bytes) for a path or the current directory.

        Usage:
            du              -> size of current directory (recursive)
            du <path>       -> size of given file or directory
        """
        if len(args) > 1:
            msg = "Usage: du [path]"
            print(msg)
            return False, "du called with too many arguments"

        if args:
            target = args[0]
        else:
            target = self.current_dir

        abs_path = self._make_abs_path(target)

        try:
            size = self.vfs.compute_size(abs_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return False, str(e)

        print(f"{size}\t{abs_path}")
        return True, None

    # --- vfs-save ---

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

    # ------------- Path helpers -------------

    def _make_abs_path(self, path: str) -> str:
        """
        Convert a possibly relative path to an absolute path in the VFS.

        Supports:
            - absolute paths: "/docs/readme.txt"
            - relative paths from current_dir: "docs/readme.txt"
            - '.', '..'
        """
        if path.startswith("/"):
            base_parts: List[str] = []
            tail = path.lstrip("/")
        else:
            # Start from current_dir
            if self.current_dir == "/":
                base_parts = []
            else:
                base_parts = [p for p in self.current_dir.lstrip("/").split("/") if p]
            tail = path

        for part in tail.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                if base_parts:
                    base_parts.pop()
                # if already at root, stay there
            else:
                base_parts.append(part)

        if not base_parts:
            return "/"
        return "/" + "/".join(base_parts)
