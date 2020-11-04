import logging
import re
import traceback

import discord
from discord.ext import commands
from ruamel import yaml

cfgfile = open("config/config.yml")
config = yaml.safe_load(cfgfile)

class ISODNBot(commands.Bot):
    def __init__(self, prefix):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(prefix, intents=intents)
        self.config = config
        self.secret_config = yaml.safe_load(open('config/secret_config.yml'))
        logging.basicConfig(level=logging.INFO, format='[%(name)s %(levelname)s] %(message)s')
        self.logger = logging.getLogger('bot')
        try:
            with open(f'config/{config["blacklist"]}', 'r') as blacklist:
                self.blacklist = list(map(
                    int, filter(lambda x: x.strip(), blacklist.readlines())
                ))
        except IOError:
            self.blacklist = []

    async def on_ready(self):
        self.logger.info('Connected to Discord')
        self.logger.info('Guilds  : {}'.format(len(self.guilds)))
        self.logger.info('Users   : {}'.format(len(set(self.get_all_members()))))
        self.logger.info('Channels: {}'.format(len(list(self.get_all_channels()))))
        await self.set_presence(
            "ISODN Bot [Discord International Network for Olympiads in Sciences: Achieving Unachievable Results]")

        for cog in self.config['cogs']:
            try:
                self.load_extension(cog)
            except Exception:
                self.logger.exception('Failed to load cog {}.'.format(cog))
            else:
                self.logger.info('Loaded cog {}.'.format(cog))

    async def on_message(self, message):
        if message.author.bot: return
        if message.author.id in self.blacklist: return
        await self.process_commands(message)

    async def set_presence(self, text):
        game = discord.Game(name=text)
        await self.change_presence(activity=game)

    async def on_command_error(self, ctx: commands.Context, exception: Exception):
        if isinstance(exception, commands.CommandInvokeError):
            # all exceptions are wrapped in CommandInvokeError if they are not a subclass of CommandError
            # you can access the original exception with .original
            exception: commands.CommandInvokeError
            if isinstance(exception.original, discord.Forbidden):
                # permissions error
                try:
                    await ctx.send('Permissions error: `{}`'.format(exception))
                except discord.Forbidden:
                    # we can't send messages in that channel
                    pass
                return

            elif isinstance(exception.original, discord.HTTPException):
                try:
                    await ctx.send('Sorry, I can\'t send that.')
                except discord.Forbidden:
                    pass

                return

            # Print to log then notify developers
            try:
                lines = traceback.format_exception(type(exception),
                                                   exception,
                                                   exception.__traceback__)
            except RecursionError:
                raise exception

            self.logger.error(''.join(lines))

            return

        if isinstance(exception, commands.CheckFailure):
            await ctx.send("You are not authorised to use this command. ")
        elif isinstance(exception, commands.CommandOnCooldown):
            exception: commands.CommandOnCooldown
            await ctx.send(f'You\'re going to fast! Try again in {exception.retry_after:.2f} seconds.')

        elif isinstance(exception, commands.CommandNotFound):
            if isinstance(ctx.channel, discord.DMChannel):
                await ctx.send("Command not recognised, please type `m.help` for help.")

        elif isinstance(exception, commands.UserInputError):
            error = ' '.join(exception.args)
            error_data = re.findall('Converting to \"(.*)\" failed for parameter \"(.*)\"\.', error)
            if not error_data:
                await ctx.send('Huh? {}'.format(' '.join(exception.args)))
            else:
                await ctx.send('Huh? I thought `{1}` was supposed to be a `{0}`...'.format(*error_data[0]))
        else:
            info = traceback.format_exception(type(exception), exception, exception.__traceback__, chain=False)
            self.logger.error('Unhandled command exception - {}'.format(''.join(info)))


if __name__ == '__main__':
    with open(f'config/{config["token"]}') as tokfile:
        token = tokfile.readline().rstrip('\n')

    ISODNBot(config['prefix']).run(token)
