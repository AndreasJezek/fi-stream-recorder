# 🎥 FI MUNI Stream Recorder

Automated stream recorder for lecture rooms at **Masaryk University – Faculty of Informatics (FI MUNI)**.

This project automatically:

- Opens a classroom stream page  
- Extracts the `.m3u8` stream URL using Playwright  
- Records the stream using FFmpeg  
- Saves it as an `.mp4` file  
- Supports scheduled start time (Europe/Prague timezone)  
- Runs locally or inside Docker  

---

# 🚀 Features

- ✅ Automatic `.m3u8` extraction  
- ✅ Scheduled recording (Brno / Europe/Prague time)  
- ✅ Configurable recording length  
- ✅ Dockerized for easy setup  
- ✅ H.264 (libx264) + AAC output  
- ✅ 1280×720 scaling  
- ✅ Timestamped output filenames  
- ✅ Interactive CLI runner  

---


# 🐳 Recommended Usage (Docker – Interactive CLI)

This is the easiest and safest way to use the recorder.

## 🔧 Requirements

- Docker installed
- Python3 (3.9+) installed for record.py launcher
- Internet connection

---

## ▶️ Run the interactive runner

```bash
python3 record.py
```

The script will:

1. Pull the Docker image:
   ```
   sjdjsifh/stream-recorder:latest
   ```
2. Ask for:
   - 📝 Recording name  
   - 🔗 Room URL (or choose predefined FI rooms)  
   - ⏱️ Recording length (minutes)  
   - 🕐 Start time (Brno timezone)  
3. Automatically run the container  
4. Save the recording into:

```
./recordings
```

---

## 🏫 Predefined FI MUNI Rooms

```
1: https://live.cesnet.cz/munifia217.html
2: https://live.cesnet.cz/munifia218.html
3: https://live.cesnet.cz/munifia318.html
4: https://live.cesnet.cz/munifia319.html
5: https://live.cesnet.cz/munifia320.html
```

You can also paste your own valid classroom stream URL.

---

# 🖥 Running Without Docker

## 🔧 Requirements

- Python 3.12+
- FFmpeg installed and available in PATH
- Chromium dependencies
- pip

---

## 📥 Install dependencies

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

---

## ▶️ Run manually

```bash
python main.py NAME SITE_URL LENGTH_SECONDS START_TIME
```

### Example

```bash
python main.py algebra https://live.cesnet.cz/munifia217.html 5400 2026-02-20-10-00
```

---

# 🧾 CLI Arguments

| Argument | Description |
|----------|------------|
| `name` | Name of output file |
| `site_url` | URL of classroom page (NOT m3u8) |
| `length` | Recording length in seconds (default: 7200) |
| `start_time` | `YYYY-MM-DD-HH-MM` (Europe/Prague timezone) |

If `start_time` is omitted, recording starts immediately.

---

# 🕐 Time Handling

- Input start time is interpreted as **Europe/Prague**
- Internally converted to **UTC**
- Recorder waits automatically until the scheduled time

Format:

```
YYYY-MM-DD-HH-MM
Example:
2026-02-20-10-30
```

If no start time is provided, current Prague time is used and recording starts immediately.

---

# 🎬 How It Works

1. Launches headless Chromium via Playwright  
2. Intercepts network requests  
3. Captures the `.m3u8` stream URL  
4. Sends the stream to FFmpeg  
5. Records into:

```
/workspace/<name>-YYYY-MM-DD-HH-MM.mp4
```

In Docker mode, `/workspace` is mapped to:

```
./recordings
```

---

# 🐳 Docker Details

### Base Image

```
python:3.12-slim-bookworm
```

### Installed in Container

- FFmpeg  
- Playwright  
- Chromium browser  
- Python dependencies  

### Entrypoint

```bash
python -u main.py
```

---

# 🎥 Output Details

- Container path: `/workspace`
- Host path (Docker mode): `./recordings`
- Video codec: libx264
- Audio codec: aac
- CRF: 23
- Preset: slower
- Resolution: 1280×720
- Output format: MP4

Output filename format:

```
<name>-YYYY-MM-DD-HH-MM.mp4
```

Timestamp is based on Europe/Prague timezone.

---

# 🧠 Internal Components

## `StreamRecorder`

Responsible for:

- Waiting until scheduled start time  
- Launching Playwright  
- Extracting `.m3u8` URL  
- Running FFmpeg  
- Logging progress  

## `record.py`

Interactive helper that:

- Pulls Docker image  
- Collects user input  
- Creates `./recordings` directory  
- Mounts volume to container  
- Executes recording  

## `main.py`

- Parses CLI arguments  
- Converts Prague time → UTC  
- Starts recording workflow  

---

# 🛠 Troubleshooting

## Recording does not start

- Ensure URL is correct  
- Verify stream is active  
- Check Docker is running  
- Confirm internet connection  

## FFmpeg error

- Stream may not be available yet  
- Network interruption  
- Invalid `.m3u8` URL  

## Playwright issues

Reinstall browsers:

```bash
playwright install --with-deps chromium
```

---

# ⚠️ Important Notes

- Do NOT interrupt the recording process  
- Existing files with the same name will be overwritten  
- Ensure Docker has permission to write into `./recordings`  
- The classroom page must contain a playable video button  

---

---
Created for personal academic use ONLY!
---

# 👨‍💻 Author

Andreas Jezek
