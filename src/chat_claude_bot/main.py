"""
起動スクリプト
Discord Bot と Chatwork Webhook サーバーを同時に起動する

トークンは環境変数で設定してください:
  export DISCORD_TOKEN=...
  export CHATWORK_API_TOKEN=...
  export CHATWORK_WEBHOOK_TOKEN=...
  export CHATWORK_BOT_ACCOUNT_ID=...
"""
import os
import threading


def main():
    from . import discord_bot, chatwork_bot

    discord_token = os.environ.get("DISCORD_TOKEN")
    chatwork_api_token = os.environ.get("CHATWORK_API_TOKEN")
    chatwork_webhook_token = os.environ.get("CHATWORK_WEBHOOK_TOKEN")
    chatwork_bot_account_id = os.environ.get("CHATWORK_BOT_ACCOUNT_ID")
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
        print("エラー: 起動できるBotがありません。環境変数を確認してください。")
        raise SystemExit(1)

    for t in threads:
        t.join()
