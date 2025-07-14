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
@app_commands.describe(period="Period number (1-5)", year="Year group", initials="Your initials", subject="Subject", room="Room")
async def timetable_claim(interaction: discord.Interaction, period: int, year: str, initials: str, subject: str, room: str):
    if interaction.channel.id != CHANNEL_TIMETABLE_CLAIM:
        return await interaction.response.send_message("You can only use this command in the timetable claim channel.", ephemeral=True)

    if period < 1 or period > 5:
        return await interaction.response.send_message("Invalid period. Must be 1 to 5.", ephemeral=True)

    entry = f"Year {year}: {initials} - {subject} ({room})"
    timetable_data[f"Period {period}"].append(entry)

    embed = discord.Embed(title=f"Period {period} Claimed", description=entry, color=0x8b2828)
    embed.set_footer(text=datetime.now(pytz.timezone("Europe/London")).strftime('%d/%m/%Y %H:%M'))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="timetable", description="View today's timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_VIEW)
async def timetable(interaction: discord.Interaction):
    if interaction.channel.id != CHANNEL_TIMETABLE_VIEW:
        return await interaction.response.send_message("You can only use this command in the timetable view channel.", ephemeral=True)

    embed = discord.Embed(title="📘 Horizon Timetable", color=0x8b2828)
    for period, entries in timetable_data.items():
        val = "\n".join(entries) if entries else "No claims"
        embed.add_field(name=period, value=val, inline=False)
    embed.set_footer(text="Auto-clears at midnight (UK)")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="timetable_clear", description="Clear the full timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLEAR)
async def timetable_clear(interaction: discord.Interaction):
    if interaction.channel.id != CHANNEL_TIMETABLE_CLEAR:
        return await interaction.response.send_message("You can only use this command in the timetable clear channel.", ephemeral=True)

    global timetable_data
    timetable_data = {f"Period {i}": [] for i in range(1, 6)}
    await interaction.response.send_message("🗑️ Timetable cleared successfully.")


@bot.tree.command(name="infract", description="Log an infraction", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
@app_commands.describe(user="User to infract", reason="Reason for infraction")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str):
    if interaction.channel.id != CHANNEL_INFRACT:
        return await interaction.response.send_message("You can only use this command in the infraction log channel.", ephemeral=True)

    embed = discord.Embed(title="⚠️ Infraction Logged", color=0x8b2828)
    embed.add_field(name="User:", value=user.mention, inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    embed.add_field(name="Logged By:", value=interaction.user.mention, inline=False)
    embed.set_footer(text=datetime.now(pytz.timezone("Europe/London")).strftime('%d/%m/%Y %H:%M'))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="promote", description="Log a promotion", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
@app_commands.describe(user="User to promote", new_rank="New rank or role")
async def promote(interaction: discord.Interaction, user: discord.Member, new_rank: str):
    if interaction.channel.id != CHANNEL_PROMOTE:
        return await interaction.response.send_message("You can only use this command in the promotion channel.", ephemeral=True)

    embed = discord.Embed(title="📈 Promotion Logged", color=0x8b2828)
    embed.add_field(name="User:", value=user.mention, inline=False)
    embed.add_field(name="New Rank:", value=new_rank, inline=False)
    embed.add_field(name="Promoted By:", value=interaction.user.mention, inline=False)
    embed.set_footer(text=datetime.now(pytz.timezone("Europe/London")).strftime('%d/%m/%Y %H:%M'))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="session_log", description="Log a session", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_SESSION_LOG)
@app_commands.describe(evidence_upload="Upload an image of the session")
async def session_log(interaction: discord.Interaction, user: discord.Member, session_date: str, evidence_upload: discord.Attachment):
    if interaction.channel.id != CHANNEL_SESSION_LOG:
        return await interaction.response.send_message("You can only use this command in the session log channel.", ephemeral=True)

    if not evidence_upload.content_type or not evidence_upload.content_type.startswith("image/"):
        return await interaction.response.send_message("Uploaded file must be an image.", ephemeral=True)

    log_id = gen_log_id()
    timestamp = datetime.now(pytz.timezone("Europe/London"))
    entry = {"id": log_id, "datetime": timestamp, "session_date": session_date, "url": evidence_upload.url}
    user_logs.setdefault(user.id, []).append(entry)

    embed = discord.Embed(title="Session Log", color=0x8b2828)
    embed.add_field(name="User:", value=user.mention, inline=False)
    embed.add_field(name="Logged By:", value=interaction.user.mention, inline=False)
    embed.add_field(name="Session Date:", value=session_date, inline=False)
    embed.set_image(url=evidence_upload.url)
    embed.set_footer(text=f"{log_id} • {timestamp.strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(user.mention, embed=embed)


@bot.tree.command(name="view_logs", description="View user's session logs for the current week", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_SESSION_LOG)
async def view_logs(interaction: discord.Interaction, user: discord.Member):
    start, end = get_week_bounds()
    logs = [e for e in user_logs.get(user.id, []) if start <= e["datetime"] < end]
    logs.sort(key=lambda e: e["datetime"])

    embed = discord.Embed(title="Session Logs", color=0x8b2828)
    embed.add_field(name=str(user), value="\u200b", inline=False)

    if not logs:
        embed.add_field(name="No logs this week", value="You have no session logs from Sunday to Saturday.", inline=False)
    else:
        for e in logs:
            dt = e["datetime"].strftime('%d/%m/%Y %H:%M')
            embed.add_field(name="\u200b", value=f"[View Log]({e['url']}) — `{e['id']}` • {dt}", inline=False)

    await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)


# Run the bot
bot.run(TOKEN)
