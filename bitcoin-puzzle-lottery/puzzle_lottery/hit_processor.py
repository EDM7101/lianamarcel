"""Trefferdatei überwachen, sichern, Telegram."""

from __future__ import annotations

import base64
import json
import logging
import os
import socket
import time
from pathlib import Path
from typing import Callable, Optional

LOG = logging.getLogger(__name__)


class HitProcessor:
    def __init__(
        self,
        hits_path: Path,
        plaintext_backup: Path,
        encrypted_path: Path,
        fernet_key_env: str,
        on_hit: Callable[[str], None],
    ) -> None:
        self.hits_path = hits_path
        self.plaintext_backup = plaintext_backup
        self.encrypted_path = encrypted_path
        self.fernet_key_env = fernet_key_env
        self.on_hit = on_hit
        self._pos = 0
        if self.hits_path.exists():
            self._pos = self.hits_path.stat().st_size

    def _fernet(self):
        from cryptography.fernet import Fernet

        key = os.environ.get(self.fernet_key_env, "").strip()
        if not key:
            return None
        return Fernet(key.encode("ascii"))

    def poll(self) -> None:
        if not self.hits_path.exists():
            return
        sz = self.hits_path.stat().st_size
        if sz <= self._pos:
            return
        with open(self.hits_path, "rb") as f:
            f.seek(self._pos)
            chunk = f.read()
        self._pos = sz
        text = chunk.decode("utf-8", errors="replace")
        if "Pub Addr:" not in text:
            return
        self._handle_block(text)

    def _handle_block(self, text: str) -> None:
        host = socket.gethostname()
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        block = f"\n--- HIT {ts} {host} ---\n{text}\n"
        self.plaintext_backup.parent.mkdir(parents=True, exist_ok=True)
        with open(self.plaintext_backup, "a", encoding="utf-8") as fp:
            fp.write(block)
        f = self._fernet()
        if f:
            token = f.encrypt(text.encode("utf-8"))
            line = base64.b64encode(token).decode("ascii") + "\n"
            with open(self.encrypted_path, "a", encoding="utf-8") as fe:
                fe.write(line)
        try:
            self.on_hit(block)
        except Exception as e:
            LOG.exception("on_hit callback: %s", e)
