import discord
from discord.ext import commands
from bot import GoModBot

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
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


def setup(bot:GoModBot):
    bot.add_cog(Moderation(bot))