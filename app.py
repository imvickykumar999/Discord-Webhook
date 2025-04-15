import discord
import requests
import time
import asyncio
from collections import defaultdict
from flask import Flask
import os
from dotenv import load_dotenv

# Flask App
app = Flask(__name__)
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Discord Intent Configuration
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Required to read messages

# Initialize Discord Bot
discord_client = discord.Client(intents=intents)

# Cooldown Tracker (Prevents Spam)
user_last_message = defaultdict(lambda: 0)

def generate_reply(message_text):
    """
    Sends the user input to Groq API using `llama-3.2-1b-preview` and returns the AI-generated response.
    Includes retry handling for rate limits.
    """
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"  # Correct API URL
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct", # https://console.groq.com/playground
            "messages": [
                {"role": "system", "content": "You are a helpful assistant and include emojis in your reply."},
                {"role": "user", "content": message_text}
            ],
            "temperature": 1,
            "max_tokens": 1024,
            "top_p": 1,
            "stream": False,
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            completion = response.json()
            return completion["choices"][0]["message"]["content"].strip()
        
        elif response.status_code == 429:  # Rate limit error
            retry_after = response.json().get("retry_after", 5)
            time.sleep(retry_after)  # Wait before retrying
            return generate_reply(message_text)
        
        else:
            return f"⚠️ Error: {response.status_code} - {response.json().get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return "❌ Sorry, I'm having trouble processing your request."

@discord_client.event
async def on_ready():
    print(f"✅ Logged in as {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return  # Ignore the bot's own messages

    now = time.time()
    if now - user_last_message[message.author.id] < 5:  # Cooldown (5 seconds per user)
        return  

    user_last_message[message.author.id] = now  # Update last message time

    print(f"{message.author}: {message.content}")  # Print received messages

    # Prevent rate limits with a slight delay
    await asyncio.sleep(1)

    # Get AI-generated reply
    bot_response = generate_reply(message.content)

    # Send the AI-generated reply to Discord
    await message.channel.send(bot_response)

# Flask Route to Keep Server Running
@app.route('/')
def home():
    return "✅ Discord Bot with Flask & Groq API is running!"

# Start Flask App in the Background
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# Start Flask & Discord Bot
if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_flask).start()
    discord_client.run(DISCORD_BOT_TOKEN)
