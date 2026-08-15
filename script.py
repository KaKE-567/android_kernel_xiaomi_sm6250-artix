#!/usr/bin/env python3
"""
ArtixV4 Telegram Uploader
Uploads Image.gz-dtb or AnyKernel3 zip to Telegram.
"""
import os
import sys
import subprocess
import json
import requests

CONFIG_FILE = os.path.expanduser("~/.tg_kernel_config")

def load_saved_credentials():
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("token"), data.get("chat_id")
        except Exception:
            pass
    return None, None

saved_token, saved_chat_id = load_saved_credentials()

KERNEL_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(KERNEL_DIR, "out/arch/arm64/boot/Image.gz-dtb")
ANYKERNEL_DIR = os.path.join(KERNEL_DIR, "anykernel")
OUT_DIR = os.path.join(KERNEL_DIR, "out")

TOKEN = (
    (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None) or
    os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TG_TOKEN") or
    saved_token
)

CHAT_ID = (
    (sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else None) or
    os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID") or os.getenv("TG_CHAT_ID") or
    saved_chat_id
)

TARGET_FILE = sys.argv[3] if len(sys.argv) > 3 else None

if not TOKEN or not CHAT_ID:
    print("❌ Error: Missing Telegram Bot Token or Chat ID!")
    print("\nUsage:")
    print("  python3 script.py <BOT_TOKEN> <CHAT_ID> [FILE_PATH]")
    print("  or: ./tg_send.py (Interactive)")
    sys.exit(1)

# If no target file specified, package AnyKernel3 zip or use Image.gz-dtb
if not TARGET_FILE:
    if os.path.isdir(ANYKERNEL_DIR) and os.path.isfile(IMAGE_PATH):
        # Auto-package AnyKernel3 zip
        commit_hash = subprocess.check_output(["git", "-C", KERNEL_DIR, "rev-parse", "--short", "HEAD"]).decode().strip()
        zip_name = f"ArtixV4-AntiGravity-{commit_hash}.zip"
        zip_path = os.path.join(OUT_DIR, zip_name)
        
        ak_image = os.path.join(ANYKERNEL_DIR, "Image.gz-dtb")
        subprocess.run(["cp", "-f", IMAGE_PATH, ak_image], check=True)
        subprocess.run(f"cd '{ANYKERNEL_DIR}' && zip -r9 '{zip_path}' . -x '*.git*' > /dev/null", shell=True, check=True)
        if os.path.isfile(ak_image):
            os.remove(ak_image)
        TARGET_FILE = zip_path
    elif os.path.isfile(IMAGE_PATH):
        TARGET_FILE = IMAGE_PATH
    else:
        print(f"❌ Error: Compiled kernel image not found at {IMAGE_PATH}")
        sys.exit(1)

if not os.path.isfile(TARGET_FILE):
    print(f"❌ Error: File '{TARGET_FILE}' not found!")
    sys.exit(1)

file_name = os.path.basename(TARGET_FILE)
file_size_mb = os.path.getsize(TARGET_FILE) / (1024 * 1024)
url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"

print(f"🚀 Uploading '{file_name}' ({file_size_mb:.2f} MB) to Telegram...")

try:
    with open(TARGET_FILE, "rb") as f:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": "🔥 ArtixV4 Gaming Kernel for Xiaomi SM6250 (BBRplus, Dynamic Fsync, KernelSU, 300Hz)"
            },
            files={"document": f},
            timeout=180
        )
    res_json = response.json()
    if res_json.get("ok"):
        print(f"✅ Success! '{file_name}' was sent to your Telegram chat.")
    else:
        print(f"❌ Telegram API Error: {res_json.get('description', 'Unknown error')}")
except requests.exceptions.RequestException as e:
    print(f"❌ Network/Request error: {e}")
