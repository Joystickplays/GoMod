import discord
from discord.ext import commands
import asyncio
from bot import GoModBot
from discord.ui import InputText, Modal

class Modal(Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(InputText(label="Give a reason for your ticket.", placeholder="I am creating this ticket because..."))

    async def callback(self, interaction: discord.Interaction):
        CreateTicket(self, interaction.message.guild, self.children[0].value, interaction.user)

class NotRequiredModal(Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(InputText(label="Give a reason for your ticket.", placeholder="I am creating this ticket because..."), required=False)

    async def callback(self, interaction: discord.Interaction):
        CreateTicket(self, interaction.message.guild, self.children[0].value, interaction.user)

class CreateTicket(discord.ui.View):
    def __init__(self, bot): 
        super().__init__(timeout=None)
        self.value = None
        self.bot = bot

    @discord.ui.button(label='Create ticket', style=discord.ButtonStyle.green, custom_id="gomod:create_ticket")
    async def create(self, button: discord.ui.Button, interaction: discord.Interaction):
        lookup = await self.bot.db.fetchrow("SELECT * FROM tickets WHERE userid = $1 AND guild = $2", interaction.user.id, interaction.message.guild.id)
        if lookup != None:
            embed = discord.Embed(title="Ticket", description=f"You already have a ticket open.", color=0x00b2ff)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if lookup["needreason"] == "t":
            modal = Modal(title="Create ticket")
        else:
            modal = NotRequiredModal(title="Create ticket")
        await interaction.response.send_modal(modal)

async def createticket(self, guild, reason, user):
    guildconfig = await self.bot.db.fetchrow("SELECT * FROM ticketconfigs WHERE guild = $1", guild.id)
    if guildconfig is None:
        return
    
    try:
        category = self.bot.get_channel(guildconfig["category"])
    except:
        return

    embed = discord.Embed(title="Ticket", description=f"{user.mention}, has made a ticket with {reason}.\n\nPlease wait for a staff member to respond.", color=0x00b2ff)
    embed.set_footer(text=f"Ticket ID: {user.id}")

    channel = await guild.create_text_channel(f"ticket-{user.id}", category=category, topic=reason, reason="Creating ticket")
    await channel.send(embed=embed)


    

async def ticket(self, channel):
    embed = discord.Embed(title="Create a ticket", description="Create a ticket by clicking the button below.")
    await channel.send(embed=embed, view=CreateTicket(self.bot))


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True, manage_messages=True)
    async def ticketsetup(self, ctx):
        lookup = await self.bot.db.fetchrow("SELECT * FROM ticketconfigs WHERE guild = $1", ctx.guild.id)
        if lookup:
            await ctx.send("Ticketing is already setup. To remove it, use `--ticketremove.")
            return

        embed = discord.Embed(title="Ticket Setup", description="Welcome to the ticket setup.\n\nSay \"cancel\" at any point to stop setup. Let's start with something simple.\n\nWhich channel can the users make their ticket?\n(Do NOT mention the channel. Instead, use their name.)", color=0x00b2ff)
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Cancelling the setup.")
            return

        if msg.content.lower() == "cancel":
            await ctx.send("Cancelling the setup.")
            return

        channel = None
        while channel == None:
            channelcheck = msg.content.replace(" ", "-")
            channelcheck2 = channelcheck.lower()
            channel = discord.utils.get(ctx.guild.text_channels, name=channelcheck2)
            if channel == None:
                await ctx.send("That channel doesn't exist. Try again...", delete_after=3)
                return

        embed = discord.Embed(title="Ticket Setup", description="Great! Now, will a reason for every ticket needed? (y/yes, n/no)", color=0x00b2ff)
        await ctx.send(embed=embed)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Cancelling the setup.")
            return

        if msg.content.lower() == "cancel":
            await ctx.send("Cancelling the setup.")
            return

        if msg.content.lower() == "y" or msg.content.lower() == "yes":
            needreason = True

        if msg.content.lower() == "n" or msg.content.lower() == "no":
            needreason = False

        embed = discord.Embed(title="Ticket Setup", description="Looking good! Last but not least, we need a place for the tickets. \n\nEnter a category name where the tickets should be. \n(Do NOT use a category that's not private. Otherwise, other people will message inside the tickets.", color=0x00b2ff)
        await ctx.send(embed=embed)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Cancelling the setup.")
            return

        if msg.content.lower() == "cancel":
            await ctx.send("Cancelling the setup.")
            return

        category = None
        while category == None:
            category = discord.utils.get(ctx.guild.categories, name=msg.content)
            if category == None:
                await ctx.send("That category doesn't exist (Look for upper/lowercase mistakes). Try again...", delete_after=3)
                return

        await self.bot.db.execute("INSERT INTO ticketconfigs (guild, channel, needreason, category) VALUES ($1, $2, $3, $4)", ctx.guild.id, channel.id, needreason, category.id)
        await ticket(self, channel)
        await ctx.send("Setup complete! Your members now may create tickets.")

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True, manage_messages=True)
    async def ticketremove(self, ctx):
        class AreYouSure(discord.ui.View):
            def __init__(self, ctx, bot):
                super().__init__()
                self.value = None
                self.ctx = ctx
                self.bot = bot

            @discord.ui.button(label='Yes', style=discord.ButtonStyle.red)
            async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    return

                lookup = await self.bot.db.fetchrow("SELECT * FROM ticketconfigs WHERE guild = $1", ctx.guild.id)
                if lookup == None:
                    await interaction.response.send_message("Ticketing is not setup. To setup, use `--ticketsetup`.")
                    return

                await self.bot.db.execute("DELETE FROM ticketconfigs WHERE guild = $1", ctx.guild.id)
                await interaction.response.send_message("Ticketing has been removed.")

            @discord.ui.button(label='No', style=discord.ButtonStyle.green)
            async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
                await interaction.response.send_message("Cancelling the setup.")

        await ctx.send("Are you sure you want to remove ticketing in your server?", view=AreYouSure(ctx, self.bot))


def setup(bot:GoModBot):
    bot.add_cog(Tickets(bot))