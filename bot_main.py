"""
Main Bot File - Iran Town Hall Discord Bot
"""
import discord
from discord.ext import commands, tasks
import os
import asyncio
import json
from utils import load_config, init_databases

# ANSI Color codes for Iran flag colors
COLOR_GREEN = '\033[92m'    # Green
COLOR_WHITE = '\033[97m'    # White
COLOR_RED = '\033[91m'      # Red
COLOR_RESET = '\033[0m'     # Reset color

# Load configuration
CONFIG = load_config()

# Setup intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Create bot
bot = commands.Bot(
    command_prefix=CONFIG['bot']['command_prefix'],
    intents=intents,
    help_command=None
)


@bot.event
async def on_ready():
    """Bot ready event"""
    print(COLOR_RED + "=" * 50 + COLOR_RESET)
    print(COLOR_GREEN + f"✓ Bot logged in as: {bot.user.name} ({bot.user.id})" + COLOR_RESET)
    print(COLOR_RED + "=" * 50 + COLOR_RESET)
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(COLOR_GREEN + f"✓ Synced {len(synced)} command(s)" + COLOR_RESET)
    except Exception as e:
        print(COLOR_RED + f"✗ Failed to sync commands: {e}" + COLOR_RESET)
    
    # Set bot presence
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} server(s) | /help"
        )
    )
    
    print(COLOR_GREEN + "✓ Bot is ready!" + COLOR_RESET + "\n")


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Handle bot joining a guild"""
    print(COLOR_GREEN + f"✓ Joined guild: {guild.name} (ID: {guild.id})" + COLOR_RESET)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    """Handle bot leaving a guild"""
    print(COLOR_RED + f"✗ Left guild: {guild.name} (ID: {guild.id})" + COLOR_RESET)


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="❌ You don't have permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            description="❌ I don't have permission to perform this action.",
            color=discord.Color.red()
        )
        await ctx.response.send_message(embed=embed, ephemeral=True)
    else:
        print(f"Error in command: {error}")


async def load_commands():
    """Load all commands from commands folder"""
    print(COLOR_WHITE + "\nLoading commands..." + COLOR_RESET)
    
    commands_dir = "commands"
    if not os.path.exists(commands_dir):
        print(COLOR_RED + f"✗ Commands folder not found: {commands_dir}" + COLOR_RESET)
        return
    
    loaded_count = 0
    for filename in os.listdir(commands_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(COLOR_GREEN + f"  ✓ Loaded: {filename[:-3]}" + COLOR_RESET)
                loaded_count += 1
            except Exception as e:
                print(COLOR_RED + f"  ✗ Failed to load {filename}: {e}" + COLOR_RESET)
    
    print(COLOR_GREEN + f"✓ Successfully loaded {loaded_count} command module(s)" + COLOR_RESET + "\n")


async def load_events():
    """Load all events from events folder"""
    print(COLOR_WHITE + "Loading events..." + COLOR_RESET)
    
    events_dir = "events"
    if not os.path.exists(events_dir):
        print(COLOR_RED + f"✗ Events folder not found: {events_dir}" + COLOR_RESET)
        return
    
    loaded_count = 0
    for filename in os.listdir(events_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'events.{filename[:-3]}')
                print(COLOR_GREEN + f"  ✓ Loaded: {filename[:-3]}" + COLOR_RESET)
                loaded_count += 1
            except Exception as e:
                print(COLOR_RED + f"  ✗ Failed to load {filename}: {e}" + COLOR_RESET)
    
    print(COLOR_GREEN + f"✓ Successfully loaded {loaded_count} event module(s)" + COLOR_RESET + "\n")


async def main():
    """Main function"""
    print(COLOR_RED + "=" * 50 + COLOR_RESET)
    print(COLOR_WHITE + "🤖 Iran Town Hall Discord Bot" + COLOR_RESET)
    print(COLOR_RED + "=" * 50 + COLOR_RESET + "\n")
    
    # Initialize databases
    print(COLOR_WHITE + "Initializing databases..." + COLOR_RESET)
    db_paths = CONFIG.get('database', {})
    await init_databases(db_paths)
    print(COLOR_GREEN + "✓ Databases initialized" + COLOR_RESET + "\n")
    
    # Load all commands
    await load_commands()
    
    # Load all events
    await load_events()
    
    # Start the bot
    try:
        await bot.start(CONFIG['bot']['token'])
    except discord.errors.LoginFailure:
        print(COLOR_RED + "✗ Failed to login. Please check your bot token in config/settings.json" + COLOR_RESET)
    except KeyboardInterrupt:
        print(COLOR_RED + "\n✗ Bot shutdown by user" + COLOR_RESET)
        await bot.close()
    except Exception as e:
        print(COLOR_RED + f"✗ Error running bot: {e}" + COLOR_RESET)
        await bot.close()


if __name__ == "__main__":
    # Check for token
    if CONFIG['bot']['token'] == "YOUR_BOT_TOKEN_HERE":
        print(COLOR_RED + "✗ ERROR: Bot token not configured!" + COLOR_RESET)
        print(COLOR_RED + "Please open config/settings.json and add your bot token." + COLOR_RESET)
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print(COLOR_RED + "\n✗ Bot stopped" + COLOR_RESET)
