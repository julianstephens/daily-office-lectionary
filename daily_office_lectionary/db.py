import redis

from daily_office_lectionary.config import conf

db = redis.Redis(
    host=conf["redis_host"],
    port=conf["redis_port"],
    password=conf["redis_password"],
    ssl=True,
)
