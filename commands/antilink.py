"""
Anti-Link System Cog
Prevents users from posting links and Discord invites
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import re
import json
from utils import create_embed


def get_config():
    """Load configuration"""
    with open("config/settings.json", "r") as f:
        return json.load(f)


class AntiLink(commands.Cog):
    """Anti-link system for preventing links and Discord invites"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = get_config()
        self.antilink_config = self.config['features'].get('antilink', {})
        
        # Discord invite patterns
        self.discord_invite_patterns = [
            r'discord\.gg/[\w]+',
            r'discord\.com/invite/[\w]+',
            r'discordapp\.com/invite/[\w]+',
            r'https?://(?:www\.)?(?:discord\.gg|discordapp\.com/invite|discord\.com/invite)/[\w]+'
        ]
        
        self.blocked_domains = self.antilink_config.get('blocked_domains', [
            'discord.gg',
            'discordapp.com',
            'discord.com/invite'
        ])
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✓ Anti-link system loaded successfully")
    
    def is_link(self, message_content: str) -> str | None:
        """
        Check if message contains links
        
        Returns:
            Type of link found or None
        """
        # Check for Discord invites first
        for pattern in self.discord_invite_patterns:
            if re.search(pattern, message_content, re.IGNORECASE):
                return "discord_invite"
        
        # Check for other links
        if re.search(r'https?://[\w\-\.]+', message_content, re.IGNORECASE):
            return "link"
        
        return None
    
    def is_whitelisted(self, member: discord.Member) -> bool:
        """
        Check if user has whitelist role
        
        Returns:
            True if user is whitelisted
        """
        whitelist_role_ids = self.antilink_config.get('whitelist_role_ids', [])
        
        if not whitelist_role_ids:
            return False
        
        return any(role.id in whitelist_role_ids for role in member.roles)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detect and handle links in messages"""
        # Don't process bot messages or DMs
        if message.author.bot or not message.guild:
            return
        
        # Skip if anti-link is disabled
        if not self.antilink_config.get('enabled', True):
            return
        
        # Skip if user is whitelisted
        if isinstance(message.author, discord.Member) and self.is_whitelisted(message.author):
            return
        
        # Skip if user is admin or has manage messages
        if isinstance(message.author, discord.Member):
            if message.author.guild_permissions.administrator:
                return
        
        # Check for links
        link_type = self.is_link(message.content)
        
        if not link_type:
            return
        
        try:
            # Delete the message
            if self.antilink_config.get('delete_message', True):
                await message.delete()
            
            # Timeout the user
            timeout_minutes = self.antilink_config.get('timeout_minutes', 5)
            timeout_duration = timedelta(minutes=timeout_minutes)
            
            await message.author.timeout(
                timeout_duration,
                reason=f"Posted {link_type.replace('_', ' ')}"
            )
            
            # Send warning DM
            if link_type == "discord_invite":
                warning_text = (
                    f"⚠️ **Discord Invite Link Detected**\n\n"
                    f"You've been timed out for {timeout_minutes} minutes for posting a Discord invite link.\n"
                    f"Discord invite links are not allowed in {message.guild.name}.\n\n"
                    f"If you believe this is a mistake, please contact a moderator."
                )
            else:
                warning_text = (
                    f"⚠️ **Link Detected**\n\n"
                    f"You've been timed out for {timeout_minutes} minutes for posting a link.\n"
                    f"Links are not allowed in {message.guild.name}.\n\n"
                    f"If you believe this is a mistake, please contact a moderator."
                )
            
            try:
                await message.author.send(warning_text)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Log to channel
            log_channel = None
            try:
                # Try to find a mod-log or logs channel
                for channel in message.guild.text_channels:
                    if 'log' in channel.name or 'mod' in channel.name:
                        log_channel = channel
                        break
                
                if log_channel and log_channel.permissions_for(message.guild.me).send_messages:
                    embed = create_embed(
                        title="🔗 Link Detected",
                        description=f"**User:** {message.author.mention}\n**Action:** Timed out for {timeout_minutes} minutes\n**Reason:** Posted {link_type.replace('_', ' ')}",
                        color=discord.Color.orange()
                    )
                    await log_channel.send(embed=embed)
            except Exception as e:
                print(f"Error logging link detection: {e}")
        
        except discord.Forbidden:
            print(f"Could not timeout user {message.author} - insufficient permissions")
        except Exception as e:
            print(f"Error handling link message: {e}")
    
    @app_commands.command(name="antilink_whitelist_add", description="Add a role to anti-link whitelist")
    @app_commands.describe(role="Role to whitelist")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_add(self, interaction: discord.Interaction, role: discord.Role):
        """Add role to anti-link whitelist"""
        with open("config/settings.json", "r") as f:
            config = json.load(f)
        
        whitelist = config['features']['antilink'].get('whitelist_role_ids', [])
        
        if role.id in whitelist:
            embed = create_embed(
                description=f"❌ {role.mention} is already whitelisted.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        whitelist.append(role.id)
        config['features']['antilink']['whitelist_role_ids'] = whitelist
        
        with open("config/settings.json", "w") as f:
            json.dump(config, f, indent=2)
        
        embed = create_embed(
            description=f"✅ {role.mention} has been added to anti-link whitelist.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="antilink_whitelist_remove", description="Remove a role from anti-link whitelist")
    @app_commands.describe(role="Role to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_remove(self, interaction: discord.Interaction, role: discord.Role):
        """Remove role from anti-link whitelist"""
        with open("config/settings.json", "r") as f:
            config = json.load(f)
        
        whitelist = config['features']['antilink'].get('whitelist_role_ids', [])
        
        if role.id not in whitelist:
            embed = create_embed(
                description=f"❌ {role.mention} is not in the whitelist.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        whitelist.remove(role.id)
        config['features']['antilink']['whitelist_role_ids'] = whitelist
        
        with open("config/settings.json", "w") as f:
            json.dump(config, f, indent=2)
        
        embed = create_embed(
            description=f"✅ {role.mention} has been removed from anti-link whitelist.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="antilink_list", description="List whitelisted roles")
    @app_commands.checks.has_permissions(administrator=True)
    async def whitelist_list(self, interaction: discord.Interaction):
        """List whitelisted roles"""
        whitelist = self.antilink_config.get('whitelist_role_ids', [])
        
        if not whitelist:
            embed = create_embed(
                description="No roles are whitelisted for anti-link.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        role_mentions = []
        for role_id in whitelist:
            role = interaction.guild.get_role(role_id)
            if role:
                role_mentions.append(f"• {role.mention}")
        
        embed = create_embed(
            title="Whitelisted Roles (Anti-Link)",
            description="\n".join(role_mentions) if role_mentions else "No valid roles found",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiLink(bot))
