"""
Voice/Video Call Manager
py-tgcalls 0.9.7 + pyrofork compatible
"""

import asyncio
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pyrogram import Client


class CallManager:
    def __init__(self, userbot: Client):
        self.pytgcalls = PyTgCalls(userbot)
        self._active_calls: dict = {}

    async def start(self):
        await self.pytgcalls.start()
        print("[CALLS] PyTgCalls started.")

    def _stream(self, file_path: str, video: bool):
        if video:
            return AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        return AudioPiped(file_path, audio_parameters=HighQualityAudio())

    async def join_and_play(self, chat_id: int, file_path: str, video: bool = False) -> bool:
        try:
            stream = self._stream(file_path, video)
            if chat_id in self._active_calls:
                await self.pytgcalls.change_stream(chat_id, stream)
            else:
                await self.pytgcalls.join_group_call(chat_id, stream)
            self._active_calls[chat_id] = {"file": file_path, "video": video, "paused": False}
            return True
        except Exception as e:
            if "already" in str(e).lower():
                try:
                    await self.pytgcalls.change_stream(chat_id, self._stream(file_path, video))
                    self._active_calls[chat_id] = {"file": file_path, "video": video, "paused": False}
                    return True
                except Exception:
                    pass
            print(f"[CALLS] Error: {e}")
            return False

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
        except Exception:
            pass
        self._active_calls.pop(chat_id, None)
        return True

    async def seek(self, chat_id: int, seconds: int) -> bool:
        try:
            info = self._active_calls.get(chat_id, {})
            if not info.get("file"):
                return False
            await self.pytgcalls.change_stream(chat_id, self._stream(info["file"], info.get("video", False)))
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

    def is_active(self, chat_id: int) -> bool:
        return chat_id in self._active_calls

    def is_paused(self, chat_id: int) -> bool:
        return self._active_calls.get(chat_id, {}).get("paused", False)

    def active_count(self) -> int:
        return len(self._active_calls)

    def active_chats(self) -> list:
        return list(self._active_calls.keys())

    def get_call_info(self, chat_id: int) -> dict:
        return self._active_calls.get(chat_id, {})
