"""
Moderation commands cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from datetime import timedelta
from typing import Optional
from utils import parse_time_string, create_embed


class ModerationCommands(commands.Cog):
    """Moderation commands for member management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✓ Moderation commands loaded successfully")
    
    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        """Ban a member from the server"""
        if member == interaction.guild.owner:
            await interaction.response.send_message("You cannot ban the server owner!", ephemeral=True)
            return
        
        if member == self.bot.user:
            await interaction.response.send_message("I cannot ban myself!", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("You cannot ban yourself!", ephemeral=True)
            return
        
        if interaction.guild.me.top_role <= member.top_role:
            await interaction.response.send_message(
                f"I cannot ban {member.mention} as their role is equal to or higher than my highest role.",
                ephemeral=True
            )
            return
        
        if interaction.user.top_role <= member.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                f"You cannot ban {member.mention} as their role is equal to or higher than your highest role.",
                ephemeral=True
            )
            return
        
        try:
            await member.ban(reason=reason)
            embed = create_embed(
                title="Member Banned",
                description=f"{member.mention} has been banned.",
                color=discord.Color.red(),
                fields=[
                    ("Reason", reason if reason else "No reason provided.", False)
                ],
                footer_text=f"Banned by {interaction.user.display_name}",
                footer_icon=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have sufficient permissions to ban this member.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        """Kick a member from the server"""
        if member == interaction.guild.owner:
            await interaction.response.send_message("You cannot kick the server owner!", ephemeral=True)
            return
        
        if member == self.bot.user:
            await interaction.response.send_message("I cannot kick myself!", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("You cannot kick yourself!", ephemeral=True)
            return
        
        if interaction.guild.me.top_role <= member.top_role:
            await interaction.response.send_message(
                f"I cannot kick {member.mention} as their role is equal to or higher than my highest role.",
                ephemeral=True
            )
            return
        
        if interaction.user.top_role <= member.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                f"You cannot kick {member.mention} as their role is equal to or higher than your highest role.",
                ephemeral=True
            )
            return
        
        try:
            await member.kick(reason=reason)
            embed = create_embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked.",
                color=discord.Color.orange(),
                fields=[
                    ("Reason", reason if reason else "No reason provided.", False)
                ],
                footer_text=f"Kicked by {interaction.user.display_name}",
                footer_icon=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have sufficient permissions to kick this member.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="timeout", description="Timeout a member for a specified duration.")
    @app_commands.describe(
        member="The member to timeout.",
        duration_minutes="Duration in minutes (max 28 days = 40320 minutes).",
        reason="Reason for the timeout."
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration_minutes: app_commands.Range[int, 1, 40320],
        reason: Optional[str] = None
    ):
        """Timeout a member"""
        if member == interaction.guild.owner:
            await interaction.response.send_message("You cannot timeout the server owner!", ephemeral=True)
            return
        
        if member == self.bot.user:
            await interaction.response.send_message("I cannot timeout myself!", ephemeral=True)
            return
        
        if member == interaction.user:
            await interaction.response.send_message("You cannot timeout yourself!", ephemeral=True)
            return
        
        if interaction.guild.me.top_role <= member.top_role:
            await interaction.response.send_message(
                f"I cannot timeout {member.mention} as their role is equal to or higher than my highest role.",
                ephemeral=True
            )
            return
        
        if interaction.user.top_role <= member.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message(
                f"You cannot timeout {member.mention} as their role is equal to or higher than your highest role.",
                ephemeral=True
            )
            return
        
        try:
            await member.timeout(timedelta(minutes=duration_minutes), reason=reason)
            embed = create_embed(
                title="Member Timed Out",
                description=f"{member.mention} has been timed out for {duration_minutes} minutes.",
                color=discord.Color.gold(),
                fields=[
                    ("Reason", reason if reason else "No reason provided.", False)
                ],
                footer_text=f"Timed out by {interaction.user.display_name}",
                footer_icon=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have sufficient permissions to timeout this member.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="warn", description="Warn a member.")
    @app_commands.describe(member="Member to warn.", reason="Reason for warning.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        """Warn a member"""
        if interaction.user.top_role <= member.top_role:
            await interaction.response.send_message(
                f"Your role must be higher than {member.mention}",
                ephemeral=True
            )
            return
        
        if interaction.guild.me.top_role <= member.top_role:
            await interaction.response.send_message(
                f"Bot's role must be higher than {member.mention}",
                ephemeral=True
            )
            return
        
        async with aiosqlite.connect("db/warnings.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS warnings (warns INTEGER, member INTEGER, guild INTEGER, PRIMARY KEY (member, guild))"
                )
                await cursor.execute(
                    "SELECT warns FROM warnings WHERE member = ? AND guild = ?",
                    (member.id, interaction.guild.id)
                )
                data = await cursor.fetchone()
                
                if data:
                    await cursor.execute(
                        "UPDATE warnings SET warns = ? WHERE member = ? AND guild = ?",
                        (data[0] + 1, member.id, interaction.guild.id)
                    )
                else:
                    await cursor.execute(
                        "INSERT INTO warnings (warns, member, guild) VALUES (?, ?, ?)",
                        (1, member.id, interaction.guild.id)
                    )
            await db.commit()
        
        embed = create_embed(
            title="Member Warned",
            description=f"{member.mention} has been warned by {interaction.user.mention}",
            color=discord.Color.yellow(),
            fields=[
                ("Reason", reason if reason else "No reason provided.", False)
            ]
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))
