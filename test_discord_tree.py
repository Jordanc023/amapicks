import discord
try:
    from discord import app_commands
    print(f"App commands imported: {app_commands}")
except ImportError:
    print("App commands NOT available via 'from discord import app_commands'")

try:
    import discord.app_commands
    print("discord.app_commands imported")
except ImportError:
    print("discord.app_commands NOT available")

print(f"Discord version: {discord.__version__}")
