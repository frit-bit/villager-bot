import os
import discord
import asyncio
import random
from discord.ext import commands
from discord import app_commands, Member
from datetime import datetime, timedelta
from keep_alive import keep_alive
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# Get the bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")

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
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self):
        channel = self.get_channel(1366904232317550683)
        print(f'✅ {self.user} is ready and online!')
        if channel:
            await channel.send(
                f"{self.user.mention} has been successfully deployed.")
        await self.change_presence(activity=discord.Game(name="Minecraft"))
        for guild in self.guilds:
            print(
                f"Connected to guild: {guild.name} (ID: {guild.id}, Member Count: {guild.member_count})"
            )
        print(f"Total visible guilds: {len(self.guilds)}")


bot = Villager()


@bot.tree.command(name="hello", description="Say hello to the villager!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hrmmm! Hello {interaction.user.mention}!")


@bot.tree.command(name="ping", description="Check bot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓  **Latency:** {round(bot.latency * 1000)} ms  🏓")


@bot.tree.command(name="serverinfo",
                  description="Get information about the server")
async def serverinfo(interaction: discord.Interaction):
    server = interaction.guild
    embed = discord.Embed(title=f"Info about {server.name}:",
                          color=discord.Color.green())
    embed.add_field(name="Server Owner",
                    value=server.owner.mention,
                    inline=False)
    embed.add_field(name="Member Count",
                    value=server.member_count,
                    inline=True)
    embed.add_field(name="Created At",
                    value=server.created_at.strftime("%B %d, %Y"),
                    inline=True)
    embed.set_thumbnail(url=server.icon.url if server.icon else None)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="report",
                  description="Report a bug to the creator/dev(s)")
@app_commands.describe(bug="The bug or error you want to report.")
async def report(interaction: discord.Interaction, bug: str):
    dev = await bot.fetch_user(947551947735576627)
    app_info = await bot.application_info()
    owner = app_info.owner
    await interaction.response.send_message(
        f"✅ Your bug has been reported to {owner.name}.", ephemeral=True)
    await dev.send(
        f"{interaction.user} reported a bug in the bot!\nThey said: '" + bug +
        "'.")


@bot.tree.command(name="speak", description="Make the bot say anything")
@app_commands.describe(
    message="The message the bot will say.",
    channel="(Optional) The channel to send the message in.")
async def speak(interaction: discord.Interaction,
                message: str,
                channel: discord.TextChannel = None):
    # Check if user has permissions or is the bot owner
    is_authorized = (interaction.user.guild_permissions.kick_members
                     or await bot.is_owner(interaction.user))

    if not is_authorized:
        await interaction.response.send_message(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.",
            ephemeral=True)
        return

    if channel:
        await interaction.response.defer(ephemeral=True)
        await channel.send(message)
        await interaction.followup.send(f"✅ Sent message in {channel.mention}",
                                        ephemeral=True)
    else:
        await interaction.response.send_message("✅ Sent message",
                                                ephemeral=True)
        await interaction.channel.send(message)


@bot.tree.command(
    name="fight",
    description="Fight people using ANY custom move (just for fun)")
@app_commands.describe(user="The user you want to attack",
                       attack="The attack you want to do")
async def fight(interaction: discord.Interaction, user: Member, attack: str):
    if user == interaction.client.user:
        await interaction.response.send_message("😡 Hrmm! *punches you*")
    else:
        await interaction.response.send_message(
            f"{user.mention}! {interaction.user.mention} has done '{attack}' to you!"
        )


@bot.tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"The coin landed on {random.choice(['heads', 'tails'])}.")


@bot.tree.command(name="8ball", description="Ask the 8ball a question")
@app_commands.describe(question="The question you want to ask the 8ball")
async def eightball(interaction: discord.Interaction, question: str):
    responses = [
        "It is certain.", "It is decidedly so.", "Without a doubt.",
        "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
        "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
        "Reply hazy, try again.", "Ask again later.",
        "Better not tell you now.", "Cannot predict now.",
        "Concentrate and ask again.", "Don't count on it.", "My reply is no.",
        "My sources say no.", "Outlook not so good.", "Very doubtful."
    ]
    embed = discord.Embed(title="🎱 8ball 🎱", color=discord.Color.blue())
    embed.add_field(name="Question",
                    value=f"{interaction.user.mention} asked: '{question}'",
                    inline=False)
    embed.add_field(name="Answer",
                    value=f"The 8ball says: '{random.choice(responses)}'",
                    inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn",
                       reason="The reason for the warn")
async def warn(interaction: discord.Interaction,
               user: Member,
               reason: str = None):

    # Check if user has permissions or is the bot owner
    is_authorized = (interaction.user.guild_permissions.kick_members
                     or await bot.is_owner(interaction.user))

    if not is_authorized:
        await interaction.response.send_message(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.",
            ephemeral=True)
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
            time_delta = timedelta(
                days=1 if warnings == 2 else 7 if warnings == 3 else 3)
            await user.timeout(time_delta,
                               reason=f"Received {warnings} warnings.")
            await channel.send(
                f"{user.mention} has been timed out for {time_delta.days} day(s)."
            )
        if warnings == 5:
            await user.ban(reason=f"Received {warnings} warns.")


@bot.tree.command(name="removewarns",
                  description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove",
                       amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: Member,
                      amount: int):
    await interaction.response.defer(ephemeral=True)
    user_id = user.id
    prune_old_warns(user_id)

    if not interaction.user.guild_permissions.kick_members:
        await interaction.followup.send(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.",
            ephemeral=True)
        return

    if user_id not in warns or len(warns[user_id]) == 0:
        await interaction.followup.send(
            f"{user.mention} doesn't have any warns to remove.",
            ephemeral=True)
        return

    if amount <= 0:
        await interaction.followup.send(
            "You must specify a positive number to remove.", ephemeral=True)
        return

    if len(warns[user_id]) < amount:
        await interaction.followup.send(
            f"{user.mention} only has {len(warns[user_id])} warns, can't remove {amount}.",
            ephemeral=True)
        return

    warns[user_id] = warns[user_id][:-amount]
    if not warns[user_id]:
        del warns[user_id]

    await interaction.followup.send(
        f"✅ {amount} warns have been removed from {user.mention}. They now have {len(warns.get(user_id, []))} warns.",
        ephemeral=True)


@bot.tree.command(name="checkwarns",
                  description="Check how many warnings a user has.")
@app_commands.describe(user="The user whose warnings you want to check")
async def checkwarns(interaction: discord.Interaction, user: Member):
    user_id = user.id
    prune_old_warns(user_id)

    # Check if user has permissions or is the bot owner
    is_authorized = (interaction.user.guild_permissions.kick_members
                     or await bot.is_owner(interaction.user))

    if not is_authorized:
        await interaction.response.send_message(
            f"Nice try, {interaction.user.mention}, but you don't have permission to use this                command.",
            ephemeral=True)
        return

    if user_id not in warns or len(warns[user_id]) == 0:
        await interaction.response.send_message(
            f"{user.mention} has no warnings.", ephemeral=True)
        return

    warnings = len(warns[user_id])
    await interaction.response.send_message(
        f"{user.mention} has {warnings} warning(s).", ephemeral=True)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "Nice try but you don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    else:
        await ctx.send("An error occurred.")
        raise error


bot.run(TOKEN)
