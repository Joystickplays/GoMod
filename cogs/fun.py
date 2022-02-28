import discord
from discord.ext import commands
import asyncio
from bot import GoModBot

async def getc(self, user):
        lookup = await self.bot.db.fetchrow("SELECT * FROM gocash WHERE uid = $1", user)
        if lookup is None:
            return 0

        return lookup['cash']

async def increc(self, user, quan):
        lookup = await self.bot.db.fetchrow("SELECT * FROM gocash WHERE uid = $1", user)
        if lookup is None:
            await self.bot.db.execute("INSERT INTO gocash (uid, cash) VALUES ($1, $2)", user, quan)
        else:
            await self.bot.db.execute("UPDATE gocash SET cash = cash + $1 WHERE uid = $2", quan, user)

async def decrec(self, user, quan):
        lookup = await self.bot.db.fetchrow("SELECT * FROM gocash WHERE uid = $1", user)
        if lookup is None:
            return 0
        else:
            if int(lookup["cash"]) - int(quan) < 0:
                return 0

            await self.bot.db.execute("UPDATE gocash SET cash = cash - $1 WHERE uid = $2", quan, user)
            return 1

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command()
    async def gcbal(self, ctx, member: discord.Member = None):
        bal = await getc(self, ctx.author.id if member is None else member.id)

        if member is None:
            embed = discord.Embed(title="Balance", description=f"Your current GoCash balance is: {bal} GCs.", color=0x00b2ff)
        else:
            embed = discord.Embed(title="Balance", description=f"{member.name}'s current GoCash balance is: {bal} GCs.", color=0x00b2ff)

        await ctx.send(embed=embed)

    @commands.command()
    async def givegc(self, ctx, member: discord.Member, amount: int):
        cash = await getc(self, ctx.author.id)
        if member.id == ctx.author.id:
            await ctx.send("You can't give yourself GoCash.")
            return

        if amount < 0:
            await ctx.send("You can't give 0 or less GoCash.")
            return

        if cash < amount:
            await ctx.send("You don't have enough GoCash to give.")
            return

        await decrec(self, ctx.author.id, amount)
        await increc(self, member.id, amount)
        await ctx.send(f"You gave {amount} GC to {member.name}.")

    # @commands.command()
    # async def modquiz(self, ctx):

    #     class TakeQuiz(discord.ui.View):
    #         def __init__(self, ctx): 
    #             super().__init__()
    #             self.ctx = ctx

    #         @discord.ui.button(label='Take the quiz', style=discord.ButtonStyle.green)
    #         async def upvote(self, button: discord.ui.Button, interaction: discord.Interaction):
    #             if interaction.user != self.ctx.author:
    #                 await interaction.response.send_message(f"You can't take this quiz. `Run --modquiz` to take a quiz too!", ephemeral=True)
    #                 return

    #             self.stop()

    #     embed = discord.Embed("Moderation quiz", description="Answer these questions correctly and you will get 5 GoCash for every question you get right.", color=0x00b2ff)
    #     view = TakeQuiz(ctx)
    #     await ctx.send(embed=embed, view=view)
    #     await view.wait()

        



    

def setup(bot:GoModBot):
    bot.add_cog(Fun(bot))