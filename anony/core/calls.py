"""
Voice/Video Call Manager
py-tgcalls 2.2.11 compatible - correct imports
"""

import asyncio
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pyrogram import Client


class CallManager:
    def __init__(self, userbot: Client):
        self.pytgcalls = PyTgCalls(userbot)
        self._active_calls: dict = {}

    async def start(self):
        await self.pytgcalls.start()
        print("[CALLS] PyTgCalls started.")

    async def join_and_play(self, chat_id: int, file_path: str, video: bool = False) -> bool:
        try:
            if video:
                stream = MediaStream(
                    file_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_parameters=VideoQuality.SD_480p,
                )
            else:
                stream = MediaStream(
                    file_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_flags=MediaStream.Flags.IGNORE,
                )

            try:
                await self.pytgcalls.join_group_call(chat_id, stream)
            except Exception:
                # Already in call - change stream instead
                await self.pytgcalls.change_stream(chat_id, stream)

            self._active_calls[chat_id] = {
                "file": file_path,
                "video": video,
                "paused": False,
            }
            return True

        except Exception as e:
            print(f"[CALLS] join_and_play error: {e}")
            return False

    async def change_stream(self, chat_id: int, file_path: str, video: bool = False) -> bool:
        try:
            if video:
                stream = MediaStream(
                    file_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_parameters=VideoQuality.SD_480p,
                )
            else:
                stream = MediaStream(
                    file_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_flags=MediaStream.Flags.IGNORE,
                )
            await self.pytgcalls.change_stream(chat_id, stream)
            self._active_calls[chat_id] = {
                "file": file_path,
                "video": video,
                "paused": False,
            }
            return True
        except Exception as e:
            print(f"[CALLS] change_stream error: {e}")
            return False

    async def pause(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.pause_stream(chat_id)
            if chat_id in self._active_calls:
                self._active_calls[chat_id]["paused"] = True
            return True
        except Exception as e:
            print(f"[CALLS] pause error: {e}")
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            await self.pytgcalls.resume_stream(chat_id)
            if chat_id in self._active_calls:
                self._active_calls[chat_id]["paused"] = False
            return True
        except Exception as e:
            print(f"[CALLS] resume error: {e}")
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
            file_path = info.get("file", "")
            video = info.get("video", False)
            if not file_path:
                return False
            return await self.change_stream(chat_id, file_path, video)
        except Exception as e:
            print(f"[CALLS] seek error: {e}")
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
