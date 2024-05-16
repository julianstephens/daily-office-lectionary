import json
import logging
import random
from datetime import datetime
from typing import Literal

import discord
import pytz
from liturgical_calendar import liturgical

from daily_office_lectionary.config import conf
from daily_office_lectionary.db import db

guild = discord.Object(id=conf["discord_guild_id"])


class LectionaryClient(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


intents = discord.Intents.default()
client = LectionaryClient(intents=intents)


def format_reading(reading: dict, time: Literal["mp", "ep"] = "mp") -> str:
    return (
        f"Psalms: {reading[time+'_psalms']}\n"
        f"Reading 1: {reading[time+'_1']}\n"
        f"Reading 2: {reading[time+'_2']}"
    )


def to_camel(*args):
    first = args[0].lower()
    rest = [x.title() for x in args[1:]]
    return first + "".join(rest)


def get_collect(date=None):
    nth = {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "ninth",
        10: "tenth",
        11: "eleventh",
        12: "twelfth",
    }
    curr_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
    date_str = curr_date.strftime("%Y-%m-%d")
    data = db.get(date_str)
    collects = [
        """Almighty and most merciful God, grant that by the indwelling
of your Holy Spirit we may be enlightened and strengthened
for your service; through Jesus Christ our Lord, who lives and
reigns with you, in the unity of the Holy Spirit, one God, now
and for ever. Amen."""
    ]
    if data:
        json_data = json.loads(str(data, "utf-8"))  # type: ignore
        if "collect" in json_data:
            collects.append(json_data["collect"])
    dayinfo = liturgical.liturgical_calendar(date_str)
    week = nth[dayinfo["weekno"]] if dayinfo["weekno"] else None  # type: ignore
    season = dayinfo["season"]  # type: ignore
    weekday = datetime.now().strftime("%A")
    name = dayinfo["name"]  # type: ignore

    if name:
        dname = (
            name.lower()
            if len(name.strip().split(" ")) == 1
            else to_camel(*name.split(" "))
        )
        potentials = [dname, dname + "I", dname + "II", dname + "III"]
        res = db.mget(*potentials)
        filtered_res = [str(r, "utf-8") for r in list(filter(lambda x: x, res))]  # type: ignore
        if len(filtered_res) == 1:
            return filtered_res[0]
        elif len(filtered_res) > 1:
            return filtered_res[random.randint(0, len(filtered_res) - 1)]

    if season.lower() == "easter" and week == 1:
        id = to_camel(weekday, "after", "easter")
        res = db.get(id)
        return str(res, "utf-8") if res else collects[0]  # type: ignore

    id = to_camel(season, week, weekday)
    backupId = to_camel(season, week, "sunday")

    res = db.get(id)
    bres = db.get(backupId)

    if not res and bres and len(collects) == 1:
        return str(bres, "utf-8")  # type: ignore
    elif res:
        return str(res, "utf-8")  # type: ignore

    return (
        collects[1:][random.randint(0, len(collects[1:]) - 1)]
        if len(collects) > 1
        else collects[0]
    )


@client.tree.command()
async def collect(interaction: discord.Interaction):
    res = get_collect()
    await interaction.response.send_message(
        f"**Collect of the Day for {datetime.now(pytz.timezone('US/Eastern')).strftime('%A, %B %d, %Y')}**\n"
        + res
    )


@client.tree.command()
async def morning(interaction: discord.Interaction):
    res = db.get(datetime.now().strftime("%Y-%m-%d"))
    if res:
        json_data = json.loads(str(res, "utf-8"))  # type: ignore
        await interaction.response.send_message(
            f"**Morning Lessons for {datetime.now(pytz.timezone('US/Eastern')).strftime('%A, %B %d, %Y')}**\n"
            + format_reading(json_data)
        )
    else:
        await interaction.response.send_message("Something went wrong")


@client.tree.command()
async def evening(interaction: discord.Interaction):
    res = db.get(datetime.now().strftime("%Y-%m-%d"))
    if res:
        json_data = json.loads(str(res, "utf-8"))  # type: ignore
        logging.info(json_data)
        await interaction.response.send_message(
            f"**Evening Lessons for {datetime.now(pytz.timezone('US/Eastern')).strftime('%A, %B %d, %Y')}**\n"
            + format_reading(json_data, "ep")
        )
    else:
        await interaction.response.send_message("Something went wrong")
