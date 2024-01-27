import re

import hikari
import lightbulb

from spellinator.spellinator import main
from spellinator.constants import *

from datetime import datetime
from pprint import pprint

spell_plugin = lightbulb.Plugin("Spell")


@spell_plugin.command
@lightbulb.option(
    'show_phonemes',
    "Show phonemes",
    type=hikari.OptionType.BOOLEAN,
    default=False,
)
@lightbulb.option(
    "word",
    "Word to spellinate",
    type=str,
    required=True,
    modifier=lightbulb.OptionModifier.GREEDY,
)
@lightbulb.command(
    "spell",
    "Respell a word",
)
@lightbulb.implements(lightbulb.SlashCommand)
async def standard_spell(ctx: lightbulb.Context) -> None:
    await spell(ctx)


async def spell(ctx: lightbulb.Context, index: int = None) -> None:
    word = ctx.options.word

    if not word:
        await ctx.respond("No word specified.")
        return

    response = hikari.Embed(
        color=color_neongreen,
        timestamp=datetime.now().astimezone()
    )
    if len(word) > 14:
        err_str = 'Sorry, that word is too long, results will take a long time to generate.'
        response.add_field(name='Error', value=err_str, inline=True)

    else:
        spell_args = [word, '-s', '20', '--print-width', '60', '--limit', '10']
        if ctx.options.show_phonemes:
            spell_args.append('-a')

        spellings = main(spell_args)

        response.add_field(name='Spellings', value=f'```{spellings}```', inline=True)

    response.description = f'```{word}```'
    response.title = None

    response.set_footer(
        text=f"Requested by {ctx.member.display_name}",
        icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
    )

    await ctx.respond(response)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(spell_plugin)
