import discord

class Caseactionsview(discord.ui.View): 
    def __init__(self, ctx): 
        super().__init__()
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='Ban', style=discord.ButtonStyle.red)
    async def ban(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "b"
        self.stop()

    @discord.ui.button(label='Kick', style=discord.ButtonStyle.red)
    async def kick(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "k"
        self.stop()

    @discord.ui.button(label='Delete', style=discord.ButtonStyle.green)
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "d"
        self.stop()

    @discord.ui.button(label='Ignore', style=discord.ButtonStyle.gray)
    async def ignore(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "i"
        self.stop()

class Helpview(discord.ui.View): 
    def __init__(self, ctx): 
        super().__init__()
        self.value = None
        self.ctx = ctx
        self.timeout = 60

    @discord.ui.button(label='Moderator', style=discord.ButtonStyle.gray)
    async def mod(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "m"
        self.stop()

    @discord.ui.button(label='AiMod [BETA]', style=discord.ButtonStyle.gray)
    async def ai(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "a"
        self.stop()

    @discord.ui.button(label='Server backups', style=discord.ButtonStyle.gray, disabled=True)
    async def server(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "s"
        self.stop()

    @discord.ui.button(label='Logging', style=discord.ButtonStyle.gray)
    async def log(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "l"
        self.stop()

    @discord.ui.button(label='Others', style=discord.ButtonStyle.gray)
    async def other(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "o"
        self.stop()
        

    @discord.ui.button(label='Exit', style=discord.ButtonStyle.gray)
    async def ex(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "x"
        self.stop()