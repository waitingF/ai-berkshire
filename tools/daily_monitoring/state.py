"""Machine-authored runtime state with schema validation and atomic writes."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any


STATE_SCHEMA = 1
_STATE_KEYS = (
    "price_states",
    "event_states",
    "sources",
    "documents",
    "completeness",
    "services",
)


class StateError(ValueError):
    """Raised when persisted monitoring state cannot be used safely."""


def empty_state() -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "updated_at": None,
        "price_states": {},
        "event_states": {},
        "sources": {},
        "documents": {},
        "completeness": {},
        "services": {},
    }


def load_state(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    if not source_path.exists():
        return empty_state()
    try:
        loaded = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(f"无法读取监控状态 {source_path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise StateError("监控状态根节点必须是对象")
    schema = loaded.get("schema")
    if schema != STATE_SCHEMA:
        raise StateError(f"不支持的监控状态 schema: {schema}")

    normalized = empty_state()
    normalized.update(copy.deepcopy(loaded))
    for key in _STATE_KEYS:
        if not isinstance(normalized.get(key), dict):
            raise StateError(f"监控状态字段 {key} 必须是对象")
    return normalized


def save_state_atomic(path: str | Path, state: dict[str, Any]) -> None:
    destination = Path(path)
    if state.get("schema") != STATE_SCHEMA:
        raise StateError(f"拒绝写入 schema={state.get('schema')} 的监控状态")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    content = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
