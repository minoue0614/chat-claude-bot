"""
Discord Bot
- メンション or DMで反応する
- チャンネルごとにセッションを維持する
"""
import discord
from . import claude_runner

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Discord Bot起動: {client.user}")


@client.event
async def on_message(message: discord.Message):
    # 自分自身のメッセージは無視
    if message.author == client.user:
        return

    # メンションまたはDMのみ反応
    is_mention = client.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)
    if not (is_mention or is_dm):
        return

    # メンション部分を除いてテキストを取得
    text = message.content
    for mention in message.mentions:
        text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    text = text.strip()

    if not text:
        return

    channel_id = f"discord_{message.channel.id}"

    async with message.channel.typing():
        response = await claude_runner.run(channel_id, text)

    # Discordの文字数制限(2000字)を超える場合は分割
    for chunk in split_message(response):
        await message.channel.send(chunk)


def split_message(text: str, limit: int = 2000) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


def start(token: str):
    client.run(token)
