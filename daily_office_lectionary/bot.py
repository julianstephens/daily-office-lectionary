import json
import pytz
import os
from datetime import datetime
from typing import Literal

import discord

from .config import conf

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


def format_oos(oos: dict):
    res = ""
    for k, v in oos.items():
        res += f"{k} => {v}\n"
    return res


@client.tree.command()
async def morning(interaction: discord.Interaction):
    with open(f"{os.path.dirname(__file__)}/lectionary.json", "r") as f:
        lectionary = json.load(f)

    await interaction.response.send_message(
        f"**Morning Lessons for {datetime.now(pytz.timezone('US/Eastern')).strftime('%A, %B %d, %Y')}**\n"
        + format_reading(
            list(
                filter(
                    lambda x: x["date"]
                    == datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d"),
                    lectionary,
                )
            )[0]
        )
    )


@client.tree.command()
async def service_morning(interaction: discord.Interaction):
    with open(f"{os.path.dirname(__file__)}/mp_oos.json", "r") as f:
        oos = json.load(f)

    await interaction.response.send_message(
        "**Morning Prayer Order of Service**:\n" + format_oos(oos)
    )


@client.tree.command()
async def evening(interaction: discord.Interaction):
    with open(f"{os.path.dirname(__file__)}/lectionary.json", "r") as f:
        lectionary = json.load(f)

    await interaction.response.send_message(
        f"**Evening Lessons for {datetime.now(pytz.timezone('US/Eastern')).strftime('%A, %B %d, %Y')}**\n"
        + format_reading(
            list(
                filter(
                    lambda x: x["date"]
                    == datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d"),
                    lectionary,
                )
            )[0],
            "ep",
        )
    )


@client.tree.command()
async def service_evening(interaction: discord.Interaction):
    with open(f"{os.path.dirname(__file__)}/ep_oos.json", "r") as f:
        oos = json.load(f)

    await interaction.response.send_message(
        "**Evening Prayer Order of Service**:\n" + format_oos(oos)
    )
