import discord
import asyncio
from discord.ext import commands
from bot import GoModBot

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, messagebefore, messageafter):
        if messagebefore.author.bot:
            return
        if messagebefore.guild is None:
            return

        for record in self.bot.logcache:
            if record["guildid"] == messagebefore.guild.id and record["loggingtype"] == "e":
                channel = self.bot.get_channel(record["channelid"])
                if channel is None:
                    return
                embed = discord.Embed(title="Message edited", description=f"The following message was edited in `{messagebefore.channel.name}` by `{messagebefore.author.name}`:\n\nFrom:\n```\n{messagebefore.content}\n```\nTo:\n```{messageafter.content}```", color=discord.Color.orange())
                await channel.send(embed=embed)
                return
        
        logs = await self.bot.db.fetch("SELECT * FROM logch")
        for log in logs:
            tempdict = {}
            tempdict["guildid"] = log["guildid"]
            tempdict["channelid"] = log["channelid"]
            tempdict["loggingtype"] = log["loggingtype"]
            self.bot.logcache.append(tempdict)
            if log["guildid"] == messagebefore.guild.id and log["loggingtype"] == "e":
                channel = self.bot.get_channel(record["channelid"])
                if channel is None:
                    return
                embed = discord.Embed(title="Message edited", description=f"The following message was edited in `{messagebefore.channel.name}` by `{messagebefore.author.name}`:\n\nFrom:\n```\n{messagebefore.content}\n```\nTo:\n```{messageafter.content}```", color=discord.Color.orange())
                await channel.send(embed=embed)
                return


    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            return

        for record in self.bot.logcache:
            if record["guildid"] == message.guild.id and record["loggingtype"] == "e":
                channel = self.bot.get_channel(record["channelid"])
                if channel is None:
                    return
                embed = discord.Embed(title="Message deleted", description=f"The following message was deleted in `{message.channel.name}` by `{message.author.name}`:\n\n```\n{message.content}\n```", color=discord.Color.red())
                await channel.send(embed=embed)
                return
        
        logs = await self.bot.db.fetch("SELECT * FROM logch")
        for log in logs:
            tempdict = {}
            tempdict["guildid"] = log["guildid"]
            tempdict["channelid"] = log["channelid"]
            tempdict["loggingtype"] = log["loggingtype"]
            self.bot.logcache.append(tempdict)
            if log["guildid"] == message.guild.id and log["loggingtype"] == "e":
                channel = self.bot.get_channel(log["channelid"])
                if channel is None:
                    return
                embed = discord.Embed(title="Message deleted", description=f"The following message was deleted in `{message.channel.name}` by `{message.author.name}`:\n\n```\n{message.content}\n```", color=discord.Color.red())
                await channel.send(embed=embed)
                return

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def createlogging(self, ctx):
        embed = discord.Embed(title="Logging setup", description=f"You will setup the channel {ctx.channel.mention}. Continue?", color=0x00b2ff)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        def check(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["✅", "❌"]
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
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
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
        except asyncio.TimeoutError:
            await msg.edit(embed=discord.Embed(title="Logging setup", description="Timed out.", color=0x00b2ff))
            return
        
        if str(reaction.emoji) == "🗑":
            embed = discord.Embed(title="Setting...", description="Setting up deletion logging...", color=0x00b2ff)
            await ctx.send(embed=embed)

            await self.bot.db.execute("INSERT INTO logch (channelid, loggingtype, guildid) VALUES ($1, $2, $3)", ctx.channel.id, "d", ctx.guild.id)

            embed = discord.Embed(title="Logging setup", description="Complete! To test, try deleting a message.", color=0x00b2ff)
            await ctx.send(embed=embed)
        elif str(reaction.emoji) == "📝":
            embed = discord.Embed(title="Setting...", description="Setting up edit logging...", color=0x00b2ff)
            await ctx.send(embed=embed)

            await self.bot.db.execute("INSERT INTO logch (channelid, loggingtype, guildid) VALUES ($1, $2, $3)", ctx.channel.id, "e", ctx.guild.id)

            embed = discord.Embed(title="Logging setup", description="Complete! To test, try editing a message.", color=0x00b2ff)
            await ctx.send(embed=embed)


def setup(bot:GoModBot):
    bot.add_cog(Logging(bot))