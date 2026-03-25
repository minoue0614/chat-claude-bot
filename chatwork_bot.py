"""
Chatwork Bot (Webhook受信サーバー)
- Chatwork の Webhook を受け取り Claude に転送する
- ルームごとにセッションを維持する
"""
import os
import hmac
import hashlib
import asyncio
import aiohttp
from aiohttp import web
import claude_runner

CHATWORK_API_BASE = "https://api.chatwork.com/v2"


async def send_message(room_id: int, text: str, api_token: str):
    url = f"{CHATWORK_API_BASE}/rooms/{room_id}/messages"
    headers = {"X-ChatWorkToken": api_token}
    # Chatworkの1メッセージ上限は約4万字なので基本分割不要
    async with aiohttp.ClientSession() as session:
        await session.post(url, headers=headers, data={"body": text})


def verify_webhook(body: bytes, signature: str, token: str) -> bool:
    expected = hmac.new(token.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def make_app(api_token: str, webhook_token: str, bot_account_id: int) -> web.Application:
    app = web.Application()

    async def handle_webhook(request: web.Request) -> web.Response:
        body = await request.read()

        # 署名検証
        signature = request.headers.get("X-ChatWorkWebhookSignature", "")
        if not verify_webhook(body, signature, webhook_token):
            return web.Response(status=400, text="Invalid signature")

        payload = await request.json()
        webhook_type = payload.get("webhook_event_type")

        # メッセージ作成イベントのみ処理
        if webhook_type != "message_created":
            return web.Response(text="ok")

        event = payload.get("webhook_event", {})
        account_id = event.get("account_id")
        room_id = event.get("room_id")
        message_body: str = event.get("body", "")

        # Bot自身のメッセージは無視
        if account_id == bot_account_id:
            return web.Response(text="ok")

        # [To:ボットID] 宛のメッセージのみ処理
        to_tag = f"[To:{bot_account_id}]"
        if to_tag not in message_body:
            return web.Response(text="ok")

        # タグを除去してテキストを取得
        text = message_body.replace(to_tag, "").strip()
        if not text:
            return web.Response(text="ok")

        channel_id = f"chatwork_{room_id}"

        # 非同期でClaudeを実行して返信
        async def process():
            response = await claude_runner.run(channel_id, text)
            await send_message(room_id, response, api_token)

        asyncio.create_task(process())
        return web.Response(text="ok")

    app.router.add_post("/chatwork/webhook", handle_webhook)
    return app


def start(api_token: str, webhook_token: str, bot_account_id: int, port: int = 8080):
    app = make_app(api_token, webhook_token, bot_account_id)
    print(f"Chatwork Webhook サーバー起動: port {port}")
    web.run_app(app, port=port)
