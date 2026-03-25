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
        # 次回から省略できるようキーリングに保存するか確認
        save = input(f"  キーリングに保存しますか？ [y/N]: ").strip().lower()
        if save == "y":
            keyring.set_password(SERVICE, key, value)
            print(f"  キーリングに保存しました。")
        return value

    return None


DISCORD_TOKEN = get_secret("DISCORD_TOKEN", required=False)
CHATWORK_API_TOKEN = get_secret("CHATWORK_API_TOKEN", required=False)
CHATWORK_WEBHOOK_TOKEN = get_secret("CHATWORK_WEBHOOK_TOKEN", required=False)
CHATWORK_BOT_ACCOUNT_ID = get_secret("CHATWORK_BOT_ACCOUNT_ID", required=False)
CHATWORK_WEBHOOK_PORT = int(os.environ.get("CHATWORK_WEBHOOK_PORT", "8080"))


def start_discord():
    import discord_bot
    discord_bot.start(DISCORD_TOKEN)


def start_chatwork():
    import chatwork_bot
    chatwork_bot.start(
        api_token=CHATWORK_API_TOKEN,
        webhook_token=CHATWORK_WEBHOOK_TOKEN,
        bot_account_id=int(CHATWORK_BOT_ACCOUNT_ID),
        port=CHATWORK_WEBHOOK_PORT,
    )


if __name__ == "__main__":
    threads = []

    if DISCORD_TOKEN:
        t = threading.Thread(target=start_discord, daemon=True)
        t.start()
        threads.append(t)
        print("Discord Bot を起動します...")
    else:
        print("DISCORD_TOKEN が未設定のためDiscord Botはスキップします")

    if CHATWORK_API_TOKEN and CHATWORK_WEBHOOK_TOKEN and CHATWORK_BOT_ACCOUNT_ID:
        t = threading.Thread(target=start_chatwork, daemon=True)
        t.start()
        threads.append(t)
        print("Chatwork Webhook サーバーを起動します...")
    else:
        print("Chatwork の環境変数が未設定のためChatwork Botはスキップします")

    if not threads:
        print("エラー: 起動できるBotがありません。環境変数またはキーリングを確認してください。")
        exit(1)

    for t in threads:
        t.join()
