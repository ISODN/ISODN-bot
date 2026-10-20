import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import asyncio

import unicodedata

Cog = commands.Cog
from datetime import datetime, timedelta, timezone
from cogs import assorted as ast
from cogs import config as cfg

PUN_RANGE = 'Log!A3:H'


def strip_fonts(txt):
    return unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')


def get_punishment_embed(interaction, punishment, reason):
    embed = discord.Embed(title=f'{punishment} from ISODN Staff', colour=0xAA0000)
    embed.add_field(name='Punishment', value=punishment, inline=False)
    embed.add_field(name='Reason', value=reason, inline=False)
    return embed


async def respond(interaction, content=None, embed=None, ephemeral=False):
    """Send a reply to the interaction, using a followup if it was already responded to."""
    if interaction.response.is_done():
        await interaction.followup.send(content, embed=embed, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content, embed=embed, ephemeral=ephemeral)


def is_mod(interaction: discord.Interaction) -> bool:
    return interaction.user.id in cfg.Config.mod_codes


class Moderation(Cog):
    SPREADSHEET_ID = None

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # NOTE: dormant unless the (privileged) members intent is enabled
        normalised = strip_fonts(member.display_name).lower()
        for bw in self.bot.secret_config['bw']:
            if bw in normalised:
                await member.kick()
                await self.bot.get_channel(self.bot.secret_config['com_chat']).send(
                    f'Kicked {str(member)} from server {member.guild.id} ({cfg.Config.server_codes[member.guild.id]}'
                )

    async def record_punishment(self, interaction, user, punishment, reason):
        # Get the number of rows
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        # Resolve the username, falling back when the user can't be fetched
        try:
            username = (await self.bot.fetch_user(user)).name
        except discord.HTTPException:
            username = 'Unknown'
        # Write this data
        r_body = {
            'values': [[num_rows + 1, datetime.now(timezone.utc).isoformat(), cfg.Config.server_codes[interaction.guild.id],
                        str(user), username, punishment, cfg.Config.mod_codes[interaction.user.id], reason]]
        }
        cfg.Config.service.spreadsheets().values().append(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range="Log!A3",
            valueInputOption='RAW', insertDataOption='OVERWRITE',
            body=r_body).execute()
        await respond(interaction, "Punishment successfully recorded. ")

    @app_commands.command(name='logbyuser', description='Lists all punishments logged for a user ID')
    @app_commands.check(is_mod)
    @app_commands.describe(user_id='Discord user ID to look up')
    async def logbyuser(self, interaction: discord.Interaction, user_id: int):
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        values = result.get('values', [])
        user_punishments = []

        for row in values:
            # print(row)
            if int(row[3]) == user_id:
                user_punishments.append(row)

        if len(user_punishments) == 0:
            await respond(interaction, "This user has no punishments logged. ", ephemeral=True)
            return
        else:
            return_string = 'User punishments for: {}\n```'.format(user_id)
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} by {} for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[6], row[7])
            return_string += '``` User has incurred {} punishments.'.format(len(user_punishments))
            # print(return_string)
            await respond(interaction, return_string)

    @app_commands.command(name='punishment_self_check', description='DMs you a list of your own punishments')
    async def punishment_self_check(self, interaction: discord.Interaction):
        # load all punishments
        userid = interaction.user.id
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
        if interaction.user.dm_channel is None:
            await interaction.user.create_dm()
        if len(user_punishments) == 0:
            await interaction.user.dm_channel.send("I couldn't find any punishments for you.")
        else:
            return_string = 'Your punishments are: ```'
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} by {} for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[6], row[7])
            return_string += '``` You have incurred {} punishments.'.format(len(user_punishments))
            # print(return_string)
            await interaction.user.dm_channel.send(return_string)
        await respond(interaction, 'Sent you a DM.', ephemeral=True)

    @app_commands.command(name='record', description='Records a punishment and DMs the user')
    @app_commands.check(is_mod)
    @app_commands.guild_only()
    @app_commands.describe(user='User to punish', punishment='Name of the punishment', reason='Reason for the punishment')
    async def record(self, interaction: discord.Interaction, user: discord.User, punishment: str, reason: str):
        await self.record_punishment(interaction, user.id, punishment, reason)
        await user.send(embed=get_punishment_embed(interaction, punishment, reason))

    @app_commands.command(name='logbymod', description='Lists all punishments issued by a mod code')
    @app_commands.check(is_mod)
    @app_commands.describe(mod_code='Mod code to look up')
    async def logbymod(self, interaction: discord.Interaction, mod_code: str):
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
            await respond(interaction, "This user has not given out any punishments. ", ephemeral=True)
            return
        else:
            return_string = 'User punishments from: {}\n```'.format(mod_code)
            for row in user_punishments:
                return_string += '#{} at {} in {} server:\t{} to {}[{}] for {}\n' \
                    .format(row[0], row[1], row[2], row[5], row[4], row[3], row[7])
            return_string += '``` {} has given {} punishments.'.format(mod_code, len(user_punishments))
            # print(return_string)
            for i in ast.split_msg_bylines(return_string):
                await respond(interaction, i)
            return

    @app_commands.command(name='warn', description='Warns a user and records the warning')
    @app_commands.check(is_mod)
    @app_commands.guild_only()
    @app_commands.describe(user='User to warn', official='Whether the warning is official',
                           reason='Reason for the warning')
    async def warn(self, interaction: discord.Interaction, user: discord.User, official: bool, reason: str):
        warn_embed = get_punishment_embed(interaction, 'Official Warning' if official else 'Unofficial Warning', reason)

        # Get the number of rows
        result = cfg.Config.service.spreadsheets().values().get(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range=PUN_RANGE).execute()
        num_rows = len(result.get('values', []))
        r_body = {
            'values': [[num_rows + 1, datetime.now(timezone.utc).isoformat(), cfg.Config.server_codes[interaction.guild.id],
                        str(user.id), user.name, 'Warn' if official else 'Unofficial',
                        cfg.Config.mod_codes[interaction.user.id],
                        reason]]
        }
        request = cfg.Config.service.spreadsheets().values().append(
            spreadsheetId=cfg.Config.config['sheets']['isodn_punishment_log'], range="Log!A3",
            valueInputOption='RAW', insertDataOption='OVERWRITE',
            body=r_body)
        response = request.execute()
        await respond(interaction, "Punishment successfully recorded. ")

        if user.dm_channel is None:
            await user.create_dm()
        await user.dm_channel.send(embed=warn_embed)
        await respond(interaction, "DM successfully sent.")

    @app_commands.command(name='netban', description='Bans a user ID from all ISODN servers')
    @app_commands.check(is_mod)
    @app_commands.guild_only()
    @app_commands.describe(user_id='Discord user ID to ban', reason='Reason for the ban')
    async def netban(self, interaction: discord.Interaction, user_id: int, reason: str):
        if user_id in cfg.Config.mod_codes:
            await respond(interaction, "Can't network ban a mod!", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(embed=get_punishment_embed(interaction, 'Network Ban', reason))
        except discord.HTTPException:
            await respond(interaction, "Can't DM to them. Maybe they aren't in any ISODN servers? ")

        for server in cfg.Config.server_codes:
            try:
                await self.bot.get_guild(server).ban(discord.Object(user_id), reason=reason)
                await respond(interaction, "Banned {} in {}. ".format(user_id, cfg.Config.server_codes[server]))
            except Exception:
                await respond(interaction, "Error banning {} in {}. Does the bot have the required permissions? ".format(user_id,
                                                                                                                         cfg.Config.server_codes[
                                                                                                                             server]))
        await self.record_punishment(interaction, user_id, 'Network Ban', reason)

    @app_commands.command(name='unnetban', description='Unbans a user ID from all ISODN servers')
    @app_commands.check(is_mod)
    @app_commands.guild_only()
    @app_commands.describe(user_id='Discord user ID to unban', reason='Reason for the unban')
    async def unnetban(self, interaction: discord.Interaction, user_id: int, reason: str):
        for server in cfg.Config.server_codes:
            try:
                await self.bot.get_guild(server).unban(discord.Object(user_id), reason=reason)
                await respond(interaction, "Unbanned {} from {}.".format(user_id, cfg.Config.server_codes[server]))
            except Exception:
                await respond(interaction,
                              "Couldn't unban {} from {}. Is the bot lacking permissions or are they not banned?".format(user_id,
                                                                                                                       cfg.Config.server_codes[
                                                                                                                           server]))

    @app_commands.command(name='purge_user', description="Purges a user's messages from all channels in this server")
    @app_commands.check(is_mod)
    @app_commands.guild_only()
    @app_commands.describe(user_id='Discord user ID whose messages to purge',
                           hours='How far back to purge, in hours')
    async def purge_user(self, interaction: discord.Interaction, user_id: int, hours: int = 24):
        for channel in interaction.guild.text_channels:
            try:
                def check(m):
                    return m.author.id == user_id
                await channel.purge(limit=500, check=check, after=datetime.now(timezone.utc) - timedelta(hours=hours))
            except Exception:
                try:
                    await respond(interaction, f'Failed to purge in {channel.mention}. Does the bot have the required permissions? ')
                except Exception:
                    pass
        await respond(interaction, f'Purged {user_id}\'s messages in this server. ')

    @Cog.listener()
    async def on_message(self, message):
        # Handle reactions and stuff
        if message.channel.id in cfg.Config.config['voting_channels']:
            if (message.channel.id != cfg.Config.config['mods_mod_announcements']) or (message.content[:4].lower() == 'vote'):
                await message.add_reaction('👍')
                await message.add_reaction('🤷')
                await message.add_reaction('👎')

        # Check pings
        # NOTE: dormant unless the (privileged) message_content intent is enabled,
        # because message content and mentions are not available without it
        ping_limit = 5
        if len(message.mentions) >= ping_limit:
            muted = get(message.guild.roles, name="muted")
            helper_team = get(message.guild.roles, name="Helper Team")
            trusted_bot = get(message.guild.roles, name="trusted bot")

            allow_mass_ping = False

            if helper_team != None and helper_team in message.author.roles:
                allow_mass_ping = True
            if trusted_bot != None and trusted_bot in message.author.roles:
                allow_mass_ping = True

            if not allow_mass_ping:
                await message.author.add_roles(muted)
                await message.channel.send(f'{message.author.mention} was muted for {len(message.mentions)} minutes for '
                                        f'pinging {len(message.mentions)} people')
                await message.author.send(
                    f'You were muted in {message.guild} for mass pinging. '
                    f'If you disagree with this, please dm one of the mods')
                await asyncio.sleep(60 * len(message.mentions))
                await message.author.remove_roles(muted)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
