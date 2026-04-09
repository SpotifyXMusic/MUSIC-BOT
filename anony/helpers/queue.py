"""
Queue Management System
Handles per-chat music queues with full state tracking
"""

from dataclasses import dataclass, field
from typing import Optional
import asyncio


@dataclass
class Track:
    title: str
    url: str
    duration: str
    duration_s: int
    thumbnail: str
    channel: str
    requested_by: int       # user_id
    requested_by_name: str  # user name
    video_id: str = ""
    file_path: str = ""
    is_video: bool = False


class QueueManager:
    def __init__(self):
        self._queues: dict[int, list[Track]] = {}   # chat_id -> queue list
        self._current: dict[int, int] = {}           # chat_id -> current index
        self._loop: dict[int, bool] = {}             # chat_id -> loop enabled
        self._repeat: dict[int, bool] = {}           # chat_id -> repeat one song
        self._shuffle: dict[int, bool] = {}          # chat_id -> shuffle

    # ─── QUEUE OPS ──────────────────────────────────────────────────

    def add(self, chat_id: int, track: Track) -> int:
        """Add track to queue. Returns position (1-indexed)."""
        if chat_id not in self._queues:
            self._queues[chat_id] = []
            self._current[chat_id] = 0
        self._queues[chat_id].append(track)
        return len(self._queues[chat_id])

    def get_queue(self, chat_id: int) -> list[Track]:
        return self._queues.get(chat_id, [])

    def get_current(self, chat_id: int) -> Optional[Track]:
        queue = self._queues.get(chat_id, [])
        idx = self._current.get(chat_id, 0)
        if queue and 0 <= idx < len(queue):
            return queue[idx]
        return None

    def get_current_index(self, chat_id: int) -> int:
        return self._current.get(chat_id, 0)

    def clear(self, chat_id: int):
        self._queues.pop(chat_id, None)
        self._current.pop(chat_id, None)
        self._loop.pop(chat_id, None)
        self._repeat.pop(chat_id, None)
        self._shuffle.pop(chat_id, None)

    def remove(self, chat_id: int, index: int) -> Optional[Track]:
        """Remove track at 1-based index"""
        queue = self._queues.get(chat_id, [])
        real_idx = index - 1
        if 0 <= real_idx < len(queue):
            track = queue.pop(real_idx)
            cur = self._current.get(chat_id, 0)
            if cur >= real_idx and cur > 0:
                self._current[chat_id] = cur - 1
            return track
        return None

    # ─── NAVIGATION ─────────────────────────────────────────────────

    def next(self, chat_id: int) -> Optional[Track]:
        queue = self._queues.get(chat_id, [])
        if not queue:
            return None

        if self._repeat.get(chat_id, False):
            # Repeat current track
            return self.get_current(chat_id)

        idx = self._current.get(chat_id, 0) + 1

        if idx >= len(queue):
            if self._loop.get(chat_id, False):
                idx = 0  # Loop back
            else:
                self.clear(chat_id)
                return None

        self._current[chat_id] = idx
        return queue[idx]

    def previous(self, chat_id: int) -> Optional[Track]:
        queue = self._queues.get(chat_id, [])
        idx = max(0, self._current.get(chat_id, 0) - 1)
        self._current[chat_id] = idx
        return queue[idx] if queue else None

    def is_empty(self, chat_id: int) -> bool:
        queue = self._queues.get(chat_id, [])
        return len(queue) == 0

    def queue_length(self, chat_id: int) -> int:
        return len(self._queues.get(chat_id, []))

    # ─── MODES ──────────────────────────────────────────────────────

    def toggle_loop(self, chat_id: int) -> bool:
        current = self._loop.get(chat_id, False)
        self._loop[chat_id] = not current
        return not current

    def toggle_repeat(self, chat_id: int) -> bool:
        current = self._repeat.get(chat_id, False)
        self._repeat[chat_id] = not current
        return not current

    def is_looping(self, chat_id: int) -> bool:
        return self._loop.get(chat_id, False)

    def is_repeating(self, chat_id: int) -> bool:
        return self._repeat.get(chat_id, False)

    # ─── FORMAT ─────────────────────────────────────────────────────

    def format_queue(self, chat_id: int, page: int = 1, per_page: int = 5) -> str:
        queue = self._queues.get(chat_id, [])
        current_idx = self._current.get(chat_id, 0)
        total = len(queue)

        if not queue:
            return "Queue is empty."

        start = (page - 1) * per_page
        end = min(start + per_page, total)
        total_pages = (total + per_page - 1) // per_page

        lines = [f"**Queue** | Page {page}/{total_pages} | {total} tracks\n"]
        for i in range(start, end):
            track = queue[i]
            marker = "▶" if i == current_idx else f"{i+1}."
            lines.append(f"`{marker}` **{track.title[:40]}** `[{track.duration}]`")
            lines.append(f"   Requested by: {track.requested_by_name}\n")

        return "\n".join(lines)


# Global queue instance
queue = QueueManager()
