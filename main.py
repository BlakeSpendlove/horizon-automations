import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import string
import pytz

TOKEN = os.getenv("TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))

# Roles
ROLE_TIMETABLE_CLAIM = 1330284350985470058
ROLE_TIMETABLE_VIEW = 1330283312089923674
ROLE_INFRACT_PROMOTE = 1330283312089923674
ROLE_SESSION_LOG = 1330284350985470058
ROLE_TIMETABLE_CLEAR = 1330283312089923674

# Channels
CHANNEL_TIMETABLE_CLAIM = 1330295535986282506
CHANNEL_TIMETABLE_VIEW = 1330295535986282506
CHANNEL_TIMETABLE_CLEAR = 1330295535986282506
CHANNEL_INFRACT = 1394403198642556948
CHANNEL_PROMOTE = 1394403244431769753
CHANNEL_SESSION_LOG = 1394403467417747598

# Storage
user_logs = {}
timetable_data = {f"Period {i}": [] for i in range(1, 6)}

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)


# Utils
def gen_log_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_week_bounds():
    now = datetime.now(pytz.timezone("Europe/London"))
    start = now - timedelta(days=(now.weekday() + 1) % 7)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end


# Events
@bot.event
async def on_ready():
    await bot.tree.sync(guild=GUILD_ID)
    reset_timetable.start()
    print(f"✅ Bot ready and synced with guild {GUILD_ID.id}")


# Timetable Reset
@tasks.loop(minutes=60)
async def reset_timetable():
    now = datetime.now(pytz.timezone("Europe/London"))
    if now.hour == 0:
        global timetable_data
        timetable_data = {f"Period {i}": [] for i in range(1, 6)}
        print("⏰ Timetable reset at midnight UK time.")


# Commands
@bot.tree.command(name="timetable_claim", description="Claim a teaching period", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLAIM)
@app_commands.describe(teaching_name="Your teaching name", period="Period number (1-5)", year="Year group", initials="Your initials", subject="Subject", room="Room")
async def timetable_claim(interaction: discord.Interaction, teaching_name: str, period: int, year: str, initials: str, subject: str, room: str):
    if interaction.channel.id != CHANNEL_TIMETABLE_CLAIM:
        return await interaction.response.send_message("You can only use this command in the timetable claim channel.", ephemeral=True)

    if period < 1 or period > 5:
        return await interaction.response.send_message("Invalid period. Must be 1 to 5.", ephemeral=True)

    entry = f"{teaching_name} | Year {year}: {initials} - {subject} ({room})"
    timetable_data[f"Period {period}"].append(entry)

    timestamp = datetime.now(pytz.timezone("Europe/London"))
    embed = discord.Embed(title=f"Period {period} Claimed", description=entry, color=0x8b2828)
    embed.set_footer(text=f"Timetable ID: {gen_log_id()} • {timestamp.strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="timetable", description="View today's timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_VIEW)
async def timetable(interaction: discord.Interaction):
    if interaction.channel.id != CHANNEL_TIMETABLE_VIEW:
        return await interaction.response.send_message("You can only use this command in the timetable view channel.", ephemeral=True)

    timestamp = datetime.now(pytz.timezone("Europe/London"))
    embed = discord.Embed(title="📘 Horizon Timetable", color=0x8b2828)
    for period, entries in timetable_data.items():
        val = "\n".join(entries) if entries else "No claims"
        embed.add_field(name=period, value=val, inline=False)
    embed.set_footer(text=f"Timetable ID: {gen_log_id()} • {timestamp.strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="timetable_clear", description="Clear the full timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLEAR)
async def timetable_clear(interaction: discord.Interaction):
    if interaction.channel.id != CHANNEL_TIMETABLE_CLEAR:
        return await interaction.response.send_message("You can only use this command in the timetable clear channel.", ephemeral=True)

    global timetable_data
    timetable_data = {f"Period {i}": [] for i in range(1, 6)}
    await interaction.response.send_message("🗑️ Timetable cleared successfully.")
