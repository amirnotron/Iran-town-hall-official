"""
Utility Commands Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils import create_embed


class UtilityCommands(commands.Cog):
    """Utility and information commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✓ Utility commands loaded successfully")
    
    @app_commands.command(name="ping", description="Check bot's latency")
    async def ping(self, interaction: discord.Interaction):
        """Check bot ping"""
        latency_ms = round(self.bot.latency * 1000)
        
        embed = create_embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency_ms}ms**",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Get user information")
    @app_commands.describe(member="Member to check (defaults to you)")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Get detailed user information"""
        if member is None:
            member = interaction.user
        
        if isinstance(member, discord.User) and interaction.guild:
            try:
                member = await interaction.guild.fetch_member(member.id)
            except discord.NotFound:
                embed = create_embed(
                    description="Could not find that member in this server.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Get user permissions
        permissions = []
        if isinstance(member, discord.Member):
            permissions = [
                perm[0].replace('_', ' ').title()
                for perm in member.guild_permissions
                if perm[1] and perm[0] not in ['read_messages', 'send_messages', 'read_message_history']
            ]
        
        # Get roles
        if isinstance(member, discord.Member):
            roles = sorted(
                [role.mention for role in member.roles if role.name != "@everyone"],
                key=lambda r: member.guild.get_role(int(r.strip('<@&>'))).position,
                reverse=True
            )
        else:
            roles = []
        
        embed = discord.Embed(title=f"User Info: {member.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Username", value=member.name, inline=True)
        
        if isinstance(member, discord.Member):
            embed.add_field(name="Display Name", value=member.display_name, inline=True)
            embed.add_field(name="Bot?", value="Yes" if member.bot else "No", inline=True)
            embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "F"), inline=False)
            embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, "F"), inline=False)
            
            if member.top_role:
                embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
            
            if roles:
                embed.add_field(name="Roles", value=", ".join(roles), inline=False)
            
            if permissions:
                perms_str = ", ".join(permissions)
                if len(perms_str) > 1024:
                    embed.add_field(name="Key Permissions", value="Too many to list", inline=False)
                else:
                    embed.add_field(name="Key Permissions", value=perms_str, inline=False)
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    @app_commands.command(name="serverinfo", description="Get server information")
    async def serverinfo(self, interaction: discord.Interaction):
        """Get server information"""
        guild = interaction.guild
        
        # Count members
        member_count = guild.member_count
        bot_count = sum(1 for m in guild.members if m.bot)
        human_count = member_count - bot_count
        
        # Count channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Count roles
        role_count = len(guild.roles)
        
        embed = discord.Embed(
            title=f"{guild.name} Server Info",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="Server ID", value=guild.id, inline=False)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "F"), inline=True)
        
        embed.add_field(name="Members", value=f"**{member_count}** total\n{human_count} humans, {bot_count} bots", inline=False)
        embed.add_field(
            name="Channels",
            value=f"**{text_channels + voice_channels}** total\n{text_channels} text, {voice_channels} voice, {categories} categories",
            inline=False
        )
        embed.add_field(name="Roles", value=str(role_count), inline=True)
        
        if guild.verification_level:
            embed.add_field(name="Verification Level", value=str(guild.verification_level).title(), inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="clear", description="Clear messages from channel")
    @app_commands.describe(amount="Number of messages to delete (1-500)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 500]):
        """Clear messages"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = create_embed(
                title="Messages Cleared",
                description=f"Successfully deleted **{len(deleted)}** messages.",
                color=discord.Color.green(),
                footer_text=f"Cleared by {interaction.user.display_name}",
                footer_icon=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = create_embed(
                description="I don't have permission to delete messages.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = create_embed(
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="avatar", description="Show a user's avatar")
    @app_commands.describe(member="Member to show avatar for (defaults to you)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        # If a plain User was supplied in a guild context, try to fetch the Member
        if isinstance(member, discord.User) and interaction.guild:
            try:
                member = await interaction.guild.fetch_member(member.id)
            except discord.NotFound:
                embed = create_embed(
                    description="Could not find that member in this server.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="invite", description="Get the bot invite link")
    async def invite(self, interaction: discord.Interaction):
        client_id = getattr(self.bot.user, "id", None)
        if not client_id:
            embed = create_embed(
                description="Bot client ID is not available.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        url = f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot%20applications.commands"
        embed = create_embed(
            title="Invite Me",
            description=f"[Click here to invite the bot]({url})",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="botinfo", description="Basic bot information")
    async def botinfo(self, interaction: discord.Interaction):
        owners = ", ".join(str(u) for u in getattr(self.bot, "owners", []) ) if getattr(self.bot, "owners", None) else "Unknown"
        shard_info = f"Shard: {self.bot.shard_count}" if getattr(self.bot, "shard_count", None) else "No sharding"
        embed = discord.Embed(title="Bot Information", color=discord.Color.blue())
        embed.add_field(name="Username", value=str(self.bot.user), inline=True)
        embed.add_field(name="ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Owners", value=owners, inline=False)
        embed.add_field(name="Sharding", value=shard_info, inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=False)



    @app_commands.command(name="payment", description="ارسال درگاه و شماره کارت نوترون")
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def payment(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"**قابلی نداره🌹 \n 6219-8618-6542-1167 - سحر اقاجانی مسعودی** \n https://www.coffeebede.com/notron")



    @app_commands.command(name="setactivity", description="Set bot's activity")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(activity_type="Type of activity (playing, streaming, listening, watching)")
    @app_commands.describe(activity_name="Activity name")
    async def set_bot_activity(self, interaction: discord.Interaction, activity_type: str, activity_name: str):
        valid_types = ["playing", "streaming", "listening", "watching"]

        if activity_type.lower() not in valid_types:
            await interaction.response.send_message("**playing, listening, watching**", ephemeral=True)
            return

        activity_type = activity_type.lower()


        if activity_type == "playing":
            activity = discord.Game(name=activity_name)
        elif activity_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=activity_name)
        elif activity_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)
        elif activity_type == "streaming":
            activity = discord.Streaming(name=activity_name, url="https://twitch.tv/amirnotron_")
        else:
            activity = discord.Activity(type=discord.ActivityType.playing, name=activity_name)

        await self.bot.change_presence(activity=activity)

        title = "Bot Status changed"
        description = f"{activity_type} {activity_name}"

        embed = discord.Embed(title=title, description=description)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cleanactivity", description="Clear status")
    @app_commands.checks.has_permissions(administrator=True)
    async def clean_bot_activity(self, interaction: discord.Interaction):


        await self.bot.change_presence(activity=None)

        title = "Bot Status cleaned"

        embed = discord.Embed(title=title)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCommands(bot))
