#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

MAPPED_VOLUME = f"{os.getcwd()}/recordings"
FI_URLS = {
    1: "https://live.cesnet.cz/munifia217.html",
    2: "https://live.cesnet.cz/munifia218.html",
    3: "https://live.cesnet.cz/munifia318.html",
    4: "https://live.cesnet.cz/munifia319.html",
    5: "https://live.cesnet.cz/munifia320.html",
}
PROMPTS = {
    "NAME": f"📝 Name of the recording\n(overwritten if exists in {MAPPED_VOLUME}): ",
    "URL": "🔗 URL (choose by number, or input your own url): ",
    "MINUTES": "⏱️ Recording length in MINUTES (default is 90): ",
    "START_TIME": "🕐 Start (YYYY-MM-DD-HH-MM) (Brno time zone)\n(Starts immediately if nothing provided): ",
}
DOCKER_IMAGE_NAME = "sjdjsifh/stream-recorder:latest"


def get_current_prague_time():
    return datetime.now(ZoneInfo("Europe/Prague")).strftime("%Y-%m-%d-%H-%M")


def build_recorder():
    cmd = ["docker", "pull", DOCKER_IMAGE_NAME]

    subprocess.run(cmd, check=True)


def get_url():
    print("-" * 40)
    print("Available URLs:")
    for key, url in FI_URLS.items():
        print(f"{key}: {url}")

    print("-" * 40)

    url: str = input(PROMPTS["URL"]).strip()

    if url.isdigit():
        url_key = int(url)

        if url_key not in FI_URLS:
            print("❌ Invalid selection.")
            return

        return FI_URLS[url_key]

    return url


def get_start_time():
    input_start = input(PROMPTS["START_TIME"]).strip()
    if not input_start:
        return get_current_prague_time()

    try:
        input_date = (datetime.strptime(input_start, "%Y-%m-%d-%H-%M")).replace(
            tzinfo=ZoneInfo("Europe/Prague")
        )
        return input_date.strftime("%Y-%m-%d-%H-%M")
    except Exception:
        print("❌ Invalid start time format!")


def get_arguments():
    result: dict[str, str] = dict()
    result["name"] = input(PROMPTS["NAME"]).strip() or "recording"

    while (url := get_url()) is None:
        print("URL required!")

    result["url"] = url

    minutes = input(PROMPTS["MINUTES"]).strip()
    result["recording_seconds"] = str(
        int(minutes) * 60 if minutes.isdigit() else 90 * 60
    )

    while (start_time := get_start_time()) is None:
        print("Input start time in valid format, or use default option.")

    result["start_time"] = start_time
    return result


def run_stream_recorder(arguments: dict[str, str]):
    cmd = ["docker", "run", "--rm", "-v", f"{MAPPED_VOLUME}:/workspace", DOCKER_IMAGE_NAME] + [
        arguments["name"],
        arguments["url"],
        arguments["recording_seconds"],
        arguments["start_time"],
    ]

    subprocess.run(cmd, check=True)


def main():
    os.makedirs(MAPPED_VOLUME, exist_ok=True)
    build_recorder()

    print("🎥 FI MUNI Stream Recorder")
    print("=" * 40)

    arguments: dict[str, Any] = get_arguments()

    print(
        f"Executing the recorder for {arguments['name']} for {int(arguments['recording_seconds']) / 60} at {arguments['start_time']}"
    )
    run_stream_recorder(arguments)
    print(f"💾 The recording is saved in: {MAPPED_VOLUME} directory.")


if __name__ == "__main__":
    main()
