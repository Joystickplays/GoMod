import discord
from discord.ext import commands
import asyncio
from bot import GoModBot
from discord.ui import InputText, Modal

class Modal(Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(InputText(label="What is your name?", placeholder="John Doe"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hello, {self.children[0].value}!")

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True, manage_messages=True)
    async def ticketsetup(self, ctx):
        class ChannelSelection(discord.ui.Select):
            def __init__(self):
                options = []
                for channel in ctx.guild.text_channels:
                    options.append(label=channel.name, description=f"Use {channel.name} as an entry.")

                super().__init__(
                    placeholder="Choose a channel.",
                    min_values=1,
                    max_values=1,
                    options=options,
                )

            async def callback(self, interaction: discord.Interaction):
                self.channelpicked = self.values[0]


        class ChannelView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = None
                self.add_item(ChannelSelection())

            async def callback(self, interaction: discord.Interaction):
                self.value = self.children[0].channelpicked
                self.stop()

        embed = discord.Embed(title="Ticket Setup", description="Welcome to the ticket setup.\n\nLet's start with something simple. Which channel can the users make their ticket?", color=0x00b2ff)
        view = ChannelView()
        await ctx.send(embed=embed, view=view)
        await view.wait()
        await ctx.send(f"You chose {view.value} as your entry channel.")



def setup(bot:GoModBot):
    bot.add_cog(Tickets(bot))