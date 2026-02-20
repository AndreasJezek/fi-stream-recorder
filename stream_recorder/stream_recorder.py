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
        self.output_name: str = (
            f"{self.name}-"
            f"{datetime.strftime((self.start_time.astimezone(ZoneInfo('Europe/Prague'))), '%Y-%m-%d-%H-%M')}"
            ".mp4"
        )
        self.output_path: str = f"/workspace/{self.output_name}"

    def wait_for_start_time(self, sleep_interval: int = 60):
        """Sleeps before the start_time comes.

        sleep_interval: how many seconds to sleep between each iteration.
        """

        now: datetime = datetime.now(tz=timezone.utc)
        # for logging purposes
        now_prague: datetime = now.astimezone(ZoneInfo("Europe/Prague"))
        time_to_sleep: int = int((self.start_time - now).total_seconds())

        if time_to_sleep <= 0:
            return

        logger.info(f"Current time: {now_prague.strftime('%d/%m/%Y, %H:%M')}.")
        logger.info(
            f"Start time: {self.start_time.astimezone(ZoneInfo("Europe/Prague")).strftime('%d/%m/%Y, %H:%M')}."
        )
        logger.info(f"Waiting for the start time...")

        while time_to_sleep - sleep_interval > 0:
            logger.info(f"{time_to_sleep // 60}m {time_to_sleep % 60}s left.")
            time.sleep(sleep_interval)
            time_to_sleep -= sleep_interval

        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

    def __handle_route(self, route: Route):
        if "m3u8" in route.request.url:
            self.m3u8_url = route.request.url
        route.continue_()

    def __click_play_button(self, page: Page) -> bool:
        try:
            page.click('button[title="Play Video"]')
            return True
        except TimeoutError as e:
            logger.warning("Play Button not found, retrying...")
            return False

    def __try_play_button(self, page: Page):
        for _ in range(3):
            if self.__click_play_button(page):
                return
            time.sleep(1)
        logger.error(
            "The page probably does not have a play button or the selector does not match."
        )

    def __extract_m3u8(self):
        logger.info("Opening browser...")
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=True)
            page: Page = browser.new_page()
            page.route("**/*", self.__handle_route)
            page.goto(self.site_url)
            self.__try_play_button(page)
            logger.info("Waiting for the stream to start...")
            page.wait_for_timeout(5000)
            browser.close()

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
