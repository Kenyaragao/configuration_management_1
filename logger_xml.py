# logger_xml.py
"""
XML-based command logger for the shell emulator (Stage 2).

Each logged event contains:
- username
- timestamp
- command name
- arguments
- whether it succeeded
- optional error message
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import xml.etree.ElementTree as ET


@dataclass
class CommandEvent:
    username: str
    command: str
    args: List[str]
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()


class CommandLogger:
    """
    Simple XML logger that appends command events to a log file.

    If log_path is None, logging is disabled.
    """

    def __init__(self, log_path: Optional[Path], username: str) -> None:
        self.log_path = log_path
        self.username = username

    def log(
        self,
        command: str,
        args: List[str],
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log a command event to the XML log file.

        If log_path is None, this function does nothing.
        """
        if self.log_path is None:
            return

        event = CommandEvent(
            username=self.username,
            command=command,
            args=args,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(),
        )

        self._append_event(event)

    def _append_event(self, event: CommandEvent) -> None:
        """
        Append an event to the XML log file, creating it if necessary.
        """
        log_path = self.log_path
        assert log_path is not None  # for type checkers

        # Make sure the directory exists.
        if log_path.parent:
            log_path.parent.mkdir(parents=True, exist_ok=True)

        if log_path.exists():
            tree = ET.parse(log_path)
            root = tree.getroot()
        else:
            root = ET.Element("log")
            tree = ET.ElementTree(root)

        event_elem = ET.SubElement(root, "event")

        username_elem = ET.SubElement(event_elem, "username")
        username_elem.text = event.username

        timestamp_elem = ET.SubElement(event_elem, "timestamp")
        timestamp_elem.text = event.timestamp.isoformat()

        command_elem = ET.SubElement(event_elem, "command")
        command_elem.text = event.command

        args_elem = ET.SubElement(event_elem, "args")
        for arg in event.args:
            arg_elem = ET.SubElement(args_elem, "arg")
            arg_elem.text = arg

        success_elem = ET.SubElement(event_elem, "success")
        success_elem.text = "true" if event.success else "false"

        if event.error_message:
            error_elem = ET.SubElement(event_elem, "error")
            error_elem.text = event.error_message

        tree.write(log_path, encoding="utf-8", xml_declaration=True)
