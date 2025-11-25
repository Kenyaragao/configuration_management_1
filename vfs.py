# vfs.py
"""
In-memory Virtual File System (VFS) for Stage 3 (Variant 27).

- All operations are in memory.
- The VFS is loaded from a CSV file.
- Binary data is stored as base64-encoded strings in the CSV.
- Nested directories/files are represented by POSIX-like paths, e.g.:
    /           (root dir)
    /docs       (dir)
    /docs/readme.txt  (file)

CSV format:

    path,type,content_base64
    /,dir,
    "/docs",dir,
    "/docs/readme.txt",file,SGVsbG8sIFdvcmxkIQ==

Only service commands (like vfs-save) are allowed to touch the physical CSV file.
"""

from __future__ import annotations

import base64
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class VfsLoadError(Exception):
    """Raised when the VFS cannot be loaded from disk."""


class VfsSaveError(Exception):
    """Raised when the VFS cannot be saved to disk."""


@dataclass
class VfsNode:
    name: str
    is_dir: bool
    children: Dict[str, "VfsNode"] = field(default_factory=dict)
    content: bytes = b""  # only used if is_dir == False

    def ensure_child_dir(self, name: str) -> "VfsNode":
        """
        Ensure there is a directory with the given name as a child.
        Returns that directory node.
        """
        if name in self.children:
            node = self.children[name]
            if not node.is_dir:
                raise VfsLoadError(
                    f"Path conflict: '{name}' is a file but used as a directory"
                )
            return node

        node = VfsNode(name=name, is_dir=True)
        self.children[name] = node
        return node

    def set_file(self, name: str, content: bytes) -> None:
        """
        Create or overwrite a file child with the given name and content.
        """
        self.children[name] = VfsNode(name=name, is_dir=False, content=content)


class Vfs:
    """
    Full in-memory VFS rooted at '/'.
    """

    def __init__(self) -> None:
        # Root directory
        self.root = VfsNode(name="/", is_dir=True)

    # ----------- Public API -----------

    @classmethod
    def from_csv(cls, path: Path) -> "Vfs":
        """
        Load VFS from a CSV file.

        Raises:
            VfsLoadError if file is missing or format is invalid.
        """
        if not path.exists():
            raise VfsLoadError(f"VFS file '{path}' not found")

        vfs = cls()

        try:
            with path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                required_fields = {"path", "type", "content_base64"}
                if not required_fields.issubset(reader.fieldnames or []):
                    raise VfsLoadError(
                        f"VFS CSV '{path}' has invalid header. "
                        f"Expected fields: {sorted(required_fields)}"
                    )

                for row in reader:
                    raw_path = (row.get("path") or "").strip()
                    node_type = (row.get("type") or "").strip()
                    content_b64 = row.get("content_base64") or ""

                    if not raw_path:
                        raise VfsLoadError("Empty 'path' field in VFS CSV")

                    Vfs._insert_row(vfs.root, raw_path, node_type, content_b64)
        except VfsLoadError:
            # re-raise as is
            raise
        except Exception as e:  # any unexpected parsing error
            raise VfsLoadError(f"Failed to read VFS CSV '{path}': {e}") from e

        return vfs

    def to_csv(self, path: Path) -> None:
        """
        Save the current VFS state to a CSV file.

        Raises:
            VfsSaveError on failure.
        """
        try:
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["path", "type", "content_base64"])
                self._write_node_recursive(writer, self.root, current_path="/")
        except Exception as e:
            raise VfsSaveError(f"Failed to save VFS to CSV '{path}': {e}") from e

    # ----------- Internal helpers -----------

    @staticmethod
    def _insert_row(
        root: VfsNode,
        raw_path: str,
        node_type: str,
        content_b64: str,
    ) -> None:
        """
        Insert a single row from CSV into the VFS tree.
        """
        # Normalize path
        if not raw_path.startswith("/"):
            raise VfsLoadError(f"Invalid path '{raw_path}': must start with '/'")

        if raw_path == "/":
            # Root node
            if node_type != "dir":
                raise VfsLoadError("Root path '/' must be of type 'dir'")
            return

        # Strip leading '/' and split
        parts: List[str] = [p for p in raw_path.lstrip("/").split("/") if p]
        if not parts:
            raise VfsLoadError(f"Invalid path '{raw_path}'")

        # Walk directories
        current = root
        for part in parts[:-1]:
            current = current.ensure_child_dir(part)

        leaf_name = parts[-1]

        if node_type == "dir":
            current.ensure_child_dir(leaf_name)
        elif node_type == "file":
            try:
                content = base64.b64decode(content_b64.encode("ascii"))
            except Exception as e:
                raise VfsLoadError(
                    f"Invalid base64 content for '{raw_path}': {e}"
                ) from e
            current.set_file(leaf_name, content)
        else:
            raise VfsLoadError(
                f"Invalid node type '{node_type}' for path '{raw_path}' "
                f"(expected 'dir' or 'file')"
            )

    def _write_node_recursive(
        self,
        writer: csv.writer,
        node: VfsNode,
        current_path: str,
    ) -> None:
        """
        Recursively write `node` and its children as CSV rows.
        """
        if current_path != "/":
            # Root is explicitly "/", subpaths are built as POSIX-style
            pass

        # Write this node
        if current_path == "/":
            writer.writerow([current_path, "dir", ""])
        else:
            if node.is_dir:
                writer.writerow([current_path, "dir", ""])
            else:
                content_b64 = base64.b64encode(node.content).decode("ascii")
                writer.writerow([current_path, "file", content_b64])

        if not node.is_dir:
            return

        # Recurse into children (directories first, then files, just for readability)
        for child_name, child_node in sorted(node.children.items()):
            if current_path == "/":
                child_path = f"/{child_name}"
            else:
                child_path = f"{current_path}/{child_name}"
            self._write_node_recursive(writer, child_node, child_path)
