from stream_recorder import StreamRecorder
import argparse
from argparse import Namespace
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def build_stream_recorder(arguments: Namespace) -> StreamRecorder | None:
    if not type(arguments.name) is str:
        return None

    if not type(arguments.site_url) is str:
        return None

    if not type(arguments.length) is int or arguments.length < 1:
        return None

    try:
        start_naive: datetime = datetime.strptime(
            arguments.start_time, "%Y-%m-%d-%H-%M"
        )
        prague_time = start_naive.replace(tzinfo=ZoneInfo("Europe/Prague"))
        start_time = prague_time.astimezone(ZoneInfo("UTC"))

    except ValueError:
        print(
            "Invalid start time date format.\n"
            "Expected (YYYY-MM-DD-HH-MM, e.g. 2026-02-18-10-30 for 18. 02. 2025 10:30)"
        )
        return None

    return StreamRecorder(
        arguments.name, arguments.site_url, arguments.length, start_time
    )


def parse_arguments() -> StreamRecorder | None:
    utc_now: datetime = datetime.now(tz=timezone.utc)
    prague_now: datetime = utc_now.astimezone(ZoneInfo("Europe/Prague"))
    datetime_now = prague_now.strftime("%Y-%m-%d-%H-%M")

    parser = argparse.ArgumentParser(
        description="FI Muni Stream link (url with classroom) and recording time in minutes"
    )
    parser.add_argument("name", type=str, help="Recording name")
    parser.add_argument(
        "site_url",
        type=str,
        help="url of the room stream (not m3u8), e.g. https://live.stream/room123.html",
    )
    parser.add_argument(
        "length",
        type=int,
        nargs="?",
        help="desired recording length in seconds (default is 7200)",
        default=7200,
    )
    parser.add_argument(
        "start_time",
        type=str,
        nargs="?",
        default=datetime_now,
        help="Start at YYYY-MM-DD-HH-MM (optional, starts immediately if omitted)",
    )

    input_args: Namespace = parser.parse_args()
    return build_stream_recorder(input_args)


def main():
    recorder: StreamRecorder | None = parse_arguments()
    if not recorder:
        return

    assert recorder is not None

    recorder.wait_for_start_time()
    recorder.record()


if __name__ == "__main__":
    main()
