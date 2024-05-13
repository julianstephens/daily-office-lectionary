from .bot import client
from .config import conf
import logging

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

if __name__ == "__main__":
    client.run(conf["discord_token"], log_handler=handler, log_level=logging.DEBUG)
