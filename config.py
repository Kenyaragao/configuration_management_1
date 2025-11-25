from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """
    Application configuration loaded from command-line arguments.

    Attributes:
        vfs_path: Path to the physical representation of the VFS on disk.
        log_path: Path to the XML log file for command events.
        startup_script: Path to the startup script with shell commands.
    """
    vfs_path: Optional[Path]
    log_path: Optional[Path]
    startup_script: Optional[Path]
