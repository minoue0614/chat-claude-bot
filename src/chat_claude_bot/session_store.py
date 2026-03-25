"""
チャンネルごとのClaudeセッションIDを管理する
"""
import json
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "chat-claude-bot"
SESSION_FILE = DATA_DIR / "sessions.json"


def _load() -> dict:
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text())
    return {}


def _save(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2))


def get(channel_id: str) -> str | None:
    return _load().get(channel_id)


def set(channel_id: str, session_id: str):
    data = _load()
    data[channel_id] = session_id
    _save(data)


def delete(channel_id: str):
    data = _load()
    data.pop(channel_id, None)
    _save(data)
