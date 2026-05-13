"""Telegram-Benachrichtigungen (Bot API)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

LOG = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, cfg: dict) -> None:
        t = cfg.get("telegram", {})
        self.enabled = bool(t.get("enabled")) and bool(t.get("bot_token")) and str(t.get("chat_id", "")).strip() != ""
        self.token = str(t.get("bot_token", "")).strip()
        self.chat_id = str(t.get("chat_id", "")).strip()
        self.base = f"https://api.telegram.org/bot{self.token}"

    def send(self, text: str, disable_notification: bool = False) -> bool:
        if not self.enabled:
            return False
        try:
            r = requests.post(
                f"{self.base}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text[:4000],
                    "parse_mode": "HTML",
                    "disable_notification": disable_notification,
                },
                timeout=30,
            )
            if r.status_code != 200:
                LOG.warning("Telegram HTTP %s: %s", r.status_code, r.text[:500])
                return False
            return True
        except requests.RequestException as e:
            LOG.error("Telegram-Fehler: %s", e)
            return False

    def hourly_lottery_card(self, payload: Dict[str, Any]) -> None:
        keys = payload.get("keys_total_fmt", "?")
        kps = payload.get("keys_per_sec_fmt", "?")
        uptime = payload.get("uptime", "?")
        temp = payload.get("gpu_temp", "?")
        vram = payload.get("vram", "?")
        fan = payload.get("fan", "?")
        mode = payload.get("mode", "?")
        puzzles = payload.get("puzzles", "?")
        health = payload.get("health", "?")
        odds = payload.get("odds", "?")
        host = payload.get("host", "?")
        restart = payload.get("last_restart", "?")
        msg = (
            "🎰 <b>Bitcoin Puzzle Lottery Update</b> 🎰\n\n"
            f"🖥 <code>{host}</code>\n"
            f"🎲 GPU läuft — Modus: <b>{mode}</b>\n"
            f"🔢 Geschätzte Keys (Vanity Total-Zeile): <b>{keys}</b>\n"
            f"⚡ Rate (GPU, gleitend): <b>{kps}</b>\n"
            f"⏱ Uptime: <b>{uptime}</b>\n"
            f"🌡 GPU-Temp: <b>{temp}</b> | VRAM: <b>{vram}</b> | Lüfter: <b>{fan}</b>\n"
            f"🧩 Aktive Puzzle-Ziele: <b>{puzzles}</b>\n"
            f"🍀 Grobe Trefferchance (Heuristik): <b>{odds}</b>\n"
            f"💚 System: <b>{health}</b>\n"
            f"🔁 Letzter Neustart Engine: <b>{restart}</b>\n\n"
            "💎 Noch kein Jackpot? Die Lotterie geht weiter…"
        )
        self.send(msg)

    def hit_alert(self, body: str) -> None:
        self.send("🚨 <b>JACKPOT / TREFFER</b> 🚨\n\n" + body, disable_notification=False)
