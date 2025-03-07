import asyncio
import os
import secrets
import shutil
from glob import glob
from traceback import format_exc

from telethon import Button

from core.bot import LOGS, Bot, Var
from database import DataBase
from functions.info import AnimeInfo
from functions.tools import Tools
from libs.logger import Reporter


class Executors:
    def __init__(
        self,
        bot: Bot,
        dB: DataBase,
        configurations: dict,
        input_file: str,
        info: AnimeInfo,
        reporter: Reporter,
    ):
        self.is_original = configurations.get("original_upload")
        self.is_button = configurations.get("button_upload")
        self.anime_info = info
        self.bot = bot
        self.input_file = input_file
        self.tools = Tools()
        self.db = dB
        self.reporter = reporter
        self.msg_id = None
        self.output_file = None

    async def execute(self):
        try:
            rename = await self.anime_info.rename(self.is_original)
            self.output_file = f"encode/{rename}"
            thumb = await self.tools.cover_dl((await self.anime_info.get_poster()))
            if self.is_original:
                await self.reporter.started_renaming()
                succ, out = await self.tools.rename_file(
                    self.input_file, self.output_file
                )
                if not succ:
                    return False, out
            else:
                _log_msg = await self.reporter.started_compressing()
                succ, _new_msg = await self.tools.compress(
                    self.input_file, self.output_file, _log_msg
                )
                if not succ:
                    return False, _new_msg
                self.reporter.msg = _new_msg

            await self.reporter.started_uploading()
            if self.is_button:
                msg = await self.bot.upload_anime(
                    self.output_file, rename, thumb or "thumb.jpg", is_button=True
                )
                btn = Button.url(
                    f"{self.anime_info.data.get('video_resolution')}",
                    url=f"https://t.me/{((await self.bot.get_me()).username)}?start={msg.id}",
                )
                self.msg_id = msg.id
                return True, btn

            msg = await self.bot.upload_anime(
                self.output_file, rename, thumb or "thumb.jpg"
            )
            self.msg_id = msg.id
            return True, []
        except BaseException:
            await self.reporter.report_error(str(format_exc()), log=True)
            return False, str(format_exc())

    def run_further_work(self):
        asyncio.run(self.further_work())

    async def further_work(self):
        try:
            if self.msg_id:
                await self.reporter.started_gen_ss()
                msg = await self.bot.get_messages(
                    Var.BACKUP_CHANNEL if self.is_button else Var.MAIN_CHANNEL,
                    ids=self.msg_id,
                )

                # ✅ Removed MediaInfo and Sample & Screenshots buttons
                btn = [[]]  # Empty buttons list

                await self.reporter.all_done()
                
                # ✅ Cleanup operation
                try:
                    os.remove(self.input_file)
                    os.remove(self.output_file)
                except BaseException:
                    LOGS.error(str(format_exc()))

        except BaseException:
            await self.reporter.report_error(str(format_exc()), log=True)
            
