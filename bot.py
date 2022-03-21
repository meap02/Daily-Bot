# bot.py

import os
import discord
from discord.ext import commands
import configparser
from datetime import datetime, time, timedelta
import asyncio


def get_config(login):
    config = configparser.ConfigParser()
    with open(login, 'r') as f:
        config.read_file(f)
    return config


config = get_config("login.ini")
TOKEN = config["appinfo"]["BOT_TOKEN"]
GUILD = config["guilds"]["testing"]

#Client will handle the discord API functions
client = discord.Client()
#bot will handle the bot functions that I want with the discord.ext.commands
bot = commands.Bot(command_prefix='!')
###############################################################################
#GLOBALS
###############################################################################
channel_home = 954808479594450975  # Put channel id that bot will inhabit
WHEN = time(20, 0, 0)  # 6:00 PM
###############################################################################


@ client.event
async def on_ready():
    #Notify user that bot is ready
    print("{0.user} has connected to Discord!".format(client))
    #Notify what Guilds it's connected to
    print("{0.user} is connected to ".format(client)
          + str(len(client.guilds))
          + " guilds within Discord: "
          + str([o.name for o in client.guilds]))
    client.loop.create_task(background_task())


@ client.event
async def on_message(message):
    pass


@bot.command
async def post(ctx):  # Fired every day
    # Make sure your guild cache is ready so the channel can be found via get_channel
    await client.wait_until_ready()
    # Note: It's more efficient to do client.get_guild(guild_id).get_channel(channel_home) as there's less looping involved, but just get_channel still works fine
    channel = client.get_channel(channel_home)
    print("The one-a-day has been triggered")
    await channel.send("Booya!")  # REDDIT POST WILL GO HERE


async def background_task():
    now = datetime.now()
    # Make sure loop doesn't start after {WHEN} as then it will send immediately the first time as negative seconds will make the sleep yield instantly
    if now.time() > WHEN:
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1), time(0))
        # Seconds until tomorrow (midnight)
        seconds = (tomorrow - now).total_seconds()
        # Sleep until tomorrow and then the loop will start
        await asyncio.sleep(seconds)
    while True:
        # You can do now() or a specific timezone if that matters, but I'll leave it with utcnow
        now = datetime.now()
        target_time = datetime.combine(
            now.date(), WHEN)  # Sets the time on today
        seconds_until_target = (target_time - now).total_seconds()
        # Sleep until we hit the target time
        await asyncio.sleep(seconds_until_target)
        await post(None)  # Call the helper function that sends the message
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1), time(0))
        # Seconds until tomorrow (midnight)
        seconds = (tomorrow - now).total_seconds()
        # Sleep until tomorrow and then the loop will start a new iteration
        await asyncio.sleep(seconds)
###############################################################################
client.run(TOKEN)  # START BOT
