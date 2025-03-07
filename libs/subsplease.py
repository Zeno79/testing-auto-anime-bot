import asyncio
import hashlib
import shutil
import sys
from itertools import count
from traceback import format_exc

import anitopy
from feedparser import parse

from database import LOGS, DataBase
from core.executors import Executors


class SubsPlease:
    def __init__(self, dB: DataBase):
        self.db = dB

    def digest(self, string: str):
        return hashlib.sha256(string.encode()).hexdigest()

    def _exit(self):
        LOGS.info("Stopping The Bot...")
        try:
            for folder in ["downloads", "thumbs", "encode"]:
                shutil.rmtree(folder, ignore_errors=True)
        except Exception:
            LOGS.error(format_exc())
        sys.exit(0)

    def rss_feed_data(self):
        """Fetch RSS feeds for available resolutions."""
        try:
            return (
                parse("https://subsplease.org/rss/?r=1080"),
                parse("https://subsplease.org/rss/?r=720"),
                parse("https://subsplease.org/rss/?r=480"),
            )
        except KeyboardInterrupt:
            self._exit()
        except Exception:
            LOGS.error(format_exc())
            return None, None, None

    async def feed_optimizer(self):
        """Process the latest anime releases and filter out batches."""
        d1080, d720, d480 = self.rss_feed_data()
        if not d1080 or not d720 or not d480:
            return None

        for i in range(2, -1, -1):  # Loop through latest entries
            try:
                f1080, f720, f480 = d1080.entries[i], d720.entries[i], d480.entries[i]
                a1080, a720, a480 = (
                    anitopy.parse(f1080.title).get("anime_title"),
                    anitopy.parse(f720.title).get("anime_title"),
                    anitopy.parse(f480.title).get("anime_title"),
                )

                if a1080 == a720 == a480:
                    if any("[Batch]" in title for title in [f1080.title, f720.title, f480.title]):
                        continue  # ✅ Skip batch releases

                    uid = self.digest(f1080.title + f720.title + f480.title)
                    if not await self.db.is_anime_uploaded(uid):
                        return {
                            "uid": uid,
                            "1080p": f1080,
                            "720p": f720,
                            "480p": f480,
                        }
            except Exception:
                LOGS.error(format_exc())
                return None

    async def generate_360p(self, file_path, output_path):
        """Convert 480p file to 360p using ffmpeg."""
        try:
            LOGS.info(f"Generating 360p version for {file_path}...")
            cmd = f"ffmpeg -i {file_path} -vf scale=-1:360 -c:v libx264 -preset fast -crf 28 -c:a copy {output_path}"
            process = await asyncio.create_subprocess_shell(cmd)
            await process.communicate()
            LOGS.info(f"360p version saved at {output_path}")
            return output_path
        except Exception as e:
            LOGS.error(f"Error generating 360p: {e}")
            return None

    async def on_new_anime(self, function):
        """Continuously check for new anime releases."""
        for _ in count():
            data = await self.feed_optimizer()
            if data:
                # ✅ Generate 360p from 480p before processing
                file_480p = f"downloads/{data['480p'].title}"
                file_360p = file_480p.replace("480p", "360p")
                
                converted_360p = await self.generate_360p(file_480p, file_360p)
                if converted_360p:
                    data["360p"] = {"title": file_360p, "link": file_360p}

                await function(data)
                await self.db.add_anime(data.get("uid"))
            await asyncio.sleep(5)
            
