import discord
import requests
import time
import asyncio
from collections import defaultdict
from flask import Flask
import os
from threading import Thread

from dotenv import load_dotenv
load_dotenv()

class DiscordGroqBot:
    def __init__(self, bot_token, groq_api_key, flask_port):
        self.bot_token = bot_token
        self.groq_api_key = groq_api_key
        self.flask_port = flask_port

        # Discord Intent Configuration
        self.intents = discord.Intents.default()
        self.intents.messages = True
        self.intents.message_content = True  # Required to read messages

        # Initialize Discord Client
        self.client = discord.Client(intents=self.intents)
        self.user_last_message = defaultdict(lambda: 0)  # Cooldown Tracker

        # Flask App
        self.app = Flask(__name__)
        self.setup_routes()

        # Setup event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

    def generate_reply(self, message_text):
        """
        Sends the user input to Groq API using `llama-3.2-1b-preview` and returns the AI-generated response.
        Includes retry handling for rate limits.
        """
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "llama-3.2-1b-preview",
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
                return self.generate_reply(message_text)
            else:
                return f"⚠️ Error: {response.status_code} - {response.json().get('error', {}).get('message', 'Unknown error')}"
        except Exception as e:
            return "❌ Sorry, I'm having trouble processing your request."

    async def on_ready(self):
        print(f"✅ Logged in as {self.client.user}")

    async def on_message(self, message):
        if message.author == self.client.user:
            return  # Ignore the bot's own messages

        now = time.time()
        if now - self.user_last_message[message.author.id] < 5:  # Cooldown (5 seconds per user)
            return  

        self.user_last_message[message.author.id] = now  # Update last message time

        print(f"{message.author}: {message.content}")  # Print received messages

        await asyncio.sleep(1)  # Prevent rate limits with a slight delay

        bot_response = self.generate_reply(message.content)  # Get AI-generated reply

        await message.channel.send(bot_response)  # Send the reply

    def setup_routes(self):
        @self.app.route('/')
        def home():
            return "✅ Discord Bot with Flask & Groq API is running!"

    def run_flask(self):
        self.app.run(host='0.0.0.0', port=self.flask_port, debug=False, use_reloader=False)

    def run(self):
        Thread(target=self.run_flask).start()
        self.client.run(self.bot_token)

# Example Usage
if __name__ == '__main__':
    DISCORD_BOT_TOKEN1 = os.getenv("DISCORD_BOT_TOKEN1")
    GROQ_API_KEY1 = os.getenv("GROQ_API_KEY1")
    DISCORD_BOT_TOKEN2 = os.getenv("DISCORD_BOT_TOKEN2")
    GROQ_API_KEY2 = os.getenv("GROQ_API_KEY2")

    bot1 = DiscordGroqBot(DISCORD_BOT_TOKEN1, GROQ_API_KEY1, 5000)
    bot2 = DiscordGroqBot(DISCORD_BOT_TOKEN2, GROQ_API_KEY2, 8000)

    # Run both bots in separate threads
    thread1 = Thread(target=bot1.run)
    thread2 = Thread(target=bot2.run)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
