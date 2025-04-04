import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
warns = {}
temp_bans = {}

class Villager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f'✅ {self.user} is ready and online!')
        await self.change_presence(activity=discord.Game(name="Minecraft"))
        await self.check_temp_bans()

    async def check_temp_bans(self):
        now = datetime.now()
        for user_id, unban_time in list(temp_bans.items()):
            if now >= unban_time:
                try:
                    guild = self.get_guild(949688632879513600)  # Replace with your actual guild ID
                    user = await self.fetch_user(user_id)
                    await guild.unban(user, reason="Temporary ban expired")
                    del temp_bans[user_id]
                    print(f"✅ {user} has been unbanned as their temp ban expired.")
                except Exception as e:
                    print(f"❌ Error unbanning {user_id}: {e}")
        
bot = Villager()

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn", reason="The reason for the warn")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    allowed_role_name = "Moderator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = user.id
    if user_id not in warns:
        warns[user_id] = []
    warns[user_id].append(datetime.now())

    await interaction.response.send_message(
        f"⚠️ {user.mention} has been warned. Reason: {reason}. They now have {len(warns[user_id])} warn(s). ⚠️"
    )

    # Handling punishments based on warn count
    if len(warns[user_id]) >= 5:
        await user.ban(reason="5 warnings")
        await interaction.followup.send(f"{user.mention} has been permanently banned (Received 5 warns).", ephemeral=True)

    elif len(warns[user_id]) >= 4:
        await user.ban(reason="3 warnings")
        await interaction.followup.send(f"{user.mention} has been banned for 3 days (Received 4 warns).", ephemeral=True)

        # Set the time for unbanning (temp ban for 3 days)
        temp_bans[user_id] = datetime.now() + timedelta(days=3)

    elif len(warns[user_id]) >= 3:
        await user.timeout_for(timedelta(days=7))  # Timeout for 7 days
        await interaction.followup.send(f"{user.mention} has been timed out for 7 days (Received 3 warns).", ephemeral=True)

    elif len(warns[user_id]) >= 2:
        await user.timeout_for(timedelta(days=1))  # Timeout for 1 day
        await interaction.followup.send(f"{user.mention} has been timed out for 1 day (Received 2 warns).", ephemeral=True)

@bot.tree.command(name="checkwarns", description="Check how many warns a user has.")
@app_commands.describe(user="The user whose warns you are checking")
async def checkwarns(interaction: discord.Interaction, user: discord.Member):
    allowed_role_name = "Moderator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = user.id
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)

    user_warns = warns.get(user_id, [])
    recent_warns = [warn_time for warn_time in user_warns if warn_time > one_week_ago]

    await interaction.response.send_message(
        f"{user.mention} has {len(recent_warns)} warn(s) in the last 7 days."
    )

@bot.tree.command(name="removewarns", description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove", amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: discord.Member, amount: int):
    allowed_role_name = "Moderator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = user.id

    if user_id not in warns or len(warns[user_id]) == 0:
        await interaction.response.send_message(f"{user.mention} doesn't have any warns to remove.", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("You must specify a positive number to remove.", ephemeral=True)
        return

    if len(warns[user_id]) < amount:
        await interaction.response.send_message(f"{user.mention} only has {len(warns[user_id])} warns, can't remove {amount}.", ephemeral=True)
        return

    warns[user_id] = warns[user_id][:-amount]

    if len(warns[user_id]) == 0:
        del warns[user_id]

    await interaction.response.send_message(f"✅ {amount} warns have been removed from {user.mention}. They now have {len(warns.get(user_id, []))} warns.", ephemeral=True)

bot.run(TOKEN)
