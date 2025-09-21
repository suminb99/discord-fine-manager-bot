import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
from keep_alive import keep_alive

keep_alive()

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if token is None:
    raise ValueError("디스코드 TOKEN이 .env 파일에 설정되어 있지 않습니다.")


handler = logging.FileHandler(filename='discord.log',
                              encoding='utf-8',
                              mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    print("봇이 성공적으로 로그인했습니다!")


# 벌금 메세지 수집
async def get_fine_messages(channel):
    messages = []
    delta = (datetime.now(timezone.utc) - timedelta(days=14))  # 2주 전 날짜 구하기

    # after=delta 로 정확히 14일 이내만 훑기, limit=None로 개수 제한 없음
    async for message in channel.history(after=delta, limit=None):
        if (not message.author.bot) and message.mentions:  # 봇이 작성하지 않은 멘션이 있는 메시지만 수집
            messages.append(message)

    return messages


# 체크 안 한 부원 판독
async def get_unchecked_members(message):
    # 멘션에서 role, channel 등 제외하고 member만 필터링
    mentioned = [m for m in message.mentions if isinstance(m, discord.Member)]  # 멘션된 부원
    if not mentioned:
        return []
    
    checked = set()  # 체크 한 부원 ID 저장용
    reaction = discord.utils.get(message.reactions, emoji="✅")  # 체크 이모지 객체 가져오기
    if reaction:
        # 체크 한 부원
        async for user in reaction.users():
            # 봇은 제외
            if getattr(user, "bot", False):
                continue
            checked.add(user.id)

    unchecked = [m for m in mentioned if m.id not in checked]  # 체크 안 한 부원
    return unchecked


# 슬래시 명령
@bot.tree.command(name="벌금체크", description="최근 14일간 벌금 납부 후 체크 안 한 부원을 멘션합니다.")
async def 벌금체크(interaction: discord.Interaction):
    messages = await get_fine_messages(interaction.channel)
    
    all_unchecked = set() # 여러 메세지에서 부원이 중복되지 않게 한 번만 멘션
    for message in messages:
        unchecked = await get_unchecked_members(message)
        all_unchecked.update(unchecked)  # 체크 안 한 부원들 모음

    if all_unchecked:
        mentions = " ".join(member.mention for member in all_unchecked)
        await interaction.response.send_message(f"{mentions}\n벌금 납부 안 하신 분들은 입금 후 체크 표시(✅) 꼭 남겨주세요!")
    else:
        await interaction.response.send_message("✅ 전원 입금 완료!")


bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)