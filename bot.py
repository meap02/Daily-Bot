# bot.py

import discord
from discord.ext import commands
import configparser
from datetime import datetime, time, timedelta
import asyncio
import json


###############################################################################
#                       CONFIGURATION FETCH
###############################################################################
def get_config(login):
    config = configparser.ConfigParser()
    with open(login, 'r') as f:
        config.read_file(f)
    return config


config = get_config("login.ini")
TOKEN = config["default"]["BOT_TOKEN"]
admin_user = config["default"]["admin_user"]
with open("servers.json", "r") as f:
    servers = json.load(f)
###############################################################################
#                               Message Prompts
###############################################################################
introduction = """Hey! I'm DailyBot, created by Kyle Just. I can do a various
amount of tasks but my main one is to fetch random posts from reddit and send
them here daily. First things first though, I will need a channel to inhabit
and send my messages in, could you use the "!assign {text channel}" command and
I will use that channel from now on. If not, I could just go ahead and keep
using this one. One more thing, if you want to know more about what I can do,
just use the "!help" command. Thank you for letting me be a part of your server
<3""".replace("\n", " ")
###############################################################################
#                               GLOBALS
###############################################################################
bot = commands.Bot(command_prefix='!')
WHEN = time(1, 24, 30)  # 6:00 PM
###############################################################################


@bot.event
async def on_ready():
    #Notify user that bot is ready
    print("{0.user} has connected to Discord!".format(bot))
    #Notify what Guilds it's connected to
    print("{0.user} is connected to ".format(bot)
          + str(len(bot.guilds))
          + " guilds within Discord: "
          + str([o.name for o in bot.guilds]))
    bot.loop.create_task(background_task())
    for guild in bot.guilds:
        if str(guild.id) in servers:
            pass
        else:
            servers[guild.id] = guild.text_channels[0].id
            await guild.text_channels[0].\
                send(content=introduction)


async def post():  # Fired every day
    await bot.wait_until_ready()
    # DUPLICATE THE METHOD, ONE FOR REQUESTED POST, THE OTHER FOR DAILY POST
    print("The one-a-day has been triggered")
    for guild in servers:
        bot.get_guild(int(guild)).get_channel(servers[guild]).send("Booya!")
        # REDDIT POST WILL GO HERE


@bot.command()
async def assign(ctx, home):
    await bot.wait_until_ready()
    names = [o.name for o in ctx.guild.text_channels]
    home = home.replace("#", "")
    if home in names:
        channel = ctx.guild.text_channels[names.index(home)]
        servers[str(ctx.guild.id)] = channel.id
        await ctx.guild.get_channel(channel.id).\
            send("Thank you for the new home!")
    else:
        await ctx.\
            send("I don't think that channel exists, is it spelled correctly?")


@assign.error
async def assign_error(ctx, error):
    await ctx.send("There were not enough arguments to assign me to a channel :(")


@bot.command(aliases=["sd", "exit"])
async def shutdown(ctx):
    if(str(ctx.author) == admin_user):
        print("Shutdown signal given...")
        await bot.close()  # STOP BOT


@bot.event
async def on_disconnect():
    print("The bot has been disconnected, saving necessary data...")
    with open("servers.json", "w") as f:
        json.dump(servers, f)


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
bot.run(TOKEN)  # START BOT
