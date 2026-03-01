from playwright.sync_api import Route
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time
from playwright.sync_api import sync_playwright, Browser, Page
from ffmpeg import FFmpeg, FFmpegError
import os
from loguru import logger


class StreamRecorder:
    def __init__(self, name: str, site_url: str, length: int, start_time: datetime):
        """Constructor for the StreamRecorder

        name: name of the output recording.\n
        site_url: url of the site from which to scrape, so not m3u8\n
        length: is the length of the recording (time) in SECONDS.\n
        start_time: UTC time from when to start recording\n
        """

        self.m3u8_url: str | None = None
        self.name: str = name
        self.site_url: str = site_url
        self.recording_length: int = length
        self.start_time: datetime = start_time
        self.output_name: str = f"{self.name}.mp4"
        self.output_path: str = f"/workspace/{self.output_name}"

    def wait_for_start_time(self, sleep_interval: int = 60):
        """Sleeps before the start_time comes.

        sleep_interval: how many seconds to sleep between each iteration.
        """

        now: datetime = datetime.now(tz=timezone.utc)
        logger.info(
            f"Current time: {(now.astimezone(ZoneInfo("Europe/Prague"))).strftime('%d/%m/%Y, %H:%M')}."
        )
        logger.info(
            f"Start time: {self.start_time.astimezone(ZoneInfo("Europe/Prague")).strftime('%d/%m/%Y, %H:%M')}."
        )
        logger.info(f"Waiting for the start time...")

        while True:
            now = datetime.now(tz=timezone.utc)
            time_diff: int = int((self.start_time - now).total_seconds())

            if time_diff <= 0:
                return

            logger.info(f"{time_diff // 60}m {time_diff % 60}s left.")
            time.sleep(min(sleep_interval, time_diff))

    def __handle_route(self, route: Route):
        if "m3u8" in route.request.url:
            self.m3u8_url = route.request.url
        route.continue_()

    def __try_play_button(self, page: Page) -> bool:
        """Try multiple play button selectors."""

        selectors = [
            'button[title="Play Video"]',
            'button:has-text("Play")',
            'button[aria-label*="play"]',
            ".play-button",
            'button[icon="play"]',
        ]

        for selector in selectors:
            try:
                logger.debug(f"Trying selector: {selector}")
                page.click(selector, timeout=1000)
                logger.info(f"Play button clicked.")
                return True
            except TimeoutError:
                continue

        logger.warning("No play button found with any selector.")
        return False

    def __extract_m3u8(self, max_retries: int = 3):
        logger.info("Opening browser...")

        for attempt in (1, max_retries + 1):
            try:
                with sync_playwright() as p:
                    browser: Browser = p.chromium.launch(headless=True)
                    page: Page = browser.new_page()
                    page.route("**/*", self.__handle_route)

                    logger.info(
                        f"Attempt {attempt}/{max_retries}: navigating to {self.site_url}"
                    )
                    page.goto(self.site_url)

                    if not self.__try_play_button(page):
                        logger.warning(
                            f"Attempt {attempt}: Play button failed, retrying..."
                        )
                        browser.close()
                        continue

                    logger.info("Waiting for the stream to start...")
                    page.wait_for_timeout(5000)
                    browser.close()

                    if self.m3u8_url:
                        logger.success(
                            f"m3u8 extracted on attempt {attempt}: {self.m3u8_url}"
                        )
                        return

                logger.warning(f"Attempt {attempt}: No m3u8 found despite play button")

            except Exception as e:
                logger.error(f"Attempt {attempt} failed with error: {e}")
                continue

    def record(self):
        """Main recording method.

        First uses playwright in extract_m3u8 to obtain stream link.
        Then blocks and records for the given time to store the stream.
        Lastly makes sure the stream recording is flushed and stored using os.sync().
        """

        self.__extract_m3u8()
        if not self.m3u8_url:
            logger.error("No m3u8 extracted. Nothing to record.")
            return

        logger.info(f"Output path: {self.output_path}")
        logger.success(f"m3u8 link found. Recording.")
        logger.info(f"Success message will appear when the recording is done.")
        logger.info(f"Do not interupt, the recording is running.")

        try:
            (
                FFmpeg()
                .input(self.m3u8_url)
                .option("y")
                .output(
                    self.output_path,
                    t=self.recording_length,
                    vcodec="libx264",
                    crf=23,
                    preset="slower",
                    vf="scale=1280:720",
                    acodec="aac",
                )
                .execute()
            )

            os.sync()
            time.sleep(1)
            logger.success(f"✅ Recording Finished!")

        except FFmpegError as error:
            logger.error(f"FFmpeg error: {error.message}")
