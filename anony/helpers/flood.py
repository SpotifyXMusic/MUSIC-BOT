"""
Flood Protection & Rate Limiting
No database needed - in-memory per restart
"""

import time
from config import Config

_last_play: dict = {}   # user_id -> timestamp
_vote_skips: dict = {}  # chat_id -> set of user_ids


def check_flood(user_id: int) -> tuple[bool, int]:
    """
    Returns (is_flooded, seconds_remaining)
    True = user is flooding, should be blocked
    """
    now = time.time()
    last = _last_play.get(user_id, 0)
    diff = now - last

    if diff < Config.FLOOD_WAIT:
        remaining = int(Config.FLOOD_WAIT - diff) + 1
        return True, remaining

    _last_play[user_id] = now
    return False, 0


def add_vote_skip(chat_id: int, user_id: int) -> set:
    """Add user to vote skip set, return current voters"""
    if chat_id not in _vote_skips:
        _vote_skips[chat_id] = set()
    _vote_skips[chat_id].add(user_id)
    return _vote_skips[chat_id]


def get_vote_skips(chat_id: int) -> set:
    return _vote_skips.get(chat_id, set())


def clear_vote_skips(chat_id: int):
    _vote_skips.pop(chat_id, None)


def reset_flood(user_id: int):
    _last_play.pop(user_id, None)
