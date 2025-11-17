"""
Complete Ticket System - Clean Implementation
Supports ticket creation via button, closing via command
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import json


def get_config():
    """Load configuration from settings.json"""
    with open("config/settings.json", "r") as f:
        return json.load(f)


class TicketFormModal(discord.ui.Modal, title="Create a Support Ticket"):
    """Modal form for creating support tickets"""
    
    name = discord.ui.TextInput(
        label="Your Name",
        placeholder="Enter your full name",
        required=True,
        min_length=2,
        max_length=100
    )
    
    subject = discord.ui.TextInput(
        label="Subject",
        placeholder="What is this ticket about?",
        required=True,
        min_length=5,
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Describe your issue in detail...",
        required=True,
        min_length=10,
        max_length=2000,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            config = get_config()
            guild = interaction.guild
            
            # Get category ID from config
            category_id = config.get('categories', {}).get('ticket_category_id')
            if not category_id:
                await interaction.followup.send("❌ Ticket category not configured", ephemeral=True)
                return
            
            category = guild.get_channel(category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                await interaction.followup.send("❌ Ticket category not found", ephemeral=True)
                return
            
            # Create channel name
            channel_name = f"ticket-{interaction.user.name.lower()}-{datetime.now().timestamp():.0f}"
            channel_name = "".join(c if c.isalnum() or c == '-' else '' for c in channel_name)[:100]
            
            # Get moderator roles
            moderator_role_ids = config.get('roles', {}).get('moderator_role_ids', [])
            
            # Create permission overwrites
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True
                )
            }
            
            # Add moderator permissions
            for role_id in moderator_role_ids:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True
                    )
            
            # Create the ticket channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Ticket created by {interaction.user}"
            )
            
            print(f"[TICKET] Created ticket channel: {ticket_channel.name}")
            
            # Create embed with ticket info
            embed = discord.Embed(
                title="📋 Support Ticket Created",
                description=f"Thank you for contacting support, {interaction.user.mention}!",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Ticket Creator", value=interaction.user.mention, inline=False)
            embed.add_field(name="Subject", value=self.subject.value, inline=False)
            embed.add_field(name="Description", value=self.description.value, inline=False)
            embed.add_field(name="Your Name", value=self.name.value, inline=False)
            embed.set_footer(text="Our team will respond shortly")
            
            # Send ticket info to the channel
            await ticket_channel.send(embed=embed)
            
            # Mention moderators
            moderator_mentions = []
            for role_id in moderator_role_ids:
                role = guild.get_role(role_id)
                if role:
                    moderator_mentions.append(role.mention)
            
            if moderator_mentions:
                await ticket_channel.send(f"{' '.join(moderator_mentions)} - New ticket from {interaction.user.mention}")
            
            # Send close command instruction
            info_embed = discord.Embed(
                title="📌 How to Close This Ticket",
                description="To close this ticket, use the command:\n\n`/close`",
                color=discord.Color.greyple()
            )
            await ticket_channel.send(embed=info_embed)
            
            # Confirm to user
            await interaction.followup.send(
                f"✅ Ticket created: {ticket_channel.mention}",
                ephemeral=True
            )
            
            print(f"[TICKET] Ticket setup complete for {interaction.user}")
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to create channels", ephemeral=True)
        except Exception as e:
            print(f"[TICKET] Error creating ticket: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)


class CreateTicketButton(discord.ui.View):
    """View with create ticket button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="create_ticket_btn",
        emoji="📝"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show ticket creation modal"""
        await interaction.response.send_modal(TicketFormModal())


class TicketSystem(commands.Cog):
    """Main ticket system cog"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Re-register views when bot starts"""
        print("✓ Ticket system loaded")
        self.bot.add_view(CreateTicketButton())
        print("✓ Ticket views registered")
    
    @app_commands.command(
        name="setup_ticket_panel",
        description="Setup the ticket creation panel (Admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_panel(self, interaction: discord.Interaction):
        """Setup ticket creation panel in current channel"""
        try:
            embed = discord.Embed(
                title="🎟️ Support Ticket System",
                description="Click the button below to create a support ticket.\n\nOur support team will assist you as soon as possible.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📝 How It Works",
                value="1. Click the **Create Ticket** button\n2. Fill out the form with your details\n3. A private channel will be created\n4. Use `/close` to close the ticket when done",
                inline=False
            )
            embed.add_field(
                name="⏱️ Response Time",
                value="We typically respond within 1-2 hours during business hours",
                inline=False
            )
            
            await interaction.response.send_message(
                embed=embed,
                view=CreateTicketButton()
            )
            
            await interaction.followup.send("✅ Ticket panel setup complete!", ephemeral=True)
            print(f"[TICKET] Setup panel command executed by {interaction.user}")
            
        except Exception as e:
            print(f"[TICKET] Error in setup_panel: {e}")
            await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)
    
    @app_commands.command(
        name="close",
        description="Close the current ticket"
    )
    async def close_ticket(self, interaction: discord.Interaction):
        """Close a ticket channel"""
        # Verify this is a ticket channel
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                "❌ This command can only be used in ticket channels",
                ephemeral=True
            )
            return
        
        try:
            config = get_config()
            moderator_ids = config.get('roles', {}).get('moderator_role_ids', [])
            
            # Check permissions
            is_creator = interaction.user == interaction.channel.owner
            is_moderator = any(role.id in moderator_ids for role in interaction.user.roles)
            is_admin = interaction.user.guild_permissions.administrator
            
            if not (is_creator or is_moderator or is_admin):
                await interaction.response.send_message(
                    "❌ You don't have permission to close this ticket",
                    ephemeral=True
                )
                return
            
            # Respond immediately
            await interaction.response.defer(ephemeral=True)
            
            print(f"[TICKET] Closing ticket: {interaction.channel.name}")
            
            # Send closing message
            closing_embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=f"This ticket was closed by {interaction.user.mention}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.channel.send(embed=closing_embed)
            
            # Delete channel
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            
            print(f"[TICKET] Ticket deleted successfully")
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to delete this channel",
                ephemeral=True
            )
        except Exception as e:
            print(f"[TICKET] Error closing ticket: {e}")
            try:
                await interaction.followup.send(
                    f"❌ Error closing ticket: {str(e)[:100]}",
                    ephemeral=True
                )
            except:
                pass


async def setup(bot: commands.Bot):
    """Load the ticket system cog"""
    await bot.add_cog(TicketSystem(bot))
    print("[TICKET] Ticket system cog loaded")
