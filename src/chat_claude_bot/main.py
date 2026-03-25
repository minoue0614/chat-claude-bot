"""
起動スクリプト
Discord Bot と Chatwork Webhook サーバーを同時に起動する

シークレットの取得優先順位:
  1. 環境変数 (export で設定)
  2. OSキーリング (keyring ライブラリ経由)
  3. 起動時にターミナルで入力 (getpass)
"""
import os
import threading
import getpass
import keyring

SERVICE = "chat-claude-bot"


def get_secret(key: str, required: bool = True) -> str | None:
    """環境変数 → keyring → 対話入力 の順で取得"""
    # 1. 環境変数
    value = os.environ.get(key)
    if value:
        return value

    # 2. OS キーリング
    value = keyring.get_password(SERVICE, key)
    if value:
        return value

    # 3. 対話入力（required=Trueのみ）
    if required:
        value = getpass.getpass(f"{key} を入力してください: ")
        save = input(f"  キーリングに保存しますか？ [y/N]: ").strip().lower()
        if save == "y":
            keyring.set_password(SERVICE, key, value)
            print(f"  キーリングに保存しました。")
        return value

    return None


def main():
    from . import discord_bot, chatwork_bot

    discord_token = get_secret("DISCORD_TOKEN", required=False)
    chatwork_api_token = get_secret("CHATWORK_API_TOKEN", required=False)
    chatwork_webhook_token = get_secret("CHATWORK_WEBHOOK_TOKEN", required=False)
    chatwork_bot_account_id = get_secret("CHATWORK_BOT_ACCOUNT_ID", required=False)
    chatwork_webhook_port = int(os.environ.get("CHATWORK_WEBHOOK_PORT", "8080"))

    threads = []

    if discord_token:
        t = threading.Thread(target=discord_bot.start, args=(discord_token,), daemon=True)
        t.start()
        threads.append(t)
        print("Discord Bot を起動します...")
    else:
        print("DISCORD_TOKEN が未設定のためDiscord Botはスキップします")

    if chatwork_api_token and chatwork_webhook_token and chatwork_bot_account_id:
        t = threading.Thread(
            target=chatwork_bot.start,
            args=(chatwork_api_token, chatwork_webhook_token, int(chatwork_bot_account_id), chatwork_webhook_port),
            daemon=True,
        )
        t.start()
        threads.append(t)
        print("Chatwork Webhook サーバーを起動します...")
    else:
        print("Chatwork の環境変数が未設定のためChatwork Botはスキップします")

    if not threads:
        print("エラー: 起動できるBotがありません。環境変数またはキーリングを確認してください。")
        raise SystemExit(1)

    for t in threads:
        t.join()
