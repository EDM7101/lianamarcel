# Telegram-Anbindung

## 1. Bot anlegen

1. In Telegram mit `@BotFather` sprechen, `/newbot` ausführen.
2. **Bot-Token** kopieren (geheim halten).
3. Deine **Chat-ID** ermitteln (z. B. `@userinfobot` oder eine kleine Testnachricht an `@RawDataBot`).

## 2. Konfiguration

In `config.yaml` unter `telegram`:

- `enabled: true`
- `bot_token: "..."`  
- `chat_id: "..."`  

Alternativ Umgebungsvariablen: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

Schnellstart: `python3 -m puzzle_lottery --wizard -c ./config.yaml`

## 3. Verschlüsselte Treffer

```bash
export PUZZLE_LOTTERY_FERNET_KEY="$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")"
```

Ohne gesetzten Schlüssel werden Treffer nur in Klartext protokolliert (`hits.txt`).

## 4. Benachrichtigungen

- Start / Stopp (wenn aktiviert)
- Ziel-Reload (diskret)
- GPU-Temperatur kritisch
- Stündlicher Lotterie-Report
- Sofort bei Treffer (`hit_alert`)

Audit-Log: `logs/telegram.log` (siehe `logging.dir` in der Konfiguration).
