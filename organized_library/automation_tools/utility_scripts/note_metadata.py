#!/usr/bin/env python3
"""Shared markdown metadata parsing utilities for fitness notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re

import yaml


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", flags=re.DOTALL)
ID_RE = re.compile(r"\*\*ID:\*\*\s*([^\n*]+?)(?:\s+\*\*Created:|\s*$)", flags=re.MULTILINE)
CREATED_RE = re.compile(r"\*\*Created:\*\*\s*([^(]+)", flags=re.MULTILINE)
UPDATED_TAG_RE = re.compile(r"\(Updated:\s*([^)]+)\)")


@dataclass
class NoteMetadata:
    note_id: str = ""
    created: str = ""
    updated: str = ""
    section: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = "none"  # yaml | bold | none


def _normalize_tags(raw_tags: Any) -> List[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, list):
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    if isinstance(raw_tags, str):
        cleaned = raw_tags.strip()
        if not cleaned:
            return []
        # Support "a, b, c" and "[a, b, c]".
        cleaned = cleaned.strip("[]")
        return [part.strip().strip("'\"") for part in cleaned.split(",") if part.strip()]
    return [str(raw_tags).strip()]


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], Optional[Tuple[int, int]]]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, None
    block = match.group(1)
    try:
        parsed = yaml.safe_load(block) or {}
    except Exception:
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}
    return parsed, match.span()


def read_metadata(text: str) -> NoteMetadata:
    frontmatter, _ = parse_frontmatter(text)
    if frontmatter:
        created = str(frontmatter.get("created", "") or "").strip()
        updated = str(frontmatter.get("updated", "") or "").strip()
        return NoteMetadata(
            note_id=str(frontmatter.get("id", "") or "").strip(),
            created=created,
            updated=updated,
            section=str(frontmatter.get("section", "") or "").strip(),
            tags=_normalize_tags(frontmatter.get("tags")),
            source="yaml",
        )

    note_id_match = ID_RE.search(text)
    created_match = CREATED_RE.search(text)
    updated_match = UPDATED_TAG_RE.search(text)
    return NoteMetadata(
        note_id=note_id_match.group(1).strip() if note_id_match else "",
        created=created_match.group(1).strip() if created_match else "",
        updated=updated_match.group(1).strip() if updated_match else "",
        source="bold" if note_id_match or created_match or updated_match else "none",
    )


def replace_or_insert_frontmatter(text: str, metadata: Dict[str, Any]) -> str:
    frontmatter, span = parse_frontmatter(text)
    merged = dict(frontmatter)
    merged.update({k: v for k, v in metadata.items() if v not in (None, "")})
    yaml_block = "---\n" + yaml.safe_dump(merged, sort_keys=False).strip() + "\n---\n"
    if span is not None:
        return yaml_block + text[span[1]:].lstrip("\n")
    return yaml_block + text.lstrip("\n")
