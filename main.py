import os
import discord
import psycopg2
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

# Get the bot token and database URL from Railway's environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
warns = {}

# Set up the database connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

# Create the table if it doesn't exist
def create_warns_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            reason TEXT,
            timestamp TIMESTAMP NOT NULL
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

class Villager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        create_warns_table()  # Ensure the table exists when the bot starts
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
    allowed_role_name = "Administrator"
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
    await interaction.response.send_message(f"{user.mention}! {interaction.user.mention} has done '{attack}' to you!")

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn", reason="The reason for the warn")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = user.id
    timestamp = datetime.now()

    # Insert a new warn entry for the user
    cursor.execute(
        "INSERT INTO warns (user_id, reason, timestamp) VALUES (%s, %s, %s)",
        (user_id, reason, timestamp)
    )

    # Commit and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    await interaction.response.send_message(
        f"⚠️ {user.mention} has been warned. Reason: {reason}. ⚠️"
    )

@bot.tree.command(name="checkwarns", description="Check how many warns a user has.")
@app_commands.describe(user="The user whose warns you are checking")
async def checkwarns(interaction: discord.Interaction, user: discord.Member):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = user.id
    now = datetime.now()
    one_week_ago = now - timedelta(days=7)

    # Retrieve the user's warns from the database in the last 7 days
    cursor.execute(
        "SELECT COUNT(*) FROM warns WHERE user_id = %s AND timestamp > %s",
        (user_id, one_week_ago)
    )
    count = cursor.fetchone()[0]

    # Close the connection
    cursor.close()
    conn.close()

    await interaction.response.send_message(
        f"{user.mention} has {count} warns in the last 7 days."
    )

@bot.tree.command(name="removewarns", description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove", amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: discord.Member, amount: int):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = user.id

    # Retrieve the user's warns from the database
    cursor.execute(
        "SELECT id FROM warns WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
        (user_id, amount)
    )
    warn_ids = cursor.fetchall()

    # If the user doesn't have enough warns
    if len(warn_ids) == 0:
        await interaction.response.send_message(f"{user.mention} doesn't have any warns to remove.", ephemeral=True)
        cursor.close()
        conn.close()
        return

    # Remove the warns from the database
    cursor.executemany(
        "DELETE FROM warns WHERE id = %s",
        [(warn_id[0],) for warn_id in warn_ids]
    )

    # Commit and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    await interaction.response.send_message(f"✅ {amount} warns have been removed from {user.mention}.", ephemeral=True)

bot.run(TOKEN)
