"""Minimal standard-library PEP 517 backend for offline MySkills installation."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
import zipfile


NAME = "obsidian-wiki-myskills"
NORMALIZED = "obsidian_wiki_myskills"
VERSION = "0.1.0"
DIST_INFO = f"{NORMALIZED}-{VERSION}.dist-info"


def _metadata() -> dict[str, bytes]:
    return {
        f"{DIST_INFO}/METADATA": (
            "Metadata-Version: 2.3\n"
            f"Name: {NAME}\n"
            f"Version: {VERSION}\n"
            "Summary: Repository-owned deterministic CLI for the MySkills Wiki suite\n"
            "Requires-Python: >=3.10\n"
            "\n"
        ).encode(),
        f"{DIST_INFO}/WHEEL": (
            "Wheel-Version: 1.0\n"
            "Generator: myskills-stdlib-backend\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
            "\n"
        ).encode(),
        f"{DIST_INFO}/entry_points.txt": (
            "[console_scripts]\n"
            "obsidian-wiki = obsidian_wiki.cli:main\n"
        ).encode(),
    }


def _record_line(path: str, content: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
    return f"{path},sha256={digest},{len(content)}"


def _wheel_contents() -> dict[str, bytes]:
    root = Path(__file__).resolve().parent
    package = root / "obsidian_wiki"
    contents: dict[str, bytes] = {}
    for path in sorted(package.rglob("*.py"), key=lambda item: item.as_posix()):
        archive_path = path.relative_to(root).as_posix()
        contents[archive_path] = path.read_bytes()
    contents.update(_metadata())
    records = [_record_line(path, content) for path, content in sorted(contents.items())]
    records.append(f"{DIST_INFO}/RECORD,,")
    contents[f"{DIST_INFO}/RECORD"] = ("\n".join(records) + "\n").encode()
    return contents


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    del config_settings, metadata_directory
    filename = f"{NORMALIZED}-{VERSION}-py3-none-any.whl"
    destination = Path(wheel_directory) / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    timestamp = (2020, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for path, content in sorted(_wheel_contents().items()):
            info = zipfile.ZipInfo(path, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            wheel.writestr(info, content)
    return filename


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    del config_settings
    root = Path(metadata_directory) / DIST_INFO
    root.mkdir(parents=True, exist_ok=True)
    for path, content in _metadata().items():
        relative = Path(path).relative_to(DIST_INFO)
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return DIST_INFO


def get_requires_for_build_wheel(
    config_settings: dict[str, object] | None = None,
) -> list[str]:
    del config_settings
    return []
