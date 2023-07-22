from datetime import datetime, time, timedelta

import hikari
import lightbulb
from pytz import timezone

from spellinator.constants import *

BZ4X_BATT = 66.6

energy_cost_plugin = lightbulb.Plugin("eCost")


@energy_cost_plugin.command
@lightbulb.option(
    'start',
    'Start Time',
    type=hikari.OptionType.STRING,
    default='17:00',
)
@lightbulb.option(
    'stop',
    'Stop Time',
    type=hikari.OptionType.STRING,
    default='22:00',
)
@lightbulb.option(
    'isoc',
    'State of Charge Start',
    type=hikari.OptionType.INTEGER,
)
@lightbulb.option(
    'esoc',
    "Ending State of Charge",
    type=hikari.OptionType.INTEGER,
)
@lightbulb.option(
    'force_peak',
    'Force peak pricing',
    default=False,
    type=hikari.OptionType.BOOLEAN,
)
@lightbulb.option(
    'force_offpeak',
    'Force offpeak pricing',
    default=False,
    type=hikari.OptionType.BOOLEAN,
)
@lightbulb.option(
    'verbose',
    'More Verbose Output',
    default=False,
    type=hikari.OptionType.BOOLEAN,
)
@lightbulb.command(
    "ecost",
    "Energy Cost",
)
@lightbulb.implements(lightbulb.SlashCommand)
async def energy_cost(ctx: lightbulb.Context) -> None:
    await ecost(ctx)


def ecost_calculator(
        soc_delta,
        charge_start_time=time.fromisoformat("17:00"),
        charge_stop_time=time.fromisoformat("21:30"),
        force_peak=False,
        force_offpeak=False,
        today_ovrd=None):
    bayarea = timezone('America/Los_Angeles')
    if today_ovrd:
        today_dt = datetime(
            today_ovrd.year,
            today_ovrd.month,
            today_ovrd.day,
            tzinfo=bayarea,
        )
    else:
        today_dt = datetime.now(bayarea)
    current_year = today_dt.year
    current_month = today_dt.month
    current_day = today_dt.day
    tou_d_summer_start = datetime(current_year, 6, 1, tzinfo=bayarea)
    tou_d_summer_end = datetime(current_year, 10, 1, tzinfo=bayarea)

    tou_d_peak_start = datetime(
        year=current_year,
        month=current_month,
        day=current_day,
        hour=17,
    )
    tou_d_peak_end = datetime(
        year=current_year,
        month=current_month,
        day=current_day,
        hour=21,
    )

    # Assume 15% loss on charger for now
    kwh_consumed = (BZ4X_BATT * soc_delta / 100) / 0.85

    charge_start = datetime(
        year=current_year,
        month=current_month,
        day=current_day,
        hour=charge_start_time.hour,
        minute=charge_start_time.minute,
    )
    charge_end = datetime(
        year=current_year,
        month=current_month,
        day=current_day,
        hour=charge_stop_time.hour,
        minute=charge_stop_time.minute,
    )

    charge_time = charge_end - charge_start
    charge_time_hr = charge_time.total_seconds() / 3600

    tou_d_start_peak_overlap = tou_d_peak_end > charge_start and charge_end > tou_d_peak_start
    tou_d_end_peak_overlap = tou_d_peak_end > charge_start and charge_end > tou_d_peak_start
    tou_d_peak_overlap = tou_d_start_peak_overlap or tou_d_end_peak_overlap

    if (today_dt.weekday() < 5) and tou_d_peak_overlap:
        peak_duration = tou_d_peak_end - tou_d_peak_start
        if tou_d_start_peak_overlap:
            peak_duration -= max(timedelta(0), charge_start - tou_d_peak_start)
        if tou_d_end_peak_overlap:
            peak_duration -= max(timedelta(0), tou_d_peak_end - charge_end)

        peak_duration = peak_duration.total_seconds() / 3600
    else:
        peak_duration = 0

    peak_price = 0.49 if (tou_d_summer_start < today_dt < tou_d_summer_end) else 0.40
    peak_price = 0.36 if force_offpeak else peak_price
    peak_price = 0.49 if force_peak else peak_price

    offpeak_price = 0.36 if (tou_d_summer_start < today_dt < tou_d_summer_end) else 0.37
    offpeak_price = 0.49 if force_peak else offpeak_price

    peak_cost = peak_price * peak_duration
    offpeak_cost = offpeak_price * (charge_time_hr - peak_duration)
    average_cost = (peak_cost + offpeak_cost) / charge_time_hr
    total_cost = average_cost * kwh_consumed

    return kwh_consumed, peak_duration, peak_cost, offpeak_cost, charge_time_hr, total_cost, average_cost


async def ecost(ctx: lightbulb.Context) -> None:
    soc_delta = ctx.options.esoc - ctx.options.isoc

    charge_start_time = time.fromisoformat(ctx.options.start)
    charge_stop_time = time.fromisoformat(ctx.options.stop)

    kwh_consumed, peak_duration, peak_cost, offpeak_cost, charge_time_hr, total_cost, average_cost = ecost_calculator(
        soc_delta, charge_start_time, charge_stop_time, ctx.options.force_peak, ctx.options.force_offpeak
    )

    response = hikari.Embed(
        color=color_neongreen,
        timestamp=datetime.now().astimezone()
    )
    response.description = "Cost of Energy"
    response.title = None
    response.add_field(name='KWh', value=f'{kwh_consumed:.3f} KWh')
    if ctx.options.verbose:
        response.add_field(name='Peak Hours', value=f'{peak_duration:.2f}', inline=True)
        response.add_field(name='Offpeak Hours', value=f'{charge_time_hr - peak_duration:.2f}', inline=True)
        response.add_field(name='Peak Cost', value=f'{peak_cost:.2f}', inline=True)
        response.add_field(name='Offpeak Cost', value=f'{offpeak_cost:.2f}', inline=True)
        response.add_field(name='Average Cost per KWh', value=f'${average_cost:.3f}')
    response.add_field(name='Cost', value=f'${total_cost:.2f}')
    response.set_footer(
        text=f"Requested by {ctx.member.display_name}",
        icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
    )
    await ctx.respond(response)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(energy_cost_plugin)
