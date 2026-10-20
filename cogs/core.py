import discord
from discord import app_commands
from discord.ext import commands

Cog = commands.Cog

async def is_owner(interaction: discord.Interaction) -> bool:
    return await interaction.client.is_owner(interaction.user)

class Core(Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description='Reloads an extension')
    @app_commands.check(is_owner)
    @app_commands.describe(cog='Name of the cog to reload, e.g. cogs.moderation')
    async def reload(self, interaction: discord.Interaction, cog: str):
        """Reloads an extension"""
        try:
            self.bot.reload_extension(cog)
        except Exception as e:
            await interaction.response.send_message('Failed to load: `{}`\n```py\n{}\n```'.format(cog, e),
                                                    ephemeral=True)
        else:
            await interaction.response.send_message('Reloaded cog {} successfully'.format(cog), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Core(bot))
