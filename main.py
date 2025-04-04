
import os
import discord
import asyncio
from keep_alive import keep_alive
from discord.ext import commands, tasks
from web3 import Web3
from flask import Flask, render_template
from threading import Thread

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

gas_channel = None

# Web3 setup for 0G Newton Testnet
RPC_URL = 'https://evmrpc-testnet.0g.ai'
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Flask app setup
app = Flask(__name__)



@app.route('/')
def home():
    try:
        if web3.is_connected():
            gas_price = web3.eth.gas_price
            gas_price_gwei = web3.from_wei(gas_price, 'gwei')
            return render_template('index.html', gas_price=f"{gas_price_gwei:.2f}")
        else:
            return render_template('index.html', error="Failed to connect to the network")
    except Exception as e:
        return render_template('index.html', error=str(e))
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    update_gas_price.start()

@tasks.loop(minutes=1)
async def update_gas_price():
    global gas_channel
    if gas_channel:
        try:
            if web3.is_connected():
                gas_price = web3.eth.gas_price
                gas_price_gwei = web3.from_wei(gas_price, 'gwei')
                # Format with 2 decimals and ensure the decimal point shows
                formatted_price = f"{gas_price_gwei:.2f}".replace('.', '・')
                await gas_channel.edit(name=f'⛽️gas-{formatted_price}-gwei🔄')
            else:
                await gas_channel.edit(name='⚠️gas-price-unavailable')
        except Exception as e:
            print(f"Error updating gas price: {e}")

@bot.command()
async def setup_gas_channel(ctx):
    global gas_channel
    try:
        # Check if gas channel already exists
        if gas_channel is not None:
            await ctx.send("❌ Gas price channel already exists!")
            return
            
        # Create channel with restricted permissions
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                send_messages=False,
                add_reactions=False,
                attach_files=False,
                embed_links=False,
                create_instant_invite=False
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                send_messages=True,
                manage_channels=True
            )
        }
        gas_channel = await ctx.guild.create_text_channel('gas-price-loading', overwrites=overwrites)
        await ctx.send(f'✅ Created gas price channel!')
        await update_gas_price()
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create channels!")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")



@bot.command()
async def gas(ctx):
    try:
        if web3.is_connected():
            gas_price = web3.eth.gas_price
            gas_price_gwei = web3.from_wei(gas_price, 'gwei')
            await ctx.send(f'⛽ Current gas price on 0G Newton Testnet: **{gas_price_gwei:.2f} Gwei** ')
        else:
            await ctx.send('❌ Failed to connect to the 0G Newton Testnet.')
    except Exception as e:
        await ctx.send(f'⚠️ Error fetching gas price: {e}')

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def run_bot():
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("⚠️ Please set your Discord bot token in the Secrets tab")
        return
    bot.run(TOKEN)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    run_bot()
