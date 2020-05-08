import discord
from discord.ext import commands
Cog = commands.Cog
import httplib2
import os
from datetime import datetime
from apiclient import discovery
from google.oauth2 import service_account

SPREADSHEET_ID = '1TVztC2NKbqwKesAh5C3u5GRi09SlwOTpMSwEasjOX4Y'
PUN_RANGE = 'Log!A3:H'

SERVER_IDS = {
    533153217119387658 : 'Mathematics',
    601528888908185655 : 'Physics',
    529123158440149046 : 'Chemistry'
}
mod_ids = []

class Moderation(Cog):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    secret_file = os.path.join(os.getcwd(), 'config/credentials.json')


    credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
    service = discovery.build('sheets', 'v4', credentials=credentials)

    def __init__(self, bot):
        self.bot = bot
        result = self.service.spreadsheets().values().get(spreadsheetId = SPREADSHEET_ID, range = "Staff Codes!A2:E").execute()
        values = result.get('values', [])
        for i in values:
            mod_ids.append(int(i[2]))

    def is_mod(ctx):
        return ctx.author.id in mod_ids

    @commands.command(aliases=['pl'])
    @commands.check(is_mod)
    async def punishmentlog(self, ctx, userid: int):
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []

        for row in values:
            #print(row)
            if int(row[3]) == userid:
                user_punishments.append(row)

        if len(user_punishments) == 0:
            await ctx.send("This user has no punishments logged. ")
            return
        else:
            return_string = 'User punishments for: {}\n```'.format(userid)
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} by {} for {}\n'\
                    .format(row[0], row[1], row[2], row[5], row[6], row[7])
            return_string += '``` User has incurred {} punishments.'.format(len(user_punishments))
            #print(return_string)
            await ctx.send(return_string)

    @commands.command(aliases=['pr'])
    @commands.check(is_mod)
    async def punishment_record(self, ctx, user: discord.User, mod, pun, *, reason):
        #Get the number of rows
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        r_body = {
            'values' : [[num_rows + 1, datetime.utcnow().isoformat(), SERVER_IDS[ctx.guild.id],
                user.id, user.name, pun, mod, reason]]
        }
        request = self.service.spreadsheets().values().append(spreadsheetId = SPREADSHEET_ID, range = "Log!A3",
            valueInputOption = 'USER_ENTERED', insertDataOption = 'OVERWRITE', body = r_body)
        response = request.execute()
        await ctx.send("Punishment successfully recorded. ")

def setup(bot):
    bot.add_cog(Moderation(bot))