#!/usr/bin/env python3
"""
ArtixV4 Kernel Telegram Uploader
Packages the compiled kernel into an AnyKernel3 zip and sends it to Telegram.
"""

import os
import sys
import subprocess
import json
import datetime
import requests

CONFIG_FILE = os.path.expanduser("~/.tg_kernel_config")
KERNEL_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(KERNEL_DIR, "out")
IMAGE_PATH = os.path.join(OUT_DIR, "arch/arm64/boot/Image.gz-dtb")
ANYKERNEL_DIR = os.path.join(KERNEL_DIR, "anykernel")

def load_saved_credentials():
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("token"), data.get("chat_id")
        except Exception:
            pass
    return None, None

def save_credentials(token, chat_id):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"token": token, "chat_id": chat_id}, f)
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass

def get_git_info():
    try:
        commit_hash = subprocess.check_output(
            ["git", "-C", KERNEL_DIR, "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        commit_msg = subprocess.check_output(
            ["git", "-C", KERNEL_DIR, "log", "-1", "--format=%s"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        branch = subprocess.check_output(
            ["git", "-C", KERNEL_DIR, "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return commit_hash, commit_msg, branch
    except Exception:
        return "unknown", "Custom build", "artixv4"

def package_anykernel_zip():
    if not os.path.isfile(IMAGE_PATH):
        print(f"❌ Error: Compiled kernel not found at {IMAGE_PATH}")
        print("Please build the kernel first (./build.sh).")
        sys.exit(1)

    if not os.path.isdir(ANYKERNEL_DIR):
        print(f"❌ Error: AnyKernel3 template directory not found at {ANYKERNEL_DIR}")
        sys.exit(1)

    commit_hash, _, _ = get_git_info()
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    zip_name = f"ArtixV4-AntiGravity-SM6250-{commit_hash}-{date_str}.zip"
    zip_out = os.path.join(OUT_DIR, zip_name)

    print(f"📦 Packaging AnyKernel3 zip: {zip_name} ...")
    
    # Copy Image.gz-dtb into anykernel folder
    ak_image = os.path.join(ANYKERNEL_DIR, "Image.gz-dtb")
    subprocess.run(["cp", "-f", IMAGE_PATH, ak_image], check=True)

    # Create zip from anykernel folder contents
    subprocess.run(
        f"cd '{ANYKERNEL_DIR}' && zip -r9 '{zip_out}' . -x '*.git*' > /dev/null",
        shell=True,
        check=True
    )
    
    # Clean up copied Image.gz-dtb from anykernel dir
    if os.path.isfile(ak_image):
        os.remove(ak_image)

    return zip_out

def send_file_to_telegram(token, chat_id, file_path, caption):
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    file_name = os.path.basename(file_path)

    print(f"🚀 Sending '{file_name}' ({file_size_mb:.2f} MB) to Telegram chat {chat_id} ...")
    
    with open(file_path, "rb") as doc_file:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML"
            },
            files={"document": doc_file},
            timeout=180
        )

    res = response.json()
    if res.get("ok"):
        print("✅ Success! File sent successfully to Telegram.")
        return True
    else:
        print(f"❌ Telegram API Error: {res.get('description')}")
        print(f"Response: {res}")
        return False

def main():
    saved_token, saved_chat_id = load_saved_credentials()

    token = (
        (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None) or
        os.getenv("TELEGRAM_BOT_TOKEN") or
        os.getenv("BOT_TOKEN") or
        os.getenv("TG_TOKEN") or
        saved_token
    )

    chat_id = (
        (sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else None) or
        os.getenv("TELEGRAM_CHAT_ID") or
        os.getenv("CHAT_ID") or
        os.getenv("TG_CHAT_ID") or
        saved_chat_id
    )

    if not token or not chat_id:
        print("==========================================")
        print("  Telegram Bot Configuration")
        print("==========================================")
        if not token:
            token = input("Enter your Telegram Bot Token: ").strip()
        if not chat_id:
            chat_id = input("Enter your Telegram Chat ID: ").strip()
        
        if token and chat_id:
            save_credentials(token, chat_id)
            print(f"Saved credentials to {CONFIG_FILE} for future builds.")

    if not token or not chat_id:
        print("❌ Error: Bot Token and Chat ID are required.")
        sys.exit(1)

    commit_hash, commit_msg, branch = get_git_info()
    build_time = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S UTC")

    # Build caption
    caption = (
        f"🔥 <b>ArtixV4 Gaming Kernel</b> 🔥\n\n"
        f"📱 <b>Device:</b> Xiaomi SM6250 / Snapdragon 720G (Atoll)\n"
        f"⚡ <b>Branch:</b> <code>{branch}</code>\n"
        f"🏷 <b>Commit:</b> <code>{commit_hash}</code> - {commit_msg}\n"
        f"🛠 <b>Compiler:</b> Proton Clang 13.0.0 (LLVM)\n"
        f"✨ <b>Features:</b>\n"
        f"   • BBRplus TCP Congestion Control\n"
        f"   • Dynamic Fsync 2.0\n"
        f"   • KernelSU Integrated\n"
        f"   • 300Hz Gaming Tick & Low-latency Sched\n"
        f"   • Multi-Queue Deadline I/O\n\n"
        f"🕒 <b>Build Date:</b> {build_time}"
    )

    # Package AnyKernel3 flashable zip
    zip_path = package_anykernel_zip()

    # Upload zip
    send_file_to_telegram(token, chat_id, zip_path, caption)

if __name__ == "__main__":
    main()
