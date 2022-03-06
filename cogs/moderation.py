import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import asyncio
from bot import GoModBot
from discord.ui import InputText, Modal

class Modal(Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(InputText(label="What is your name?", placeholder="John Doe"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hello, {self.children[0].value}!")

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = self.bot.get_user(payload.user_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        guild = self.bot.get_guild(payload.guild_id)
        if user is None or message is None or channel is None or guild is None:
            return

        member = guild.get_member(user.id)

        if member is None:
            return

        if user.bot:
            return
            
        lookup = await self.bot.db.fetch("SELECT * FROM reactroles WHERE message = $1 AND channel = $2", message.id, message.channel.id)
        if lookup:
            for entry in lookup:
                if str(payload.emoji) == str(entry['reaction']):
                    role = discord.utils.get(guild.roles, id=entry['role'])
                    if role == None:
                        return

                    if role in member.roles:
                        pass
                    else:
                        try:
                            await member.add_roles(role)
                        except discord.Forbidden:
                            embed = discord.Embed(title="Urgent message", description=f"A [reaction role]({message.jump_url}) in your server ({guild.name}) is failing to add roles to members. Please check if the reaction role's role ({role.name}) is below GoMod's role and GoMod is able to add roles.", color=discord.Color.red())
                            await guild.owner.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user = self.bot.get_user(payload.user_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        guild = self.bot.get_guild(payload.guild_id)
        if user is None or message is None or channel is None or guild is None:
            return

        member = guild.get_member(user.id)

        if member is None:
            return

        if user.bot:
            return
            
        lookup = await self.bot.db.fetch("SELECT * FROM reactroles WHERE message = $1 AND channel = $2", message.id, message.channel.id)
        if lookup:
            for entry in lookup:
                if str(payload.emoji) == str(entry['reaction']):
                    role = discord.utils.get(guild.roles, id=entry['role'])
                    if role == None:
                        return

                    if role in member.roles:
                        try:
                            await member.remove_roles(role)
                        except discord.Forbidden:
                            embed = discord.Embed(title="Urgent message", description=f"A [reaction role]({message.jump_url}) in your server ({guild.name}) is failing to remove roles from members. Please check if the reaction role's role ({role.name}) is below GoMod's role and GoMod is able to remove roles.", color=discord.Color.red())
                            await guild.owner.send(embed=embed)
        

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        lookup = await self.bot.db.fetchrow("SELECT * FROM reactroles WHERE message = $1 AND channel = $2", message.id, message.channel.id)
        if lookup:
            await self.bot.db.execute("DELETE FROM reactroles WHERE message = $1 AND channel = $2", message.id, message.channel.id)
    

    # @commands.command()
    # async def modaltest(self, ctx):
    #     class MyView(discord.ui.View):
    #         @discord.ui.button(label="Tell GoMod your name.", style=discord.ButtonStyle.primary)
    #         async def button_callback(self, button, interaction):
    #             modal = Modal(title="Greetings.")
    #             await interaction.response.send_modal(modal)

    #     view = MyView()
    #     await ctx.send("Hello! I am GoMod.", view=view)

    @slash_command()
    async def kick(self, ctx, member: Option(discord.Member, "Member to kick"), reason: Option(str, "Reason for kicking", required=False)):
        """
        Kick a member from the server.
        """
        if not ctx.author.guild_permissions.kick_members:
            await ctx.respond("You do not have permission to kick members.")
            return
        if member == ctx.author:
            await ctx.respond("You cannot kick yourself.", delete_after=3)
            return
        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot kick members with a higher role than you.", delete_after=3)
            return
        try:
            embed = discord.Embed(title=f"Kicked from {ctx.guild.name}", description=f"You have been kicked from {ctx.guild.name} by {ctx.author.name} with reason: {reason}", color=discord.Color.red())
            await member.send(embed=embed)
        except:
            pass
        await ctx.guild.kick(member, reason=reason)
        embed = discord.Embed(title="Kicked", description=f"{member.mention} has been kicked from {ctx.guild.name} with reason: {reason}", color=0x00b2ff)
        await ctx.respond(embed=embed)

    @slash_command()
    async def ban(self, ctx, member: Option(discord.Member, "Member to ban"), reason: Option(str, "Reason for banning", required=False)):
        """
        Bans a member from the server.
        """
        if not ctx.author.guild_permissions.ban_members:
            await ctx.respond("You do not have the ban members permission.", delete_after=3)
            return

        if member == ctx.author:
            await ctx.respond("You cannot ban yourself.", delete_after=3)
            return

        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot ban members with a higher role than you.", delete_after=3)
            return
        try:
            embed = discord.Embed(title=f"Banned from {ctx.guild.name}", description=f"You have been banned from {ctx.guild.name} by {ctx.author.name} with reason: {reason}", color=discord.Color.red())
            await member.send(embed=embed)
        except:
            pass
        await ctx.guild.ban(member, reason=reason)
        embed = discord.Embed(title="Banned", description=f"{member.mention} has been banned from {ctx.guild.name} with reason: {reason}", color=0x00b2ff)
        await ctx.respond(embed=embed)

    @slash_command()
    async def block(self, ctx, member: discord.Member):
        """
        Blocks a member from the current channel.
        """
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.respond("You do not have the manage roles permission.", delete_after=3)
            return
        if member == ctx.author:
            await ctx.respond("You cannot block yourself.", delete_after=3)
            return
        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot block members with a higher role than you.", delete_after=3)
            return
        await ctx.channel.set_permissions(member, add_reactions = False, send_messages = False)
        embed = discord.Embed(title="Blocked", description=f"{member.mention} has been blocked from {ctx.channel.mention}", color=0x00b2ff)
        await ctx.respond(embed=embed)

    # @commands.command()
    # @commands.has_guild_permissions(manage_messages=True, manage_channels=True)
    # async def unblock(self, ctx, member: discord.Member):
    #     if member == ctx.author:
    #         await ctx.send("You cannot unblock yourself.", delete_after=3)
    #         return
    #     if member.top_role >= ctx.author.top_role:
    #         await ctx.send("You cannot unblock members with a higher role than you.", delete_after=3)
    #         return
    #     await ctx.channel.set_permissions(member, add_reactions = True, send_messages = True)
    #     embed = discord.Embed(title="Unblocked", description=f"{member.mention} has been unblocked from {ctx.channel.mention}", color=0x00b2ff)
    #     await ctx.send(embed=embed)

    @slash_command()
    async def unblock(self, ctx, member: Option(discord.Member, "Member to unblock")):
        """
        Unblocks a member from the current channel.
        """
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.respond("You do not have the manage roles permission.", delete_after=3)
            return

        if member == ctx.author:
            await ctx.respond("You cannot unblock yourself.", delete_after=3)
            return

        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot unblock members with a higher role than you.", delete_after=3)
            return
        await ctx.channel.set_permissions(member, add_reactions = True, send_messages = True)
        embed = discord.Embed(title="Unblocked", description=f"{member.mention} has been unblocked from {ctx.channel.mention}", color=0x00b2ff)
        await ctx.respond(embed=embed)
    

    @slash_command()
    async def warn(self, ctx, member: Option(discord.Member, "Member to warn"), reason: Option(str, "Reason for warning", required=False)):
        """
        Warns a member.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.respond("You do not have the manage messages permission.", delete_after=3)
            return
        if member == ctx.author:
            await ctx.respond("You cannot warn yourself.", delete_after=3)
            return
        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot warn members with a higher role than you.", delete_after=3)
            return
        try:
            embed = discord.Embed(title=f"Warned", description=f"You have been warned from {ctx.guild.name} by {ctx.author.name} with reason: {reason}", color=discord.Color.orange())
            await member.send(embed=embed)
        except:
            pass
        if reason == None:
            await self.bot.db.execute("INSERT INTO warns VALUES ($1, $2, $3, $4)", member.id, ctx.guild.id, ctx.author.id, "No reason given.")
            reason = "no reason"
        else:
            await self.bot.db.execute("INSERT INTO warns VALUES ($1, $2, $3, $4)", member.id, ctx.guild.id, ctx.author.id, reason)

        embed = discord.Embed(title="Warned", description=f"{member.mention} has been warned by {ctx.author.mention} for {reason}", color=0x00b2ff)
        await ctx.respond(embed=embed)

    @slash_command()
    async def clearwarns(self, ctx, member: Option(discord.Member, "Member to clear warnings for")):
        """
        Clears all warnings for a member.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.respond("You do not have the manage messages permission.", delete_after=3)
            return
        if member == ctx.author:
            await ctx.respond("You cannot clear your own warnings.", delete_after=3)
            return
        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot clear warnings of members with a higher role than you.", delete_after=3)
            return
        await self.bot.db.execute("DELETE FROM warns WHERE userid = $1 AND serverid = $2", member.id, ctx.guild.id)
        embed = discord.Embed(title="Warns cleared", description=f"{member.mention}'s warnings have been cleared.", color=0x00b2ff)
        await ctx.respond(embed=embed)

    @slash_command()
    async def purge(self, ctx, amount: Option(int, "Amount of messages to delete", min_value=1, max_value=1000)):
        """
        Purges a specified amount of messages from the current channel.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.respond("You do not have the manage messages permission.", delete_after=3)
            return
        await ctx.channel.purge(limit=amount+1)
        embed = discord.Embed(title="Messages purged", description=f"{amount} messages have been purged.", color=0x00b2ff)
        await ctx.send(embed=embed, delete_after=3)

    @slash_command()
    async def warns(self, ctx, member: Option(discord.Member, "Member to view warnings for")):
        """
        Lists all the warns a member has.
        """
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.respond("You do not have the manage messages permission.", delete_after=3)
            return
        if member == ctx.author:
            await ctx.respond("You cannot view your own warnings.", delete_after=3)
            return
        if len(member.roles) > 0 and member.top_role >= ctx.author.top_role:
            await ctx.respond("You cannot view warnings of members with a higher role than you.", delete_after=3)
            return
        warns = await self.bot.db.fetch("SELECT * FROM warns WHERE userid = $1 AND serverid = $2", member.id, ctx.guild.id)
        if warns == []:
            embed = discord.Embed(title="No warns", description=f"{member.mention} has no warns.", color=0x00b2ff)
            await ctx.respond(embed=embed)
            return
        embed = discord.Embed(title="Warns", description=f"{member.mention} has {len(warns)} warns.", color=0x00b2ff)
        for warn in warns:
            embed.add_field(name=f"{warn['reason']}", value=f"Warned by {ctx.guild.get_member(warn['invokerid']).mention}", inline=False)
        await ctx.respond(embed=embed)

    @slash_command()
    async def reactrole(self, ctx, channel: Option(discord.TextChannel, "The channel the message is in"), message: Option(str, "The message that will have the reaction in ID form."), emoji: Option(str, "The emoji to react with"), role: Option(discord.Role, "The role to give to the user")):
        """
        Run a reaction role setup.
        """
        if not ctx.author.guild_permissions.manage_roles or not ctx.author.guild_permissions.manage_messages:
            await ctx.respond("You do not have the manage roles or manage messages permission.", delete_after=3)
            return

        try:
            id = int(message)
        except:
            await ctx.respond("The message ID must be an integer.", delete_after=3)
            return
        try:
            messageobj = await channel.fetch_message(id)
        except Exception as e:
            await ctx.respond("The message ID is invalid.", delete_after=3)
            print(e)
            return

        await self.bot.db.execute("INSERT INTO reactroles VALUES ($1, $2, $3, $4)", messageobj.id, channel.id, role.id, emoji)
        reaction = await messageobj.add_reaction(emoji)
        embed = discord.Embed(title="Reaction role setup", description="Reaction role setup complete.", color=0x00b2ff)
        await ctx.respond(embed=embed)

    # @commands.command()
    # @commands.has_guild_permissions(manage_messages=True)
    # async def reactrole(self, ctx):
    #     embed = discord.Embed(title="Reaction role setup", description="1/4\nWhat channel is the message you're using is in? (Do NOT mention the channel. Instead, use the name.\nStuck? Read our [wiki](https://github.com/Joystickplays/GoMod/wiki/Verification-systems).", color=0x00b2ff)
    #     msg = await ctx.send(embed=embed)

    #     def check(m):
    #         return m.channel == ctx.channel and m.author == ctx.author

    #     while True:
    #         try:
    #             msg = await self.bot.wait_for('message', check=check, timeout=60)
    #         except asyncio.TimeoutError:
    #             await ctx.send("Timed out.", delete_after=3)
    #             return

    #         if msg.content.lower() == "cancel":
    #             await ctx.send("Cancelled.", delete_after=3)
    #             return

    #         channelcheck = msg.content.replace(" ", "-")
    #         channelcheck2 = channelcheck.lower()
    #         channel = discord.utils.get(ctx.guild.text_channels, name=channelcheck2)
    #         if channel != None:
    #             break
                
    #         await ctx.send("That channel doesn't exist. Try again...", delete_after=3)
        
    #     embed = discord.Embed(title="Reaction role setup", description="2/4\nWhat is your message's ID? More on getting message IDs [here](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-). You can also say \"create one\" to make GoMod create a message for you.", color=0x00b2ff)
    #     msg = await ctx.send(embed=embed)

    #     while True:
    #         try:
    #             msg = await self.bot.wait_for('message', check=check, timeout=60)   
    #         except asyncio.TimeoutError:
    #             await ctx.send("Timed out.", delete_after=3)
    #             return

    #         if msg.content.lower() == "cancel":
    #             await ctx.send("Cancelled.", delete_after=3)
    #             return

    #         message = None

    #         if msg.content.lower() == "create one":
    #             embed = discord.Embed(title="Reaction role setup", description="3.5/4\nWhat will be the title of the message?", color=0x00b2ff)
    #             msg = await ctx.send(embed=embed)

    #             try:
    #                 title = await self.bot.wait_for('message', check=check, timeout=60)
    #             except asyncio.TimeoutError:
    #                 await ctx.send("Timed out.", delete_after=3)
    #                 return

    #             if title.content.lower() == "cancel":
    #                 await ctx.send("Cancelled.", delete_after=3)
    #                 return
                
    #             embed = discord.Embed(title="Reaction role setup", description="3.5/4\nWhat will be the description of the message?", color=0x00b2ff)
    #             msg = await ctx.send(embed=embed)

    #             try:
    #                 description = await self.bot.wait_for('message', check=check, timeout=60)
    #             except asyncio.TimeoutError:
    #                 await ctx.send("Timed out.", delete_after=3)
    #                 return

    #             if description.content.lower() == "cancel":
    #                 await ctx.send("Cancelled.", delete_after=3)
    #                 return

    #             embed = discord.Embed(title=title.content, description=description.content, color=0x00b2ff)
    #             message = await channel.send(embed=embed)
    #             break

                
    #         if message == None:
    #             try:
    #                 message = await channel.fetch_message(int(msg.content))
    #                 break
    #             except:
    #                 await ctx.send("That message doesn't exist. Try again...", delete_after=3)

    #     while True:
    #         embed = discord.Embed(title="Reaction role setup", description="3/4\nWhat will be the emoji for your reaction?", color=0x00b2ff)
    #         msg = await ctx.send(embed=embed)

    #         try:
    #             msg = await self.bot.wait_for('message', check=check, timeout=60)
    #         except asyncio.TimeoutError:
    #             await ctx.send("Timed out.", delete_after=3)
    #             return

    #         if msg.content.lower() == "cancel":
    #             await ctx.send("Cancelled.", delete_after=3)
    #             return


    #         reactionname = msg.content
    #         try:
    #             reaction = await message.add_reaction(msg.content)
    #             break
    #         except:
    #             await ctx.send("That emoji is invalid. Try again...", delete_after=3)

    #     while True:
    #         embed = discord.Embed(title="Reaction role setup", description="4/4\nWhat role will be given to the user when they react? (Do NOT mention the role. Instead, use the name.", color=0x00b2ff)
    #         msg = await ctx.send(embed=embed)

    #         try:
    #             msg = await self.bot.wait_for('message', check=check, timeout=60)
    #         except asyncio.TimeoutError:
    #             await ctx.send("Timed out.", delete_after=3)
    #             return

    #         if msg.content.lower() == "cancel":
    #             await ctx.send("Cancelled.", delete_after=3)
    #             return

    #         role = discord.utils.get(ctx.guild.roles, name=msg.content)
    #         if role != None:
    #             break

    #         await ctx.send("That role doesn't exist. Try again...", delete_after=3)

    #     await self.bot.db.execute("INSERT INTO reactroles VALUES ($1, $2, $3, $4)", message.id, channel.id, role.id, reactionname)
    #     embed = discord.Embed(title="Reaction role setup", description="Reaction role setup complete.", color=0x00b2ff)
    #     await ctx.send(embed=embed)

    # @commands.command()
    # async def qasetup(self, ctx):
    #     lookup = await self.bot.db.fetchrow("SELECT * FROM qas WHERE guild = $1", ctx.guild.id)
    #     if lookup != None:
    #         embed = discord.Embed(title="Error", description="Question and answer are limited to one per server. If you want to change the question and answer, please delete the current one and run this command again.", color=0x00b2ff)
    #         await ctx.send(embed=embed)

        




def setup(bot:GoModBot):
    bot.add_cog(Moderation(bot))