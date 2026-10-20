import logging
import traceback

import discord
from discord import app_commands
from discord.ext import commands
from ruamel.yaml import YAML

yaml = YAML(typ='safe', pure=True)
cfgfile = open("config/config.yml")
config = yaml.load(cfgfile)

class ISODNBot(commands.Bot):
    def __init__(self, prefix):
        intents = discord.Intents.default()
        super().__init__(prefix, intents=intents)
        self.config = config
        self.secret_config = yaml.load(open('config/secret_config.yml'))
        logging.basicConfig(level=logging.INFO, format='[%(name)s %(levelname)s] %(message)s')
        self.logger = logging.getLogger('bot')
        try:
            with open(f'config/{config["blacklist"]}', 'r') as blacklist:
                self.blacklist = list(map(
                    int, filter(lambda x: x.strip(), blacklist.readlines())
                ))
        except IOError:
            self.blacklist = []

        self.tree.interaction_check = self.not_blacklisted
        self.tree.on_error = self.on_tree_error

    async def setup_hook(self):
        for cog in self.config['cogs']:
            try:
                await self.load_extension(cog)
            except Exception:
                self.logger.exception('Failed to load cog {}.'.format(cog))
            else:
                self.logger.info('Loaded cog {}.'.format(cog))
        await self.tree.sync()

    async def on_ready(self):
        self.logger.info('Connected to Discord')
        self.logger.info('Guilds  : {}'.format(len(self.guilds)))
        self.logger.info('Users   : {}'.format(len(set(self.get_all_members()))))
        self.logger.info('Channels: {}'.format(len(list(self.get_all_channels()))))
        await self.set_presence(
            "ISODN Bot [Discord International Network for Olympiads in Sciences: Achieving Unachievable Results]")

    async def not_blacklisted(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id not in self.blacklist

    async def set_presence(self, text):
        game = discord.Game(name=text)
        await self.change_presence(activity=game)

    async def respond(self, interaction: discord.Interaction, text: str):
        try:
            if interaction.response.is_done():
                await interaction.followup.send(text, ephemeral=True)
            else:
                await interaction.response.send_message(text, ephemeral=True)
        except discord.HTTPException:
            pass

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            # all exceptions are wrapped in CommandInvokeError if they are not a subclass of AppCommandError
            # you can access the original exception with .original
            error: app_commands.CommandInvokeError
            if isinstance(error.original, discord.Forbidden):
                # permissions error
                await self.respond(interaction, 'Permissions error: `{}`'.format(error.original))
                return

            elif isinstance(error.original, discord.HTTPException):
                await self.respond(interaction, 'Sorry, I can\'t send that.')
                return

            # Print to log
            try:
                lines = traceback.format_exception(type(error),
                                                   error,
                                                   error.__traceback__)
            except RecursionError:
                raise error

            self.logger.error(''.join(lines))

            return

        if isinstance(error, app_commands.CommandOnCooldown):
            error: app_commands.CommandOnCooldown
            await self.respond(interaction, f'You\'re going too fast! Try again in {error.retry_after:.2f} seconds.')

        elif isinstance(error, app_commands.CheckFailure):
            await self.respond(interaction, "You are not authorised to use this command.")

        else:
            info = traceback.format_exception(type(error), error, error.__traceback__, chain=False)
            self.logger.error('Unhandled command exception - {}'.format(''.join(info)))


if __name__ == '__main__':
    with open(f'config/{config["token"]}') as tokfile:
        token = tokfile.readline().rstrip('\n')

    ISODNBot(config['prefix']).run(token)
