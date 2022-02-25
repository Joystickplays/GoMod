import discord
from discord.ext import commands
from bot import GoModBot

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        if member == ctx.author:
            await ctx.send("You cannot ban yourself..", delete_after=3)
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
    @commands.has_permissions(manage_messages=True, manage_channels=True)
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
    @commands.has_permissions(manage_messages=True, manage_channels=True)
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
    @commands.has_permissions(manage_messages=True)
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
    @commands.has_permissions(manage_messages=True)
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
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount+1)
        embed = discord.Embed(title="Messages purged", description=f"{amount} messages have been purged.", color=0x00b2ff)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
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


def setup(bot:GoModBot):
    bot.add_cog(Moderation(bot))