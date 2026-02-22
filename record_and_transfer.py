import record
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
from pathlib import Path
from loguru import logger
from db import RecordingDB
import requests

TEMP_DIR = f"{os.getcwd()}/tmp_recordings"
RECORDER_DOCKER_IMAGE = "sjdjsifh/stream-recorder:latest"
KOTOL_BASE_URL = "https://temp.kotol.cloud"
KOTOL_API_URL = f"{KOTOL_BASE_URL}/api/file-upload?expiration=900000"


def upload_and_cleanup(name: str, directory: str = TEMP_DIR):
    file_path = Path(os.path.join(directory, name))
    if not file_path.exists:
        logger.error(f"path: {file_path} does not exist")
        return

    db = RecordingDB()

    with open(file_path, mode="rb") as f:
        headers = {
            "File-Name": name
        }

        response = requests.post(KOTOL_API_URL, headers=headers, files={"file": (name, f, "video/mp4")})

        try:
            data = response.json()

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Post response error: {e.msg}")
            logger.debug(f"Reponse: {response}: {response.text}")
            db.update_recording_status(name, "error")
            return

        cloud_url = f"{KOTOL_BASE_URL}/?c={data['code']}"
        expire_epoch = int(data["expiration"])

        if not db.set_recording_url(name, cloud_url, expire_epoch):
            logger.error("db error. URL not saved.")
            return

        logger.success(f"File {name} uploaded to kotol cloud. Link: {cloud_url}")

    try:
        file_path.unlink()
        logger.success(f"File {name} cleaned up after successful upload and DB update.")
    except OSError as e:
        logger.warning(f"Failed to delete {file_path}: {e}")


def record_and_transfer(
    name: str, url: str, seconds: str, start_date_prague: str | None = None
):
    os.makedirs(TEMP_DIR, exist_ok=True)
    record.build_recorder(recorder_image=RECORDER_DOCKER_IMAGE)

    if not start_date_prague:
        now = datetime.now().astimezone(ZoneInfo("Europe/Prague"))
        start_date_prague = now.strftime("%Y-%m-%d-%H-%M")

    name = f"{name}-{start_date_prague}"

    args = [name, url, seconds, start_date_prague]
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{TEMP_DIR}:/workspace",
        RECORDER_DOCKER_IMAGE,
    ] + args

    db = RecordingDB()
    db.insert_recording(f"{name}.mp4", "pending")
    try:
        subprocess.run(cmd, check=True)
        upload_and_cleanup(f"{name}.mp4")
    except:
        logger.error("error.")


# def main():
#     os.makedirs(TEMP_DIR, exist_ok=True)

#     arguments = {}

#     record.build_recorder()
#     record.run_recorder(arguments)
# upload_and_cleanup(name)
