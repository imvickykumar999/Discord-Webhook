import discord
import asyncio
import threading

# Load Discord bot token
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  

if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ ERROR: Discord bot token is missing!")

# Discord Intent Configuration
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  

# Initialize Discord Client
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return  
    print(f"📩 {message.author} (ID: {message.author.id}) said in channel {message.channel.id}: {message.content}")

# Function to start the bot
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client.run(DISCORD_BOT_TOKEN)

# Start bot in a new thread
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# Keep the script running
while True:
    pass  # Prevents script from exiting
