import discord
from discord.ext import commands
import asyncio
from bot import GoModBot

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        lookup = self.bot.fetchrow("SELECT * FROM reactroles WHERE message = $1 AND channel = $2", reaction.message.id, reaction.message.channel.id)
        if lookup:
            if reaction.emoji.id == lookup['reaction']:
                role = discord.utils.get(user.guild.roles, id=lookup['role'])
                if role == None:
                    return

                if role in user.roles:
                    pass
                else:
                    await user.add_roles(role)

    @commands.command()
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
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

    @commands.command()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
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

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True, manage_channels=True)
    async def block(self, ctx, member: discord.Member):
        if member == ctx.author:
            await ctx.send("You cannot block yourself.", delete_after=3)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot block members with a higher role than you.", delete_after=3)
            return
        await ctx.channel.set_permissions(member, add_reactions = False, send_messages = False)
        embed = discord.Embed(title="Blocked", description=f"{member.mention} has been blocked from {ctx.channel.mention}", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True, manage_channels=True)
    async def unblock(self, ctx, member: discord.Member):
        if member == ctx.author:
            await ctx.send("You cannot unblock yourself.", delete_after=3)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot unblock members with a higher role than you.", delete_after=3)
            return
        await ctx.channel.set_permissions(member, add_reactions = True, send_messages = True)
        embed = discord.Embed(title="Unblocked", description=f"{member.mention} has been unblocked from {ctx.channel.mention}", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
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
            await self.bot.db.execute("INSERT INTO warns VALUES ($1, $2, $3, $4)", member.id, ctx.guild.id, ctx.author.id, "No reason given.")
            reason = "no reason"
        else:
            await self.bot.db.execute("INSERT INTO warns VALUES ($1, $2, $3, $4)", member.id, ctx.guild.id, ctx.author.id, reason)

        embed = discord.Embed(title="Warned", description=f"{member.mention} has been warned by {ctx.author.mention} for {reason}", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def clearwarns(self, ctx, member: discord.Member):
        if member == ctx.author:
            await ctx.send("You cannot clear your own warnings.", delete_after=3)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot clear warnings of members with a higher role than you.", delete_after=3)
            return
        await self.bot.db.execute("DELETE FROM warns WHERE userid = $1 AND serverid = $2", member.id, ctx.guild.id)
        embed = discord.Embed(title="Warns cleared", description=f"{member.mention}'s warnings have been cleared.", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount+1)
        embed = discord.Embed(title="Messages purged", description=f"{amount} messages have been purged.", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def warns(self, ctx, member: discord.Member):
        if member == ctx.author:
            await ctx.send("You cannot view your own warnings.", delete_after=3)
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot view warnings of members with a higher role than you.", delete_after=3)
            return
        warns = await self.bot.db.fetch("SELECT * FROM warns WHERE userid = $1 AND serverid = $2", member.id, ctx.guild.id)
        if warns == []:
            embed = discord.Embed(title="No warns", description=f"{member.mention} has no warns.", color=0x00b2ff)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title="Warns", description=f"{member.mention} has {len(warns)} warns.", color=0x00b2ff)
        for warn in warns:
            embed.add_field(name=f"{warn['reason']}", value=f"Warned by {ctx.guild.get_member(warn['invokerid']).mention}", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def test(self, ctx):
        await ctx.send(ctx.message.content)
        print(ctx.message.content)
        await ctx.message.add_reaction(ctx.message.content.replace("--test ", ""))

    # @commands.command()
    # @commands.has_guild_permissions(manage_messages=True)
    # async def reactrole(self, ctx):
    #     embed = discord.Embed(title="Reaction role setup", description="1/4\nWhat channel is the message you're using is in?", color=0x00b2ff)
    #     msg = await ctx.send(embed=embed)

    #     def check(m):
    #         return m.channel == ctx.channel and m.author == ctx.author

    #     try:
    #         msg = await self.bot.wait_for('message', check=check, timeout=60)
    #     except asyncio.TimeoutError:
    #         await ctx.send("Timed out.", delete_after=3)
    #         return

    #     channel = discord.utils.get(ctx.guild.text_channels, name=msg.content)
    #     if channel == None:
    #         await ctx.send("That channel doesn't exist.", delete_after=3)
    #         return
        
    #     embed = discord.Embed(title="Reaction role setup", description="2/4\nWhat is your message's ID? More on getting message IDs [here](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-)", color=0x00b2ff)
    #     msg = await ctx.send(embed=embed)

    #     try:
    #         msg = await self.bot.wait_for('message', check=check, timeout=60)   
    #     except asyncio.TimeoutError:
    #         await ctx.send("Timed out.", delete_after=3)
    #         return

    #     try:
    #         message = await channel.fetch_message(int(msg.content))
    #     except:
    #         await ctx.send("That message doesn't exist.", delete_after=3)
    #         return

    #     embed = discord.Embed(title="Reaction role setup", description="3/4\nWhat will be the emoji for your reaction?", color=0x00b2ff)
    #     msg = await ctx.send(embed=embed)

    #     try:
    #         msg = await self.bot.wait_for('message', check=check, timeout=60)
    #     except asyncio.TimeoutError:
    #         await ctx.send("Timed out.", delete_after=3)
    #         return

    #     reactionname = msg.content
    #     try:
    #         reaction = await message.add_reaction(msg.content)
    #     except:
    #         await ctx.send("That emoji is invalid.", delete_after=3)
    #         return

    #     embed = discord.Embed(title="Reaction role setup", description="4/4\nWhat role will be given to the user when they react?", color=0x00b2ff)
    #     msg = await ctx.send(embed=embed)

    #     try:
    #         msg = await self.bot.wait_for('message', check=check, timeout=60)
    #     except asyncio.TimeoutError:
    #         await ctx.send("Timed out.", delete_after=3)
    #         return

    #     role = discord.utils.get(ctx.guild.roles, name=msg.content)
    #     if role == None:
    #         await ctx.send("That role doesn't exist.", delete_after=3)
    #         return

    #     await self.bot.db.execute("INSERT INTO reactroles VALUES ($1, $2, $3, $4)", message.id, channel.id, role.id, reactionname)
    #     embed = discord.Embed(title="Reaction role setup", description="Reaction role setup complete.", color=0x00b2ff)
    #     await ctx.send(embed=embed)




def setup(bot:GoModBot):
    bot.add_cog(Moderation(bot))