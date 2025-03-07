#    This file is part of the AutoAnime distribution.
#    Copyright (c) 2025 Kaif_00z
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/kaif-00z/AutoAnimeBot/blob/main/LICENSE > .

# if you are using this following code then don't forgot to give proper
# credit to t.me/kAiF_00z (github.com/kaif-00z)

from traceback import format_exc

import anitopy

from libs.kitsu import RawAnimeInfo
from libs.logger import LOGS


class AnimeInfo:
    def __init__(self, name):
        self.kitsu = RawAnimeInfo()
        self.CAPTION = """
**{}
━━━━━━━━━━━━━━━
‣ Language:** `Japanese [#    This file is part of the AutoAnime distribution.
#    Copyright (c) 2025 Kaif_00z
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in <
# https://github.com/kaif-00z/AutoAnimeBot/blob/main/LICENSE > .

# if you are using this following code then don't forgot to give proper
# credit to t.me/kAiF_00z (github.com/kaif-00z)

from decouple import config


class Var:
    # Version

    __version__ = "v0.0.8"

    # Telegram Credentials

    API_ID = config("API_ID", default=6, cast=int)
    API_HASH = config("API_HASH", default="eb06d4abfb49dc3eeb1aeb98ae0f581e")
    BOT_TOKEN = config("BOT_TOKEN", default=None)
    SESSION = config("SESSION", default=None)

    # Database Credentials

    MONGO_SRV = config("MONGO_SRV", default=None)

    # Channels Ids

    BACKUP_CHANNEL = config("BACKUP_CHANNEL", default=0, cast=int)
    MAIN_CHANNEL = config("MAIN_CHANNEL", cast=int)
    LOG_CHANNEL = config("LOG_CHANNEL", cast=int)
    CLOUD_CHANNEL = config("CLOUD_CHANNEL", cast=int)
    FORCESUB_CHANNEL = config("FORCESUB_CHANNEL", default=0, cast=int)
    OWNER = config("OWNER", default=0, cast=int)

    # Other Configs

    THUMB = config(
        "THUMBNAIL", default="https://graph.org/file/ad1b25807b81cdf1dff65.jpg"
    )
    FFMPEG = config("FFMPEG", default="ffmpeg")
    CRF = config("CRF", default="27")
    SEND_SCHEDULE = config("SEND_SCHEDULE", default=False, cast=bool)
    RESTART_EVERDAY = config("RESTART_EVERDAY", default=True, cast=bool)
    LOG_ON_MAIN = config("LOG_ON_MAIN", default=False, cast=bool)
    FORCESUB_CHANNEL_LINK = config("FORCESUB_CHANNEL_LINK", default="", cast=str)

    # Dev Configs

    DEV_MODE = config("DEV_MODE", default=False, cast=bool)
]`
**‣ Quality:** `480p|720p|1080p`
**‣ Season:** `{}`
**‣ Episode:** `{}`
**━━━━━━━━━━━━━━━**
**‣Join :- @Unfold_Network
"""
        self.proper_name = self.get_proper_name_for_func(name)
        self.name = name
        self.data = anitopy.parse(name)

    async def get_english(self):
        anime_name = self.data.get("anime_title")
        try:
            anime = (await self.kitsu.search(self.proper_name)) or {}
            return anime.get("english_title") or anime_name
        except BaseException:
            LOGS.error(str(format_exc()))
            return anime_name.strip()

    async def get_poster(self):
        try:
            if self.proper_name:
                anime_poster = await self.kitsu.search(self.proper_name)
                return anime_poster.get("poster_img") or None
        except BaseException:
            LOGS.error(str(format_exc()))

    async def get_cover(self):
        try:
            if self.proper_name:
                anime_poster = await self.kitsu.search(self.proper_name)
                if anime_poster.get("anilist_id"):
                    return anime_poster.get("anilist_poster")
                return None
        except BaseException:
            LOGS.error(str(format_exc()))

    async def get_caption(self):
        try:
            if self.proper_name or self.data:
                return self.CAPTION.format(
                    (await self.get_english()),
                    str(self.data.get("anime_season") or 1).zfill(2),
                    (
                        str(self.data.get("episode_number")).zfill(2)
                        if self.data.get("episode_number")
                        else "N/A"
                    ),
                )
        except BaseException:
            LOGS.error(str(format_exc()))
            return ""

    async def rename(self, original=False):
        try:
            anime_name = self.data.get("anime_title")
            if anime_name and self.data.get("episode_number"):
                return (
                    f"[S{self.data.get('anime_season') or 1}-{self.data.get('episode_number') or ''}] {(await self.get_english())} [{self.data.get('video_resolution')}].mkv".replace(
                        "‘", ""
                    )
                    .replace("’", "")
                    .strip()
                )
            if anime_name:
                return (
                    f"{(await self.get_english())} [{self.data.get('video_resolution')}].mkv".replace(
                        "‘", ""
                    )
                    .replace("’", "")
                    .strip()
                )
            return self.name
        except Exception as error:
            LOGS.error(str(error))
            LOGS.exception(format_exc())
            return self.name

    def get_proper_name_for_func(self, name):
        try:
            data = anitopy.parse(name)
            anime_name = data.get("anime_title")
            if anime_name and data.get("episode_number"):
                return (
                    f"{anime_name} S{data.get('anime_season')} {data.get('episode_title')}"
                    if data.get("anime_season") and data.get("episode_title")
                    else (
                        f"{anime_name} S{data.get('anime_season')}"
                        if data.get("anime_season")
                        else anime_name
                    )
                )
            return anime_name
        except Exception as error:
            LOGS.error(str(error))
            LOGS.exception(format_exc())
            
