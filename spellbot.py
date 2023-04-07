import os

from datetime import datetime
from spellinator.constants import color_crimson

import dotenv
import hikari
import lightbulb


def create_help(embed: hikari.Embed) -> hikari.Embed:
    cmd = (
        '''```
/spell <word> [<show_phonemes>: True | False]
```'''
    )

    embed.title = "Spellbot Command Help"
    embed.description = cmd

    return embed


class CustomHelp(lightbulb.BaseHelpCommand):
    async def send_bot_help(self, context: lightbulb.context) -> None:
        help_embed = (
            hikari.Embed(
                title="Spellbot Help",
                color=color_crimson,
                timestamp=datetime.now().astimezone(),
            )

            .set_footer(
                text=f"Requested by {context.member.display_name}",
                icon=context.member.avatar_url or context.member.default_avatar_url,
            )

            .add_field(
                "Valid Commands",
                "```spell <word> [<show_phonemes>: True | False]```",
                inline=False,
            )
        )

        await context.bot.sync_application_commands()

        await context.respond(help_embed)

    async def send_command_help(self, context: lightbulb.context, command: lightbulb.command) -> None:
        help_embed = (
            hikari.Embed(
                title="Spellbot Command Help",
                color=color_crimson,
                timestamp=datetime.now().astimezone(),
            )

            .set_footer(
                text=f"Requested by {context.member.display_name}",
                icon=context.member.avatar_url or context.member.default_avatar_url,
            )

            .add_field(
                "Valid Commands",
                "```spell <word> [<show_phonemes>: True | False]```",
                inline=False,
            )
        )

        if command.name == "spell":
            help_embed = create_help(help_embed)

        await context.respond(help_embed)

    async def send_group_help(
            self,
            context: lightbulb.context,
            group
    ) -> None:
        pass

    async def send_plugin_help(self, context: lightbulb.context, plugin: lightbulb.plugins.Plugin) -> None:
        pass


dotenv.load_dotenv()

bot = lightbulb.BotApp(
    os.environ['BOT_TOKEN'],
    prefix='+',
    banner=None,
    intents=hikari.Intents.ALL,
    #default_enabled_guilds=(694706423170465877, 687788876286394373, 694226432586547231),
    help_class=CustomHelp,
    help_slash_command=True,
)

bot.load_extensions_from("./extensions", must_exist=True)

if __name__ == '__main__':
    if os.name != 'nt':
        import uvloop

        uvloop.install()

    bot.run()
