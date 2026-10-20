import discord
from discord import app_commands
from discord.ext import commands
import bidict

Cog = commands.Cog
from discord.ext import commands
from ruamel.yaml import YAML
import os
from apiclient import discovery
from google.oauth2 import service_account


class Config(Cog):
    config = None
    server_codes = bidict.bidict()
    mod_codes = bidict.bidict()

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    secret_file = os.path.join(os.getcwd(), 'config/credentials.json')

    credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
    service = discovery.build('sheets', 'v4', credentials=credentials)

    def __init__(self, bot):
        yaml = YAML(type='safe', pure=True)
        with open('config/config.yml') as cfgfile:
            Config.config = yaml.load(cfgfile)
        self.bot = bot

        # Load mod codes
        result = Config.service.spreadsheets().values().get(
            spreadsheetId=Config.config['sheets']['isodn_punishment_log'],
            range="Staff Codes!A2:E").execute()
        values = result.get('values', [])
        for i in values:
            Config.mod_codes[int(i[2])] = i[4]
        print(Config.mod_codes)

        # Load server codes
        server_codes_result = Config.service.spreadsheets().values().get(
            spreadsheetId=Config.config['sheets']['isodn_punishment_log'],
            range="Server Codes!A1:B").execute()
        server_codes_values = server_codes_result.get('values', [])
        for i in server_codes_values:
            Config.server_codes[int(i[0])] = i[1]
        print(Config.server_codes)

    @app_commands.command(description='Prints the value of a config entry by name')
    @app_commands.describe(name='Name of the config entry to look up')
    async def config_load(self, interaction: discord.Interaction, name: str):
        if name not in Config.config:
            await interaction.response.send_message("No config with that name found!", ephemeral=True)
        else:
            await interaction.response.send_message(str(Config.config[name]))



async def setup(bot):
    await bot.add_cog(Config(bot))
