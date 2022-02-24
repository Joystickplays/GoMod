print('Init..')
import discord

from discord.ext import commands, tasks
import os

import asyncio
import asyncpg
import aiohttp

from io import StringIO
import time
import openai
import random
import traceback
import sys
import json

from dotenv import load_dotenv

load_dotenv()


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
        
# Views
class Caseactionsview(discord.ui.View): 
    def __init__(self, ctx): 
        super().__init__()
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='Ban', style=discord.ButtonStyle.red)
    async def ban(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "b"
        self.stop()

    @discord.ui.button(label='Kick', style=discord.ButtonStyle.red)
    async def kick(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "k"
        self.stop()

    @discord.ui.button(label='Delete', style=discord.ButtonStyle.green)
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "d"
        self.stop()

    @discord.ui.button(label='Ignore', style=discord.ButtonStyle.gray)
    async def ignore(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "i"
        self.stop()

class Helpview(discord.ui.View): 
    def __init__(self, ctx): 
        super().__init__()
        self.value = None
        self.ctx = ctx
        self.timeout = 60

    @discord.ui.button(label='Moderator', style=discord.ButtonStyle.gray)
    async def mod(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "m"
        self.stop()

    @discord.ui.button(label='AiMod [BETA]', style=discord.ButtonStyle.gray)
    async def ai(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "a"
        self.stop()

    @discord.ui.button(label='Server backups', style=discord.ButtonStyle.gray, disabled=True)
    async def server(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "s"
        self.stop()

    @discord.ui.button(label='Logging', style=discord.ButtonStyle.gray)
    async def log(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "l"
        self.stop()

    @discord.ui.button(label='Others', style=discord.ButtonStyle.gray)
    async def other(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "o"
        self.stop()
        

    @discord.ui.button(label='Exit', style=discord.ButtonStyle.gray)
    async def ex(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "x"
        self.stop()

        

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


activity = discord.Activity(name='for rulebreakers', type=discord.ActivityType.watching)
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("--"), activity=activity, intents=intents)
bot.remove_command("help")
bot.logcache = list()
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

@bot.event
async def on_ready():
    print("Ready")
    logs = await bot.db.fetch("SELECT * FROM logch")
    for log in logs:
        tempdict = {}
        tempdict["guildid"] = log["guildid"]
        tempdict["channelid"] = log["channelid"]
        tempdict["loggingtype"] = log["loggingtype"]
        bot.logcache.append(tempdict)
    print("Log channels cache locked and loaded B)")


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

@bot.event
async def on_message_edit(messagebefore, messageafter):
    if messagebefore.author.bot:
        return
    if messagebefore.guild is None:
        return

    for record in bot.logcache:
        if record["guildid"] == messagebefore.guild.id and record["loggingtype"] == "e":
            channel = bot.get_channel(record["channelid"])
            if channel is None:
                return
            embed = discord.Embed(title="Message edited", description=f"The following message was edited in `{messagebefore.channel.name}` by `{messagebefore.author.name}`:\n\nFrom:\n```\n{messagebefore.content}\n```\nTo:\n```{messageafter.content}```", color=discord.Color.orange())
            await channel.send(embed=embed)
            return
    
    logs = await bot.db.fetch("SELECT * FROM logch")
    for log in logs:
        tempdict = {}
        tempdict["guildid"] = log["guildid"]
        tempdict["channelid"] = log["channelid"]
        tempdict["loggingtype"] = log["loggingtype"]
        bot.logcache.append(tempdict)
        if log["guildid"] == messagebefore.guild.id and log["loggingtype"] == "e":
            channel = bot.get_channel(record["channelid"])
            if channel is None:
                return
            embed = discord.Embed(title="Message edited", description=f"The following message was edited in `{messagebefore.channel.name}` by `{messagebefore.author.name}`:\n\nFrom:\n```\n{messagebefore.content}\n```\nTo:\n```{messageafter.content}```", color=discord.Color.orange())
            await channel.send(embed=embed)
            return


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    if message.guild is None:
        return

    for record in bot.logcache:
        if record["guildid"] == message.guild.id and record["loggingtype"] == "e":
            channel = bot.get_channel(record["channelid"])
            if channel is None:
                return
            embed = discord.Embed(title="Message deleted", description=f"The following message was deleted in `{message.channel.name}` by `{message.author.name}`:\n\n```\n{message.content}\n```", color=discord.Color.red())
            await channel.send(embed=embed)
            return
    
    logs = await bot.db.fetch("SELECT * FROM logch")
    for log in logs:
        tempdict = {}
        tempdict["guildid"] = log["guildid"]
        tempdict["channelid"] = log["channelid"]
        tempdict["loggingtype"] = log["loggingtype"]
        bot.logcache.append(tempdict)
        if log["guildid"] == message.guild.id and log["loggingtype"] == "e":
            channel = bot.get_channel(log["channelid"])
            if channel is None:
                return
            embed = discord.Embed(title="Message deleted", description=f"The following message was deleted in `{message.channel.name}` by `{message.author.name}`:\n\n```\n{message.content}\n```", color=discord.Color.red())
            await channel.send(embed=embed)
            return

@bot.event
async def on_guild_remove(guild):
    servers = await bot.db.fetch("SELECT * FROM discservers")
    for server in servers:
        if server["discordid"] == guild.id:
            await bot.db.execute("DELETE FROM discservers WHERE discordid = $1", guild.id)
            await bot.db.execute("DELETE FROM ignoredchannels WHERE serverid = $1", guild.id)

@bot.event
async def on_guild_join(guild):
    user = bot.get_user(534596269574979595)
    await user.send(f"I have been added to a new server: {guild.name}")
    

@bot.listen('on_message')
async def on_message(message):
    timestart = time.time()
    if message.author.bot or message.guild == None:
        return

    servercheck = await bot.db.fetch("SELECT * FROM discservers WHERE discordid = $1", message.guild.id)

    if not servercheck == [] or servercheck == None:
        warningchannel = bot.get_channel(servercheck[0]['warningch'])


        if len(message.content) > 150:
            return

        if len(message.content) < 2:
            return

        if message.content.startswith("--"):
            return

        if "adult content" in message.content.lower():
            return

        disalloweds = await bot.db.fetch("SELECT * FROM ignoredchannels")
        for disallowedentry in disalloweds:
            if disallowedentry["channelid"] == message.channel.id:
                return

        ignoredusers = await bot.db.fetch("SELECT * FROM ignoredusers WHERE serverid = $1", message.guild.id)
        for ignoreduser in ignoredusers:
            if ignoreduser["userid"] == message.author.id:
                return

        print("Evaluating")

        completion = evalu("Things to know:\n- THIS IS VERY IMPORTANT! CONSIDER \"YES\" AS SAFE.\n- If the message mentions they hate a person, consider it as hate.\n- If the message mentions they hate an object, consider it safe.\n- If the message mentions they hate PEOPLE who HATES an object, consider it as hate.\n- If the message has sexual assault towards a person, consider it as harassment.\n- If the message has explicit words, consider it as adult content.\n- If the message is someone screaming (like \"AAAAAAAAAAAAA\"), consider it safe.\n-- (IMPORTANT) If the message has only 1 letter but may complete to an explicit word (like \"d\"), consider it SAFE.\n-- If the message has explicit words, but not too explicit (like \"frick\", \"dang\", etc.), consider it safe.\n- If the message has unrecognized words (like \"bruh\", \"noway\", \"amogus\", \"i forgot\", etc.), consider it safe.\n-- If the message has unrecognized words BUT RESEMBLES A SWEAR (like \"pvvsy\", \"f3ck\", \"sh1t\"), consider it as adult content.\n- If the message has shortened explicit words (like \"fk\", \"btch\", etc.), consider it as adult content.\n- If the message has misspelled mild explicit words (Like \"fricl\", etc.), consider it safe.\n-If the message has random numbers (like \"234739\", \"333822\", etc.), consider it safe.\n-If the message has an unrecognized set of patterns (like \"--case 838374\", \"?ban\", etc.), consider it safe.\n- If the message has someone having problems with their mental health (like \"Im getting insane\", etc.), consider it safe.\n- If the message has emoticons (like \":P\", \":O\", \":)\", \"xD\", \"Xd\", \":-)\", etc.), consider it safe.\n- If the message only has 1 letter, consider it safe.\n- If the message is random characters (like \"dsfhiufhudsafjddi\", \"dksfjsdksksksfksfjdks\", \"epoiwfjoheroe\", etc.), consider it SAFE.\n- If the message is random characters (like \"dsfhiufhudsafjddi\", \"dksfjsdksksksfksfjdks\", \"epoiwfjoheroe\", etc.), consider it SAFE.\n- If the message is literally the word \"hate\",  consider it SAFE.\n- If the message is literally the word \"adult content\",  consider it SAFE.\n- If the message is literally the word \"harassment\",  consider it SAFE.\n\nClassify the following message if it has hate, or adult content, or harassment using the points provided:\n\n\"" + message.content +"\"\n\nResult:", 16)

        result = completion.choices[0].text.lower()
        print(result + "\nTime taken: " + str(time.time() - timestart))

        if "none" in result or "not" in result or "no" in result or "safe" in result:
            return
            
        if "hate" in result:
            await warning("hate", message, warningchannel)

        if "adult" in result:
            await warning("adult", message, warningchannel)

        if "harassment" in result:
            await warning("harassment", message, warningchannel)


@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms.")

@bot.command()
async def help(ctx):
    chosen = "m"
    helpmsg = await ctx.send("Loading...")
    while True:
        viewthing = Helpview(ctx)
        if chosen == "a":
            viewthing.ai.disabled = True
            viewthing.ai.style = discord.ButtonStyle.green
            embed = discord.Embed(title="AiMod help", description="You discovered a BETA feature!\nUs at the GoMod team has made a feature for GoMod, AiMod, your AI moderator. This helps moderators review potentially message that contain either hate, adult content or harassment using artificial intelligence. **Be aware that this is BETA and false reports may happen.**\n\nTip:\n<required>\n[optional]", color=0x00b2ff)
            embed.add_field(name="--setup", value="Sets up AiMod to your liking. This command will be necessary when you first invite it to a new server.", inline=False)
            embed.add_field(name="--rulemaker", value="Makes a set of rules for you, according to your community.")
            embed.add_field(name="--case <case ID>", value="Shows available actions you can do on a case. Case ID can be obtained from your log channel.", inline=False)
            embed.add_field(name="--ignorechannel <channel>", value="AiMod will ignore this channel.", inline=False)
            embed.add_field(name="--unignorechannel <channel>", value="If ignored previously, AiMod will not ignore this channel.", inline=False)
            embed.add_field(name="--ignoreuser <member>", value="AiMod will ignore this user.", inline=False)
            embed.add_field(name="--unignoreuser <member>", value="If ignored previously, AiMod will not ignore this user.", inline=False)
            embed.add_field(name="--settings", value="Shows the current settings of AiMod for this server.", inline=False)

        if chosen == "m":
            viewthing.mod.disabled = True
            viewthing.mod.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Moderator help", description="Tip:\n<required>\n[optional]", color=0x00b2ff)
            embed.add_field(name="--kick <member> [reason]", value="Kicks a member and if specified, with a reason.", inline=False)
            embed.add_field(name="--ban <member> [reason]", value="Bans a member and if specified, with a reason.", inline=False)
            embed.add_field(name="--warn <member> [reason]", value="Warns a member.", inline=False)
            embed.add_field(name="--warns <member>", value="Lists all the warnings the member has.", inline=False)
            embed.add_field(name="--clearwarns <member>", value="Clears all warnings the member has.", inline=False)
            embed.add_field(name="--purge <amount>", value="Deletes the specificed number of messages.", inline=False)
            embed.add_field(name="???", value="Coming soon.", inline=False)
            # embed.add_field(name="--mute <member> [reason]", value="Mutes a member and if specified, with a reason.", inline=False)
            embed.add_field(name="???", value="Coming soon.", inline=False)
            # embed.add_field(name="--unmute <member> [reason]", value="Unmutes a member and if specified, with a reason.", inline=False)
            embed.add_field(name="--block <member>", value="Blocks a member from the channel this command is run in.", inline=False)
            embed.add_field(name="--unblock <member>", value="Unblocks a member from the channel this command is run in.", inline=False)

        if chosen == "o":
            viewthing.other.disabled = True
            viewthing.other.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Other help", description="Tip:\n<required>\n[optional]", color=0x00b2ff)
            embed.add_field(name="--vote", value="Show us some love by voting us on top.gg!", inline=False)

        if chosen == "s":
            viewthing.server.disabled = True
            viewthing.server.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Server backups help", description="Tip:\n<required>\n[optional]", color=0x00b2ff)
            embed.add_field(name="--createbackup", value="Creates a server backup file for you. The backup for now only includes channels and roles. (THIS WILL OVERWRITE EXISTING BACKUPS!)", inline=False)
            embed.add_field(name="--applybackup <file>", value="Applies a backup to your server. The backup must be a valid backup file.", inline=False)


        if chosen == "l":
            viewthing.log.disabled = True
            viewthing.log.style = discord.ButtonStyle.green
            embed = discord.Embed(title="Log help", description="Tip:\n<required>\n[optional]", color=0x00b2ff)
            embed.add_field(name="--createlogging", value="Makes a channel a place to log all edits and deletions of messages.  ", inline=False)

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
async def sqlquery(ctx, *, query):
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


@bot.command()
@commands.has_guild_permissions(manage_messages=True)
async def setup(ctx):
    servercheck = await bot.db.fetch("SELECT * FROM discservers WHERE discordid = $1", ctx.guild.id)
    if servercheck == [] or servercheck == None:
        embed = discord.Embed(title="Setup", description="Do you want to start setup?", color=0x00b2ff)
        react = await ctx.send(embed=embed)
        await react.add_reaction("\U00002705")
        await react.add_reaction("\U0000274C")
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["\U00002705", "\U0000274C"]

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")
            return

        if str(reaction.emoji) == "\U0000274C":
            await ctx.send("Setup cancelled.")
            return


        embed = discord.Embed(title="Setup", description="Please enter the channel you want to use for the bot's warnings.", color=0x00b2ff)
        react = await ctx.send(embed=embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        while True:
            response = await bot.wait_for("message", check=check)
            try:
                channelwarns = await commands.TextChannelConverter().convert(ctx, response.content)
                break
            except:
                embed = discord.Embed(title="Setup", description="We can't find that channel, try again?", color=0x00b2ff)
                await ctx.send(embed=embed, delete_after=2)

        embed = discord.Embed(title="Finishing setup...", description="Give us a a second, you're almost there.", color=0x00b2ff)
        await ctx.send(embed=embed)
        
        try:
            await bot.db.execute("INSERT INTO discservers (discordid, warningch, invokerid) VALUES ($1, $2, $3)", ctx.guild.id, channelwarns.id, ctx.author.id)
            embed = discord.Embed(title="Setup success", description="Setup finished! GoMod will now listen for messages.\n\nTip: You should restrict GoMod to high traffic channels and ignoring NSFW channels and bot channels.", color=0x00b2ff)
            await ctx.send(embed=embed)
        except Exception:
            embed = discord.Embed(title="Setup failure", description="Something went wrong. Try again later.", color=discord.Color.red())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Setup failure", description="It looks like this server has already been set up.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command()
@commands.has_guild_permissions(manage_messages=True, kick_members=True, ban_members=True)
async def case(ctx, casenumber):
    try:
        casenumber = int(casenumber)
    except:
        await ctx.send("Invalid case number.")
        return

    await ctx.channel.trigger_typing()
    case = await bot.db.fetch("SELECT * FROM cases WHERE caseid = $1", casenumber)
    if case == [] or case == None:
        await ctx.send("Case not found.")
        return
    try:
        message = await bot.get_channel(case[0]["channelid"]).fetch_message(case[0]["messageid"])
    except:
        await ctx.send("We can't get the message for this case.")
        return

    if not message.guild == ctx.guild:
        await ctx.send("Case not found.")
        return

    embed = discord.Embed(title=f"Case {casenumber}", description=f"```\n{message.content}\n```\n\nActions available for this case (Every action deletes this case):\n- Ban (Bans the user)\n- Kick (Kicks the user)\n- Delete (Deletes the original message)\n- Ignore (Deletes this case)", color=0x00b2ff)
    view = Caseactionsview(ctx)
    original = await ctx.send(embed=embed, view=view)
    await view.wait()

    await original.delete()
    await bot.db.execute("DELETE FROM cases WHERE caseid = $1", casenumber)
    if view.value == "d":
        if ctx.me.guild_permissions.manage_messages == True:
            await message.delete()
            await ctx.send("Action taken and case deleted.", delete_after=5)
            embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Message deleted\n- Case deleted", color=0x00b2ff)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Tried to delete message, failed\n- Case deleted", color=0x00b2ff)
        await ctx.send(embed=embed)

        await ctx.send("GoMod does not have the ability to delete messages (Consider granting Manage messages). Case deleted.", delete_after=5)
    elif view.value == "i":
        embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Case ignored and deleted", color=0x00b2ff)
        await ctx.send(embed=embed)
        await ctx.send("Case deleted.", delete_after=5)
    elif view.value == "b":
        if ctx.me.guild_permissions.ban_members == True:
            reasonembed = discord.Embed(title="Reason", description="Please enter a reason for the ban, this will be sent to the user.", color=0x00b2ff)
            await ctx.send(embed=reasonembed)
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                response = await bot.wait_for("message", check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
                return
            
            
            try:
                await ctx.guild.ban(message.author, reason=response.content)
            except:
                embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Tried to ban user, failed\n- Case deleted", color=0x00b2ff)
                await ctx.send(embed=embed)
                await ctx.send("It seems I can't ban this member. This member may be on top of me or the member is the owner. Try again later. Case deleted.", delete_after=5)
                return

            embedreason = discord.Embed(title=f"Banned from {ctx.guild.name}", description=f"You have been banned from {ctx.guild.name} by {ctx.author.name}. The following message caused you to be banned: ```\n{message.content}\n```\n\nThe moderator has given a reason for the ban: {response.content}", color=discord.Color.red())
            embedreason.set_footer(text=f"Case {casenumber}")
            await message.author.send(embed=embedreason)
            embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- User banned\n- Case deleted", color=0x00b2ff)
            await ctx.send(embed=embed)
            await ctx.send("Action taken and case deleted.", delete_after=5)
            return

        embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Tried to ban user, failed\n- Case deleted", color=0x00b2ff)
        await ctx.send(embed=embed)
        await ctx.send("GoMod does not have the ability to ban users (Consider granting Ban members). Case deleted.", delete_after=5)
    elif view.value == "k":
        if ctx.me.guild_permissions.ban_members == True:
            reasonembed = discord.Embed(title="Reason", description="Please enter a reason for the kick, this will be sent to the user.", color=0x00b2ff)
            await ctx.send(embed=reasonembed)
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                response = await bot.wait_for("message", check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
                return

            
            try:
                await ctx.guild.kick(message.author, reason=response.content)
            except:
                embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Tried to kick user, failed\n- Case deleted", color=0x00b2ff)
                await ctx.send(embed=embed)
                await ctx.send("It seems I can't kick this member. This member may be on top of me or the member is the owner. Try again later. Case deleted.", delete_after=5)
                return

            embedreason = discord.Embed(title=f"Kicked from {ctx.guild.name}", description=f"You have been kicked from {ctx.guild.name} by {ctx.author.name}. The following message caused you to be kicked: ```\n{message.content}\n```\n\nThe moderator has given a reason for the kick: {response.content}", color=discord.Color.red())
            embedreason.set_footer(text=f"Case {casenumber}")
            await message.author.send(embed=embedreason) 
            await ctx.send("Action taken and case deleted.", delete_after=5)
            embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- User kicked\n- Case deleted", color=0x00b2ff)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Summarization", description=f"Case {casenumber}\n\nActions by {ctx.author.name}\n- Tried to kick user, failed\n- Case deleted", color=0x00b2ff)
        await ctx.send(embed=embed)
        await ctx.send("GoMod does not have the ability to kick members (Consider granting Kick members). Case deleted.", delete_after=5)

@bot.command()
@commands.has_guild_permissions(manage_messages=True)
async def ignorechannel(ctx, channel: discord.TextChannel):
    try:
        channelget = bot.get_channel(channel.id)
    except:
        await ctx.send("Invalid channel.")
        return

    if channelget.guild == ctx.guild:
        await bot.db.execute("INSERT INTO ignoredchannels (channelid) VALUES ($1)", channelget.id)
        await ctx.send(f"Channel {channel.mention} will now be ignored.")
    else:
        await ctx.send("Invalid channel.")
        return
        

@bot.command()
@commands.has_guild_permissions(manage_messages=True)
async def unignorechannel(ctx, channel: discord.TextChannel):
    try:
        channelget = bot.get_channel(channel.id)
    except:
        await ctx.send("Invalid channel.")
        return

    result = await bot.db.fetch("SELECT * FROM ignoredchannels WHERE channelid = $1", channelget.id)
    if result == [] or result == None:
        await ctx.send("This channel is not yet ignored.")
        return

    if channelget.guild == ctx.guild:
        await bot.db.execute("DELETE FROM ignoredchannels WHERE channelid = $1", channelget.id)
        await ctx.send(f"Channel {channel.mention} will no longer be ignored.")
    else:
        await ctx.send("Invalid channel.")
        return

@bot.command()
@commands.has_guild_permissions(manage_messages=True)
async def ignoreuser(ctx, user: discord.Member):
    try:
        userget = bot.get_member(user.id)
    except:
        await ctx.send("Invalid user.")
        return

    if userget.guild == ctx.guild:
        await bot.db.execute("INSERT INTO ignoredusers (userid, serverid) VALUES ($1, $2)", userget.id, ctx.guild.id)
        await ctx.send(f"User {user.mention} will now be ignored.")
    else:
        await ctx.send("Invalid user.")
        return

@bot.command()
@commands.has_guild_permissions(manage_messages=True)
async def unignoreuser(ctx, user: discord.Member):
    try:
        userget = bot.get_member(user.id)
    except Exception as e:
        print(e)
        await ctx.send("Invalid user.")
        return

    result = await bot.db.fetch("SELECT * FROM ignoredusers WHERE userid = $1 AND serverid = $2", userget.id, ctx.guild.id)
    if result == [] or result == None:
        await ctx.send("This user is not yet ignored.")
        return

    if userget.guild == ctx.guild:
        await bot.db.execute("DELETE FROM ignoredusers WHERE userid = $1 AND serverid = $2", userget.id, ctx.guild.id)
        await ctx.send(f"User {user.mention} will no longer be ignored.")
    else:
        await ctx.send("Invalid user.")
        return
    
@bot.command()
async def settings(ctx):
    embed = discord.Embed(title="Coming soon", description="This command is still in development. But don't expect too much.", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_guild_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = None):
    if member == ctx.author:
        await ctx.send("You cannot kick yourself.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot kick members with a higher role than you.", delete_after=3)
        return
    try:
        embed = discord.Embed(title=f"Kicked from {ctx.guild.name}", description=f"You have been kicked from {ctx.guild.name} by {ctx.author.name} with reason: {reason}", color=discord.Color.red())
        await member.send(embed=embed)
    except:
        pass
    await ctx.guild.kick(member, reason=reason)
    embed = discord.Embed(title="Kicked", description=f"{member.mention} has been kicked from {ctx.guild.name} with reason: {reason}", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = None):
    if member == ctx.author:
        await ctx.send("You cannot ban yourself.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot ban members with a higher role than you.", delete_after=3)
        return
    try:
        embed = discord.Embed(title=f"Banned from {ctx.guild.name}", description=f"You have been banned from {ctx.guild.name} by {ctx.author.name} with reason: {reason}", color=discord.Color.red())
        await member.send(embed=embed)
    except:
        pass
    await ctx.guild.ban(member, reason=reason)
    embed = discord.Embed(title="Banned", description=f"{member.mention} has been banned from {ctx.guild.name} with reason: {reason}", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True, manage_channels=True)
async def block(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("You cannot block yourself.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot block members with a higher role than you.", delete_after=3)
        return
    await ctx.channel.set_permissions(member, add_reactions = False, send_messages = False)
    embed = discord.Embed(title="Blocked", description=f"{member.mention} has been blocked from {ctx.channel.mention}", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True, manage_channels=True)
async def unblock(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("You cannot unblock yourself.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot unblock members with a higher role than you.", delete_after=3)
        return
    await ctx.channel.set_permissions(member, add_reactions = True, send_messages = True)
    embed = discord.Embed(title="Unblocked", description=f"{member.mention} has been unblocked from {ctx.channel.mention}", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = None):
    if member == ctx.author:
        await ctx.send("You cannot warn yourself.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot warn members with a higher role than you.", delete_after=3)
        return
    try:
        embed = discord.Embed(title=f"Warned", description=f"You have been warned from {ctx.guild.name} by {ctx.author.name} with reason: {reason}", color=discord.Color.orange())
        await member.send(embed=embed)
    except:
        pass
    if reason == None:
        await bot.db.execute("INSERT INTO warns VALUES ($1, $2, $3, $4)", member.id, ctx.guild.id, ctx.author.id, "No reason given.")
        reason = "no reason"
    else:
        await bot.db.execute("INSERT INTO warns VALUES ($1, $2, $3, $4)", member.id, ctx.guild.id, ctx.author.id, reason)

    embed = discord.Embed(title="Warned", description=f"{member.mention} has been warned by {ctx.author.mention} for {reason}", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearwarns(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("You cannot clear your own warnings.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot clear warnings of members with a higher role than you.", delete_after=3)
        return
    await bot.db.execute("DELETE FROM warns WHERE userid = $1 AND serverid = $2", member.id, ctx.guild.id)
    embed = discord.Embed(title="Warns cleared", description=f"{member.mention}'s warnings have been cleared.", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    embed = discord.Embed(title="Messages purged", description=f"{amount} messages have been purged.", color=0x00b2ff)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warns(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("You cannot view your own warnings.", delete_after=3)
        return
    if member.top_role >= ctx.author.top_role:
        await ctx.send("You cannot view warnings of members with a higher role than you.", delete_after=3)
        return
    warns = await bot.db.fetch("SELECT * FROM warns WHERE userid = $1 AND serverid = $2", member.id, ctx.guild.id)
    if warns == []:
        embed = discord.Embed(title="No warns", description=f"{member.mention} has no warns.", color=0x00b2ff)
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(title="Warns", description=f"{member.mention} has {len(warns)} warns.", color=0x00b2ff)
    for warn in warns:
        embed.add_field(name=f"{warn['reason']}", value=f"Warned by {ctx.guild.get_member(warn['invokerid']).mention}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 1800)
@commands.has_permissions(manage_messages=True)
async def rulemaker(ctx):
    embed = discord.Embed(title="Rulemaker setup", description="Rulemaker helps you create rules using AI, so any rules you get is NOT predefined. The rules is set based on what your community does.\n\nLet's start: What is your community about? (We recommend 1 to 2 words.)", color=0x00b2ff)
    init = await ctx.send(embed=embed)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await init.edit("Timed out.", delete_after=3)
        await bot.get_command('rulemaker').reset_cooldown(ctx) 
        return

    if len(msg.content) > 50:
        await init.edit("You can't input 50 or more characters.", delete_after=3)
        await bot.get_command('rulemaker').reset_cooldown(ctx)
        return

    embed = discord.Embed(title="Rulemaker setup", description="We're creating the set of rules now...", color=0x00b2ff)
    setrules = await ctx.send(embed=embed)

    completion = evalu("Create 10 rules for a digital community that is about: " + msg.content + "\n\n1.", 80)

    result = completion.choices[0].text
    embed = discord.Embed(title="Rulemaker setup", description="Complete! Review the following set of rules. \n\n1." + result + "\n\nDon't like how it turned out? You can re-run this command. **Please do know that this command has a 30 minute cooldown to prevent abuse.**", color=0x00b2ff)
    await setrules.edit(embed=embed)

@rulemaker.error
async def rulemaker_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(title="Rulemaker setup", description=f"You are on cooldown. Please try again in {round(error.retry_after / 60)} minutes.", color=0x00b2ff)
        await ctx.send(embed=embed)

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

@bot.command()
@commands.has_permissions(manage_messages=True)
async def createlogging(ctx):
    embed = discord.Embed(title="Logging setup", description=f"You will setup the channel {ctx.channel.mention}. Continue?", color=0x00b2ff)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["✅", "❌"]
    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)
    except asyncio.TimeoutError:
        await msg.edit(embed=discord.Embed(title="Logging setup", description="Timed out.", color=0x00b2ff))
        return

    if str(reaction.emoji) == "❌":
        await msg.edit(embed=discord.Embed(title="Logging setup", description="Cancelled.", color=0x00b2ff))
        return

    embed = discord.Embed(title="Logging setup", description="Do you want to make the channel a deletion log or edit log?", color=0x00b2ff)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🗑")
    await msg.add_reaction("📝")
    
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["🗑", "📝"]
    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60)
    except asyncio.TimeoutError:
        await msg.edit(embed=discord.Embed(title="Logging setup", description="Timed out.", color=0x00b2ff))
        return
    
    if str(reaction.emoji) == "🗑":
        embed = discord.Embed(title="Setting...", description="Setting up deletion logging...", color=0x00b2ff)
        await ctx.send(embed=embed)

        await bot.db.execute("INSERT INTO logch (channelid, loggingtype, guildid) VALUES ($1, $2, $3)", ctx.channel.id, "d", ctx.guild.id)

        embed = discord.Embed(title="Logging setup", description="Complete! To test, try deleting a message.", color=0x00b2ff)
        await ctx.send(embed=embed)
    elif str(reaction.emoji) == "📝":
        embed = discord.Embed(title="Setting...", description="Setting up edit logging...", color=0x00b2ff)
        await ctx.send(embed=embed)

        await bot.db.execute("INSERT INTO logch (channelid, loggingtype, guildid) VALUES ($1, $2, $3)", ctx.channel.id, "e", ctx.guild.id)

        embed = discord.Embed(title="Logging setup", description="Complete! To test, try editing a message.", color=0x00b2ff)
        await ctx.send(embed=embed)

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
            

bot.run(os.environ.get("BOT_TOKEN"))
