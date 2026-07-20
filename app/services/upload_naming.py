from datetime import UTC, datetime
from pathlib import Path
import re


def safe_path_component(value: str | None, fallback: str) -> str:
    name = Path(value or fallback).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()).strip("._-")
    return cleaned[:80] or fallback


def resolve_upload_name(
    provided_name: str | None,
    kind: str,
    ion_mode: str,
    source_filename: str | None,
) -> str:
    custom_name = provided_name.strip() if provided_name else ""

    if custom_name:
        return custom_name

    source_stem = safe_path_component(Path(source_filename or kind).stem, kind)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    return f"{kind}_{ion_mode.upper()}_{source_stem}_{timestamp}"
