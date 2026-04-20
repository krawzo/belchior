import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
import sys

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_API_URL = "http://192.168.0.11:8001/chat"

if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN não encontrado em .env")
    sys.exit(1)

print(f"✓ Token carregado: {DISCORD_TOKEN[:20]}...")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✓ Bot Discord '{bot.user}' conectado!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return
    
    try:
        async with message.channel.typing():
            response = requests.post(
                BOT_API_URL,
                json={
                    "user_id": str(message.author.id),
                    "message": message.content
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                await message.reply(data["response"], mention_author=False)
            else:
                await message.reply("❌ Erro ao processar")
    
    except Exception as e:
        await message.reply(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
