"""
Leveling System Cog
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
import random
import time
import json
from utils import xp_for_next_level, create_embed


def get_config():
    """Load configuration"""
    with open("config/settings.json", "r") as f:
        return json.load(f)


class LevelingSystem(commands.Cog):
    """User leveling system with XP progression"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_cooldowns = {}
        self.config = get_config()
        self.level_up_channel_id = self.config['channels']['level_up_channel_id']
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("✓ Leveling system loaded successfully")
        self.voice_xp_loop.start()
    
    def cog_unload(self):
        self.voice_xp_loop.cancel()
    
    async def grant_xp(self, user_id: int, guild_id: int, amount: int):
        """Grant XP to a user and handle level ups"""
        async with aiosqlite.connect("db/levels.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS users (user_id INTEGER, guild_id INTEGER, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, PRIMARY KEY (user_id, guild_id))"
                )
                
                await cursor.execute(
                    "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
                    (user_id, guild_id)
                )
                user_data = await cursor.fetchone()
                
                if not user_data:
                    await cursor.execute(
                        "INSERT INTO users (user_id, guild_id, level, xp) VALUES (?, ?, 1, ?)",
                        (user_id, guild_id, amount)
                    )
                    current_level = 1
                    current_xp = amount
                else:
                    current_level = user_data[2]
                    current_xp = user_data[3] + amount
                    await cursor.execute(
                        "UPDATE users SET xp = ? WHERE user_id = ? AND guild_id = ?",
                        (current_xp, user_id, guild_id)
                    )
                
                # Check for level up
                xp_needed = xp_for_next_level(current_level)
                if current_xp >= xp_needed:
                    new_level = current_level + 1
                    remaining_xp = current_xp - xp_needed
                    await cursor.execute(
                        "UPDATE users SET level = ?, xp = ? WHERE user_id = ? AND guild_id = ?",
                        (new_level, remaining_xp, user_id, guild_id)
                    )
                    
                    # Send level up message
                    channel = self.bot.get_channel(self.level_up_channel_id)
                    if channel:
                        try:
                            guild = self.bot.get_guild(guild_id)
                            member = guild.get_member(user_id)
                            if member:
                                embed = create_embed(
                                    title="🎉 Level Up!",
                                    description=f"{member.mention} has reached level **{new_level}**!",
                                    color=discord.Color.gold(),
                                    fields=[
                                        ("Previous Level", str(current_level), True),
                                        ("New Level", str(new_level), True),
                                        ("XP for Next Level", str(xp_for_next_level(new_level)), True)
                                    ]
                                )
                                await channel.send(embed=embed)
                        except Exception as e:
                            print(f"Error sending level up message: {e}")
                
                await db.commit()
    
    @app_commands.command(name="level", description="Check your or another member's level and XP.")
    @app_commands.describe(member="The member to check (defaults to you).")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        """Check user level and XP"""
        target_user = member or interaction.user
        
        async with aiosqlite.connect("db/levels.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS users (user_id INTEGER, guild_id INTEGER, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, PRIMARY KEY (user_id, guild_id))"
                )
                await cursor.execute(
                    "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
                    (target_user.id, interaction.guild.id)
                )
                user_data = await cursor.fetchone()
        
        if not user_data:
            embed = create_embed(
                description=f"{target_user.mention} hasn't earned any XP yet.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_level = user_data[2]
        user_xp = user_data[3]
        xp_needed = xp_for_next_level(user_level)
        progress = int((user_xp / xp_needed) * 20)
        progress_bar = '█' * progress + '░' * (20 - progress)
        
        embed = create_embed(
            title=f"{target_user.display_name}'s Level",
            color=discord.Color.blue(),
            thumbnail_url=target_user.display_avatar.url,
            fields=[
                ("Level", str(user_level), True),
                ("Current XP", f"`{user_xp} / {xp_needed}`", True),
                ("Progress", f"`[{progress_bar}]`", False)
            ]
        )
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Grant XP for messages"""
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        current_time = time.time()
        
        # Check cooldown
        if user_id in self.user_cooldowns:
            if current_time - self.user_cooldowns[user_id] < 60:
                return
        
        self.user_cooldowns[user_id] = current_time
        xp_to_grant = random.randint(
            self.config['features']['leveling']['xp_per_message_min'],
            self.config['features']['leveling']['xp_per_message_max']
        )
        await self.grant_xp(user_id, guild_id, xp_to_grant)
    
    @tasks.loop(seconds=60)
    async def voice_xp_loop(self):
        """Grant XP for voice channel activity"""
        await self.bot.wait_until_ready()
        
        for guild in self.bot.guilds:
            for member in guild.members:
                if (member.voice and 
                    not member.voice.afk and 
                    not member.voice.self_mute and 
                    not member.voice.self_deaf):
                    
                    xp_to_grant = random.randint(
                        self.config['features']['leveling']['xp_per_voice_min'],
                        self.config['features']['leveling']['xp_per_voice_max']
                    )
                    await self.grant_xp(member.id, guild.id, xp_to_grant)


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingSystem(bot))
