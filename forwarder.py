import os
import time
import shutil
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

SCANS_DIR = os.environ.get("SCANS_DIR", "/scans")
SENT_DIR = os.environ.get("SENT_DIR", os.path.join(SCANS_DIR, "_sent"))
FAILED_DIR = os.environ.get("FAILED_DIR", os.path.join(SCANS_DIR, "_failed"))
CAPTION_PREFIX = os.environ.get("CAPTION_PREFIX", "New scan")

os.makedirs(SENT_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

def is_stable_file(path: str, checks: int = 6, delay: float = 0.75) -> bool:
    last = -1
    for _ in range(checks):
        try:
            size = os.path.getsize(path)
        except FileNotFoundError:
            return False
        if size == last and size > 0:
            return True
        last = size
        time.sleep(delay)
    return False

def send_to_telegram(path: str) -> None:
    filename = os.path.basename(path)
    caption = f"{CAPTION_PREFIX}: {filename}"
    with open(path, "rb") as f:
        r = requests.post(
            TELEGRAM_URL,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"document": (filename, f)},
            timeout=90,
        )
    r.raise_for_status()

def move_file(src: str, dst_dir: str) -> None:
    base = os.path.basename(src)
    dst = os.path.join(dst_dir, base)
    if os.path.exists(dst):
        name, ext = os.path.splitext(base)
        dst = os.path.join(dst_dir, f"{name}_{int(time.time())}{ext}")
    shutil.move(src, dst)

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        path = event.src_path

        if "/_sent/" in path or "/_failed/" in path:
            return

        ext = os.path.splitext(path)[1].lower()
        if ext not in [".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
            return

        if not is_stable_file(path):
            return

        try:
            send_to_telegram(path)
            move_file(path, SENT_DIR)
            print(f"Sent: {path}", flush=True)
        except Exception as e:
            print(f"Failed: {path} error={e}", flush=True)
            try:
                move_file(path, FAILED_DIR)
            except Exception:
                pass

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(Handler(), SCANS_DIR, recursive=True)
    observer.start()
    print(f"Watching {SCANS_DIR}", flush=True)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
