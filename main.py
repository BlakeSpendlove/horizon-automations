@bot.tree.command(name="infract", description="Log an infraction for a user", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
@app_commands.describe(user="User to infract", reason="Reason for the infraction", infraction_type="Type of infraction")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, infraction_type: str):
    if interaction.channel.id != CHANNEL_INFRACT:
        return await interaction.response.send_message("This command can only be used in the infraction channel.", ephemeral=True)

    timestamp = datetime.now(pytz.timezone("Europe/London"))
    embed = discord.Embed(title="📕 Infraction Notice", color=0x8b2828)
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Infraction Type", value=infraction_type, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Infraction ID: {gen_log_id()} • {timestamp.strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="promote", description="Log a promotion for a user", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_INFRACT_PROMOTE)
@app_commands.describe(user="User to promote", new_rank="New rank given", promotion_type="Type of promotion")
async def promote(interaction: discord.Interaction, user: discord.Member, new_rank: str, promotion_type: str):
    if interaction.channel.id != CHANNEL_PROMOTE:
        return await interaction.response.send_message("This command can only be used in the promote channel.", ephemeral=True)

    timestamp = datetime.now(pytz.timezone("Europe/London"))
    embed = discord.Embed(title="📘 Promotion Notice", color=0x8b2828)
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="New Rank", value=new_rank, inline=True)
    embed.add_field(name="Promotion Type", value=promotion_type, inline=False)
    embed.set_footer(text=f"Promotion ID: {gen_log_id()} • {timestamp.strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="session_log", description="Log a session you've hosted", guild=GUILD_ID)
@app_commands.checks.has_role(ROLE_SESSION_LOG)
@app_commands.describe(user="Yourself (host)", session_type="Type of session")
async def session_log(interaction: discord.Interaction, user: discord.Member, session_type: str):
    if interaction.channel.id != CHANNEL_SESSION_LOG:
        return await interaction.response.send_message("This command can only be used in the session log channel.", ephemeral=True)

    timestamp = datetime.now(pytz.timezone("Europe/London"))
    log_id = gen_log_id()
    embed = discord.Embed(title="📗 Session Log", color=0x8b2828)
    embed.add_field(name="Host", value=user.mention, inline=True)
    embed.add_field(name="Type", value=session_type, inline=True)
    embed.set_footer(text=f"Session ID: {log_id} • {timestamp.strftime('%d/%m/%Y %H:%M')}")

    if user.id not in user_logs:
        user_logs[user.id] = []
    user_logs[user.id].append((log_id, session_type, timestamp))

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="view_logs", description="View a user's session logs (past 7 days)", guild=GUILD_ID)
@app_commands.describe(user="User to view logs for")
async def view_logs(interaction: discord.Interaction, user: discord.Member):
    logs = user_logs.get(user.id, [])
    start, end = get_week_bounds()
    recent_logs = [(id, stype, ts) for id, stype, ts in logs if start <= ts < end]

    embed = discord.Embed(title=f"📝 Session Logs for {user.display_name}", color=0x8b2828)
    if recent_logs:
        for log_id, session_type, timestamp in recent_logs:
            embed.add_field(name=f"{session_type}", value=f"{timestamp.strftime('%d/%m/%Y %H:%M')} — ID: {log_id}", inline=False)
    else:
        embed.description = "No sessions found in the current week."
    embed.set_footer(text=f"Retrieved at {datetime.now(pytz.timezone('Europe/London')).strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(embed=embed)
