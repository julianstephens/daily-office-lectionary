from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod"), env_file_encoding="utf-8"
    )

    discord_token: str = "xxx"
    discord_guild_id: str = "xxx"
    redis_host: str = "xxx"
    redis_port: int = 6379
    redis_password: str = "xxx"


conf = Settings().model_dump()
