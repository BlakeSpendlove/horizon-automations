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

# Channel restrictions
CHANNEL_TIMETABLE_CLAIM = 1330295535986282506
CHANNEL_TIMETABLE_VIEW = 1330295535986282506
CHANNEL_TIMETABLE_CLEAR = 1330295535986282506
CHANNEL_INFRACT = 1394403198642556948
CHANNEL_PROMOTE = 1394403244431769753
CHANNEL_SESSION_LOG = 1394403467417747598

# In-memory storage for logs: {user_id: [ {id, datetime, session_date, attachment_url} ] }
user_logs = {}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

timetable_data = {f"Period {i}": [] for i in range(1, 6)}

def generate_footer(label):
    rand_id = random.randint(100000, 999999)
    ts = datetime.now(pytz.timezone("Europe/London")).strftime('%d/%m/%Y %H:%M')
    return f"Horizon {label} • ID: {rand_id} • {ts}"

def gen_log_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_week_bounds():
    now = datetime.now(pytz.timezone("Europe/London"))
    start = now - timedelta(days=(now.weekday()+1)%7)  # Sunday
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end

@bot.event
async def on_ready():
    await bot.tree.sync(guild=GUILD_ID)
    reset_timetable.start()
    print(f"Bot ready and synced with guild {GUILD_ID.id}")

@tasks.loop(minutes=60)
async def reset_timetable():
    now = datetime.now(pytz.timezone("Europe/London"))
    if now.hour == 0:
        global timetable_data
        timetable_data = {f"Period {i}": [] for i in range(1, 6)}
        print("Timetable data reset at UK midnight.")

# ... timetable_claim, timetable, timetable_clear, infract, promote commands remain unchanged ...

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

    header = f"{interaction.user.mention}\n\n"
    embed = discord.Embed(title="Session Logs", color=0x8b2828)
    embed.add_field(name=str(user), value="\u200b", inline=False)  # mention inside

    if not logs:
        embed.add_field(name="No logs this week", value="You have no session logs from Sunday to Saturday.", inline=False)
    else:
        for e in logs:
            dt = e["datetime"].strftime('%d/%m/%Y %H:%M')
            embed.add_field(name="\u200b", value=f"[View Log]({e['url']})", inline=False)
            embed.set_footer(text=f"{e['id']} • {dt}")

    await interaction.response.send_message(header, embed=embed)

bot.run(TOKEN)
