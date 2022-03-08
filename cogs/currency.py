import random
import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import asyncio
from bot import GoModBot

async def memberaddcash(self, guild, member, incre):
    lookup = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", guild.id, member.id)
    if lookup is None:
        await self.bot.db.execute("INSERT INTO currencyusers (guildid, uid, cash) VALUES ($1, $2, $3)", guild.id, member.id, 0)

    await self.bot.db.execute("UPDATE currencyusers SET cash = cash + $1 WHERE guildid = $2 AND uid = $3", incre, guild.id, member.id)
        
async def memberremovecash(self, guild, member, decre):
    lookup = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", guild.id, member.id)
    if lookup is None:
        await self.bot.db.execute("INSERT INTO currencyusers (guildid, uid, cash) VALUES ($1, $2, $3)", guild.id, member.id, 0)

    await self.bot.db.execute("UPDATE currencyusers SET cash = cash - $1 WHERE guildid = $2 AND uid = $3", decre, guild.id, member.id)

async def check(self, member):
    lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", member.guild.id)
    if lookup is None:
        return False
    return lookup

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @slash_command(guild_ids=[940076462881513482])
    # async def ccsetup(self, ctx, *, currencyname: Option(str, "The name of the currency. For example, if you do G$: 10G$")):
    #     """
    #     Setup the currency system.
    #     """
    #     if not ctx.author.guild_permissions.manage_guild:
    #         await ctx.respond("You don't have permission to do that.")
    #         return

    #     lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", ctx.guild.id)
    #     if lookup is not None:
    #         await ctx.respond("Currency system already setup.")
    #         return

    #     await self.bot.db.execute("INSERT INTO currency (guildid, currencyname) VALUES ($1, $2)", ctx.guild.id, currencyname)
    #     await ctx.respond("Currency system set up! try doing /ccbal to see your balance.")

    @slash_command(guild_ids=[940076462881513482])
    async def cccreate(self, ctx, currency: Option(str, "The name of the currency. For example, if you do G$: 10 G$")):
        """
        Setup the currency system.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.")
            return

        lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", ctx.guild.id)
        if lookup is not None:
            await ctx.respond("Currency system already setup.")
            return

        await self.bot.db.execute("INSERT INTO currency (guildid, currencyname) VALUES ($1, $2)", ctx.guild.id, currency)
        await ctx.respond("Currency system set up! try doing /ccbal to see your balance.")

    @slash_command(guild_ids=[940076462881513482])
    async def ccremove(self, ctx):
        """
        Remove the currency system.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.")
            return
            
        lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", ctx.guild.id)
        if lookup is None:
            await ctx.respond("Currency system not setup.")
            return

        await self.bot.db.execute("DELETE FROM currency WHERE guildid = $1", ctx.guild.id)
        await self.bot.db.execute("DELETE FROM currencyusers WHERE guildid = $1", ctx.guild.id)
        await ctx.respond("Currency system removed.")
        

    @slash_command(guild_ids=[940076462881513482])
    async def bal(self, ctx, member: Option(discord.Member, "Which member to check.", required=False)):
        """
        Get the current balance of a user.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Please set up the currency system first using /ccsetup.")
            return

        bal = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", ctx.guild.id, ctx.author.id if member is None else member.id)
        if bal is None:
            bal = {"guildid": ctx.guild.id, "uid": ctx.author.id if member is None else member.id, "cash": 0}

        embed = discord.Embed(title="Balance", description=f"{ctx.author.name if member is None else member.name}'s current {lookup['currencyname']} balance is: {bal['cash']} {lookup['currencyname']}.", color=0x00b2ff)

        await ctx.respond(embed=embed) 

    @slash_command(guild_ids=[940076462881513482])
    async def add(self, ctx, member: Option(discord.Member, "Which member to add cash to."), amount: Option(int, "How much to add.")):
        """
        Add cash to a user.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.")
            return

        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Please set up the currency system first using /ccsetup.")
            return

        await memberaddcash(self, ctx.guild, member, amount)
        await ctx.respond(f"Added {amount} {lookup['currencyname']} to {member.name}.")
    
    @slash_command(guild_ids=[940076462881513482])
    async def remove(self, ctx, member: Option(discord.Member, "Which member to remove cash from."), amount: Option(int, "How much to remove.")):
        """
        Remove cash from a user.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.")
            return

        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Please set up the currency system first using /ccsetup.")
            return

        await memberremovecash(self, ctx.guild, member, amount)
        await ctx.respond(f"Removed {amount} {lookup['currencyname']} from {member.name}.")

    @slash_command(guild_ids=[940076462881513482])
    async def give(self, ctx, member: Option(discord.Member, "Which member to give cash to."), amount: Option(int, "How much to give.")):
        """
        Give cash to a user.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Please set up the currency system first using /ccsetup.")
            return

        await memberaddcash(self, ctx.guild, member, amount)
        await memberremovecash(self, ctx.guild, ctx.author, amount)
        await ctx.respond(f"Gave {amount} {lookup['currencyname']} to {member.name}.")


    @slash_command(guild_ids=[940076462881513482])
    async def flipbet(self, ctx, amount: Option(int, "The amount you're betting."), *, bet: Option(str, "Heads or Tails.", autocomplete=discord.utils.basic_autocomplete(("Heads", "Tails")))):
        """
        Flip a coin and get or lose on the outcome.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Please set up the currency system first using /ccsetup.")
            return

        bal = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", ctx.guild.id, ctx.author.id)
        if bal is None:
            bal = {"guildid": ctx.guild.id, "uid": ctx.author.id, "cash": 0}

        if amount > bal["cash"]:
            await ctx.respond("You don't have enough money to bet that much.")
            return

        if amount < 1:
            await ctx.respond("You can't bet a negative amount or 0.")
            return

        if not bet.lower() in ("heads", "tails"):
            await ctx.respond("Please enter heads or tails.")
            return

        coin = random.randint(1, 2) #idk if this is ineffective code but it works   
        if coin == 1 and bet.lower() == "heads":
            embed = discord.Embed(title="Flip", description=f"The coin flipped and landed on Heads. You win {amount} {lookup['currencyname']}!", color=0x00b2ff)
            await ctx.respond(embed=embed)
            await memberaddcash(self, ctx.guild, ctx.author, amount)
        elif coin == 2 and bet.lower() == "tails":
            embed = discord.Embed(title="Flip", description=f"The coin flipped and landed on Tails. You win {amount} {lookup['currencyname']}!", color=0x00b2ff)
            await ctx.respond(embed=embed)
            await memberaddcash(self, ctx.guild, ctx.author, amount)
        elif coin == 1 and bet.lower() == "tails":
            embed = discord.Embed(title="Flip", description=f"The coin flipped and landed on Heads. You lose {amount} {lookup['currencyname']}.", color=0x00b2ff)
            await ctx.respond(embed=embed)
            await memberremovecash(self, ctx.guild, ctx.author, amount)
        elif coin == 2 and bet.lower() == "heads":
            embed = discord.Embed(title="Flip", description=f"The coin flipped and landed on Tails. You lose {amount} {lookup['currencyname']}.", color=0x00b2ff)
            await ctx.respond(embed=embed)
            await memberremovecash(self, ctx.guild, ctx.author, amount)                
    

        

def setup(bot:GoModBot):
    bot.add_cog(Currency(bot))