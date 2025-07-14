import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import pytz

TOKEN = os.getenv("TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))

ROLE_TIMETABLE_CLAIM = 1311733474436190321
ROLE_TIMETABLE_VIEW = 1311733474436190321
ROLE_INFRACT_PROMOTE = 1311733474436190321
ROLE_SESSION_LOG = 1311733474436190321
ROLE_TIMETABLE_CLEAR = 1311733474436190321

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

timetable_data = {
    "Period 1": [],
    "Period 2": [],
    "Period 3": [],
    "Period 4": [],
    "Period 5": []
}

def generate_footer(label):
    random_id = random.randint(100000, 999999)
    timestamp = datetime.now(pytz.timezone("Europe/London")).strftime('%d/%m/%Y %H:%M')
    return f"Horizon {label} • ID: {random_id} • {timestamp}"

@bot.event
async def on_ready():
    await bot.tree.sync(guild=GUILD_ID)
    reset_timetable.start()
    print(f"Bot is ready and synced with guild {GUILD_ID.id}")

@tasks.loop(minutes=60)
async def reset_timetable():
    now = datetime.now(pytz.timezone("Europe/London"))
    if now.hour == 0:
        global timetable_data
        timetable_data = {f"Period {i}": [] for i in range(1, 6)}
        print("Timetable reset at UK midnight.")

@bot.tree.command(name="timetable_claim", description="Claim a lesson", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLAIM)
async def timetable_claim(interaction: discord.Interaction, teaching_name: str, year: int, period: int, subject: str, room: str):
    if f"Period {period}" not in timetable_data:
        await interaction.response.send_message("Invalid period.", ephemeral=True)
        return

    entry = {
        "year": year,
        "subject": subject,
        "room": room,
        "teaching_name": teaching_name
    }
    timetable_data[f"Period {period}"].append(entry)
    timetable_data[f"Period {period}"] = sorted(timetable_data[f"Period {period}"], key=lambda x: x["year"])

    embed = discord.Embed(title="Timetable Claim", color=0x8b2828)
    embed.add_field(name="User:", value=f"{interaction.user.mention}", inline=False)
    embed.add_field(name="Teaching Name:", value=teaching_name, inline=False)
    embed.add_field(name="Year:", value=f"Year {year}", inline=False)
    embed.add_field(name="Period:", value=f"Period {period}", inline=False)
    embed.add_field(name="Subject:", value=subject, inline=False)
    embed.add_field(name="Room:", value=room, inline=False)
    embed.set_footer(text=generate_footer("Timetable Claim"))
    await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

@bot.tree.command(name="timetable", description="View timetable", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_VIEW)
async def timetable(interaction: discord.Interaction):
    embed = discord.Embed(title="Timetable", color=0x8b2828)
    embed.add_field(name="User:", value=f"{interaction.user.mention}", inline=False)
    for period in [f"Period {i}" for i in range(1, 6)]:
        details = timetable_data[period]
        if details:
            formatted = "\n".join([f"Year {d['year']} - {d['subject']} ({d['room']}) by {d['teaching_name']}" for d in details])
        else:
            formatted = "N/A"
        embed.add_field(name=f"**{period}:**", value=formatted, inline=False)
    embed.set_footer(text=generate_footer("Timetable"))
    await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

@bot.tree.command(name="timetable_clear", description="Clear the timetable manually", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_TIMETABLE_CLEAR)
async def timetable_clear(interaction: discord.Interaction):
    global timetable_data
    timetable_data = {f"Period {i}": [] for i in range(1, 6)}
    await interaction.response.send_message("Timetable cleared.", ephemeral=True)

@bot.tree.command(name="infract", description="Issue a staff infraction", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: str = None):
    embed = discord.Embed(title="Infraction Notice", color=0x8b2828)
    embed.add_field(name="User:", value=f"{user.mention}", inline=False)
    embed.add_field(name="Infracted By:", value=f"{interaction.user.mention}", inline=False)
    embed.add_field(name="Type:", value=type, inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    if demotion_role:
        embed.add_field(name="Demotion Role:", value=demotion_role, inline=False)
    embed.set_footer(text=generate_footer("Staff Member Infraction"))
    await interaction.response.send_message(f"{user.mention}", embed=embed)

@bot.tree.command(name="promote", description="Promote a staff member", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    embed = discord.Embed(title="Promotion Notice", color=0x8b2828)
    embed.add_field(name="User:", value=f"{user.mention}", inline=False)
    embed.add_field(name="Promoted By:", value=f"{interaction.user.mention}", inline=False)
    embed.add_field(name="Role:", value=promotion_to, inline=False)
    embed.add_field(name="Reason:", value=reason, inline=False)
    embed.set_footer(text=f"{generate_footer('Promotion Notice')} • Check your DMs")
    await interaction.response.send_message(f"{user.mention}", embed=embed)

@bot.tree.command(name="session_log", description="Log a session", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_SESSION_LOG)
async def session_log(interaction: discord.Interaction, user: discord.Member, evidence: str, session_date: str):
    if not (evidence.startswith("http://") or evidence.startswith("https://")) or not any(evidence.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
        await interaction.response.send_message("Evidence must be an image URL.", ephemeral=True)
        return
    embed = discord.Embed(title="Session Log", color=0x8b2828)
    embed.add_field(name="User:", value=f"{user.mention}", inline=False)
    embed.add_field(name="Logged By:", value=f"{interaction.user.mention}", inline=False)
    embed.add_field(name="Session Date:", value=session_date, inline=False)
    embed.set_image(url=evidence)
    embed.set_footer(text=f"{generate_footer('Session Log')} • Check your DMs")
    await interaction.response.send_message(f"{interaction.user.mention}", embed=embed)

bot.run(TOKEN)
