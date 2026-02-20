import os
import time
import shutil
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

SCANS_DIR = os.environ.get("SCANS_DIR", "/scans")
SENT_DIR = os.environ.get("SENT_DIR", os.path.join(SCANS_DIR, "_sent"))
FAILED_DIR = os.environ.get("FAILED_DIR", os.path.join(SCANS_DIR, "_failed"))
CAPTION_PREFIX = os.environ.get("CAPTION_PREFIX", "New scan")

POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "2.0"))

ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}

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
            timeout=120,
        )
    r.raise_for_status()

def move_file(src: str, dst_dir: str) -> None:
    base = os.path.basename(src)
    dst = os.path.join(dst_dir, base)
    if os.path.exists(dst):
        name, ext = os.path.splitext(base)
        dst = os.path.join(dst_dir, f"{name}_{int(time.time())}{ext}")
    shutil.move(src, dst)

def should_ignore(path: str) -> bool:
    p = path.replace("\\", "/")
    if "/_sent/" in p or "/_failed/" in p:
        return True
    return False

def iter_candidate_files(root: str):
    try:
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isdir(path):
                continue
            if should_ignore(path):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in ALLOWED_EXTS:
                yield path
    except FileNotFoundError:
        return

if __name__ == "__main__":
    print(f"Polling {SCANS_DIR} every {POLL_SECONDS}s", flush=True)
    seen = set()

    while True:
        for path in iter_candidate_files(SCANS_DIR):
            if path in seen:
                continue

            if not is_stable_file(path):
                continue

            try:
                send_to_telegram(path)
                move_file(path, SENT_DIR)
                print(f"Sent: {path}", flush=True)
                seen.add(path)
            except Exception as e:
                print(f"Failed: {path} error={e}", flush=True)
                try:
                    move_file(path, FAILED_DIR)
                except Exception:
                    pass
                seen.add(path)

        time.sleep(POLL_SECONDS)
