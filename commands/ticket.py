"""
Enhanced Ticket System with Modal Form
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os
import json
from utils import CONFIG


# Load configuration
def get_config():
    with open("config/settings.json", "r") as f:
        return json.load(f)


class TicketFormModal(discord.ui.Modal, title="Create a Support Ticket"):
    """Modal form for ticket creation"""
    
    product = discord.ui.TextInput(
        label="Enter your name",
        placeholder="Enter your name to continue",
        required=True,
        min_length=3,
        max_length=100
    )
    
    name = discord.ui.TextInput(
        label="Enter your age",
        placeholder="Enter your age (or leave blank)",
        required=False,
        max_length=100
    )
    
    date = discord.ui.TextInput(
        label="Today's Date (optional)",
        placeholder="Enter the date (or leave blank)...",
        required=False,
        max_length=50
    )
    
    description = discord.ui.TextInput(
        label="Issue Description",
        placeholder="Describe your issue in detail...",
        required=True,
        min_length=10,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process the submitted form"""
        config = get_config()
        guild = interaction.guild
        category_id = config['categories']['ticket_category_id']
        moderator_role_ids = config['roles']['moderator_role_ids']
        
        category = discord.utils.get(guild.categories, id=category_id)
        if not category:
            await interaction.response.send_message(
                "❌ Ticket category not found. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Check if user already has a ticket
        channel_name = f"ticket-{self.product.value.lower().replace(' ', '-')}-{interaction.user.name.lower()}"
        channel_name = "".join(c for c in channel_name if c.isalnum() or c == '-')[:100]
        
        for channel in category.channels:
            if channel.name == channel_name:
                await interaction.response.send_message(
                    f"You already have an open ticket for this product: {channel.mention}",
                    ephemeral=True
                )
                return
        
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
                read_message_history=True
            )
        }
        
        # Add moderator roles
        for role_id in moderator_role_ids:
            moderator_role = guild.get_role(role_id)
            if moderator_role:
                overwrites[moderator_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
        
        try:
            # Create ticket channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Ticket for {interaction.user} - {self.product.value}"
            )
            
            # Create ticket info embed
            embed = discord.Embed(
                title=f"📋 Support Ticket - {self.product.value}",
                description="Thank you for creating a ticket. Our team will assist you shortly.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Product/Category", value=self.product.value, inline=False)
            embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Created at", value=discord.utils.format_dt(datetime.now(), "F"), inline=True)
            
            if self.name.value:
                embed.add_field(name="Your Name", value=self.name.value, inline=False)
            
            if self.date.value:
                embed.add_field(name="Date", value=self.date.value, inline=False)
            
            embed.add_field(name="Issue Description", value=self.description.value, inline=False)
            
            # Add moderator mentions
            moderator_mentions = []
            for role_id in moderator_role_ids:
                moderator_role = guild.get_role(role_id)
                if moderator_role:
                    moderator_mentions.append(moderator_role.mention)
            
            mention_text = " ".join(moderator_mentions) if moderator_mentions else ""
            
            await ticket_channel.send(
                f"{mention_text}\n{interaction.user.mention} has created a ticket. Please review the details below:",
                embed=embed,
                view=TicketCloseView()
            )
            
            # Confirm to user
            await interaction.response.send_message(
                f"✅ Your ticket has been created: {ticket_channel.mention}\n\n"
                f"**Product:** {self.product.value}\n"
                f"**Description:** {self.description.value[:100]}...",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create channels. Please contact an administrator.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An error occurred: {e}",
                ephemeral=True
            )


class TicketCreateView(discord.ui.View):
    """View for ticket creation button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Create a Ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="ticket_create_button",
        emoji="📩"
    )
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the ticket creation modal"""
        await interaction.response.send_modal(TicketFormModal())


class TicketCloseView(discord.ui.View):
    """View for closing ticket"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close_button",
        emoji="🔒"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket channel"""
        config = get_config()
        moderator_role_ids = config['roles']['moderator_role_ids']
        
        # Check if user has permission to close
        is_ticket_creator = interaction.user == interaction.channel.owner
        is_moderator = any(role.id in moderator_role_ids for role in interaction.user.roles)
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_ticket_creator or is_moderator or is_admin):
            await interaction.response.send_message(
                "❌ You don't have permission to close this ticket.",
                ephemeral=True
            )
            return
        
        # Confirm close
        confirm_embed = discord.Embed(
            title="⚠️ Close Ticket?",
            description="Are you sure you want to close this ticket? This action cannot be undone.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(
            embed=confirm_embed,
            view=ConfirmCloseView(interaction.channel),
            ephemeral=True
        )


class ConfirmCloseView(discord.ui.View):
    """Confirmation view for closing ticket"""
    
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=60)
        self.channel = channel
    
    @discord.ui.button(label="Yes, Close Ticket", style=discord.ButtonStyle.red)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and close the ticket"""
        config = get_config()
        transcript_channel_id = config['channels']['transcript_channel_id']
        
        try:
            # Generate transcript
            transcript_lines = ["# Ticket Transcript\n"]
            async for message in self.channel.history(limit=None, oldest_first=True):
                created = discord.utils.format_dt(message.created_at, "f")
                if message.edited_at:
                    edited = discord.utils.format_dt(message.edited_at, "f")
                    transcript_lines.append(
                        f"**{message.author}** ({created}) - *Edited: {edited}*\n{message.clean_content}\n"
                    )
                else:
                    transcript_lines.append(f"**{message.author}** ({created})\n{message.clean_content}\n")
            
            transcript_lines.append(f"\n*Generated at {discord.utils.format_dt(datetime.now(), 'F')}*")
            transcript_text = "\n".join(transcript_lines)
            
            # Save transcript
            transcript_path = f"{self.channel.id}.md"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            # Send to transcript channel
            transcript_channel = interaction.client.get_channel(transcript_channel_id)
            if transcript_channel:
                with open(transcript_path, 'rb') as f:
                    await transcript_channel.send(
                        f"Transcript for {self.channel.mention}",
                        file=discord.File(f, f"{self.channel.name}_transcript.md")
                    )
            
            # Clean up
            os.remove(transcript_path)
            
            # Delete channel
            await interaction.response.send_message("✅ Ticket closed and transcript saved.", ephemeral=True)
            await self.channel.delete(reason="Ticket closed")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error closing ticket: {e}", ephemeral=True)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the close operation"""
        await interaction.response.defer()


class TicketSystem(commands.Cog):
    """Ticket system cog"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Re-register persistent views on bot startup"""
        print("✓ Ticket system loaded successfully")
        
        # Re-register persistent views so buttons work after restart
        self.bot.add_view(TicketCreateView())
        self.bot.add_view(TicketCloseView())
        
        print("✓ Ticket system views re-registered (buttons will work)")
    
    @app_commands.command(name="setup_tickets", description="Setup the ticket system in current channel")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        """Setup ticket creation panel"""
        config = get_config()
        ticket_channel_id = config['channels']['ticket_channel_id']
        
        if interaction.channel.id != ticket_channel_id:
            await interaction.response.send_message(
                f"⚠️ This command should be used in the designated ticket channel.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 Support Ticket System",
            description="Click the button below to create a support ticket. Our team will assist you as soon as possible.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 What is a Ticket?",
            value="A ticket is a private channel where you can discuss your issue with our support team.",
            inline=False
        )
        embed.add_field(
            name="⏱️ Response Time",
            value="Our team typically responds within 1-2 hours during business hours.",
            inline=False
        )
        
        await interaction.response.send_message(
            embed=embed,
            view=TicketCreateView(),
            ephemeral=False
        )
        
        await interaction.followup.send(
            "✅ Ticket system setup complete!",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketSystem(bot))
