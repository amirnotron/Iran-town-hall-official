"""
Main Bot File - Iran Town Hall Discord Bot
"""
import discord
from discord.ext import commands, tasks
import os
import asyncio
import json
from utils import load_config, init_databases

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
    print("=" * 50)
    print(f"✓ Bot logged in as: {bot.user.name} ({bot.user.id})")
    print("=" * 50)
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f"✓ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"✗ Failed to sync commands: {e}")
    
    # Set bot presence
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} server(s) | /help"
        )
    )
    
    print("✓ Bot is ready!\n")


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Handle bot joining a guild"""
    print(f"✓ Joined guild: {guild.name} (ID: {guild.id})")


@bot.event
async def on_guild_remove(guild: discord.Guild):
    """Handle bot leaving a guild"""
    print(f"✗ Left guild: {guild.name} (ID: {guild.id})")


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
    print("\nLoading commands...")
    
    commands_dir = "commands"
    if not os.path.exists(commands_dir):
        print(f"✗ Commands folder not found: {commands_dir}")
        return
    
    loaded_count = 0
    for filename in os.listdir(commands_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(f"  ✓ Loaded: {filename[:-3]}")
                loaded_count += 1
            except Exception as e:
                print(f"  ✗ Failed to load {filename}: {e}")
    
    print(f"✓ Successfully loaded {loaded_count} command module(s)\n")


async def load_events():
    """Load all events from events folder"""
    print("Loading events...")
    
    events_dir = "events"
    if not os.path.exists(events_dir):
        print(f"✗ Events folder not found: {events_dir}")
        return
    
    loaded_count = 0
    for filename in os.listdir(events_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            try:
                await bot.load_extension(f'events.{filename[:-3]}')
                print(f"  ✓ Loaded: {filename[:-3]}")
                loaded_count += 1
            except Exception as e:
                print(f"  ✗ Failed to load {filename}: {e}")
    
    print(f"✓ Successfully loaded {loaded_count} event module(s)\n")


async def main():
    """Main function"""
    print("=" * 50)
    print("🤖 Iran Town Hall Discord Bot")
    print("=" * 50 + "\n")
    
    # Initialize databases
    print("Initializing databases...")
    db_paths = CONFIG.get('database', {})
    await init_databases(db_paths)
    print("✓ Databases initialized\n")
    
    # Load all commands
    await load_commands()
    
    # Load all events
    await load_events()
    
    # Start the bot
    try:
        await bot.start(CONFIG['bot']['token'])
    except discord.errors.LoginFailure:
        print("✗ Failed to login. Please check your bot token in config/settings.json")
    except KeyboardInterrupt:
        print("\n✗ Bot shutdown by user")
        await bot.close()
    except Exception as e:
        print(f"✗ Error running bot: {e}")
        await bot.close()


if __name__ == "__main__":
    # Check for token
    if CONFIG['bot']['token'] == "YOUR_BOT_TOKEN_HERE":
        print("✗ ERROR: Bot token not configured!")
        print("Please open config/settings.json and add your bot token.")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n✗ Bot stopped")
