import os
import discord
import firebase_admin
from firebase_admin import credentials, firestore
from discord.ext import commands
from discord import app_commands
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Firebase
cred = credentials.Certificate("/Users/arnav/Downloads/villager-bot-d7647-firebase-adminsdk-fbsvc-eee25c51dc.json")
firebase_admin.initialize_app(cred)

db = firestore.client()  # Access Firestore database

# Save a warning for a user with timestamp and reason
def save_warn(user_id, reason):
    try:
        user_ref = db.collection('warns').document(str(user_id))
        user_data = user_ref.get()

        # If user exists, add to their existing warns list, otherwise create a new list
        warn_data = {"timestamp": firestore.SERVER_TIMESTAMP, "reason": reason}
        if user_data.exists:
            user_ref.update({
                'warns': firestore.ArrayUnion([warn_data])
            })
        else:
            user_ref.set({
                'warns': [warn_data]
            })
        logging.info(f"Warn saved for user {user_id}: {reason}")
    except Exception as e:
        logging.error(f"Error saving warn for user {user_id}: {e}")

def get_warn_count(user_id):
    try:
        user_ref = db.collection('warns').document(str(user_id))
        user_data = user_ref.get()

        if user_data.exists:
            warns = user_data.to_dict().get('warns', [])
            return len(warns)
        else:
            return 0
    except Exception as e:
        logging.error(f"Error retrieving warn count for user {user_id}: {e}")
        return 0

# Get the bot token from Railway's environment variables
TOKEN = os.getenv("DISCORD_TOKEN")

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

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user you want to warn", reason="The reason for the warn")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return
    
    if reason is None or reason.strip() == "":
        reason = "No reason provided"
        
    user_id = user.id
    save_warn(user_id, reason)  # Save warn to Firestore
    
    warn_count = get_warn_count(user_id)  # Get the updated warn count
    
    await interaction.response.send_message(
        f"⚠️ {user.mention} has been warned. Reason: {reason}. They now have {warn_count} warns. ⚠️"
    )

@bot.tree.command(name="checkwarns", description="Check how many warns a user has.")
@app_commands.describe(user="The user whose warns you are checking")
async def checkwarns(interaction: discord.Interaction, user: discord.Member):
    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_id = user.id
    user_ref = db.collection('warns').document(str(user_id))
    try:
        user_data = user_ref.get()
        
        if user_data.exists:
            user_warns = user_data.to_dict().get('warns', [])
            await interaction.response.send_message(
                f"{user.mention} has {len(user_warns)} warns."
            )
        else:
            await interaction.response.send_message(f"{user.mention} has no warns.")
    except Exception as e:
        logging.error(f"Error checking warns for {user_id}: {e}")
        await interaction.response.send_message(f"An error occurred while checking warns for {user.mention}.", ephemeral=True)

@bot.tree.command(name="removewarns", description="Remove a warning from a user.")
@app_commands.describe(user="The user whose warn you want to remove", amount="The number of warns to remove")
async def removewarns(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_id = user.id

    allowed_role_name = "Administrator"
    if not any(role.name == allowed_role_name for role in interaction.user.roles):
        await interaction.response.send_message(f"Nice try, {interaction.user.mention}, but you don't have permission to use this command.", ephemeral=True)
        return

    user_ref = db.collection('warns').document(str(user_id))
    try:
        user_data = user_ref.get()

        if user_data.exists:
            user_warns = user_data.to_dict().get('warns', [])
            if len(user_warns) < amount:
                await interaction.response.send_message(f"{user.mention} only has {len(user_warns)} warns, can't remove {amount}.", ephemeral=True)
                return
            
            # Remove the warns from Firestore
            user_warns = user_warns[:-amount]
            user_ref.update({'warns': user_warns})

            await interaction.response.send_message(f"✅ {amount} warns have been removed from {user.mention}. They now have {len(user_warns)} warns.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention} has no warns to remove.", ephemeral=True)
    except Exception as e:
        logging.error(f"Error removing warns for {user_id}: {e}")
        await interaction.response.send_message(f"An error occurred while removing warns for {user.mention}.", ephemeral=True)

bot.run(TOKEN)
