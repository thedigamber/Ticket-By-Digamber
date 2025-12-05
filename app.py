import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# ✅ WEB SERVER FOR RENDER
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Digamber Free Fire Ticket Bot Running"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

# ✅ BOT SETUP
intents = discord.Intents.all()

class DigamberBot(commands.Bot):
    async def setup_hook(self):
        # ✅ SAFE WAY TO LOAD COGS (NO LOOP ERROR)
        await self.load_extension("cogs.ticket")
        print("✅ Ticket Cog Loaded Successfully")

bot = DigamberBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot Online As: {bot.user}")

# ✅ START WEB + BOT
keep_alive()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("❌ TOKEN environment variable not set!")

bot.run(TOKEN)
