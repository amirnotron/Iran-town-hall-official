"""
Database initialization and utilities
"""
import sqlite3
import aiosqlite
from pathlib import Path


async def init_databases(db_paths: dict) -> None:
    """
    Initialize all required databases
    
    Args:
        db_paths: Dictionary of database names and paths
    """
    # Create db directory if it doesn't exist
    Path("db").mkdir(exist_ok=True)
    
    for db_name, db_path in db_paths.items():
        await create_database_tables(db_path)


async def create_database_tables(db_path: str) -> None:
    """
    Create necessary tables for database
    
    Args:
        db_path: Path to database file
    """
    async with aiosqlite.connect(db_path) as db:
        # Warnings table
        if "warnings" in db_path:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    warns INTEGER,
                    member INTEGER,
                    guild INTEGER,
                    PRIMARY KEY (member, guild)
                )
            """)
        
        # Levels table
        elif "levels" in db_path:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
        
        # Giveaway tables
        elif "giveaway" in db_path:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    guild_id INTEGER,
                    message_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    end_timestamp INTEGER,
                    required_invites INTEGER,
                    prize TEXT,
                    winner_count INTEGER DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS invites (
                    guild_id INTEGER,
                    user_id INTEGER,
                    invite_count INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    giveaway_message_id INTEGER,
                    user_id INTEGER,
                    invite_count INTEGER DEFAULT 0,
                    PRIMARY KEY (giveaway_message_id, user_id),
                    FOREIGN KEY (giveaway_message_id) REFERENCES giveaways(message_id)
                )
            """)
        
        # Antispam table
        elif "antispam" in db_path:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS antispam (
                    switch INTEGER,
                    punishment TEXT,
                    whitelist TEXT,
                    guild INTEGER PRIMARY KEY
                )
            """)
        
        # Tickets table
        elif "tickets" in db_path:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets_role (
                    role INTEGER,
                    guild INTEGER PRIMARY KEY
                )
            """)
        
        await db.commit()


def get_sync_connection(db_path: str) -> sqlite3.Connection:
    """
    Get a synchronous database connection
    
    Args:
        db_path: Path to database file
        
    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
