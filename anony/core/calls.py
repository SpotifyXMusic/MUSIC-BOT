"""
Voice/Video Call Manager using PyTgCalls
Handles all streaming operations
"""

import asyncio
from pytgcalls import PyTgCalls
from pytgcalls.types import (
    AudioPiped,
    AudioVideoPiped,
    MediaStream,
    AudioQuality,
    VideoQuality,
)
from pytgcalls.exceptions import (
    GroupCallNotFound,
    NoActiveGroupCall,
    AlreadyJoinedError,
    TelegramServerError,
)
from pyrogram import Client
from config import Config


class CallManager:
    def __init__(self, userbot: Client):
        self.pytgcalls = PyTgCalls(userbot)
        self._active_calls: dict = {}  # chat_id -> stream info

    async def start(self):
        await self.pytgcalls.start()
        print("[CALLS] PyTgCalls started.")

    # ─── JOIN & STREAM ──────────────────────────────────────────────

    async def join_and_play(
        self,
        chat_id: int,
        file_path: str,
        video: bool = False,
        ffmpeg_parameters: str = None,
    ) -> bool:
        try:
            if video:
                stream = MediaStream(
                    file_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_parameters=VideoQuality.SD_480p,
                )
            else:
                stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH)

            if chat_id in self._active_calls:
                await self.pytgcalls.change_stream(chat_id, stream)
            else:
                await self.pytgcalls.join_group_call(chat_id, stream)

            self._active_calls[chat_id] = {
                "file": file_path,
                "video": video,
                "paused": False,
            }
            return True
        except AlreadyJoinedError:
            await self.pytgcalls.change_stream(chat_id, stream)
            return True
        except Exception as e:
            print(f"[CALLS] Error joining call: {e}")
            return False

    # ─── CONTROLS ───────────────────────────────────────────────────

    async def pause(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.pause_stream(chat_id)
            if chat_id in self._active_calls:
                self._active_calls[chat_id]["paused"] = True
            return True
        except Exception:
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.resume_stream(chat_id)
            if chat_id in self._active_calls:
                self._active_calls[chat_id]["paused"] = False
            return True
        except Exception:
            return False

    async def stop(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.leave_group_call(chat_id)
            self._active_calls.pop(chat_id, None)
            return True
        except Exception:
            return False

    async def seek(self, chat_id: int, seconds: int) -> bool:
        """Seek forward in current stream"""
        try:
            await self.pytgcalls.seek_stream(chat_id, seconds)
            return True
        except Exception:
            return False

    async def mute(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.mute_stream(chat_id)
            return True
        except Exception:
            return False

    async def unmute(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.unmute_stream(chat_id)
            return True
        except Exception:
            return False

    # ─── STATUS ─────────────────────────────────────────────────────

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._active_calls

    def is_paused(self, chat_id: int) -> bool:
        info = self._active_calls.get(chat_id, {})
        return info.get("paused", False)

    def active_count(self) -> int:
        return len(self._active_calls)

    def active_chats(self) -> list:
        return list(self._active_calls.keys())

    def get_call_info(self, chat_id: int) -> dict:
        return self._active_calls.get(chat_id, {})
