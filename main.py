import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random, string, pytz

TOKEN = os.getenv("TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))

# Role IDs
ROLE_TIMETABLE_CLAIM = 1330284350985470058
ROLE_TIMETABLE_VIEW = 1330283312089923674
ROLE_INFRACT_PROMOTE = 1330283312089923674
ROLE_SESSION_LOG = 1330284350985470058
ROLE_TIMETABLE_CLEAR = 1330283312089923674

# Channel IDs
CHANNEL_TIMETABLE_CLAIM = 1330295535986282506
CHANNEL_TIMETABLE_VIEW = 1330295535986282506
CHANNEL_TIMETABLE_CLEAR = 1330295535986282506
CHANNEL_INFRACT = 1394403198642556948
CHANNEL_PROMOTE = 1394403244431769753
CHANNEL_SESSION_LOG = 1394403467417747598

# In-memory storage
user_logs = {}
timetable_data = {f"Period {i}": [] for i in range(1, 6)}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

def gen_log_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_week_bounds():
    now = datetime.now(pytz.timezone("Europe/London"))
    start = now - timedelta(days=(now.weekday() + 1) % 7)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end

@bot.event
async def on_ready():
    await bot.tree.sync(guild=GUILD_ID)
    reset_timetable.start()
    print(f"✅ Bot ready and synced with guild {GUILD_ID.id}")

@tasks.loop(minutes=60)
async def reset_timetable():
    now = datetime.now(pytz.timezone("Europe/London"))
    if now.hour == 0:
        global timetable_data
        timetable_data = {f"Period {i}": [] for i in range(1, 6)}
        print("⏰ Timetable reset at midnight UK time.")

@bot.tree.command(name="timetable_claim", description="Claim a teaching period", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLAIM)
@app_commands.describe(
    teaching_name="Your name",
    period="Period number (1–5)",
    year="Year group",
    initials="Your initials",
    subject="Subject",
    room="Room"
)
async def timetable_claim(interaction: discord.Interaction, teaching_name: str, period: int, year: str, initials: str, subject: str, room: str):
    if interaction.channel.id != CHANNEL_TIMETABLE_CLAIM:
        return await interaction.response.send_message("You can only use this command in the correct channel.", ephemeral=True)
    if period < 1 or period > 5:
        return await interaction.response.send_message("Period must be between 1 and 5.", ephemeral=True)

    entry = f"{teaching_name} | Year {year}: {initials} – {subject} (Room {room})"
    timetable_data[f"Period {period}"].append(entry)
    embed = discord.Embed(title="Timetable Claim", description=entry, color=0x8b2828)
    embed.set_footer(text=f"ID: {gen_log_id()} • {datetime.now(pytz.timezone('Europe/London')).strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(interaction.user.mention, embed=embed)

@bot.tree.command(name="timetable", description="View today's timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_VIEW)
async def view_timetable(interaction: discord.Interaction):
    if interaction.channel.id != CHANNEL_TIMETABLE_VIEW:
        return await interaction.response.send_message("You can only use this command in the correct channel.", ephemeral=True)

    embed = discord.Embed(title="Timetable", color=0x11806A)
    for period, entries in timetable_data.items():
        embed.add_field(name=period, value="\n".join(entries) if entries else "No claims", inline=False)
    embed.set_footer(text=f"Auto‑clears at midnight (UK) • ID: {gen_log_id()}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="timetable_clear", description="Clear full timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLEAR)
async def timetable_clear(interaction: discord.Interaction):
    if interaction.channel.id != CHANNEL_TIMETABLE_CLEAR:
        return await interaction.response.send_message("You can only use this command in the correct channel.", ephemeral=True)
    global timetable_data
    timetable_data = {f"Period {i}": [] for i in range(1, 6)}
    await interaction.response.send_message("🗑️ Timetable cleared.", ephemeral=True)

@bot.tree.command(name="infract", description="Log an infraction", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
@app_commands.describe(user="User to discipline", reason="Reason", type="Infraction type (Termination/Infraction/Demotion)", demotion_role="(optional) demotion role")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: discord.Role = None):
    if interaction.channel.id != CHANNEL_INFRACT:
        return await interaction.response.send_message("You can only use this command in the correct channel.", ephemeral=True)

    embed = discord.Embed(title="Infraction Notice", color=0x8b2828)
    embed.add_field(name="Disciplined User:", value=user.mention, inline=False)
    embed.add_field(name="Disciplined By:", value=interaction.user.mention, inline=False)
    embed.add_field(name="Type:", value=type, inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    if demotion_role:
        await user.remove_roles(demotion_role)
        embed.add_field(name="Demotion Role Removed:", value=demotion_role.mention, inline=False)
    embed.set_footer(text=f"ID: {gen_log_id()} • {datetime.now(pytz.timezone('Europe/London')).strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(user.mention, embed=embed)

@bot.tree.command(name="promote", description="Log a promotion", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
@app_commands.describe(user="User to promote", promotion_to="Promoted to (new rank)", reason="Reason")
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if interaction.channel.id != CHANNEL_PROMOTE:
        return await interaction.response.send_message("You can only use this command in the correct channel.", ephemeral=True)

    embed = discord.Embed(title="Promotion Notice", color=0x8b2828)
    embed.add_field(name="Promoted User:", value=user.mention, inline=False)
    embed.add_field(name="Promoted By:", value=interaction.user.mention, inline=False)
    embed.add_field(name="Promotion To:", value=promotion_to, inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    embed.set_footer(text=f"Please check your direct messages. • ID: {gen_log_id()}")
    await interaction.response.send_message(user.mention, embed=embed)

@bot.tree.command(name="session_log", description="Log a session", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_SESSION_LOG)
@app_commands.describe(user="User who hosted", session_date="Date of session", evidence_upload="Image proof")
async def session_log(interaction: discord.Interaction, user: discord.Member, session_date: str, evidence_upload: discord.Attachment):
    if interaction.channel.id != CHANNEL_SESSION_LOG:
        return await interaction.response.send_message("You can only use this command in the correct channel.", ephemeral=True)
    if not evidence_upload.content_type or not evidence_upload.content_type.startswith("image/"):
        return await interaction.response.send_message("Please upload a valid image.", ephemeral=True)

    log_id = gen_log_id()
    timestamp = datetime.now(pytz.timezone("Europe/London"))
    user_logs.setdefault(user.id, []).append({"id": log_id, "dt": timestamp, "date": session_date, "url": evidence_upload.url})

    embed = discord.Embed(title="Session Log", color=0x8b2828)
    embed.add_field(name="User:", value=user.mention, inline=False)
    embed.add_field(name="Logged By:", value=interaction.user.mention, inline=False)
    embed.add_field(name="Session Date:", value=session_date, inline=False)
    embed.set_image(url=evidence_upload.url)
    embed.set_footer(text=f"Check your DMs • ID: {log_id} • {timestamp.strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(user.mention, embed=embed)

@bot.tree.command(name="view_logs", description="View session logs this week", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_SESSION_LOG)
async def view_logs(interaction: discord.Interaction, user: discord.Member):
    start, end = get_week_bounds()
    entries = [e for e in user_logs.get(user.id, []) if start <= e["dt"] < end]
    entries.sort(key=lambda e: e["dt"])

    embed = discord.Embed(title="Session Logs", color=0x8b2828)
    embed.add_field(name=str(user), value="​", inline=False)
    if not entries:
        embed.add_field(name="No logs this week", value="No session logs from Sunday to Saturday.", inline=False)
    else:
        for e in entries:
            ts = e["dt"].strftime('%d/%m/%Y %H:%M')
            embed.add_field(name="​", value=f"[View Log]({e['url']}) — `{e['id']}` • {ts}", inline=False)
    await interaction.response.send_message(interaction.user.mention, embed=embed)

bot.run(TOKEN)
