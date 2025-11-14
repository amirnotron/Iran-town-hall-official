"""
Giveaway System Cog
"""
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random
from datetime import datetime, timedelta
import asyncio
import json


def get_config():
    """Load configuration"""
    with open("config/settings.json", "r") as f:
        return json.load(f)


def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string to timedelta"""
    try:
        unit_map = {
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks'
        }
        value = int(duration_str[:-1])
        unit = duration_str[-1].lower()
        
        if unit not in unit_map:
            raise ValueError("Invalid time unit.")
        
        return timedelta(**{unit_map[unit]: value})
    except (ValueError, IndexError):
        raise ValueError("Invalid duration format. Example: `7d`, `12h`, `30m`.")


class GiveawayCog(commands.Cog):
    """Giveaway system for contests and rewards"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server_invites = {}
        self.con = sqlite3.connect("db/giveaway.db")
        self.con.row_factory = sqlite3.Row
    
    def cog_unload(self):
        self.con.close()
        print("[INFO] Closed database connection for GiveawayCog.")
    
    async def cog_load(self):
        print("[INFO] GiveawayCog loaded. Caching invites and resuming giveaways...")
        
        for guild in self.bot.guilds:
            try:
                self.server_invites[guild.id] = {
                    invite.code: invite.uses for invite in await guild.invites()
                }
            except discord.Forbidden:
                print(f"[WARNING] Missing permissions to view invites in {guild.name}")
        
        cur = self.con.cursor()
        cur.execute("SELECT * FROM giveaways")
        active_giveaways = cur.fetchall()
        
        current_time = int(datetime.utcnow().timestamp())
        for gw in active_giveaways:
            remaining_time = gw['end_timestamp'] - current_time
            giveaway_data = (
                gw['guild_id'],
                gw['message_id'],
                gw['channel_id'],
                gw['required_invites'],
                gw['prize'],
                gw['winner_count']
            )
            
            if remaining_time > 0:
                print(f"[INFO] Resuming giveaway {gw['message_id']}")
                self.bot.loop.create_task(self._schedule_giveaway_end(remaining_time, giveaway_data))
    
    async def _schedule_giveaway_end(self, delay, data):
        """Schedule giveaway end"""
        await asyncio.sleep(delay)
        await self._end_giveaway_task(data)
    
    async def _end_giveaway_task(self, giveaway_data):
        """End giveaway and pick winner"""
        guild_id, message_id, channel_id, required_invites, prize, winner_count = giveaway_data
        
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden) as e:
            print(f"[ERROR] Could not find giveaway message {message_id}: {e}")
            self._cleanup_db_for_giveaway(message_id)
            return
        
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        participants = [user async for user in reaction.users() if not user.bot] if reaction else []
        
        cur = self.con.cursor()
        cur.execute(
            "SELECT user_id FROM entries WHERE giveaway_message_id = ? AND invite_count >= ?",
            (message_id, required_invites)
        )
        db_eligible_ids = {row['user_id'] for row in cur.fetchall()}
        
        eligible_entrants = [p for p in participants if p.id in db_eligible_ids]
        
        if not eligible_entrants:
            winners = []
        else:
            num_winners = min(winner_count, len(eligible_entrants))
            winners = random.sample(eligible_entrants, k=num_winners)
        
        # Create result embed
        if winners:
            winner_mentions = ", ".join(w.mention for w in winners)
            title = "🎊 WINNERS ANNOUNCED 🎊" if len(winners) > 1 else "🎊 WINNER ANNOUNCED 🎊"
            embed = discord.Embed(
                title=title,
                description=f"**Prize:** {prize}\n**Winner(s):** {winner_mentions}",
                color=discord.Color.gold()
            )
            announcement = f"Congratulations {winner_mentions}! You won the **{prize}**!"
        else:
            embed = discord.Embed(
                title="😭 GIVEAWAY ENDED 😭",
                description=f"**Prize:** {prize}\n\nNo one met the requirements.",
                color=discord.Color.red()
            )
            announcement = f"The giveaway for **{prize}** has ended. No eligible participants."
        
        try:
            await message.edit(embed=embed)
            await channel.send(announcement)
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"[ERROR] Failed to announce giveaway: {e}")
        
        self._cleanup_db_for_giveaway(message_id)
    
    def _cleanup_db_for_giveaway(self, message_id):
        """Clean up database entries"""
        try:
            cur = self.con.cursor()
            cur.execute("DELETE FROM giveaways WHERE message_id = ?", (message_id,))
            cur.execute("DELETE FROM entries WHERE giveaway_message_id = ?", (message_id,))
            self.con.commit()
        except sqlite3.Error as e:
            print(f"[ERROR] Database error: {e}")
    
    @app_commands.command(name="gstart", description="Start a giveaway with optional invite requirements")
    @app_commands.describe(
        duration="Duration (e.g., 1d, 8h, 30m)",
        winners="Number of winners",
        prize="Prize description",
        require_invites="Require invites to participate? (yes/no)",
        invite_count="Number of invites required (if require_invites=yes)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def gstart(
        self,
        interaction: discord.Interaction,
        duration: str,
        winners: int,
        prize: str,
        require_invites: str = "no",
        invite_count: int = 0
    ):
        """Start a giveaway with optional invite requirements"""
        cur = self.con.cursor()
        cur.execute("SELECT 1 FROM giveaways WHERE guild_id = ?", (interaction.guild.id,))
        
        if cur.fetchone():
            embed = discord.Embed(
                description="❌ A giveaway is already running in this server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if winners < 1:
            embed = discord.Embed(
                description="❌ The number of winners must be at least 1.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate and normalize require_invites parameter
        require_invites_lower = require_invites.lower().strip()
        if require_invites_lower not in ("yes", "no", "true", "false", "1", "0"):
            embed = discord.Embed(
                title="❌ Invalid invite requirement",
                description="Use `yes` or `no` for require_invites parameter.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        should_require_invites = require_invites_lower in ("yes", "true", "1")
        
        # If invites are required, validate invite_count
        if should_require_invites and invite_count < 0:
            embed = discord.Embed(
                description="❌ Invite count cannot be negative.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Set invite count to 0 if not requiring invites
        final_invite_count = invite_count if should_require_invites else 0
        
        try:
            giveaway_duration = parse_duration(duration)
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Invalid duration format",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        end_time = datetime.utcnow() + giveaway_duration
        end_timestamp = int(end_time.timestamp())
        
        # Build requirements field text
        if should_require_invites and final_invite_count > 0:
            requirements_text = f"Invite **{final_invite_count}** new member(s)"
        elif should_require_invites:
            requirements_text = "Have at least **1** invite"
        else:
            requirements_text = "None — Anyone can enter!"
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY STARTED 🎉",
            description=f"**Prize:** {prize}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Ends In", value=f"<t:{end_timestamp}:R>", inline=False)
        embed.add_field(name="Winners", value=f"**{winners}**", inline=True)
        embed.add_field(name="Requirements", value=requirements_text, inline=True)
        embed.set_footer(text="React with 🎉 to enter!")
        
        await interaction.response.send_message("✅ Giveaway starting...", ephemeral=True)
        
        giveaway_message = await interaction.channel.send(embed=embed, content="@everyone")
        await giveaway_message.add_reaction("🎉")
        
        cur.execute(
            "INSERT INTO giveaways (guild_id, message_id, channel_id, end_timestamp, required_invites, prize, winner_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                interaction.guild.id,
                giveaway_message.id,
                giveaway_message.channel.id,
                end_timestamp,
                final_invite_count,
                prize,
                winners
            )
        )
        self.con.commit()
        
        giveaway_data = (
            interaction.guild.id,
            giveaway_message.id,
            giveaway_message.channel.id,
            final_invite_count,
            prize,
            winners
        )
        self.bot.loop.create_task(self._schedule_giveaway_end(giveaway_duration.total_seconds(), giveaway_data))
    
    @app_commands.command(name="invites", description="Check invite count")
    @app_commands.describe(member="Member to check (defaults to you)")
    async def invites(self, interaction: discord.Interaction, member: discord.Member = None):
        """Check user's invite count"""
        if member is None:
            member = interaction.user
        
        cur = self.con.cursor()
        cur.execute(
            "SELECT invite_count FROM invites WHERE guild_id = ? AND user_id = ?",
            (interaction.guild.id, member.id)
        )
        total_res = cur.fetchone()
        total_invs = total_res['invite_count'] if total_res else 0
        
        embed = discord.Embed(
            title=f"✉️ Invites for {member.display_name}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Total Invites", value=f"`{total_invs}`", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="gend", description="End current giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def gend(self, interaction: discord.Interaction):
        """End the current giveaway"""
        cur = self.con.cursor()
        cur.execute("SELECT * FROM giveaways WHERE guild_id = ?", (interaction.guild.id,))
        giveaway_info = cur.fetchone()
        
        if not giveaway_info:
            embed = discord.Embed(
                description="❌ There is no active giveaway in this server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.send_message("✅ Forcing giveaway to end...", ephemeral=True)
        
        await self._end_giveaway_task((
            giveaway_info['guild_id'],
            giveaway_info['message_id'],
            giveaway_info['channel_id'],
            giveaway_info['required_invites'],
            giveaway_info['prize'],
            giveaway_info['winner_count']
        ))


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
