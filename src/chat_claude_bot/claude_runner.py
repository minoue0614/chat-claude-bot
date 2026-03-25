"""
Claude Code CLI をサブプロセスで実行し、セッションを管理する
"""
import asyncio
import json
from . import session_store

RESET_COMMAND = "/reset"


async def run(channel_id: str, message: str) -> str:
    # リセットコマンド
    if message.strip() == RESET_COMMAND:
        session_store.delete(channel_id)
        return "セッションをリセットしました。"

    session_id = session_store.get(channel_id)

    cmd = ["claude", "--output-format", "json", "--permission-mode", "dontAsk"]
    if session_id:
        cmd += ["--resume", session_id]
    cmd += ["-p", message]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
    except FileNotFoundError:
        return "エラー: `claude` コマンドが見つかりません。Claude Codeがインストールされているか確認してください。"

    if proc.returncode != 0:
        err = stderr.decode().strip()
        return f"エラー: {err or '不明なエラーが発生しました'}"

    try:
        data = json.loads(stdout.decode())
    except json.JSONDecodeError:
        return stdout.decode().strip()

    # セッションIDを保存
    new_session_id = data.get("session_id")
    if new_session_id:
        session_store.set(channel_id, new_session_id)

    result = data.get("result", "").strip()
    return result if result else "（応答なし）"
