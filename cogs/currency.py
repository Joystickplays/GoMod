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

async def getbal(self, guild, member):
    bal = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", guild.id, member.id)
    if bal is None:
        return {"guildid": guild.id, "uid": member.id, "cash": 0}
    return bal

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @slash_command(guild_ids=[940076462881513482])
    # async def ccsetup(self, ctx, *, currencyname: Option(str, "The name of the currency. For example, if you do G$: 10G$")):
    #     """
    #     Setup the currency system.
    #     """
    #     if not ctx.author.guild_permissions.manage_guild:
    #         await ctx.respond("You don't have permission to do that.", ephemeral=True)
    #         return

    #     lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", ctx.guild.id)
    #     if lookup is not None:
    #         await ctx.respond("Currency system already setup.")
    #         return

    #     await self.bot.db.execute("INSERT INTO currency (guildid, currencyname) VALUES ($1, $2)", ctx.guild.id, currencyname)
    #     await ctx.respond("Currency system set up! try doing /ccbal to see your balance.")

    @slash_command(guild_ids=[940076462881513482])
    async def cccreate(self, ctx, currencyabbv: Option(str, "The abbreviation of the currency. For example, if you do G$: 10 G$")):
        """
        Setup the currency system.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.", ephemeral=True)
            return

        lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", ctx.guild.id)
        if lookup is not None:
            await ctx.respond("Currency system already setup.", ephemeral=True)
            return

        await self.bot.db.execute("INSERT INTO currency (guildid, currencyname) VALUES ($1, $2)", ctx.guild.id, currencyabbv)
        await ctx.respond("Currency system set up! try doing /bal to see your balance.", ephemeral=True)

    @slash_command(guild_ids=[940076462881513482])
    async def ccremove(self, ctx):
        """
        Remove the currency system. This will remove all currency from all members!
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.", ephemeral=True)
            return
            
        lookup = await self.bot.db.fetchrow("SELECT * FROM currency WHERE guildid = $1", ctx.guild.id)
        if lookup is None:
            await ctx.respond("Currency system not setup.", ephemeral=True)
            return

        await self.bot.db.execute("DELETE FROM currency WHERE guildid = $1", ctx.guild.id)
        await self.bot.db.execute("DELETE FROM currencyusers WHERE guildid = $1", ctx.guild.id)
        await ctx.respond("Currency system removed.", ephemeral=True)
        

    @slash_command(guild_ids=[940076462881513482])
    async def bal(self, ctx, member: Option(discord.Member, "Which member to check.", required=False)):
        """
        Get the current balance of a user.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        bal = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", ctx.guild.id, ctx.author.id if member is None else member.id)
        if bal is None:
            bal = {"guildid": ctx.guild.id, "uid": ctx.author.id if member is None else member.id, "cash": 0}

        embed = discord.Embed(title="Balance", description=f"{ctx.author.name if member is None else member.name}'s current {lookup['currencyname']} balance is: {bal['cash']} {lookup['currencyname']}.", color=0x00b2ff)

        await ctx.respond(embed=embed) 

    @slash_command(guild_ids=[940076462881513482])
    async def baladd(self, ctx, member: Option(discord.Member, "Which member to add cash to."), amount: Option(int, "How much to add.")):
        """
        Add cash to a user.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.", ephemeral=True)
            return

        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        await memberaddcash(self, ctx.guild, member, amount)
        await ctx.respond(f"Added {amount} {lookup['currencyname']} to {member.name}.", ephemeral=True)
    
    @slash_command(guild_ids=[940076462881513482])
    async def balremove(self, ctx, member: Option(discord.Member, "Which member to remove cash from."), amount: Option(int, "How much to remove.")):
        """
        Remove cash from a user.
        """
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.", ephemeral=True)
            return

        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        await memberremovecash(self, ctx.guild, member, amount)
        await ctx.respond(f"Removed {amount} {lookup['currencyname']} from {member.name}.", ephemeral=True)

    @slash_command(guild_ids=[940076462881513482])
    async def give(self, ctx, member: Option(discord.Member, "Which member to give cash to."), amount: Option(int, "How much to give.")):
        """
        Give cash to a user.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        await memberaddcash(self, ctx.guild, member, amount)
        await memberremovecash(self, ctx.guild, ctx.author, amount)
        await ctx.respond(f"Gave {amount} {lookup['currencyname']} to {member.name}.")


    @slash_command(guild_ids=[940076462881513482])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def flipbet(self, ctx, amount: Option(int, "The amount you're betting."), *, bet: Option(str, "Heads or Tails.", autocomplete=discord.utils.basic_autocomplete(("Heads", "Tails")))):
        """
        Flip a coin and get or lose on the outcome.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        bal = await self.bot.db.fetchrow("SELECT * FROM currencyusers WHERE guildid = $1 AND uid = $2", ctx.guild.id, ctx.author.id)
        if bal is None:
            bal = {"guildid": ctx.guild.id, "uid": ctx.author.id, "cash": 0}

        if amount > bal["cash"]:
            await ctx.respond("You don't have enough money to bet that much.", ephemeral=True)
            return

        if amount < 1:
            await ctx.respond("You can't bet a negative amount or 0.", ephemeral=True)
            return

        if not bet.lower() in ("heads", "tails"):
            await ctx.respond("Please enter heads or tails.", ephemeral=True)
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
    
    @slash_command(guild_ids=[940076462881513482])
    async def shop(self, ctx):
        """
        View the shop.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        embed = discord.Embed(title="Shop", description="Here's the shop.\n\nBuy items with `/buy <item>`", color=0x00b2ff)
        shop = await self.bot.db.fetch("SELECT * FROM ccshop WHERE guildid = $1", ctx.guild.id)
        for i in shop:
            embed.add_field(name=f"{i['name']} - {i['price']} {lookup['currencyname']}", value=i["description"] if i["description"] is not None else "No description provided", inline=False)
        if len(shop) == 0:
            embed.description = "There are currently no items in the shop. Ask a moderator to make one."
        await ctx.respond(embed=embed)

    @slash_command(guild_ids=[940076462881513482])
    async def createitem(self, ctx, name: Option(str, "The name of the item."), price: Option(int, "The price of the item."), description: Option(str, "The description of the item.", required=False), reply: Option(str, "What to reply to the user when the user bought this item.", required=False), roletogive: Option(discord.Role, "The role to give to the user when they buy this item.", required=False)):
        """
        Create an item in the shop.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.", ephemeral=True)
            return

        count = await self.bot.db.fetchrow("SELECT COUNT(*) FROM ccshop WHERE guildid = $1", ctx.guild.id)
        if int(count["count"]) >= 25:
            await ctx.respond("You can only have 25 items in the shop.", ephemeral=True)
            return

        await self.bot.db.execute("INSERT INTO ccshop (guildid, name, price, description, reply, roletogive) VALUES ($1, $2, $3, $4, $5, $6)", ctx.guild.id, name, price, description, reply, roletogive.id)
        await ctx.respond(f"Created item `{name}` for {price} {lookup['currencyname']}.", ephemeral=True)

    @slash_command(guild_ids=[940076462881513482])
    async def deleteitem(self, ctx, name: Option(str, "The name of the item.")):
        """
        Delete an item in the shop.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You don't have permission to do that.", ephemeral=True)
            return

        item = await self.bot.db.execute("SELECT name FROM ccshop WHERE guildid = $1 AND name = $2", ctx.guild.id, name)
        if item is None:
            await ctx.respond("That item doesn't exist.", ephemeral=True)
            return
        await self.bot.db.execute("DELETE FROM ccshop WHERE guildid = $1 AND name = $2", ctx.guild.id, name)
        await ctx.respond(f"Deleted item `{name}`.", ephemeral=True)
    
    @slash_command(guild_ids=[940076462881513482])
    async def buy(self, ctx, item: Option(str, "The name of the item to buy.")):
        """
        Buy an item in the shop.
        """
        lookup = await check(self, ctx.author)
        if not lookup:
            await ctx.respond("Hey there! Custom currency isn't ready for this server yet. Contact a server moderator!", ephemeral=True)
            return

        item = await self.bot.db.fetchrow("SELECT * FROM ccshop WHERE guildid = $1 AND name = $2", ctx.guild.id, item)
        if item is None:
            await ctx.respond("That item doesn't exist.", ephemeral=True)
            return

        bal = await getbal(self, ctx.guild, ctx.author)
        if int(bal["cash"]) < int(item["price"]):
            await ctx.respond("You don't have enough money to buy that.", ephemeral=True)
            return

        await memberremovecash(self, ctx.guild, ctx.author, item["price"])

        if item["reply"] is None:
            await ctx.respond(f"You bought `{item['name']}` for {item['price']} {lookup['currencyname']}.")
        else:
            await ctx.respond(item["reply"])

        try:
            await ctx.author.add_roles(ctx.guild.get_role(int(item["roletogive"])))
        except:
            await ctx.respond("Something went wrong while trying to add your role. Please contact a server moderator.", ephemeral=True)

def setup(bot:GoModBot):
    bot.add_cog(Currency(bot))