import os, time, asyncio

DL_DIR = "downloads/"
MAX_AGE = 1800  # 30 min


async def cleanup_old():
    now = time.time()
    if not os.path.exists(DL_DIR): return
    for f in os.listdir(DL_DIR):
        fp = os.path.join(DL_DIR, f)
        if os.path.isfile(fp) and now - os.path.getmtime(fp) > MAX_AGE:
            try: os.remove(fp)
            except: pass


async def cleanup_loop():
    while True:
        await asyncio.sleep(900)
        await cleanup_old()


def start_cleanup():
    asyncio.ensure_future(cleanup_loop())
