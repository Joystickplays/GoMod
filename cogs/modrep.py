import discord
from discord.ext import commands
import asyncio
from bot import GoModBot
from discord.ui import InputText, Modal
from cogs.views import UpDownvote

async def getvotes(self, member):
    upvotes = await self.bot.db.fetch("SELECT COUNT(*) FROM repvotes WHERE who = $1 AND type = 'up'", member.id)
    downvotes = await self.bot.db.fetch("SELECT COUNT(*) FROM repvotes WHERE who = $1 AND type = 'down'", member.id)
    votes = upvotes[0]["count"] - downvotes[0]["count"]
    return discord.Embed(title="Reputation", description=f"{member.mention} has {votes} votes.", color=0x00b2ff)

class ModRep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def modrep(self, ctx, member: discord.Member):
        embed = await getvotes(self, member)
        await ctx.send(embed=embed, view=UpDownvote(self.bot, member))

def setup(bot:GoModBot):
    bot.add_cog(ModRep(bot))