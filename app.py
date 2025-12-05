import discord
from discord.ext import commands
import os

# ✅ KEEP ALIVE (RENDER SAFE)
from flask import Flask
from threading import Thread

app = Flask('server')

@app.route('/')
def home():
    return "✅ Digamber Free Fire Ticket Bot Running"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ✅ DISCORD BOT SETUP
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Digamber Ticket Bot Online: {bot.user}")

async def load_cogs():
    await bot.load_extension("cogs.ticket")

bot.loop.create_task(load_cogs())

keep_alive()

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
