import discord
from discord.ext import commands
import random
import threading
import asyncio
import sys

import os

# --- CONFIG ---
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
WELCOME_CHANNEL_ID = 123456789012345678 
STAFF_LOG_CHANNEL_ID = 1410750578057023689  
AUTOMOD_ALERT_USER_ID = 1133115938858864701  

BANNED_WORDS = ["nigger", "nigga", "fucker", "retard", "fucktard", "shitter", "fucking", "test1", "fuck", "faggot", "kys", "kill your self"]

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Track selected server
active_guild = None

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"🐋 Orca's Aquarium Bot is online as {bot.user}")
    print("Type 'servers' in console to list servers the bot is in.")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"🌊 Welcome {member.mention} to **Orca's Aquarium**! 🐠🐋")

@bot.event
async def on_message(message):
    global active_guild
    if message.author == bot.user:
        return

    msg_content = message.content.lower()
    for word in BANNED_WORDS:
        if word in msg_content:
            try:
                # Delete offending message
                await message.delete()
                # Warn user in chat
                await message.channel.send(f"⚠️ {message.author.mention}, your message contained a banned word!", delete_after=5)
                # Log to console
                print(f"[AutoMod] {message.author} said a banned word in #{message.channel.name}: {message.content}")

                # DM alert to specified user
                alert_user = bot.get_user(AUTOMOD_ALERT_USER_ID)
                if alert_user:
                    try:
                        await alert_user.send(
                            f"🚨 AutoMod Alert! 🚨\nUser: {message.author} ({message.author.id})\n"
                            f"Channel: {message.channel.name}\nMessage: `{message.content}`"
                        )
                        print(f"[AutoMod] Alert sent to {alert_user}")
                    except discord.Forbidden:
                        print(f"[AutoMod] Could not DM alert user ({AUTOMOD_ALERT_USER_ID}). DMs closed.")
                else:
                    print(f"[AutoMod] Alert user ({AUTOMOD_ALERT_USER_ID}) not found in cache.")

                # Optional: send alert to staff channel
                staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
                if staff_channel:
                    await staff_channel.send(
                        f"🚨 AutoMod Alert! 🚨\nUser: {message.author.mention}\n"
                        f"Channel: {message.channel.mention}\nMessage: `{message.content}`"
                    )

            except Exception as e:
                print(f"[AutoMod Error] {e}")
            return

    # process normal commands
    await bot.process_commands(message)

# --- RANDOM COMMANDS ---
@bot.command()
async def orca(ctx):
    responses = [
        "🐋 Splash! An orca just swam by!",
        "Orca says hello! 🌊",
        "Did you know? Orcas are apex predators of the sea!"
    ]
    await ctx.send(random.choice(responses))

@bot.command()
async def fish(ctx):
    fishes = ["🐠", "🐡", "🦈", "🐟", "🦑", "🦐"]
    await ctx.send(f"You caught a {random.choice(fishes)}!")

@bot.command()
async def feed(ctx):
    foods = ["🍤 shrimp", "🦀 crab", "🐟 fish", "🦑 squid"]
    await ctx.send(f"You fed the aquarium {random.choice(foods)}! The animals are happy 🐋✨")

# --- MODERATION COMMANDS ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"⛔ {member.name} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"🚫 {member.name} has been banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"🧹 Cleared {amount} messages!", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, user: discord.User, *, message: str):
    try:
        await user.send(message)
        await ctx.send(f"📩 Sent DM to {user.name}.")
    except discord.Forbidden:
        await ctx.send(f"⚠️ Cannot DM {user.name}, they may have DMs disabled.")

# --- CONSOLE CONTROL ---
def console_input():
    global active_guild
    while True:
        try:
            command = input("> ").strip()

            if command == "servers":
                if not bot.guilds:
                    print("[Console] Bot is not in any servers.")
                else:
                    print("Servers:")
                    for i, g in enumerate(bot.guilds, 1):
                        print(f"  {i}. {g.name} (ID: {g.id})")

            elif command.startswith("use "):
                try:
                    index = int(command.split(" ")[1]) - 1
                    if 0 <= index < len(bot.guilds):
                        active_guild = bot.guilds[index]
                        print(f"[Console] Active server set to: {active_guild.name}")
                    else:
                        print("[Console] Invalid server number.")
                except:
                    print("[Console] Usage: use <number> (from 'servers' list)")

            elif command.startswith("say "):
                if not active_guild:
                    print("[Console] No active server selected. Use 'servers' then 'use <num>'.")
                    continue
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    channel_id, message = int(parts[1]), parts[2]
                    channel = bot.get_channel(channel_id)
                    if channel and channel.guild == active_guild:
                        asyncio.run_coroutine_threadsafe(channel.send(message), bot.loop)
                        print(f"[Console] Sent to #{channel.id}: {message}")
                    else:
                        print(f"[Console] Channel ID {channel_id} not found in active server.")

            elif command.startswith("kick "):
                if not active_guild:
                    print("[Console] No active server selected.")
                    continue
                parts = command.split(" ", 2)
                user_id = int(parts[1])
                reason = parts[2] if len(parts) == 3 else "No reason provided"
                member = active_guild.get_member(user_id)
                if member:
                    asyncio.run_coroutine_threadsafe(member.kick(reason=reason), bot.loop)
                    print(f"[Console] Kicked {member} (Reason: {reason})")
                else:
                    print(f"[Console] User ID {user_id} not found in active server.")

            elif command.startswith("ban "):
                if not active_guild:
                    print("[Console] No active server selected.")
                    continue
                parts = command.split(" ", 2)
                user_id = int(parts[1])
                reason = parts[2] if len(parts) == 3 else "No reason provided"
                member = active_guild.get_member(user_id)
                if member:
                    asyncio.run_coroutine_threadsafe(member.ban(reason=reason), bot.loop)
                    print(f"[Console] Banned {member} (Reason: {reason})")
                else:
                    print(f"[Console] User ID {user_id} not found in active server.")

            elif command.startswith("dm "):
                parts = command.split(" ", 2)
                user_id, message = int(parts[1]), parts[2]
                user = bot.get_user(user_id)
                if user:
                    future = asyncio.run_coroutine_threadsafe(user.send(message), bot.loop)
                    try:
                        future.result()
                        print(f"[Console] Sent DM to {user.name}")
                    except discord.Forbidden:
                        print(f"[Console] Could not DM {user.name}, DMs closed.")
                else:
                    print(f"[Console] User ID {user_id} not found in cache.")

            elif command == "stop":
                print("[Console] Stopping bot...")
                asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
                sys.exit(0)

            else:
                print("[Console] Unknown command. Options: servers, use <num>, say <channel_id> <msg>, kick <user_id> [reason], ban <user_id> [reason], dm <user_id> <msg>, stop")

        except Exception as e:
            print(f"[Console Error] {e}")

# Run console listener in a separate thread
threading.Thread(target=console_input, daemon=True).start()

# --- RUN BOT ---
bot.run(TOKEN)
