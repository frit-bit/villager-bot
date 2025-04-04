import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

# Get the bot token from Railway's environment variables
TOKEN = os.getenv("DISCORD_TOKEN")

# Load warns from a file if it exists
if os.path.exists("warns.json"):
    with open("warns.json", "r") as f:
        warns = json.load(f)
        # Convert string timestamps back to datetime objects
        for user_id in warns:
            warns[user_id] = [datetime.fromisoformat(ts) for ts in warns[user_id]]
else:
    warns = {}

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

bot = Villager()

def save_warns():
    with open("warns.json", "w") as f:
        json.dump({k: [t.isoformat() for t in v] for k, v in warns.items()}, f)

@bot.tree.command(name="hello", description="Say hello to the villager!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hrmmm! Hello {interaction.user.mention}!")

@bot.tree.command(name="ping", description="Check bot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="serverinfo", description="Get information about the server")
async def serverinfo(interaction: discord.Interaction):
    server = interaction.guild
    embed = discord.Embed(title=f"{server.name} Info", color=discord.Color.green())
    embed.add_field(name="Server Owner", value=server.owner.mention, inline=False)
    embed.add_field(name="Member Count", value=server.member_count, inline=True)
    embed.add_field(name="Created At", value=server.created_at.strftime("%B %d, %Y"), inline=True)
    embed.set_thumbnail(url=server.icon.url if server.icon else None)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="speak", description="Make the bot say something!")
@app_commands.describe(message="The message the bot will say.", channel="(Optional) The channel to send the message in.")
async def speak(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return
    if channel:
        await interaction.response.defer(ephemeral=True)
        await channel.send(message)
        await interaction.followup.send(f"✅ Sent message in {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message(message)
        await interaction.followup.send(f"✅ Sent message", ephemeral=True)

@bot.tree.command(name="fight", description="Fight people using different moves (just for fun)")
@app_commands.describe(user="The user you want to attack", attack="The attack you want to do")
async def fight(interaction: discord.Interaction, user: discord.Member, attack: str):
    await interaction.response.send_message(f"{user.mention}! {interaction.user.mention} has done '{attack}' to you!")

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn", reason="The reason for the warn")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = str(user.id)
    if user_id not in warns:
        warns[user_id] = []
    warns[user_id].append(datetime.now())
    save_warns()

    await interaction.response.send_message(
        f"⚠️ {user.mention} has been warned. Reason: {reason}. They now have {len(warns[user_id])} warns. ⚠️"
    )

@bot.tree.command(name="checkwarns", description="Check how many warns a user has.")
@app_commands.describe(user="The user whose warns you are checking")
async def checkwarns(interaction: discord.Interaction, user: discord.Member):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = str(user.id)
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)

    user_warns = warns.get(user_id, [])
    recent_warns = [warn_time for warn_time in user_warns if warn_time > one_week_ago]

    await interaction.response.send_message(
        f"{user.mention} has {len(recent_warns)} warns in the last 7 days."
    )

@bot.tree.command(name="removewarns", description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove", amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: discord.Member, amount: int):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = str(user.id)

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

    save_warns()

    await interaction.response.send_message(f"✅ {amount} warns have been removed from {user.mention}. They now have {len(warns.get(user_id, []))} warns.", ephemeral=True)

bot.run(TOKEN)
