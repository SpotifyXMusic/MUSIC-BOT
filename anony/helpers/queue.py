from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    title: str
    url: str
    duration: str
    duration_s: int
    thumbnail: str
    channel: str
    requested_by: int
    requested_by_name: str
    video_id: str = ""
    file_path: str = ""
    is_video: bool = False
    views: int = 0


class QueueManager:
    def __init__(self):
        self._q: dict[int, list[Track]] = {}
        self._idx: dict[int, int] = {}
        self._loop: dict[int, bool] = {}
        self._repeat: dict[int, bool] = {}

    def add(self, chat_id: int, track: Track) -> int:
        if chat_id not in self._q:
            self._q[chat_id] = []
            self._idx[chat_id] = 0
        self._q[chat_id].append(track)
        return len(self._q[chat_id])

    def get_current(self, chat_id: int) -> Optional[Track]:
        q = self._q.get(chat_id, [])
        i = self._idx.get(chat_id, 0)
        return q[i] if q and 0 <= i < len(q) else None

    def get_queue(self, chat_id: int) -> list:
        return self._q.get(chat_id, [])

    def get_index(self, chat_id: int) -> int:
        return self._idx.get(chat_id, 0)

    def length(self, chat_id: int) -> int:
        return len(self._q.get(chat_id, []))

    def next(self, chat_id: int) -> Optional[Track]:
        q = self._q.get(chat_id, [])
        if not q: return None
        if self._repeat.get(chat_id): return self.get_current(chat_id)
        i = self._idx.get(chat_id, 0) + 1
        if i >= len(q):
            if self._loop.get(chat_id): i = 0
            else:
                self.clear(chat_id)
                return None
        self._idx[chat_id] = i
        return q[i]

    def remove(self, chat_id: int, pos: int) -> Optional[Track]:
        q = self._q.get(chat_id, [])
        ri = pos - 1
        if 0 <= ri < len(q):
            t = q.pop(ri)
            cur = self._idx.get(chat_id, 0)
            if cur > ri and cur > 0: self._idx[chat_id] = cur - 1
            return t
        return None

    def clear(self, chat_id: int):
        self._q.pop(chat_id, None)
        self._idx.pop(chat_id, None)
        self._loop.pop(chat_id, None)
        self._repeat.pop(chat_id, None)

    def toggle_loop(self, chat_id: int) -> bool:
        v = not self._loop.get(chat_id, False)
        self._loop[chat_id] = v
        return v

    def toggle_repeat(self, chat_id: int) -> bool:
        v = not self._repeat.get(chat_id, False)
        self._repeat[chat_id] = v
        return v

    def is_looping(self, c): return self._loop.get(c, False)
    def is_repeating(self, c): return self._repeat.get(c, False)

    def format_queue(self, chat_id: int, page: int = 1, per: int = 5) -> str:
        q = self._q.get(chat_id, [])
        cur = self._idx.get(chat_id, 0)
        total = len(q)
        if not q: return "Queue is empty."
        start = (page - 1) * per
        end = min(start + per, total)
        pages = (total + per - 1) // per
        lines = [f"**Queue** | Page {page}/{pages} | {total} tracks\n"]
        for i in range(start, end):
            t = q[i]
            marker = "▶" if i == cur else f"{i+1}."
            lines.append(f"`{marker}` **{t.title[:40]}** `[{t.duration}]`\n   by {t.requested_by_name}")
        return "\n".join(lines)


queue = QueueManager()
