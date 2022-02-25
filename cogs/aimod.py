import discord
import asyncio
import openai
import os
from cogs.views import Caseactionsview, Helpview
from discord.ext import commands
from bot import GoModBot
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")

def evalu(msg, tokens):
    return openai.Completion.create(
            engine="text-davinci-001",
            temperature=0.5,
            top_p=0.5,
            prompt=msg,
            max_tokens=tokens
        )

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def setup(self, ctx):
        servercheck = await self.bot.db.fetch("SELECT * FROM discservers WHERE discordid = $1", ctx.guild.id)
        if servercheck == [] or servercheck == None:
            embed = discord.Embed(title="Setup", description="Do you want to start setup?", color=0x00b2ff)
            react = await ctx.send(embed=embed)
            await react.add_reaction("\U00002705")
            await react.add_reaction("\U0000274C")
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["\U00002705", "\U0000274C"]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
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
                response = await self.bot.wait_for("message", check=check)
                try:
                    channelwarns = await commands.TextChannelConverter().convert(ctx, response.content)
                    break
                except:
                    embed = discord.Embed(title="Setup", description="We can't find that channel, try again?", color=0x00b2ff)
                    await ctx.send(embed=embed, delete_after=2)

            embed = discord.Embed(title="Finishing setup...", description="Give us a a second, you're almost there.", color=0x00b2ff)
            await ctx.send(embed=embed)
            
            try:
                await self.bot.db.execute("INSERT INTO discservers (discordid, warningch, invokerid) VALUES ($1, $2, $3)", ctx.guild.id, channelwarns.id, ctx.author.id)
                embed = discord.Embed(title="Setup success", description="Setup finished! GoMod will now listen for messages.\n\nTip: You should restrict GoMod to high traffic channels and ignoring NSFW channels and bot channels.", color=0x00b2ff)
                await ctx.send(embed=embed)
            except Exception:
                embed = discord.Embed(title="Setup failure", description="Something went wrong. Try again later.", color=discord.Color.red())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Setup failure", description="It looks like this server has already been set up.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True, kick_members=True, ban_members=True)
    async def case(self, ctx, casenumber):
        try:
            casenumber = int(casenumber)
        except:
            await ctx.send("Invalid case number.")
            return

        await ctx.channel.trigger_typing()
        case = await self.bot.db.fetch("SELECT * FROM cases WHERE caseid = $1", casenumber)
        if case == [] or case == None:
            await ctx.send("Case not found.")
            return
        try:
            message = await self.bot.get_channel(case[0]["channelid"]).fetch_message(case[0]["messageid"])
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
        await self.bot.db.execute("DELETE FROM cases WHERE caseid = $1", casenumber)
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
                    response = await self.bot.wait_for("message", check=check, timeout=30.0)
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
                    response = await self.bot.wait_for("message", check=check, timeout=30.0)
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

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def ignorechannel(self, ctx, channel: discord.TextChannel):
        try:
            channelget = self.bot.get_channel(channel.id)
        except:
            await ctx.send("Invalid channel.")
            return

        if channelget.guild == ctx.guild:
            await self.bot.db.execute("INSERT INTO ignoredchannels (channelid) VALUES ($1)", channelget.id)
            await ctx.send(f"Channel {channel.mention} will now be ignored.")
        else:
            await ctx.send("Invalid channel.")
            return
            

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def unignorechannel(self, ctx, channel: discord.TextChannel):
        try:
            channelget = self.bot.get_channel(channel.id)
        except:
            await ctx.send("Invalid channel.")
            return

        result = await self.bot.db.fetch("SELECT * FROM ignoredchannels WHERE channelid = $1", channelget.id)
        if result == [] or result == None:
            await ctx.send("This channel is not yet ignored.")
            return

        if channelget.guild == ctx.guild:
            await self.bot.db.execute("DELETE FROM ignoredchannels WHERE channelid = $1", channelget.id)
            await ctx.send(f"Channel {channel.mention} will no longer be ignored.")
        else:
            await ctx.send("Invalid channel.")
            return

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def ignoreuser(self, ctx, user: discord.Member):
        try:
            userget = self.bot.get_member(user.id)
        except:
            await ctx.send("Invalid user.")
            return

        if userget.guild == ctx.guild:
            await self.bot.db.execute("INSERT INTO ignoredusers (userid, serverid) VALUES ($1, $2)", userget.id, ctx.guild.id)
            await ctx.send(f"User {user.mention} will now be ignored.")
        else:
            await ctx.send("Invalid user.")
            return

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def unignoreuser(self, ctx, user: discord.Member):
        try:
            userget = self.bot.get_member(user.id)
        except Exception as e:
            print(e)
            await ctx.send("Invalid user.")
            return

        result = await self.bot.db.fetch("SELECT * FROM ignoredusers WHERE userid = $1 AND serverid = $2", userget.id, ctx.guild.id)
        if result == [] or result == None:
            await ctx.send("This user is not yet ignored.")
            return

        if userget.guild == ctx.guild:
            await self.bot.db.execute("DELETE FROM ignoredusers WHERE userid = $1 AND serverid = $2", userget.id, ctx.guild.id)
            await ctx.send(f"User {user.mention} will no longer be ignored.")
        else:
            await ctx.send("Invalid user.")
            return
        
    @commands.command()
    async def settings(ctx):
        embed = discord.Embed(title="Coming soon", description="This command is still in development. But don't expect too much.", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 1800)
    @commands.has_permissions(manage_messages=True)
    async def rulemaker(self, ctx):
        embed = discord.Embed(title="Rulemaker setup", description="Rulemaker helps you create rules using AI, so any rules you get is NOT predefined. The rules is set based on what your community does.\n\nLet's start: What is your community about? (We recommend 1 to 2 words.)", color=0x00b2ff)
        init = await ctx.send(embed=embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await init.edit("Timed out.", delete_after=3)
            await self.bot.get_command('rulemaker').reset_cooldown(ctx) 
            return

        if len(msg.content) > 50:
            await init.edit("You can't input 50 or more characters.", delete_after=3)
            await self.bot.get_command('rulemaker').reset_cooldown(ctx)
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


def setup(bot:GoModBot):
    bot.add_cog(Moderation(bot))