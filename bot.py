# bot.py

import discord
from discord.ext import commands
import configparser
from datetime import datetime, time, timedelta
import asyncio
import json
import re
import asyncpraw
import asyncprawcore
from pprint import pprint
import random


###############################################################################
#                       CONFIGURATION FETCH
###############################################################################
def get_config(login):
    config = configparser.ConfigParser()
    with open(login, 'r') as f:
        config.read_file(f)
    return config


config = get_config("login.ini")

###DISCORD###
TOKEN = config["DISCORD"]["bot_token"]
admin_user = config["DISCORD"]["admin_user"]

###REDDIT###
reddit = asyncpraw.Reddit(
    client_id=config["REDDIT"]["client_id"],
    client_secret=config["REDDIT"]["client_secret"],
    user_agent=config["REDDIT"]["user_agent"]
)
###LOCAL FILES###
with open("servers.json", "r") as f:
    servers = json.load(f)
with open("reddit.json", "r") as f:
    feed = json.load(f)
#feed = {"954653107734851645": ["shitposting", "mildlyinfuriating"]}
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
home_thank = "Thank you for the new home!"
channel_dne = "I don't think that channel exists, is it spelled correctly?"
subreddit_dne = "I don't think that subreddit exists, is it spelled correctly?"
subreddit_add = "The subreddit \"{}\" has been added to the feed!"
subreddit_exist = "The subreddit \"{}\" has already been added!"
assign_error_s = "There were not enough arguments to assign me to a channel :("
add_error_s = "There were not enough arguments to add anything to the feed :/"
subreddit_rm = "The subreddit \"{}\" has been removed from the feed"
subreddit_rm_error = "\"{}\" is not a subreddit in the current feed"
###############################################################################
#                               GLOBALS
###############################################################################
bot = commands.Bot(command_prefix='!')
WHEN = time(0, 19, 30)  # 6:00 PM
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
    #Start the clock for the daily post
    bot.loop.create_task(background_task())
    #Check if any new guilds have been added and send the intro if new
    for guild in bot.guilds:
        if str(guild.id) in feed:
            pass
        else:
            feed[guild.id] = []
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
        await bot.get_guild(int(guild)).get_channel(servers[guild]).\
            send("Booya!")
        # REDDIT POST WILL GO HERE


@bot.command()
async def add(ctx, new):  # Will add a specidic subreddit or user to the selected pool
    await bot.wait_until_ready()
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    try:
        subject = await reddit.subreddit(new, fetch=True)
        if subject.display_name in feed[str(ctx.guild.id)]:
            await ctx.send(subreddit_exist.format(new))
        else:
            feed[str(ctx.guild.id)].append(subject.display_name)
            print("{0.user} has added ".format(bot)
                  + new + " to the feed in " + str(ctx.guild))
            await ctx.send(subreddit_add.format(new))
    except asyncprawcore.exceptions.Redirect as e:
        await ctx.send(subreddit_dne)


@add.error
async def add_error(ctx, error):
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    await ctx.send(add_error_s)


@bot.command(aliases= ["rm"])
async def remove(ctx, rid):
    await bot.wait_until_ready()
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    list = feed[str(ctx.guild.id)]
    if rid in list:
        del list[list.index(rid)]
        await ctx.send(subreddit_rm.format(rid))
    else:
        await ctx.send(subreddit_rm_error.format(rid))


@bot.command(name="random")
async def randomPost(ctx):
    await bot.wait_until_ready()
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    list = feed[str(ctx.guild.id)]
    for i in range(0, 4):
        sub = await reddit.subreddit(random.choice(list))
        media = extract(await sub.random())


@bot.command()
async def assign(ctx, home):
    await bot.wait_until_ready()
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    names = [o.name for o in ctx.guild.text_channels]
    if home in names:
        channel = ctx.guild.text_channels[names.index(home)]
        servers[str(ctx.guild.id)] = channel.id
        print("{0.user} has been assigned to ".format(bot) + home)

        await ctx.guild.get_channel(channel.id).send(home_thank)
        return
    try:
        home = re.sub("#|<|>", "", home)
        home = int(home)
        ids = [o.id for o in ctx.guild.text_channels]
        if home in ids:
            channel = ctx.guild.get_channel(home)
            servers[str(ctx.guild.id)] = home
            print("{0.user} has been assigned to ".format(bot) + channel.name)
            await channel.send(home_thank)
            return
    except ValueError:
        pass
    await ctx.send(channel_dne)


@assign.error
async def assign_error(ctx, error):
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    await ctx.send(assign_error_s)


@bot.command(aliases=["sd", "exit"])
async def shutdown(ctx):
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    if(str(ctx.author) == admin_user):
        print("Shutdown signal given...")
        await bot.close()  # STOP BOT

@bot.command(name="save")
async def CalledSave(ctx):
    await bot.wait_until_ready()
    if ctx.channel.id != servers[str(ctx.guild.id)]:
        return
    if(str(ctx.author) == admin_user):
        await ctx.send("Saving data...")
        save()
        print("Saved data")

@bot.event
async def on_disconnect():
    print("The bot has been disconnected, saving necessary data...")
    save()


@bot.event
async def on_error(event):
    on_disconnect()
    sys.exc_info()


def extract(post):
    try:
        match post.post_hint:
            case 'image':
                print("This is an image: https://www.reddit.com" + post.permalink)
            case 'hosted:video':
                print(
                    "This is a video on reddit: https://www.reddit.com" + post.permalink)
            case 'rich:video':
                print("This is a rich video: https://www.reddit.com" + post.permalink)
            case _:
                print(
                    "I'm not sure what this is: https://www.reddit.com" + post.permalink + " " + post.post_hint)
    except:
        if "https://www.reddit.com" + post.permalink == post.url:
            print("This post is text: https://www.reddit.com" + post.permalink)
        elif (re.search("/www\.reddit\.com/gallery", post.url) != None):
            print("This is a series of images on reddit: https://www.reddit.com" + post.permalink)
        else:
            print(
                "This post does not have a hint: https://www.reddit.com" + post.permalink)
            print(post.url)

def save():
    with open("servers.json", "w") as f:
        json.dump(servers, f)
    with open("reddit.json", "w") as f:
        json.dump(feed, f)


async def background_task():
    now = datetime.now()
    if now.time() > WHEN:
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1), time(0))
        # Seconds until tomorrow (midnight)
        seconds = (tomorrow - now).total_seconds()
        # Sleep until tomorrow and then the loop will start
        await asyncio.sleep(seconds)
    while True:
        now = datetime.now()
        target_time = datetime.combine(
            now.date(), WHEN)  # Sets the time on today
        seconds_until_target = (target_time - now).total_seconds()
        # Sleep until we hit the target time
        await asyncio.sleep(seconds_until_target)
        await post()  # Call the helper function that sends the message
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1), time(0))
        # Seconds until tomorrow (midnight)
        seconds = (tomorrow - now).total_seconds()
        # Sleep until tomorrow and then the loop will start a new iteration
        await asyncio.sleep(seconds)
###############################################################################
bot.run(TOKEN)  # START BOT
