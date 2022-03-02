import discord
from discord.ext import commands
import asyncio
from bot import GoModBot

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        lookup = await self.bot.db.fetchrow("SELECT * FROM modules WHERE server = $1 AND module = $2", ctx.guild.id, "tg")
        return lookup is not None

    @commands.group(invoke_without_command=True, aliases=["t"])
    async def tag(self, ctx, tag):
        lookup = await self.bot.db.fetchrow("SELECT * FROM tags WHERE tagname = $1 AND serverid = $2", tag, ctx.guild.id)
        if lookup is None:
            embed = discord.Embed(title="Tag", description=f"Tag `{tag}` does not exist.", color=0x00b2ff)
            await ctx.send(embed=embed)
            return
        await ctx.send(lookup["tagcontent"])

    @tag.command()
    async def create(self, ctx, tag, *, content):
        if len(tag) > 254:
            embed = discord.Embed(title="Tag", description="Tag name too long.", color=0x00b2ff)
            await ctx.send(embed=embed)
            return

        lookup = await self.bot.db.fetchrow("SELECT * FROM tags WHERE tagname = $1 AND serverid = $2", tag, ctx.guild.id)
        if lookup is not None:
            embed = discord.Embed(title="Tag", description=f"Tag `{tag}` already exists.", color=0x00b2ff)
            await ctx.send(embed=embed)
            return

        await self.bot.db.execute("INSERT INTO tags (tagname, tagcontent, serverid) VALUES ($1, $2, $3)", tag, content, ctx.guild.id)
        embed = discord.Embed(title="Tag", description=f"Tag `{tag}` created.", color=0x00b2ff)
        await ctx.send(embed=embed)


def setup(bot:GoModBot):
    bot.add_cog(Tags(bot))