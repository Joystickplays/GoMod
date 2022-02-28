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

    @discord.ui.button(label='ModRep', style=discord.ButtonStyle.gray)
    async def modrep(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.ctx.author != interaction.user:
            await interaction.response.send_message("You can't do this, sorry.", ephemeral=True)
            return

        self.value = "mr"
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

# class SingleConfirm(discord.ui.View):
#     def __init__(self, bot, ): 
#         super().__init__()
#         self.value = None
#         self.bot = bot
