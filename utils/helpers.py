"""
Common utilities and helpers
"""
import discord
from datetime import timedelta
from typing import Dict, Optional


def parse_time_string(time_str: str) -> int:
    """
    Parse time string to seconds
    
    Args:
        time_str: Time string (e.g., '1h', '30m', '2d')
        
    Returns:
        Time in seconds
        
    Raises:
        ValueError: If format is invalid
    """
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800,
        'mo': 2592000,
        'y': 31104000
    }
    
    try:
        unit = time_str[-1].lower()
        value = int(time_str[:-1])
        
        if unit not in time_units:
            raise ValueError(f"Invalid time unit: {unit}")
        
        return time_units[unit] * value
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format: {time_str}. Use format like '1h', '30m', '2d'") from e


def create_permission_overwrite(
    role: Optional[discord.Role] = None,
    user: Optional[discord.Member] = None,
    permissions: Optional[Dict[str, bool]] = None
) -> dict:
    """
    Create permission overwrite configuration
    
    Args:
        role: Role to set permissions for
        user: User to set permissions for
        permissions: Dictionary of permissions
        
    Returns:
        Dictionary with role/user and permissions
    """
    if permissions is None:
        permissions = {}
    
    overwrite = discord.PermissionOverwrite(**permissions)
    
    if role:
        return {role: overwrite}
    elif user:
        return {user: overwrite}
    return {}


def xp_for_next_level(level: int) -> int:
    """
    Calculate XP required for next level
    
    Args:
        level: Current level
        
    Returns:
        XP required for next level
    """
    return 5 * (level ** 2) + 50 * level + 100


def create_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: discord.Color = discord.Color.blue(),
    fields: Optional[list] = None,
    footer_text: Optional[str] = None,
    footer_icon: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None
) -> discord.Embed:
    """
    Create a Discord embed with common settings
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color
        fields: List of (name, value, inline) tuples
        footer_text: Footer text
        footer_icon: Footer icon URL
        thumbnail_url: Thumbnail URL
        image_url: Image URL
        
    Returns:
        Discord embed object
    """
    embed = discord.Embed(title=title, description=description, color=color)
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    
    if footer_text:
        embed.set_footer(text=footer_text, icon_url=footer_icon)
    
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    if image_url:
        embed.set_image(url=image_url)
    
    return embed
