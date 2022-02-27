import discord
from discord.ext import commands
import asyncio
from bot import GoModBot
from discord.ui import InputText, Modal

async def getvotes(self, member):
    upvotes = await self.bot.db.fetch("SELECT COUNT(*) FROM repvotes WHERE who = $1 AND type = 'up'", member.id)
    downvotes = await self.bot.db.fetch("SELECT COUNT(*) FROM repvotes WHERE who = $1 AND type = 'down'", member.id)
    votes = upvotes[0]["count"] - downvotes[0]["count"]
    return discord.Embed(title="Reputation", description=f"{member.mention} has {votes} votes.", color=0x00b2ff)

class UpDownvote(discord.ui.View):
    def __init__(self, bot, mem): 
        super().__init__()
        self.value = None
        self.bot = bot
        self.mem = mem

    @discord.ui.button(label='Upvote', style=discord.ButtonStyle.green)
    async def upvote(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.mem.id == interaction.user.id:
            await interaction.response.send_message("You cannot upvote or downvote yourself.", ephemeral=True)
            return

        lookup = await self.bot.db.fetchrow("SELECT * FROM repvotes WHERE who = $1 AND voted = $2", self.mem.id, interaction.user.id)
        if lookup:
            if lookup["type"] == "down":
                await self.bot.db.execute("DELETE FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'down'", self.mem.id, interaction.user.id)
                await self.bot.db.execute("INSERT INTO repvotes (who, voted, type) VALUES ($1, $2, 'up')", self.mem.id, interaction.user.id)
                embed = await getvotes(self, self.mem)
                await interaction.message.edit(content=f"Update: {interaction.user.mention} cancelled the downvote and upvote this member.", embed=embed)
                return
            elif lookup["type"] == "up":
                await self.bot.db.execute("DELETE FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'up'", self.mem.id, interaction.user.id)
                embed = await getvotes(self, self.mem)
                await interaction.message.edit(f"Update: {interaction.user.mention} cancelled the upvote for this user.", embed=embed)
                return

        await self.bot.db.execute("INSERT INTO repvotes (who, voted, type) VALUES ($1, $2, 'up')", self.mem.id, interaction.user.id)
        embed = await getvotes(self, self.mem)
        await interaction.message.edit(content=f"Update: {interaction.user.mention} upvoted this member.", embed=embed)

    @discord.ui.button(label='Downvote', style=discord.ButtonStyle.red)
    async def downvote(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.mem.id == interaction.user.id:
            await interaction.response.send_message("You cannot upvote or downvote yourself.", ephemeral=True)
            return

        lookup = await self.bot.db.fetchrow("SELECT * FROM repvotes WHERE who = $1 AND voted = $2", self.mem.id, interaction.user.id)
        if lookup:
            if lookup["type"] == "down":
                await self.bot.db.execute("DELETE FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'down'", self.mem.id, interaction.user.id)
                embed = await getvotes(self, self.mem)
                await interaction.message.edit(f"Update: {interaction.user.mention} cancelled the downvote for this user.", embed=embed)
                return
            elif lookup["type"] == "up":
                await self.bot.db.execute("DELETE FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'up'", self.mem.id, interaction.user.id)
                await self.bot.db.execute("INSERT INTO repvotes (who, voted, type) VALUES ($1, $2, 'down')", self.mem.id, interaction.user.id)
                embed = await getvotes(self, self.mem)
                await interaction.message.edit(content=f"Update: {interaction.user.mention} cancelled the upvote and downvoted this member.", embed=embed)
                return

        await self.bot.db.execute("INSERT INTO repvotes (who, voted, type) VALUES ($1, $2, 'down')", self.mem.id, interaction.user.id)
        embed = await getvotes(self, self.mem)
        await interaction.message.edit(content=f"Update: {interaction.user.mention} downvoted this member.", embed=embed)


class ModRep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def modrep(self, ctx, member: discord.Member):
        embed = await getvotes(self, member)
        await ctx.send(embed=embed, view=UpDownvote(self.bot, member))

def setup(bot:GoModBot):
    bot.add_cog(ModRep(bot))