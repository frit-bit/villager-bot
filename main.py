import os
import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

# Get the bot token from Railway's environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
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
    allowed_role_name = "Moderator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return
    if channel:
        await interaction.response.defer(ephemeral=True)  # Let Discord know you're working
        await channel.send(message)
        await interaction.followup.send(f"✅ Sent message in {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message(message)
        await interaction.followup.send(f"✅ Sent message", ephemeral=True)

@bot.tree.command(name="fight", description="Fight people using different moves (just for fun)")
@app_commands.describe(user="The user you want to attack", attack="The attack you want to do")
async def fight(interaction: discord.Interaction, user: discord.Member, attack: str):
    if user == interaction.client.user:
        await interaction.response.send_message(f"Hrmm! *punches you*")
        return
    else:
        await interaction.response.send_message(f"{user.mention}! {interaction.user.mention} has done '{attack}' to you!")

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

    channel = bot.get_channel(1096981058228064468)

    if channel:
        if len(warns[user_id]) >= 5:
            await user.ban(reason="5 warnings")
            await interaction.followup.send(f"{user.mention} has been permanently banned (Received 5 warns).", ephemeral=True)

        elif len(warns[user_id]) >= 4:
            await user.ban(reason="3 warnings")
            await interaction.followup.send(f"{user.mention} has been banned for 3 days (Received 4 warns).", ephemeral=True)
            
            await asyncio.sleep(259200)

            user_obj = await bot.fetch_user(user_id)
            await interaction.guild.unban(user_obj, reason="Temp ban expired")
    
        elif len(warns[user_id]) >= 3:
            await user.timeout_for(timedelta(days=7))
            await interaction.followup.send(f"{user.mention
