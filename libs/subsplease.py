import asyncio
import hashlib
import shutil
import sys
from itertools import count
from traceback import format_exc

import anitopy
from feedparser import parse

from database import LOGS, DataBase


class SubsPlease:
    def __init__(self, dB: DataBase):
        self.db = dB

    def digest(self, string: str):
        """Generate a SHA-256 hash of a string."""
        return hashlib.sha256(string.encode()).hexdigest()

    def _exit(self):
        """Handles bot shutdown."""
        LOGS.info("Stopping The Bot...")
        try:
            for folder in ["downloads", "thumbs", "encode"]:
                shutil.rmtree(folder, ignore_errors=True)
        except BaseException:
            LOGS.error(format_exc())
        sys.exit(0)

    def rss_feed_data(self):
        """Fetches RSS feeds for different resolutions."""
        try:
            feeds = {
                "1080p": parse("https://subsplease.org/rss/?r=1080"),
                "720p": parse("https://subsplease.org/rss/?r=720"),
                "sd": parse("https://subsplease.org/rss/?r=sd"),  # Contains both 480p & 360p
            }
            if not feeds["1080p"].entries or not feeds["720p"].entries or not feeds["sd"].entries:
                LOGS.warning("One or more RSS feeds are empty.")
                return None
            return feeds
        except KeyboardInterrupt:
            self._exit()
        except BaseException:
            LOGS.error(format_exc())
            return None

    async def feed_optimizer(self):
        """Parses and matches anime episodes across different resolutions."""
        feeds = self.rss_feed_data()
        if not feeds:
            return None

        d1080, d720, dsd = feeds["1080p"], feeds["720p"], feeds["sd"]

        for i in range(min(len(d1080.entries), len(d720.entries), 3)):  # Ensures valid index range
            try:
                f1080, f720 = d1080.entries[i], d720.entries[i]
                f480, f360 = None, None  # Default to None

                # Find 480p and 360p versions in SD feed
                for entry in dsd.entries:
                    title = entry.title.lower()
                    if "480p" in title:
                        f480 = entry
                    elif "360p" in title:
                        f360 = entry
                    if f480 and f360:
                        break  # Stop searching once both are found

                # Extract anime title safely
                a1080 = anitopy.parse(f1080.title).get("anime_title", "")
                a720 = anitopy.parse(f720.title).get("anime_title", "")
                a480 = anitopy.parse(f480.title).get("anime_title", "") if f480 else ""
                a360 = anitopy.parse(f360.title).get("anime_title", "") if f360 else ""

                # Ensure all resolutions belong to the same anime
                if a1080 and a1080 == a720 == a480 == a360:
                    if any("[Batch]" in f.title for f in [f1080, f720, f480 or "", f360 or ""]):
                        continue  # Skip batch releases

                    uid = self.digest(f"{f1080.title}{f720.title}{f480.title if f480 else ''}{f360.title if f360 else ''}")

                    if not await self.db.is_anime_uploaded(uid):
                        return {
                            "uid": uid,
                            "1080p": f1080,
                            "720p": f720,
                            "480p": f480,  # Can be None if not found
                            "360p": f360,  # Can be None if not found
                        }
            except BaseException:
                LOGS.error(format_exc())
                return None

    async def on_new_anime(self, function):
        """Continuously fetches new anime and triggers processing function."""
        while True:
            data = await self.feed_optimizer()
            if data:
                await function(data)
                await self.db.add_anime(data.get("uid"))
            await asyncio.sleep(5)
            
