"""
Cleanup System
Auto-delete downloaded files after 30 minutes to save disk space
"""

import os
import time
import asyncio

DOWNLOAD_DIR = "downloads/"
MAX_AGE_SECONDS = 1800  # 30 minutes


async def cleanup_old_files():
    """Delete files older than MAX_AGE_SECONDS"""
    now = time.time()
    deleted = 0
    freed_mb = 0

    if not os.path.exists(DOWNLOAD_DIR):
        return

    for fname in os.listdir(DOWNLOAD_DIR):
        fpath = os.path.join(DOWNLOAD_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            age = now - os.path.getmtime(fpath)
            if age > MAX_AGE_SECONDS:
                size = os.path.getsize(fpath) / (1024 * 1024)
                os.remove(fpath)
                deleted += 1
                freed_mb += size
        except Exception:
            pass

    if deleted > 0:
        print(f"[CLEANUP] Deleted {deleted} files, freed {freed_mb:.1f} MB")


async def cleanup_loop():
    """Run cleanup every 15 minutes"""
    while True:
        await asyncio.sleep(900)  # 15 min
        await cleanup_old_files()


def start_cleanup():
    asyncio.ensure_future(cleanup_loop())
