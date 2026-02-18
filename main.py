from stream_recorder import StreamRecorder
from playwright.sync_api import sync_playwright, Browser, Page
import ffmpeg
import argparse
from argparse import Namespace
from datetime import datetime, timezone, timedelta
import time
import os


def main():
    print("Parsing Arguments...")
    now = datetime.now()
    datetime_now = now.strftime("%Y-%m-%d-%H-%M")

    parser = argparse.ArgumentParser(description='FI Muni Stream link (url with classroom) and recording time in seconds')
    parser.add_argument('recording_name', type=str, help='Recording name')
    parser.add_argument('stream_url', type=str, help='url of the stream')
    parser.add_argument('recording_time', type=int, nargs='?', help='recording time of the recording in seconds', default=5400)
    parser.add_argument('start_str', type=str, nargs='?', default=datetime_now, 
                        help='Start at YYYY-MM-DD-HH-MM (optional, starts immediately if omitted)')

    args: Namespace = parser.parse_args()

    if args.start_str:
        start_naive = datetime.strptime(args.start_str, '%Y-%m-%d-%H-%M')
        CET = timezone(timedelta(hours=1))
        start_cet = start_naive.replace(tzinfo=CET)

        print(f'Going to record "{args.recording_name}" from {args.stream_url} at {start_cet.strftime("%d. %m. %Y %H:%M")} for {args.recording_time} seconds.')
        wait_until_start(now, start_cet)
    
    record_stream(args.stream_url, args.recording_time, args.recording_name, args.start_str)

def wait_until_start(now: datetime, start_cet: datetime):
    now_utc = now.replace(tzinfo=timezone.utc)
    time_to_sleep = (start_cet - now_utc).total_seconds()
    
    if time_to_sleep > 0:
        print(f'There is time before the stream...\nGoing to sleep for {time_to_sleep} seconds.')
        time.sleep(time_to_sleep)


def record_stream(site_url: str, recording_time: int, recording_name: str, start_datetime: str):
    recorder: StreamRecorder = StreamRecorder()
    
    print('Opening browser.')
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)
        page: Page = browser.new_page()
        page.route('**/*', recorder.handle_route)
        page.goto(site_url)
        page.click('button[title="Play Video"]')
        page.wait_for_timeout(5000)
        browser.close()
    

    if recorder.m3u8_url:
        print('Stream m3u8 link obtained!')
        print('Recording!')
        print('Do not interupt to obtain the recording.')
        output_name = f'recording_{recording_name}_{start_datetime}.mp4'

        ffmpeg.input(recorder.m3u8_url).output(f'/workspace/{output_name}', t=recording_time, c='copy').run()

        print(f'\n\n')
        print(f'✅ Recording Finished!')
        print(f"💾 The recording is saved at: {os.path.basename(f"/workspace/{output_name}")}")
        print(f"Check: ls {output_name}")

if __name__ == '__main__':
    main()