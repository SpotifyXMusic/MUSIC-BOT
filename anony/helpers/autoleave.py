"""
Auto Leave System
Bot leaves voice chat if no one is listening
Uses APScheduler for background checks
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import Config

scheduler = AsyncIOScheduler()
_leave_timers: dict = {}   # chat_id -> scheduled job id
_auto_leave_enabled: dict = {}  # chat_id -> bool (default True)


def init_scheduler():
    if not scheduler.running:
        scheduler.start()


async def _do_leave(chat_id: int):
    """Actually leave the voice chat"""
    try:
        from anony.core import call_manager
        from anony.helpers.queue import queue
        if call_manager.is_active(chat_id):
            await call_manager.stop(chat_id)
            queue.clear(chat_id)
            print(f"[AUTO-LEAVE] Left chat {chat_id} - no listeners")
    except Exception as e:
        print(f"[AUTO-LEAVE] Error: {e}")
    finally:
        _leave_timers.pop(chat_id, None)


def schedule_leave(chat_id: int, bot=None, delay: int = None):
    """Schedule auto-leave after delay seconds"""
    if not _auto_leave_enabled.get(chat_id, True):
        return

    delay = delay or Config.AUTO_LEAVE_DELAY
    cancel_leave(chat_id)

    loop = asyncio.get_event_loop()
    handle = loop.call_later(delay, lambda: asyncio.ensure_future(_do_leave(chat_id)))
    _leave_timers[chat_id] = handle


def cancel_leave(chat_id: int):
    """Cancel scheduled leave (music resumed or someone joined)"""
    handle = _leave_timers.pop(chat_id, None)
    if handle:
        handle.cancel()


def toggle_auto_leave(chat_id: int) -> bool:
    current = _auto_leave_enabled.get(chat_id, True)
    _auto_leave_enabled[chat_id] = not current
    return not current


def is_auto_leave_on(chat_id: int) -> bool:
    return _auto_leave_enabled.get(chat_id, True)
