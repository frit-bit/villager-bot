import os
import discord
import asyncio
import socket
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from discord import Member

# [FOR RENDER]:
'''HOST = '0.0.0.0'  # Or '127.0.0.1', or your specific IP if needed
PORT = 10000     # Changed to 10000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Listening on {HOST}:{PORT}")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Accepted connection from {client_address}:{client_address}")

    while True:
        data = client_socket.recv(1024)
        if not data:
            break  
        client_socket.sendall(data)  # Echo back the received data
    
    client_socket.close()'''


# Get the bot token from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

# In-memory warning storage
warns = {}

def prune_old_warns(user_id):
    if user_id in warns:
        warns[user_id] = [
            dt for dt in warns[user_id]
            if datetime.now() - dt < timedelta(days=7)
        ]
        if not warns[user_id]:  # Remove empty lists
            del warns[user_id]

class Villager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        channel = self.get_channel(1366904346578649168)
        print(f'✅ {self.user} is ready and online!')
        if channel:
            await channel.send(f"{self.user.mention} has been successfully deployed")
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
    embed = discord.Embed(title=f"Info about {server.name}:", color=discord.Color.green())
    embed.add_field(name="Server Owner", value=server.owner.mention, inline=False)
    embed.add_field(name="Member Count", value=server.member_count, inline=True)
    embed.add_field(name="Created At", value=server.created_at.strftime("%B %d, %Y"), inline=True)
    embed.set_thumbnail(url=server.icon.url if server.icon else None)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="speak", description="Make the bot say anything")
@app_commands.describe(message="The message the bot will say.", channel="(Optional) The channel to send the message in.")
async def speak(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    if channel:
        await interaction.response.defer(ephemeral=True)
        await channel.send(message)
        await interaction.followup.send(f"✅ Sent message in {channel.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("✅ Sent message", ephemeral=True)
        await interaction.channel.send(message)

@bot.tree.command(name="fight", description="Fight people using ANY custom move (just for fun)")
@app_commands.describe(user="The user you want to attack", attack="The attack you want to do")
async def fight(interaction: discord.Interaction, user: Member, attack: str):
    if user == interaction.client.user:
        await interaction.response.send_message("😡 Hrmm! *punches you*")
    else:
        await interaction.response.send_message(f"{user.mention}! {interaction.user.mention} has done '{attack}' to you!")

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn", reason="The reason for the warn")
async def warn(interaction: discord.Interaction, user: Member, reason: str = None):
    
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.",
            ephemeral=True
        )
        return

    user_id = user.id
    prune_old_warns(user_id)  # Remove expired warns

    if user_id not in warns:
        warns[user_id] = []

    warns[user_id].append(datetime.now())

    await interaction.response.send_message(
        f"⚠️ {user.mention} has been warned. Reason: {reason}. They now have {len(warns[user_id])} warn(s). ⚠️"
    )

    warnings = len(warns[user_id])
    channel = bot.get_channel(1358592562620796981)

    if channel:
        if 1 < warnings <= 4:
            time_delta = timedelta(days=1 if warnings == 2 else 7 if warnings == 3 else 3)
            await user.timeout(time_delta, reason=f"Received {warnings} warnings.")
            await channel.send(f"{user.mention} has been timed out for {time_delta.days} day(s).")
        if warnings == 5:
            await user.ban(reason=f"Received {warnings} warns.")

@bot.tree.command(name="removewarns", description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove", amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: Member, amount: int):
    await interaction.response.defer(ephemeral=True)
    user_id = user.id
    prune_old_warns(user_id)

    if not interaction.user.guild_permissions.kick_members:
        await interaction.followup.send(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.",
            ephemeral=True
        )
        return

    if user_id not in warns or len(warns[user_id]) == 0:
        await interaction.followup.send(f"{user.mention} doesn't have any warns to remove.", ephemeral=True)
        return

    if amount <= 0:
        await interaction.followup.send("You must specify a positive number to remove.", ephemeral=True)
        return

    if len(warns[user_id]) < amount:
        await interaction.followup.send(
            f"{user.mention} only has {len(warns[user_id])} warns, can't remove {amount}.", ephemeral=True
        )
        return

    warns[user_id] = warns[user_id][:-amount]
    if not warns[user_id]:
        del warns[user_id]

    await interaction.followup.send(
        f"✅ {amount} warns have been removed from {user.mention}. They now have {len(warns.get(user_id, []))} warns.",
        ephemeral=True
    )

@bot.tree.command(name="checkwarns", description="Check how many warnings a user has.")
@app_commands.describe(user="The user whose warnings you want to check")
async def checkwarns(interaction: discord.Interaction, user: Member):
    user_id = user.id
    prune_old_warns(user_id)

    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    if user_id not in warns or len(warns[user_id]) == 0:
        await interaction.response.send_message(f"{user.mention} has no warnings.", ephemeral=True)
        return

    warnings = len(warns[user_id])
    await interaction.response.send_message(f"{user.mention} has {warnings} warning(s).", ephemeral=True)


@bot.tree.command(name="annoy", description="annoy someone by repeatedly pinging and sending pointless messages")
@app_commands.describe(user="The user you want to annoy")
async def annoy(interaction: discord.Interaction, user: Member):
    if not interaction.user.guild_permissions.mute_members:
        await interaction.response.send_message(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.",
            ephemeral=True
        )
        return

    # First response: ephemeral
    await interaction.response.send_message(
        f"{user.mention} will be very annoyed with you, {interaction.user.mention}",
        ephemeral=True
    )

    # Send public spam messages separately
    await asyncio.sleep(1)  # Short delay to separate the first response

    annoying_lines = [
        f"{user.mention}", f"{user.mention}", "oiiaiaoiiiai",
        "hawduiiuqhhqefpihwihiskajwhdjhkhiwqhuie", "aaaaaaa",
        f"{user.mention}", "awhqewfhriuoyiogqhjbjkefhus", 
        f"{user.mention}", f"{user.mention}", f"{user.mention}", 
        f"{user.mention}", f"{user.mention}", f"{user.mention}", 
        f"{user.mention}", f"{user.mention}", f"{user.mention}"
    ]

    for line in annoying_lines:
        await interaction.channel.send(line)  # ✅ Public
        await asyncio.sleep(0.5)


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
