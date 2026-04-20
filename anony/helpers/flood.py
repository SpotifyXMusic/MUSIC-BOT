import time
from config import Config

_last: dict = {}
_votes: dict = {}


def check_flood(user_id: int) -> tuple:
    now = time.time()
    diff = now - _last.get(user_id, 0)
    if diff < Config.FLOOD_WAIT:
        return True, int(Config.FLOOD_WAIT - diff) + 1
    _last[user_id] = now
    return False, 0


def add_vote(chat_id: int, user_id: int) -> set:
    if chat_id not in _votes: _votes[chat_id] = set()
    _votes[chat_id].add(user_id)
    return _votes[chat_id]


def get_votes(chat_id: int) -> set:
    return _votes.get(chat_id, set())


def clear_votes(chat_id: int):
    _votes.pop(chat_id, None)
