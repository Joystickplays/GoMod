print('Loading cogs...')
import discord
from discord.ext import commands
import os

import asyncio
import asyncpg
import aiohttp

# from io import StringIO
import time
import openai
import random
import traceback
import sys
# import json
import warnings
import datetime
from discord.commands import Option, permissions

from dotenv import load_dotenv

from cogs.views import Caseactionsview, Helpview

load_dotenv()

warnings.filterwarnings("ignore", category=DeprecationWarning) 


async def delallchannels(context):
    allchannels = context.guild.text_channels
    
    for chan in allchannels:
        if not chan == context.channel:
            await chan.delete(reason="Applying backup")

    allvoice = context.guild.voice_channels
    
    for voice in allvoice:
        await voice.delete(reason="Applying backup")

    allcat = context.guild.categories
        
    for cat in allcat:
        await cat.delete(reason="Applying backup")
        

async def warning(warning, message, channel):
    while True:
        casenumber = random.randint(111111, 999999)
        result = await bot.db.fetch("SELECT * FROM cases WHERE caseid = $1", casenumber)
        if result == [] or result == None:
            break

    await bot.db.execute("INSERT INTO cases (caseid, messageid, channelid) VALUES ($1, $2, $3)", casenumber, message.id, message.channel.id)
    
    if warning == "hate":
        embed = discord.Embed(title="Potential hate content (Case "+ str(casenumber) +")", description="The following [message](" + message.jump_url + ") may have hate contained in it, consider reviewing this:\n\n```\n" + message.content + "\n```", color=discord.Color.red())
    elif warning == "harassment":
        embed = discord.Embed(title="Potential harassment content (Case "+ str(casenumber) +")", description="The following [message](" + message.jump_url + ") may have harassment contained in it, consider reviewing this:\n\n```\n" + message.content + "\n```", color=discord.Color.red())
    elif warning == "adult":
        embed = discord.Embed(title="Potential adult content (Case "+ str(casenumber) +")", description="The following [message](" + message.jump_url + ") may have adult content contained in it, consider reviewing this:\n\n```\n" + message.content + "\n```", color=discord.Color.red())


    embed.set_footer(text="To take action, run: --case (case number)")
    await channel.send(embed=embed)

def evalu(msg, tokens):
    return openai.Completion.create(
            engine="text-davinci-001",
            temperature=0.5,
            top_p=0.5,
            prompt=msg,
            max_tokens=tokens
        )


openai.api_key = os.environ.get("OPENAI_API_KEY")

activity = discord.Activity(name='over Ukraine.', type=discord.ActivityType.watching)
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
class GoModBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

bot = GoModBot(command_prefix=commands.when_mentioned_or("--" if os.environ.get("BOT_ENV") == "production" else "=="), activity=activity, intents=intents)
bot.remove_command("help")
bot.logcache = list()
bot.logign = list()
bot.starttime = datetime.datetime.utcnow()
bot.topggheaders = {
    "Authorization": os.environ.get("TOPGG_TOKEN")
}
db_credentials = {
    'host': os.environ.get("DB_HOST"),
    'user': os.environ.get("DB_USER"),
    'password': os.environ.get("DB_PASSWORD"),
    'database': os.environ.get("DB_NAME")
}
bot.db = asyncio.get_event_loop().run_until_complete(asyncpg.create_pool(**db_credentials))
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        if filename == "views.py":
            continue
        bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print("Ready")

    # if not self.ticket_views_added:
    #     self.add_view(CreateTicket())
    #     self.ticket_views_added = True

    logs = await bot.db.fetch("SELECT * FROM logch")
    for log in logs:
        tempdict = {}
        tempdict["guildid"] = log["guildid"]
        tempdict["channelid"] = log["channelid"]
        tempdict["loggingtype"] = log["loggingtype"]
        bot.logcache.append(tempdict)
    print("Log channels cache locked and loaded B)")
    ignored = await bot.db.fetch("SELECT * FROM ignoredlogs")
    for ign in ignored:
        tempdict = {}
        tempdict["server"] = ign["server"]
        tempdict["channel"] = ign["channel"]
        bot.logign.append(tempdict)
    print("Ignored logs cache fire!!!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"You do not have permission to run this command.")
    elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.ChannelNotFound) or isinstance(error, commands.MemberNotFound):
        await ctx.send(f"{error}")
    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.event
async def on_guild_channel_delete(channel):
    disalloweds = await bot.db.fetch("SELECT * FROM ignoredchannels")
    for disallowedentry in disalloweds:
        if disallowedentry["channelid"] == channel.id:
            await bot.db.execute("DELETE FROM ignoredchannels WHERE channelid = $1", channel.id)

    servers = await bot.db.fetch("SELECT * FROM discservers")
    for server in servers:
        if server["warningch"] == channel.id:
            await bot.db.execute("DELETE FROM discservers WHERE warningch = $1", channel.id)
            await bot.db.execute("DELETE FROM ignoredchannels WHERE serverid = $1", channel.guild.id)
            embed = discord.Embed(title="Logging channel deleted", description=f"Logs channel for your server `{channel.guild.name}` has been unexpectedly deleted. You will need to restart setup to fix this.", color=discord.Color.red())
            await channel.guild.owner.send(embed=embed)

    await bot.db.execute("DELETE FROM logch WHERE channelid = $1", channel.id)

@bot.event
async def on_guild_remove(guild):
    servers = await bot.db.fetch("SELECT * FROM discservers")
    for server in servers:
        if server["discordid"] == guild.id:
            await bot.db.execute("DELETE FROM discservers WHERE discordid = $1", guild.id)
            await bot.db.execute("DELETE FROM ignoredchannels WHERE serverid = $1", guild.id)
            await bot.db.execute("DELETE FROM logch WHERE guildid = $1", guild.id)

@bot.event
async def on_guild_join(guild):
    user = bot.get_user(534596269574979595) # me
    await user.send(f"I have been added to a new server: {guild.name}")
    

# @bot.listen('on_message')
# async def on_message(message):
#     timestart = time.time()
#     if message.author.bot or message.guild == None:
#         return

#     servercheck = await bot.db.fetch("SELECT * FROM discservers WHERE discordid = $1", message.guild.id)

#     if not servercheck == [] or servercheck == None:
#         warningchannel = bot.get_channel(servercheck[0]['warningch'])


#         if len(message.content) > 150:
#             return

#         if len(message.content) < 2:
#             return

#         if message.content.startswith("--"):
#             return

#         if "adult content" in message.content.lower():
#             return

#         disalloweds = await bot.db.fetch("SELECT * FROM ignoredchannels")
#         for disallowedentry in disalloweds:
#             if disallowedentry["channelid"] == message.channel.id:
#                 return

#         ignoredusers = await bot.db.fetch("SELECT * FROM ignoredusers WHERE serverid = $1", message.guild.id)
#         for ignoreduser in ignoredusers:
#             if ignoreduser["userid"] == message.author.id:
#                 return

#         completion = evalu("Things to know:\n- THIS IS VERY IMPORTANT! CONSIDER \"YES\" AS SAFE.\n- If the message mentions they hate a person, consider it as hate.\n- If the message mentions they hate an object, consider it safe.\n- If the message mentions they hate PEOPLE who HATES an object, consider it as hate.\n- If the message has sexual assault towards a person, consider it as harassment.\n- If the message has explicit words, consider it as adult content.\n- If the message is someone screaming (like \"AAAAAAAAAAAAA\"), consider it safe.\n-- (IMPORTANT) If the message has only 1 letter but may complete to an explicit word (like \"d\"), consider it SAFE.\n-- If the message has explicit words, but not too explicit (like \"frick\", \"dang\", etc.), consider it safe.\n- If the message has unrecognized words (like \"bruh\", \"noway\", \"amogus\", \"i forgot\", etc.), consider it safe.\n-- If the message has unrecognized words BUT RESEMBLES A SWEAR (like \"pvvsy\", \"f3ck\", \"sh1t\"), consider it as adult content.\n- If the message has shortened explicit words (like \"fk\", \"btch\", etc.), consider it as adult content.\n- If the message has misspelled mild explicit words (Like \"fricl\", etc.), consider it safe.\n-If the message has random numbers (like \"234739\", \"333822\", etc.), consider it safe.\n-If the message has an unrecognized set of patterns (like \"--case 838374\", \"?ban\", etc.), consider it safe.\n- If the message has someone having problems with their mental health (like \"Im getting insane\", etc.), consider it safe.\n- If the message has emoticons (like \":P\", \":O\", \":)\", \"xD\", \"Xd\", \":-)\", etc.), consider it safe.\n- If the message only has 1 letter, consider it safe.\n- If the message is random characters (like \"dsfhiufhudsafjddi\", \"dksfjsdksksksfksfjdks\", \"epoiwfjoheroe\", etc.), consider it SAFE.\n- If the message is random characters (like \"dsfhiufhudsafjddi\", \"dksfjsdksksksfksfjdks\", \"epoiwfjoheroe\", etc.), consider it SAFE.\n- If the message is literally the word \"hate\",  consider it SAFE.\n- If the message is literally the word \"adult content\",  consider it SAFE.\n- If the message is literally the word \"harassment\",  consider it SAFE.\n\nClassify the following message if it has hate, or adult content, or harassment using the points provided:\n\n\"" + message.content +"\"\n\nResult:", 16)

#         result = completion.choices[0].text.lower()

#         if "none" in result or "not" in result or "no" in result or "safe" in result:
#             return
            
#         if "hate" in result:
#             await warning("hate", message, warningchannel)

#         if "adult" in result:
#             await warning("adult", message, warningchannel)

#         if "harassment" in result:
#             await warning("harassment", message, warningchannel)


@bot.command()
async def ping(ctx):
    delta_uptime = datetime.datetime.utcnow() - bot.starttime
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    embed = discord.Embed(title="Bot info and ping", color=discord.Color.blue())
    embed.add_field(name="Bot latency", value=f"{round(bot.latency * 1000)}ms", inline=False)
    embed.add_field(name="Database latency", value="<1ms", inline=True)
    embed.add_field(name="Bot uptime", value=f"{days}d {hours}h {minutes}m {seconds}s ", inline=False)
    embed.add_field(name="System uptime", value=f"{os.popen('uptime -p').read()[:-1]}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def reloadcog(ctx, cog):
    try:
        bot.unload_extension(f"cogs.{cog}")
        bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"Reloaded {cog}!")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.is_owner()
async def loadcog(ctx, cog):
    try:
        bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"Loaded {cog}!")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.is_owner()
async def unloadcog(ctx, cog):
    try:
        bot.unload_extension(f"cogs.{cog}")
        await ctx.send(f"Unloaded {cog}!")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
@commands.is_owner()
async def recogs(ctx):
    for filename in os.listdir("./cogs"):
        if filename.endswith('.py'):
            if filename == "views.py":
                continue
            bot.unload_extension(f"cogs.{filename[:-3]}")
            bot.load_extension(f"cogs.{filename[:-3]}")

    await ctx.send("Reloaded all cogs!")

@bot.command()
@commands.is_owner()
async def rsl(ctx):
    await bot.sync_commands()
    await ctx.send("Reloaded slash commands!")

@bot.command()
async def help(ctx):
    """
    Shows a list of usable commands.
    """
    chosen = "m"
    helpmsg = await ctx.send("Loading...")
    rawmodules = await bot.db.fetch("SELECT * FROM modules WHERE server = $1", ctx.guild.id)
    installedmods = []
    for module in rawmodules:
        installedmods.append(module["module"])

    while True:
        viewthing = Helpview(ctx)
        if chosen == "a":
            viewthing.ai.disabled = True
            viewthing.ai.style = discord.ButtonStyle.red
            # embed = discord.Embed(title="AiMod help", description="You discovered a BETA feature!\nUs at the GoMod team has made a feature for GoMod, AiMod, your AI moderator. This helps moderators review potentially message that contain either hate, adult content or harassment using artificial intelligence. **Be aware that this is BETA and false reports may happen.**\n\nTip:\n<required>\n[optional]", color=0x00b2ff)
            embed = discord.Embed(title="AiMod help", description="You may (or may not) remember there were a few more commands here, but the reason for that is we disabled them temporarily. When we will enable them back? No one knows.\n\nTip:\n<required>\n[optional]", color=0x00b2ff)
            # embed.add_field(name="--setup", value="Sets up AiMod to your liking. This command will be necessary when you first invite it to a new server.", inline=False)
            embed.add_field(name="--rulemaker", value="Makes a set of rules for you, according to your community.")
            # embed.add_field(name="--case <case ID>", value="Shows available actions you can do on a case. Case ID can be obtained from your log channel.", inline=False)
            # embed.add_field(name="--ignorechannel <channel>", value="AiMod will ignore this channel.", inline=False)
            # embed.add_field(name="--unignorechannel <channel>", value="If ignored previously, AiMod will not ignore this channel.", inline=False)
            # embed.add_field(name="--ignoreuser <member>", value="AiMod will ignore this user.", inline=False)
            # embed.add_field(name="--unignoreuser <member>", value="If ignored previously, AiMod will not ignore this user.", inline=False)
            # embed.add_field(name="--settings", value="Shows the current settings of AiMod for this server.", inline=False)

        if chosen == "m":
            viewthing.mod.disabled = True
            viewthing.mod.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Moderator help", description="**We are now migrating to Slash commands, so use / instead of --\n\nTip:\n<required>\n[optional]\nPrefix: /", color=0x00b2ff)
            embed.add_field(name="/kick <member> [reason]", value="Kicks a member and if specified, with a reason.", inline=False)
            embed.add_field(name="/ban <member> [reason]", value="Bans a member and if specified, with a reason.", inline=False)
            embed.add_field(name="/warn <member> [reason]", value="Warns a member.", inline=False)
            embed.add_field(name="/warns <member>", value="Lists all the warnings the member has.", inline=False)
            embed.add_field(name="/clearwarns <member>", value="Clears all warnings the member has.", inline=False)
            embed.add_field(name="/purge <amount>", value="Deletes the specificed number of messages.", inline=False)
            embed.add_field(name="???", value="Coming soon.", inline=False)
            # embed.add_field(name="/mute <member> [reason]", value="Mutes a member and if specified, with a reason.", inline=False)
            embed.add_field(name="???", value="Coming soon.", inline=False)
            # embed.add_field(name="/unmute <member> [reason]", value="Unmutes a member and if specified, with a reason.", inline=False)
            embed.add_field(name="/block <member>", value="Blocks a member from the channel this command is run in.", inline=False)
            embed.add_field(name="/unblock <member>", value="Unblocks a member from the channel this command is run in.", inline=False)
            embed.add_field(name="/reactrole", value="Run a reaction role setup.", inline=False)
            # embed.add_field(name="/ticketsetup", value="Run a ticket management setup.", inline=False)
            embed.add_field(name="/modules", value="Shows a list of installable modules.", inline=False)
            embed.add_field(name="--instmod <module code>", value="Installs a module.", inline=False)
            embed.add_field(name="--uninstmod <module code>", value="Uninstalls a module.", inline=False)

        if chosen == "o":
            viewthing.other.disabled = True
            viewthing.other.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Other help", description="Tip:\n<required>\n[optional]\nPrefix: --", color=0x00b2ff)
            embed.add_field(name="--vote", value="Show us some love by voting us on top.gg!", inline=False)
            if "tg" in installedmods:
                embed.add_field(name="--tag/t <tag name>", value="Quickly send a message using the specified tag.", inline=False)
                embed.add_field(name="--tag/t create <tag name> <message>", value="Creates a tag with the name and message included.", inline=False)

        if chosen == "s":
            viewthing.server.disabled = True
            viewthing.server.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Server backups help", description="Tip:\n<required>\n[optional]\nPrefix: --", color=0x00b2ff)
            embed.add_field(name="--createbackup", value="Creates a server backup file for you. The backup for now only includes channels and roles. (THIS WILL OVERWRITE EXISTING BACKUPS!)", inline=False)
            embed.add_field(name="--applybackup <file>", value="Applies a backup to your server. The backup must be a valid backup file.", inline=False)


        if chosen == "l":
            viewthing.log.disabled = True
            viewthing.log.style = discord.ButtonStyle.green
            if "lg" in installedmods:
                embed = discord.Embed(title="Log help", description="Tip:\n<required>\n[optional]\nPrefix: --", color=0x00b2ff)
                embed.add_field(name="--createlogging", value="Makes a channel a place to log all edits, deletions of messages and more.", inline=False)
                embed.add_field(name="--ignorelogging <channel>", value="Logging will ignore this channel.", inline=False)
            else:
                embed = discord.Embed(title="Log help", description="Logging is not available for this server yet. A moderator will need to install the `logging` module.", color=0x00b2ff)

        if chosen == "mr":
            viewthing.modrep.disabled = True
            viewthing.modrep.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Moderation Reputation help", description="Us at GoTeam developed a new way of identifiying potentially unwanted members: ModRep (or Moderation Reputation). ModRep allows any member to vote on other members, which if they find a good member, they'll upvote the member. Otherwise, they'll downvote the member.\n\nTip:\n<required>\n[optional]\nPrefix: --", color=0x00b2ff)
            embed.add_field(name="--modrep <member>", value="Shows the current ModRep of the member. This will allow you to also upvote or downvote the member this way.", inline=False)

        if chosen == "cc":
            viewthing.cc.disabled = True
            viewthing.cc.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Custom currency help (CC for short)", description="Custom currency are a great way to keep users engaged at your server and reward them with their earnings.\n\nTip:\n<required>\n[optional]\nPrefix: --", color=0x00b2ff)
            embed.add_field(name="/cccreate <currency name>" , value="Creates a custom currency with the specified name.", inline=False)
            embed.add_field(name="/ccremove", value="Removes the currency system.", inline=False)
            embed.add_field(name="/baladd", value="Adds the specified amount of currency to the user.", inline=False)
            embed.add_field(name="/balremove", value="Removes the specified amount of currency from the user.", inline=False)
            embed.add_field(name="/give", value="Gives the specified amount of currency to the user.", inline=False)
            embed.add_field(name="/flipbet <amount> <cointype>", value="Flip a coin and get or lose from the outcome.", inline=False)
            embed.add_field(name="/shop", value="Shows the shop.", inline=False)
            embed.add_field(name="/buy <item>", value="Buys the specified item.", inline=False)
            embed.add_field(name="/createitem <...> [...]", value="Creates an item with the specified name, description and cost.", inline=False)
            embed.add_field(name="/removeitem <item>", value="Removes the specified item from the shop.", inline=False)

        helpmsg = await helpmsg.edit(content=None, embed=embed, view=viewthing)
        await viewthing.wait()
        chosen = viewthing.value
        if chosen == "x" or chosen == None:
            for buttons in viewthing.children:
                buttons.style = discord.ButtonStyle.gray
                buttons.disabled = True

            helpmsg = await helpmsg.edit(embed=embed, view=viewthing)
            break

@bot.command()
@commands.is_owner()
async def sql(ctx, *, query):
    async with ctx.channel.typing():
        try:
            if "SELECT" in query:
                results = await bot.db.fetch(query)
                await ctx.send(f"```{results}```")
            else:
                await bot.db.execute(query)
                await ctx.send("Query executed.")
        except Exception as e:
            await ctx.send(e)

@bot.slash_command()
async def modules(ctx):
    """
    Shows a list of installable modules.
    """
    embed = discord.Embed(title="Installable modules", description="Modules are a way to extend your use for GoMod. These are modules that can be installed to GoMod for your server. The 2 characters in square brackets is the module code. To install a module, run `--instmod <module code>`.", color=0x00b2ff)
    embed.add_field(name="[tg] Tags", value="Tags are a fast way to retrieve text for later use.", inline=False)
    # embed.add_field(name="[tm] Ticket management", value="Ticket management is a way to create and manage tickets for your server.", inline=False)
    # embed.add_field(name="[sb] Server backups", value="A way to backup and restore your server.", inline=False)
    embed.add_field(name="[lg] Logging", value="Logging will log any message edits or deletion, member joins and leaves, and kicks and bans.", inline=False)
    embed.add_field(name="[qa] Question and answer", value="**UNSTABLE MODULE** Allows your members to answer questions you provide. If a member get **x** questions right, they will get something.", inline=False)
    # embed.add_field(name="[cc] Custom currency", value="Allows you to create a custom currency system for your server.", inline=False)
    await ctx.respond(embed=embed)

# Modules codes:
# tg -> Tags
# tm -> Ticket management
# sb -> Server backups
# lg -> Logging

@bot.command()
@commands.has_guild_permissions(manage_guild=True, manage_channels=True)
async def instmod(ctx, module):
    """
    Installs a module.
    """
    rawallowed = await bot.db.fetch("SELECT * FROM testerguilds")
    allowed = []
    for i in rawallowed:
        allowed.append(i["id"])
    if not module.lower() in ("tg", "lg", "qa", "cc"):
        await ctx.send("Invalid module code. To see a list of codes, run `--modules`.")
        return
    elif module.lower() in ("qa"):
        if not ctx.guild.id in allowed:
            embed = discord.Embed(title="Exclusive module", description="This is a module restricted to a few guilds. This is due to the module still being unstable. Once we get it fixed, we'll release this module to every guild ASAP!", color=0x00b2ff)
            await ctx.send(embed=embed)
            return

    lookup = await bot.db.fetchrow("SELECT * FROM modules WHERE server = $1 AND module = $2", ctx.guild.id, module)
    if lookup:
        await ctx.send("This module is already installed.")
        return
        
    embed = discord.Embed(title="Installing module", description="This may take a while...", color=0x00b2ff)
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(random.randint(1, 3))
    await bot.db.execute("INSERT INTO modules (server, module) VALUES ($1, $2)", ctx.guild.id, module)
    embed = discord.Embed(title="Module installed", description="Module installed successfully. If you ever changed your mind, run `--uninstmod <module code>`.", color=0x00b2ff)
    await msg.edit(embed=embed)

@bot.command()
@commands.has_guild_permissions(manage_guild=True, manage_channels=True)
async def uninstmod(ctx, module):
    if module.lower() in ("tg", "lg", "qa"):
        lookup = await bot.db.fetchrow("SELECT * FROM modules WHERE server = $1 AND module = $2", ctx.guild.id, module)
        if not lookup:
            await ctx.send("This module is not installed.")
            return

        embed = discord.Embed(title="Uninstalling module", description="This may take a while...", color=0x00b2ff)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(random.randint(1, 3))
        if module.lower() == "tg":
            await bot.db.execute("DELETE FROM tags WHERE serverid = $1", ctx.guild.id)
        
        if module.lower() == "lg":
            await bot.db.execute("DELETE FROM logch WHERE guildid = $1", ctx.guild.id)
        await bot.db.execute("DELETE FROM modules WHERE server = $1 AND module = $2", ctx.guild.id, module)
        embed = discord.Embed(title="Module uninstalled", description="Module uninstalled successfully.", color=0x00b2ff)
        await msg.edit(embed=embed)
    else:
        await ctx.send("Invalid module code. To see a list of codes, run `--modules`.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def vote(ctx):
    embed = discord.Embed(title="Vote", description="Vote for the bot here: https://top.gg/bot/940038014153949254/vote", color=0x00b2ff)
    msg = await ctx.send(embed=embed)

    
    params = {
        "userId": ctx.author.id
    }

    async with aiohttp.ClientSession() as session:
        async with session.get("https://top.gg/api/bots/940038014153949254/check", headers=bot.topggheaders, params=params) as r:
            data = await r.json()
            if data['voted'] == 1:
                await msg.edit(embed=discord.Embed(title="Vote", description="Yay! It looks like you already voted for this bot. Thank you!", color=0x00b2ff))



# @bot.command()
# @commands.has_permissions(manage_guild=True)
# async def createbackup(ctx):
#     embed = discord.Embed(title="Backup", description="This command will create a .gomodback server file for you. Continue?", color=0x00b2ff)
#     msg = await ctx.send(embed=embed)

#     await msg.add_reaction("✅")
#     await msg.add_reaction("❌")
#     def check(reaction, user):
#         return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["✅", "❌"]

#     try:
#         reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)
#     except asyncio.TimeoutError:
#         await msg.edit(embed=discord.Embed("Timed out.", color=0x00b2ff))
#         return

#     if str(reaction.emoji) == "❌":
#         await msg.edit(embed=discord.Embed("Cancelled.", color=0x00b2ff))
#         return
    
#     embed = discord.Embed(title="Creating backup...", description="Please do not add, remove, or edit any channels! This may take some time. In the meantime, continue to interact with your community!", color=0x00b2ff)
#     await ctx.send(embed=embed)

#     await asyncio.sleep(20)

#     guild = ctx.guild
#     channels = guild.channels
#     roles = guild.roles

#     data = {
#         "channels": [],
#         "roles": []
#     }

#     for channel in channels:
#         if channel.type != discord.ChannelType.category:
#             data["channels"].append({"name": channel.name, "position": channel.position, "type": channel.type.name, "topic": channel.topic})
#         else:
#             data["channels"].append({"name": channel.name, "position": channel.position, "type": channel.type.name})

#     for role in roles:
#         data["roles"].append({"name": role.name, "position": role.position, "permissions": role.permissions.value, "color": role.color.value})


#     s = StringIO()
#     json.dump(data, s)
#     s.seek(0)
#     await ctx.send("Done! The file should be sent to your DMs.")
#     embed = discord.Embed(title="Backup", description="Complete!", color=0x00b2ff)
#     await ctx.author.send(embed=embed, file=discord.File(s, filename=f"{ctx.guild.id}.gmback"))
    
# @bot.command()
# @commands.has_permissions(manage_guild=True)
# async def applybackup(ctx):
#     ctx.message.attachments.save(f"/tmp/{ctx.guild.id}.gmback")
#     channels = {
#         "text": ctx.guild.create_text_channel,
#         "voice": ctx.guild.create_voice_channel
#     }
#     await ctx.message.delete()
#     embed = discord.Embed(title="Backup", description="This command will apply a .gmback server file for you. This account will delete every single channel. Continue?", color=0x00b2ff)
#     msg = await ctx.send(embed=embed)

#     await msg.add_reaction("✅")
#     await msg.add_reaction("❌")
#     def check(reaction, user):
#         return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["✅", "❌"]

#     try:
#         reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)
#     except asyncio.TimeoutError:
#         await msg.edit(embed=discord.Embed("Timed out.", color=0x00b2ff))
#         return

#     if str(reaction.emoji) == "❌":
#         await msg.edit(embed=discord.Embed("Cancelled.", color=0x00b2ff))
#         return
    

#     with open(f"/tmp/{ctx.guild.id}.gmback", "r") as f:
#         data = json.load(f)

#     embed = discord.Embed(title="Applying backup...", description="Applying...", color=0x00b2ff)
#     await ctx.send(embed=embed)


#     # blocked lol

if __name__ == "__main__":
    if os.environ.get("BOT_ENV") == "development":
        bot.run(os.environ.get("BETA_BOT_TOKEN"))
    else:
        bot.run(os.environ.get("BOT_TOKEN"))
