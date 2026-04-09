"""
Audio Filters/Effects using FFmpeg
No extra libraries needed - FFmpeg already required for pytgcalls
"""

import os
import asyncio

DOWNLOAD_DIR = "downloads/"


# FFmpeg filter presets
AUDIO_FILTERS = {
    "bass":      "equalizer=f=100:width_type=o:width=2:g=10,equalizer=f=200:width_type=o:width=2:g=5",
    "treble":    "equalizer=f=8000:width_type=o:width=2:g=8",
    "nightcore": "asetrate=44100*1.25,aresample=44100,atempo=1.0",
    "slow":      "asetrate=44100*0.85,aresample=44100",
    "8d":        "apulsator=hz=0.08",
    "reverb":    "aecho=0.8:0.9:1000:0.3",
    "loud":      "volume=2.5",
    "soft":      "volume=0.5",
    "mono":      "pan=mono|c0=c0",
    "clear":     "highpass=f=80,lowpass=f=12000",
    "karaoke":   "pan=stereo|c0=c0-c1|c1=c1-c0",
    "vocalboost":"equalizer=f=1000:width_type=o:width=2:g=6,equalizer=f=3000:width_type=o:width=2:g=4",
}

FILTER_DESCRIPTIONS = {
    "bass":       "Bass Boost - Heavy bass effect",
    "treble":     "Treble Boost - Sharp high frequencies",
    "nightcore":  "Nightcore - Speed up + higher pitch",
    "slow":       "Slow - Slowed down version",
    "8d":         "8D Audio - Spatial rotating effect",
    "reverb":     "Reverb - Echo room effect",
    "loud":       "Loud - Volume boost 2.5x",
    "soft":       "Soft - Reduced volume",
    "mono":       "Mono - Merge stereo to mono",
    "clear":      "Clear - Remove low/high noise",
    "karaoke":    "Karaoke - Remove center vocals",
    "vocalboost": "Vocal Boost - Enhance vocals",
}


async def apply_filter(input_path: str, filter_name: str) -> str:
    """
    Apply FFmpeg audio filter to a file.
    Returns path to new filtered file.
    """
    if filter_name not in AUDIO_FILTERS:
        return input_path

    filter_str = AUDIO_FILTERS[filter_name]
    base = os.path.splitext(input_path)[0]
    output_path = f"{base}_{filter_name}.mp3"

    if os.path.exists(output_path):
        return output_path

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", filter_str,
        "-b:a", "192k",
        output_path
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()

    if proc.returncode == 0 and os.path.exists(output_path):
        return output_path

    return input_path


async def apply_speed(input_path: str, speed: float) -> str:
    """Apply speed change. speed: 0.5 to 2.0"""
    speed = max(0.5, min(2.0, speed))
    base = os.path.splitext(input_path)[0]
    output_path = f"{base}_speed{speed}.mp3"

    if os.path.exists(output_path):
        return output_path

    # atempo supports 0.5 to 2.0
    # For values outside, chain multiple atempo filters
    if speed <= 2.0 and speed >= 0.5:
        af = f"atempo={speed}"
    elif speed > 2.0:
        af = f"atempo=2.0,atempo={speed/2.0:.2f}"
    else:
        af = f"atempo=0.5,atempo={speed*2.0:.2f}"

    cmd = ["ffmpeg", "-y", "-i", input_path, "-af", af, "-b:a", "192k", output_path]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()

    return output_path if os.path.exists(output_path) else input_path
