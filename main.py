import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")


# 벌금 메세지 수집
async def get_fine_messages(channel):
    messages = []
    delta = (datetime.now(timezone.utc) - timedelta(days=14)) # 2주 전 날짜 구하기
    
    async for message in channel.history(limit=50):
        if message.created_at < delta:
            break

        if not (message.author.bot) and message.mentions:  # 봇이 작성하지 않은 멘션이 있는 메시지만 수집
            messages.append(message)

    return messages
    
# 체크 안 한 부원 판독
async def get_unchecked_members(message):
    mentioned = message.mentions # 멘션된 부원
    checked = [] 
    unchecked = [] 
    reaction = discord.utils.get(message.reactions, emoji="✅") # 체크 이모지 객체 가져오기
    if reaction:
        # 체크 한 부원
        async for member in reaction.users():
            checked.append(member.id)
    
    unchecked = [member for member in mentioned if member.id not in checked] # 체크 안 한 부원

    return unchecked


@bot.command()
async def 벌금체크(ctx):
    messages = await get_fine_messages(ctx.channel)
    all_unchecked = []

    for message in messages:
        unchecked = await get_unchecked_members(message)
        all_unchecked.extend(unchecked) # 체크 안 한 부원들 모음

    if all_unchecked:
        mentions = " ".join(f"<@{member.id}>" for member in all_unchecked)
        await ctx.send(
            f"아직 벌금 안 내신 분들은 \n{mentions}\n입금 후 체크 표시(✅) 꼭 남겨주세요! "
        )
    else:
        await ctx.send("✅ 전원 입금 완료!")


bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)

