"""
Member Events - Join/Leave handlers
"""
import discord
from discord.ext import commands
from discord.ext.commands import Cog
import json
from utils import create_embed


def get_config():
    """Load configuration"""
    with open("config/settings.json", "r") as f:
        return json.load(f)


class MemberEvents(Cog):
    """Handle member join and leave events"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = get_config()
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join"""
        # Get member role from config
        member_role_id = self.config['roles'].get('member_role_id')
        
        if member_role_id:
            member_role = member.guild.get_role(member_role_id)
            if member_role:
                try:
                    await member.add_roles(member_role)
                    print(f"✓ Gave {member} the member role")
                except discord.Forbidden:
                    print(f"✗ Could not give member role to {member}")
        
        # Send welcome message
        welcome_config = self.config['features']['welcome_message']
        if welcome_config.get('enabled'):
            welcome_channel_id = self.config['channels'].get('welcome_channel_id')
            if welcome_channel_id:
                channel = self.bot.get_channel(welcome_channel_id)
                if channel:
                    try:
                        embed = create_embed(
                            title=f"Welcome {member.name}!",
                            description=f"We're glad to have you in {member.guild.name}!",
                            color=discord.Color.blue(),
                            thumbnail_url=member.display_avatar.url
                        )
                        
                        if welcome_config.get('gif_url'):
                            embed.set_image(url=welcome_config['gif_url'])
                        
                        await channel.send(f"{member.mention}", embed=embed)
                    except discord.Forbidden:
                        print(f"✗ Could not send welcome message in {channel.name}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leave"""
        print(f"✗ {member} left {member.guild.name}")


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberEvents(bot))
