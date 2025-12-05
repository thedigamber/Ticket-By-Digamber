import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --------------------------
# Web server (Render)
# --------------------------
app = Flask("server")

@app.route("/")
def home():
    return "✅ Digamber Free Fire Ticket Bot Running"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run_web).start()

# --------------------------
# Bot Setup
# --------------------------
intents = discord.Intents.all()

class DigamberBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, application_id=None)  # application_id optional
        # ensure tree sync controlled by setup_hook

    async def setup_hook(self):
        # load cogs safely
        await self.load_extension("cogs.ticket")
        # sync commands to guilds on first load (defer global if you want)
        # We DO NOT automatically call bot.tree.sync() globally here to avoid long delays.
        print("✅ Cogs loaded.")

bot = DigamberBot()

@bot.event
async def on_ready():
    print(f"✅ Bot ready as: {bot.user} (ID: {bot.user.id})")

# Start webserver and run bot
keep_alive()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN env var not set. Add TOKEN to environment variables on Render.")

bot.run(TOKEN)
