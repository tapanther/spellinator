import hikari
import lightbulb
import json
import re
from random import choice, randint, shuffle
from spellinator.constants import *
from datetime import datetime
from pathlib import Path

from spellinator.spellinator import list_columns

beat_of_four_plugin = lightbulb.Plugin("Beat-of-Four")
_syllables = []


@beat_of_four_plugin.command
@lightbulb.option(
    'number',
    'How many names to generate.',
    type=hikari.OptionType.INTEGER,
    default=10,
)
@lightbulb.command(
    'beat-of-four',
    'Generate a Beat-of-Four name.',
)
@lightbulb.implements(lightbulb.SlashCommand)
async def beat_of_four(ctx: lightbulb.Context) -> None:
    await gen_bof_names(ctx)


async def gen_bof_names(ctx: lightbulb.Context) -> None:
    global _syllables
    beat_of_fours = list()
    for x in range(ctx.options.number):
        beat_of_fours.append(gen_beat_of_four(_syllables))

    formatted_bof_names = list_columns(beat_of_fours, 2, True, 6, 20)

    response = hikari.Embed(
        color=color_royalblue,
        timestamp=datetime.now().astimezone()
    )

    response.description = "Beat-of-Four"
    response.title = None
    response.add_field(
        name="List of Beat-of-Four Names",
        value=f'```{formatted_bof_names}```',
        inline=True
    )
    response.set_footer(
        text=f"Requested by {ctx.member.display_name}",
        icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
    )

    await ctx.respond(response)


def gen_beat_of_four(syllables):
    joined = ''

    two_beat = syllables[0]
    three_beat = syllables[1]

    twos = randint(2, 5)
    threes = 4 - twos
    retry = True

    while retry:
        beat_of_four_str = []
        for x in range(twos):
            beat_of_four_str.append(choice(two_beat))

        for x in range(threes):
            beat_of_four_str.append(choice(three_beat))

        shuffle(beat_of_four_str)
        if beat_of_four_str[-1][-1] not in ['a', 'e', 'i', 'o', 'u']:
            if beat_of_four_str[0][0] not in ['y']:
                retry = False

        joined = ''.join(beat_of_four_str).capitalize()
        if re.search(r'((\w)\2)+', joined):
            retry = True

    return joined


def load(bot: lightbulb.BotApp) -> None:
    global _syllables
    syllables_path = Path('spellinator/en/', 'syllables.json')
    with open(syllables_path, 'r') as json_syllable_file:
        _syllables = json.load(json_syllable_file)
    bot.add_plugin(beat_of_four_plugin)


# @beat_of_four_plugin.command
# @lightbulb.command(
#     'sync',
#     'Sync Commands',
# )
# @lightbulb.implements(lightbulb.SlashCommand)
# async def sync_commands(ctx: lightbulb.Context) -> None:
#     guild = hikari.Snowflake(694226432586547231)
#     await ctx.bot.purge_application_commands(guild)
