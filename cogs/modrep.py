import discord
from discord.ext import commands
import asyncio
from bot import GoModBot
from discord.ui import InputText, Modal

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

        lookup = await self.bot.db.fetchrow("SELECT * FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'up'", self.mem.id, interaction.user.id)
        if lookup:
            await self.bot.db.execute("DELETE FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'up'", self.mem.id, interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.mention} cancelled the upvote for this user.")
            return

        await self.bot.db.execute("INSERT INTO repvotes (who, voted, type) VALUES ($1, $2, 'up')", self.mem.id, interaction.user.id)
        await interaction.response.send_message(content=f"{interaction.user.mention} upvoted this member.")

    @discord.ui.button(label='Downvote', style=discord.ButtonStyle.red)
    async def downvote(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.mem.id == interaction.user.id:
            await interaction.response.send_message("You cannot upvote or downvote yourself.", ephemeral=True)
            return

        lookup = await self.bot.db.fetchrow("SELECT * FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'down'", self.mem.id, interaction.user.id)
        if lookup:
            await self.bot.db.execute("DELETE FROM repvotes WHERE who = $1 AND voted = $2 AND type = 'down'", self.mem.id, interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.mention} cancelled the downvote for this user.")
            return

        await self.bot.db.execute("INSERT INTO repvotes (who, voted, type) VALUES ($1, $2, 'down')", self.mem.id, interaction.user.id)
        await interaction.response.send_message(content=f"{interaction.user.mention} downvoted this member.")


class ModRep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def modrep(self, ctx, member: discord.Member):
        votes = await self.bot.db.fetch("SELECT COUNT(*) FROM repvotes WHERE who = $1", member.id)
        votes = votes[0]["count"]
        embed = discord.Embed(title="Reputation", description=f"{member.mention} has {votes} votes.", color=0x00b2ff)
        await ctx.send(embed=embed, view=UpDownvote(self.bot))

def setup(bot:GoModBot):
    bot.add_cog(ModRep(bot))