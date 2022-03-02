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

    #             self.result = 1
    #             self.stop()
        
    #     class DropDownAnswers(discord.ui.Select):
    #         def __init__(self, ls):
    #             self.ls = ls
                
    #             ind = 0
    #             options = []
    #             for it in ls:
    #                 options.append(discord.SelectOption(label=it["t"], value=ind, description=it["d"]))
    #                 ind += 1

    #             super().__init__(placeholder='Choose an answer', min_values=1, max_values=1, options=options)

    #         async def callback(self, interaction: discord.Interaction):
    #             self.result = self.values[0]
    #             self.view.stop()
        
    #     class AnswersView(discord.ui.View):
    #         def __init__(self, ls):
    #             super().__init__()

    #             self.dd = DropDownAnswers(ls)
    #             self.add_item(self.dd)

    #     embed = discord.Embed(title="Moderation quiz", description="Answer these questions correctly and you will get 5 GoCash for every question you get right.", color=0x00b2ff)
    #     view = TakeQuiz(ctx)
    #     await ctx.send(embed=embed, view=view)
    #     await view.wait()

    #     if view.result is None:
    #         return

    #     embed = discord.Embed(title="Question 1", description="If your server has a channel that allows you to vent about personal stuff, would you allow image attachments on it?", color=0x00b2ff)
    #     ddview = AnswersView([{"t":"Yes, I would.","d":"Because this way, other people can express their emotions through image.",},{"t":"Yes, I would.","d":"Because people can send increased context."},{"t":"No, I wouldn't.","d":"Because people may send images that contain self harm or weapons they intend to use."},{"t":"No, I wouldn't.","d":"Because to prevent memes or s*htpost on these channels."}])
    #     await ctx.send(embed=embed, view=ddview)
    #     await ddview.wait()

    #     await ctx.send(str(ddview.dd.values[0]))
        



    

def setup(bot:GoModBot):
    bot.add_cog(Fun(bot))