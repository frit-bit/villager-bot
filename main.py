import os
import discord
import asyncio
import json
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from discord import Member

# Get the bot token from Railway's environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

def load_warns():
    if os.path.exists("warns.json"):
        with open("warns.json", "r") as f:
            return json.load(f)
    return {}

def save_warns():
    with open("warns.json", "w") as f:
        json.dump(warns, f, indent=4)

warns = load_warns()

class Villager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        channel = self.get_channel(1096981058228064468)
        print(f'✅ {self.user} is ready and online!')
        if channel:
            await channel.send(f"{self.user.mention} has been deployed successfully")
        await self.change_presence(activity=discord.Game(name="Minecraft"))

bot = Villager()

# Other commands omitted for brevity...

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn", reason="The reason for the warn")
async def warn(interaction: discord.Interaction, user: Member, reason: str = None):
    allowed_role_name = "Moderator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return
    
    user_id = str(user.id)
    if user_id not in warns:
        warns[user_id] = []
    warns[user_id].append(datetime.now().isoformat())
    save_warns()  # Make sure to save after modifying the warns

    await interaction.response.send_message(
        f"⚠️ {user.mention} has been warned. Reason: {reason}. They now have {len(warns[user_id])} warn(s). ⚠️"
    )

    warnings = len(warns.get(user_id, []))

    channel = bot.get_channel(1358592562620796981)

    if channel:
        if 1 < warnings <= 4:
            if warnings == 2:
                time_delta = timedelta(days=1)
            elif warnings == 3:
                time_delta = timedelta(days=7)
            elif warnings == 4:
                time_delta = timedelta(days=3)
            await user.timeout(time_delta, reason=f"Received {warnings} warnings.")
            await channel.send(f"{user.mention} has been timed out for {time_delta} days.")
        if warnings == 5:
            await user.ban(reason=f"Received {warnings} warns.")

@bot.tree.command(name="removewarns", description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove", amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: Member, amount: int):
    user_id = str(user.id)

    allowed_role_name = "Moderator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return
    
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

    save_warns()  # Make sure to save after modifying the warns

    await interaction.response.send_message(f"✅ {amount} warns have been removed from {user.mention}. They now have {len(warns.get(user_id, []))} warns.", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nice try, but you don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    else:
        await ctx.send("An error occurred.")
        raise error

bot.run(TOKEN)
