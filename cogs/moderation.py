import discord
from discord.ext import commands
from discord.utils import get

import unicodedata

Cog = commands.Cog
from datetime import datetime, timedelta
from cogs import assorted as ast
from cogs import config as cfg

PUN_RANGE = 'Log!A3:H'


def strip_fonts(txt):
    return unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')


def get_punishment_embed(ctx, punishment, reason):
    embed = discord.Embed(title=f'{punishment} from ISODN Staff', colour=0xAA0000)
    embed.add_field(name='Punishment', value=punishment, inline=False)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed


class Moderation(Cog):
    SPREADSHEET_ID = None

    def __init__(self, bot):
        self.bot = bot

    def is_mod(ctx):
        return ctx.author.id in cfg.Config.mod_codes

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        normalised = strip_fonts(member.display_name).lower()
        for bw in self.bot.secret_config['bw']:
            if bw in normalised:
                await member.kick()
                await self.bot.get_channel(self.bot.secret_config['com_chat']).send(
                    f'Kicked {str(member)} from server {member.guild.id} ({cfg.Config.server_codes[member.guild.id]}'
                )

    async def record_punishment(self, ctx, user, punishment, reason):
        # Get the number of rows
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        # Write this data
        r_body = {
            'values': [[num_rows + 1, datetime.utcnow().isoformat(), cfg.Config.server_codes[ctx.guild.id],
                        str(user), self.bot.get_user(user).name if self.bot.get_user(user) is not None else 'Unknown',
                        punishment, cfg.Config.mod_codes[ctx.author.id], reason]]
        }
        cfg.Config.service.spreadsheets().values().append(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range="Log!A3",
            valueInputOption='RAW', insertDataOption='OVERWRITE',
            body=r_body).execute()
        await ctx.send("Punishment successfully recorded. ")

    @commands.command(aliases=['pl', 'pun_log'])
    @commands.check(is_mod)
    async def logbyuser(self, ctx, userid: int):
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
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

    @commands.command(aliases=['psc', 'my_punishments'])
    async def punishment_self_check(self, ctx):
        # load all punishments
        userid = ctx.author.id
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []

        # get all punishments which pertain to that user
        for row in values:
            # print(row)
            if int(row[3]) == userid:
                user_punishments.append(row)

        # send it in DMs
        if ctx.author.dm_channel is None:
            await ctx.author.create_dm()
        if len(user_punishments) == 0:
            await ctx.author.dm_channel.send("I couldn't find any punishments for you.")
            return
        else:
            return_string = 'Your punishments are: ```'
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} by {} for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[6], row[7])
            return_string += '``` You have incurred {} punishments.'.format(len(user_punishments))
            # print(return_string)
            await ctx.author.dm_channel.send(return_string)

    @commands.command(aliases=['pr'])
    @commands.check(is_mod)
    async def record(self, ctx, user: discord.User, pun, *, reason):
        await self.record_punishment(ctx, user.id, pun, reason)
        await user.send(embed=get_punishment_embed(ctx, pun, reason))

    @commands.command(aliases=['pc'])
    @commands.check(is_mod)
    async def logbymod(self, ctx, mod_code):
        # load all punishments
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []

        # get punishments which relate to the particular user
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

    @commands.command()
    @commands.check(is_mod)
    async def warn(self, ctx, user: discord.User, official: bool, *, reason):
        warn_embed = get_punishment_embed(ctx, 'Official Warning' if official else 'Unofficial Warning', reason)

        if user.dm_channel is None:
            await user.create_dm()
        await user.dm_channel.send(embed=warn_embed)

        # Get the number of rows
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        r_body = {
            'values': [[num_rows + 1, datetime.utcnow().isoformat(), cfg.Config.server_codes[ctx.guild.id],
                        str(user.id), user.name, 'Warn' if official else 'Unofficial',
                        cfg.Config.mod_codes[ctx.author.id],
                        reason]]
        }
        request = cfg.Config.service.spreadsheets().values().append(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range="Log!A3",
            valueInputOption='RAW', insertDataOption='OVERWRITE',
            body=r_body)
        response = request.execute()
        await ctx.send("Punishment successfully recorded. ")

    @commands.command()
    @commands.check(is_mod)
    async def netban(self, ctx, user: int, *, reason):
        if user in cfg.Config.mod_codes:
            await ctx.send("Can't network ban a mod!")
            return

        try:
            await self.bot.get_user(user).send(embed=get_punishment_embed(ctx, 'Network Ban', reason))
        except:
            await ctx.send("Can't DM to them. Maybe they aren't in any ISODN servers? ")

        for server in cfg.Config.server_codes:
            try:
                await self.bot.get_guild(server).ban(discord.Object(user), reason=reason)
                await ctx.send("Banned {} in {}. ".format(user, cfg.Config.server_codes[server]))
            except:
                await ctx.send("Error banning {} in {}. Does the bot have the required permissions? ".format(user,
                                                                                                             cfg.Config.server_codes[
                                                                                                                 server]))
        await self.record_punishment(ctx, user, 'Network Ban', reason)

    @commands.command()
    @commands.check(is_mod)
    async def unnetban(self, ctx, userid: int, *, reason):
        for server in cfg.Config.server_codes:
            try:
                await self.bot.get_guild(server).unban(discord.Object(userid), reason=reason)
                await ctx.send("Unbanned {} from {}.".format(userid, cfg.Config.server_codes[server]))
            except:
                await ctx.send(
                    "Couldn't unban {} from {}. Is the bot lacking permissions or are they not banned?".format(userid,
                                                                                                               cfg.Config.server_codes[
                                                                                                                   server]))

    @Cog.listener()
    async def on_message(self, message):
        def strToT(x):
            return datetime.strptime(x, r'%Y-%m-%d %H:%M')
        def tToStr(x):
            return x.strftime(r'%Y-%m-%d %H:%M')
        def roundMin(x):
            return x - timedelta(seconds = x.second, microseconds = x.microsecond)

        # Handle reactions and stuff
        if message.channel.id in cfg.Config.config['voting_channels']:
            if (message.channel.id != cfg.Config.config['mod_announcements']) or (message.content[:4].lower() == 'vote'):
                await message.add_reaction('👍')
                await message.add_reaction('🤷')
                await message.add_reaction('👎')

        # Moderate pings
        mentions = len(set(filter(lambda x: not x.bot, message.mentions)))
        if not message.author.bot and message.guild != None and mentions > 0:
        
            ss_id = cfg.Config.config['sheets']['isodn_punishment_log']
            ss = cfg.Config.service.spreadsheets().get(
                spreadsheetId=ss_id).execute()
            # Create sheet 'Pings' if doesn't exist
            if not 'Pings' in [i['properties']['title'] for i in ss['sheets']]:
                cfg.Config.service.spreadsheets().batchUpdate(
                    spreadsheetId=ss_id,
                    body={"requests": [{"addSheet": {"properties": {"title": "Pings"}}}]} 
                    ).execute()
                cfg.Config.service.spreadsheets().values().append(
                    spreadsheetId=ss_id, range='Pings!A1', valueInputOption='RAW', insertDataOption='OVERWRITE',
                    body={"values": [['Last updated', '2000-01-01 00:00'],
                        ['Guild', 'User ID', 'Username', 'Minute count', 'Violate count', 'Unmute']]}
                    ).execute()

            # Record pings
            now = datetime.now()
            ping_log = cfg.Config.service.spreadsheets().values().get(
                spreadsheetId=ss_id, range='Pings!A3:F'
                ).execute().get('values', [])
            length = len(ping_log)
            last_time = strToT(cfg.Config.service.spreadsheets().values().get(
                spreadsheetId=ss_id, range='Pings!B1'
                ).execute().get('values', [])[0][0])
            index = None
            if now.date() != last_time.date():
                ping_log = []
            if roundMin(now) != roundMin(last_time):
                ping_log = list(filter(lambda x: x[4] != '0', ping_log))
                for i in ping_log:
                    i[3] = '0'
            for i in range(len(ping_log)):
                if int(ping_log[i][1]) == message.author.id and int(ping_log[i][0]) == message.guild.id:
                    ping_log[i][3] = str(int(ping_log[i][3]) + mentions)
                    index = i
                    break
            else:
                index = len(ping_log)
                ping_log.append([str(message.guild.id), str(message.author.id), message.author.name, str(mentions), '0', '/'])

            # Check pings
            ping_limit = 5
            min_limit = 10          # Number of pings in a minute
            daily_limit = 30        # Number of pings involved in violations in a day
            muted = get(message.guild.roles, name="muted")

            async def mute(minutes):
                mute_until = datetime.now() + timedelta(minutes = minutes)
                if ping_log[index][5] == '/' or strToT(ping_log[index][5]) < mute_until:
                    ping_log[index][5] = tToStr(mute_until)
                    try:
                        await message.author.add_roles(muted)
                        ast.Timer(60 * minutes, unmute)
                    except:
                        await message.channel.send(f"Error muting {message.author.mention}. Does the bot have the required permissions? ")
                    await message.channel.send(f'{message.author.mention} was muted for {minutes} minutes for spam pinging')
                    try:
                        await message.author.send(
                            f'You were muted in {message.guild} for spam pinging. '
                            f'If you disagree with this, please dm one of the mods')
                    except:
                        await message.channel.send("Can't DM to them. Maybe they aren't in any ISODN servers? ")
            async def unmute():
                try:
                    if strToT(ping_log[index][5]) <= datetime.now():
                        await message.author.remove_roles(muted)
                except:
                    pass

            if int(ping_log[index][3]) >= min_limit:
                await mute(int(ping_log[index][3]))
                ping_log[index][4] = str(int(ping_log[index][4]) + int(ping_log[index][3]))
                ping_log[index][3] = '0'
            if mentions >= ping_limit:
                await mute(mentions)
                ping_log[index][4] = str(int(ping_log[index][4]) + mentions)
                ping_log[index][3] = '0'
            if int(ping_log[index][4]) >= daily_limit:
                ctx = await self.bot.get_context(message)
                ctx.author = self.bot.user
                await self.netban(ctx, message.author.id, reason = 'Spam pinging')

            # Update sheet
            if length > len(ping_log):
                print(cfg.Config.service.spreadsheets().values().clear(
                spreadsheetId=ss_id, range=f"Pings!A{len(ping_log)+3}:F{length+2}", body={}).execute())
            cfg.Config.service.spreadsheets().values().update(
                spreadsheetId=ss_id, range="Pings!B1", valueInputOption="RAW", 
                body={"range": "Pings!B1", "values": [[tToStr(now)]]} 
                ).execute()
            cfg.Config.service.spreadsheets().values().update(
                spreadsheetId=ss_id, range="Pings!A3:F", valueInputOption="RAW", 
                body={"range": "Pings!A3:F", "values": ping_log} 
                ).execute()
        


def setup(bot):
    bot.add_cog(Moderation(bot))
