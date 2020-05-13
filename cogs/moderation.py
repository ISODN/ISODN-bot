import discord
from discord.ext import commands

Cog = commands.Cog
import os
from datetime import datetime
from apiclient import discovery
from google.oauth2 import service_account
from cogs import assorted as ast

SPREADSHEET_ID = '1TVztC2NKbqwKesAh5C3u5GRi09SlwOTpMSwEasjOX4Y'
PUN_RANGE = 'Log!A3:H'

server_codes = {}
mod_codes = {}


class Moderation(Cog):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    secret_file = os.path.join(os.getcwd(), 'config/credentials.json')

    credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
    service = discovery.build('sheets', 'v4', credentials=credentials)

    def __init__(self, bot):
        self.bot = bot
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                          range="Staff Codes!A2:E").execute()
        values = result.get('values', [])
        for i in values:
            mod_codes[int(i[2])] = i[4]
        print(mod_codes)

        server_codes_result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                                       range="Server Codes!A1:B").execute()
        server_codes_values = server_codes_result.get('values', [])
        for i in server_codes_values:
            server_codes[int(i[0])] = i[1]
        print(server_codes)

    def is_mod(ctx):
        return ctx.author.id in mod_codes

    @commands.command(aliases=['pl'])
    @commands.check(is_mod)
    async def punishment_log(self, ctx, userid: int):
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []

        for row in values:
            # print(row)
            if int(row[3]) == userid:
                user_punishments.append(row)

        if len(user_punishments) == 0:
            await ctx.send("This user has no punishments logged. ")
            return
        else:
            return_string = 'User punishments for: {}\n```'.format(userid)
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} by {} for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[6], row[7])
            return_string += '``` User has incurred {} punishments.'.format(len(user_punishments))
            # print(return_string)
            await ctx.send(return_string)

    @commands.command(aliases=['psc'])
    async def punishment_self_check(self, ctx):
        userid = ctx.author.id
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []

        for row in values:
            # print(row)
            if int(row[3]) == userid:
                user_punishments.append(row)

        if len(user_punishments) == 0:
            await ctx.send("I couldn't find any punishments for you.")
            return
        else:
            return_string = 'Your punishments are: ```'
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} by {} for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[6], row[7])
            return_string += '``` You have incurred {} punishments.'.format(len(user_punishments))
            # print(return_string)
            await ctx.send(return_string)

    @commands.command(aliases=['pr'])
    @commands.check(is_mod)
    async def punishment_record(self, ctx, user: discord.User, pun, *, reason):
        # Get the number of rows
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        r_body = {
            'values': [[num_rows + 1, datetime.utcnow().isoformat(), server_codes[ctx.guild.id],
                        str(user.id), user.name, pun, mod_codes[ctx.author.id], reason]]
        }
        request = self.service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range="Log!A3",
                                                              valueInputOption='RAW', insertDataOption='OVERWRITE',
                                                              body=r_body)
        response = request.execute()
        await ctx.send("Punishment successfully recorded. ")

    @commands.command(aliases=['pc'])
    @commands.check(is_mod)
    async def punishment_check(self, ctx, mod_code):
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []
        for row in values:
            if row[6] == mod_code:
                user_punishments.append(row)
        if len(user_punishments) == 0:
            await ctx.send("This user has not given out any punishments. ")
            return
        else:
            return_string = 'User punishments from: {}\n```'.format(mod_code)
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} to {}[{}] for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[4], row[3], row[7])
            return_string += '``` {} has given {} punishments.'.format(mod_code, len(user_punishments))
            # print(return_string)
            for i in ast.split_msg_bylines(return_string):
                await ctx.send(i)
            return

    @commands.command(aliases=['pw'])
    @commands.check(is_mod)
    async def punishment_warn(self, ctx, user: discord.User, official: bool, *, reason):
        warn_embed = discord.Embed(
            title='Official Warning from ISODN Staff' if official else 'Unofficial Warning from ISODN Staff',
            color=0xFF0000)
        warn_embed.add_field(name='Server', value=server_codes[ctx.guild.id], inline=False)
        warn_embed.add_field(name='Staff Member', value=mod_codes[ctx.author.id], inline=False)
        warn_embed.add_field(name='Reason', value=reason, inline=False)

        if user.dm_channel is None:
            await user.create_dm()
        await user.dm_channel.send(embed=warn_embed)

        # Get the number of rows
        result = self.service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        r_body = {
            'values': [[num_rows + 1, datetime.utcnow().isoformat(), server_codes[ctx.guild.id],
                        str(user.id), user.name, 'Warn' if official else 'Unofficial', mod_codes[ctx.author.id],
                        reason]]
        }
        request = self.service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, range="Log!A3",
                                                              valueInputOption='RAW', insertDataOption='OVERWRITE',
                                                              body=r_body)
        response = request.execute()
        await ctx.send("Punishment successfully recorded. ")


def setup(bot):
    bot.add_cog(Moderation(bot))
