"""
Calls Manager - pytgcalls 4.x (pure Python, no Node.js)
"""
import asyncio
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pyrogram import Client


class CallManager:
    def __init__(self, userbot: Client):
        self._app = PyTgCalls(userbot)
        self._calls: dict = {}

    async def start(self):
        await self._app.start()
        print("[CALLS] PyTgCalls 4.x started OK")

    def _stream(self, path: str, video: bool) -> MediaStream:
        if video:
            return MediaStream(
                path,
                audio_parameters=AudioQuality.HIGH,
                video_parameters=VideoQuality.SD_480p,
            )
        return MediaStream(
            path,
            audio_parameters=AudioQuality.HIGH,
            video_flags=MediaStream.Flags.IGNORE,
        )

    async def join_and_play(self, chat_id: int, path: str, video: bool = False) -> bool:
        try:
            stream = self._stream(path, video)
            if chat_id in self._calls:
                await self._app.change_stream(chat_id, stream)
            else:
                await self._app.join_group_call(chat_id, stream)
            self._calls[chat_id] = {"file": path, "video": video, "paused": False}
            return True
        except Exception as e:
            print(f"[CALLS] join error: {e}")
            try:
                await self._app.change_stream(chat_id, self._stream(path, video))
                self._calls[chat_id] = {"file": path, "video": video, "paused": False}
                return True
            except Exception as e2:
                print(f"[CALLS] change error: {e2}")
                return False

    async def pause(self, chat_id: int) -> bool:
        try:
            await self._app.pause_stream(chat_id)
            if chat_id in self._calls:
                self._calls[chat_id]["paused"] = True
            return True
        except Exception:
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            await self._app.resume_stream(chat_id)
            if chat_id in self._calls:
                self._calls[chat_id]["paused"] = False
            return True
        except Exception:
            return False

    async def stop(self, chat_id: int) -> bool:
        try:
            await self._app.leave_group_call(chat_id)
        except Exception:
            pass
        self._calls.pop(chat_id, None)
        return True

    async def mute(self, chat_id: int) -> bool:
        try:
            await self._app.mute_stream(chat_id)
            return True
        except Exception:
            return False

    async def unmute(self, chat_id: int) -> bool:
        try:
            await self._app.unmute_stream(chat_id)
            return True
        except Exception:
            return False

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._calls

    def is_paused(self, chat_id: int) -> bool:
        return self._calls.get(chat_id, {}).get("paused", False)

    def active_count(self) -> int:
        return len(self._calls)

    def active_chats(self) -> list:
        return list(self._calls.keys())

    def get_info(self, chat_id: int) -> dict:
        return self._calls.get(chat_id, {})
