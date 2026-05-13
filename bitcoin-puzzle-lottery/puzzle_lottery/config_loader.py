"""YAML-Konfiguration laden und mit Umgebungsvariablen mergen."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import yaml


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Konfiguration muss ein YAML-Mapping sein")

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if token:
        raw.setdefault("telegram", {})["bot_token"] = token
    if chat:
        raw.setdefault("telegram", {})["chat_id"] = chat

    return raw


def ensure_dirs(cfg: Dict[str, Any]) -> Path:
    wd = Path(cfg["orchestrator"]["work_dir"])
    wd.mkdir(parents=True, exist_ok=True)
    log_dir = Path(cfg["logging"]["dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    return wd
