"""
Anti-Spam System Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from datetime import timedelta
from utils import create_embed


class AntiSpam(commands.GroupCog, name="antispam"):
    """Anti-spam system for preventing message spam"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.anti_spam = commands.CooldownMapping.from_cooldown(5, 15, commands.BucketType.member)
        self.too_many_violations = commands.CooldownMapping.from_cooldown(4, 60, commands.BucketType.member)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✓ Anti-spam system loaded successfully")
    
    @app_commands.command(name="enable-anti-spam", description="Enable anti-spam system")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def enable(self, interaction: discord.Interaction):
        """Enable anti-spam"""
        async with aiosqlite.connect("db/antispam.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS antispam (switch INTEGER, punishment TEXT, whitelist TEXT, guild INTEGER PRIMARY KEY)"
                )
                await cursor.execute("SELECT switch FROM antispam WHERE guild = ?", (interaction.guild.id,))
                data = await cursor.fetchone()
                
                if data:
                    embed = create_embed(
                        title="Anti-Spam",
                        description="Anti-spam is already enabled in this server.",
                        color=discord.Color.orange()
                    )
                else:
                    await cursor.execute(
                        "INSERT INTO antispam (switch, punishment, whitelist, guild) VALUES (?, ?, ?, ?)",
                        (1, "timeout", "0", interaction.guild.id)
                    )
                    embed = create_embed(
                        title="Anti-Spam Enabled",
                        description="Anti-spam system is now active in this server.",
                        color=discord.Color.green()
                    )
                
                await interaction.response.send_message(embed=embed)
            await db.commit()
    
    @app_commands.command(name="disable-anti-spam", description="Disable anti-spam system")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def disable(self, interaction: discord.Interaction):
        """Disable anti-spam"""
        async with aiosqlite.connect("db/antispam.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS antispam (switch INTEGER, punishment TEXT, whitelist TEXT, guild INTEGER PRIMARY KEY)"
                )
                await cursor.execute("SELECT switch FROM antispam WHERE guild = ?", (interaction.guild.id,))
                data = await cursor.fetchone()
                
                if data:
                    await cursor.execute("DELETE FROM antispam WHERE guild = ?", (interaction.guild.id,))
                    embed = create_embed(
                        title="Anti-Spam Disabled",
                        description="Anti-spam system has been disabled.",
                        color=discord.Color.green()
                    )
                else:
                    embed = create_embed(
                        title="Anti-Spam",
                        description="Anti-spam is already disabled in this server.",
                        color=discord.Color.orange()
                    )
                
                await interaction.response.send_message(embed=embed)
            await db.commit()
    
    @app_commands.command(name="punishment", description="Set punishment for spam")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(punishment="The punishment to apply.")
    @app_commands.choices(punishment=[
        app_commands.Choice(name="none", value="none"),
        app_commands.Choice(name="mute", value="mute"),
        app_commands.Choice(name="timeout", value="timeout"),
        app_commands.Choice(name="warn", value="warn"),
        app_commands.Choice(name="kick", value="kick"),
        app_commands.Choice(name="ban", value="ban")
    ])
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def punishment(self, interaction: discord.Interaction, punishment: app_commands.Choice[str]):
        """Set spam punishment"""
        async with aiosqlite.connect("db/antispam.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS antispam (switch INTEGER, punishment TEXT, whitelist TEXT, guild INTEGER PRIMARY KEY)"
                )
                await cursor.execute("SELECT switch FROM antispam WHERE guild = ?", (interaction.guild.id,))
                data = await cursor.fetchone()
                
                if data:
                    await cursor.execute(
                        "UPDATE antispam SET punishment = ? WHERE guild = ?",
                        (punishment.value, interaction.guild.id)
                    )
                    embed = create_embed(
                        title="Anti-Spam Punishment Updated",
                        description=f"Punishment set to: **{punishment.value}**",
                        color=discord.Color.green()
                    )
                else:
                    embed = create_embed(
                        title="Anti-Spam",
                        description="Anti-spam system is not enabled in this server.",
                        color=discord.Color.red()
                    )
                
                await interaction.response.send_message(embed=embed)
            await db.commit()
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detect and handle spam"""
        if message.author.bot or not message.guild:
            return
        
        async with aiosqlite.connect("db/antispam.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS antispam (switch INTEGER, punishment TEXT, whitelist TEXT, guild INTEGER PRIMARY KEY)"
                )
                await cursor.execute("SELECT switch FROM antispam WHERE guild = ?", (message.guild.id,))
                data = await cursor.fetchone()
                
                if not data:
                    return
                
                # Check spam in all channels (removed whitelist check)
                bucket = self.anti_spam.get_bucket(message)
                retry_after = bucket.update_rate_limit()
                
                if retry_after:
                    try:
                        await message.delete()
                    except:
                        pass
                    
                    embed = create_embed(
                        description=f"{message.author.mention} please don't spam!",
                        color=discord.Color.orange()
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                    
                    violations = self.too_many_violations.get_bucket(message)
                    if violations.update_rate_limit():
                        await cursor.execute(
                            "SELECT punishment FROM antispam WHERE guild = ?",
                            (message.guild.id,)
                        )
                        punishment_data = await cursor.fetchone()
                        
                        if punishment_data and punishment_data[0] != "none":
                            if message.guild.me.top_role <= message.author.top_role:
                                return
                            
                            punishment_type = punishment_data[0]
                            
                            if punishment_type == "timeout":
                                await message.author.timeout(timedelta(minutes=10), reason="Spam detected")
                            elif punishment_type == "kick":
                                await message.author.kick(reason="Spam detected")
                            elif punishment_type == "ban":
                                await message.author.ban(reason="Spam detected")
                            # Add other punishments as needed


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))
