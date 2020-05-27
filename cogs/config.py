from discord.ext import commands
import bidict

Cog = commands.Cog
from discord.ext import commands
from ruamel import yaml
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
        with open('config/config.yml') as cfgfile:
            Config.config = yaml.safe_load(cfgfile)
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

    @commands.command(aliases=['cfl'])
    async def config_load(self, ctx, name):
        if name not in Config.config:
            await ctx.send("No config with that name found!")
        else:
            await ctx.send(str(Config.config[name]))



def setup(bot):
    bot.add_cog(Config(bot))
