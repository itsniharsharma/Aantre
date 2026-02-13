import os
import subprocess
from typing import List
from pydub import AudioSegment
from pydub.effects import normalize
from pydub.utils import which

DOWNLOAD_DIR = "downloads"
TRIM_DIR = "trimmed"

# Cache ffmpeg availability check
_FFMPEG_CHECKED = False

def ensure_ffmpeg_tools() -> None:
    """Check ffmpeg tools availability (cached)"""
    global _FFMPEG_CHECKED
    if not _FFMPEG_CHECKED:
        if not which("ffmpeg") or not which("ffprobe"):
            raise RuntimeError("ffmpeg/ffprobe not found in PATH. Install ffmpeg and restart the terminal.")
        _FFMPEG_CHECKED = True


def get_duration_seconds(path: str) -> float:
    """Get audio duration using ffprobe with optimized args"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=True,
        timeout=10
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise RuntimeError(f"Could not read duration for: {path}")


def trim_mid_chunk(path: str, out_path: str, duration_sec: int, timeout: int = 60) -> None:
    """Trim audio from middle section with optimized ffmpeg call"""
    total = get_duration_seconds(path)
    if total <= 0:
        raise RuntimeError(f"Invalid duration for: {path}")

    # Calculate start position from center
    start = max(0.0, (total - duration_sec) / 2.0) if total > duration_sec else 0

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", path, "-t", str(duration_sec),
             "-vn", "-acodec", "libmp3lame", out_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Timeout trimming {path} (likely corrupted or live stream)")



def trim_all_mid(duration_sec: int) -> List[str]:
    """Trim all downloads from middle, using list comprehension for efficiency"""
    ensure_ffmpeg_tools()
    print("\nTrimming audio files from the middle...")
    
    trimmed_files = []
    for file in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, file)
        if not os.path.isfile(path):
            continue
            
        print(f"Trimming: {file}")
        try:
            out_name = os.path.splitext(file)[0] + ".mp3"
            out_path = os.path.join(TRIM_DIR, out_name)
            trim_mid_chunk(path, out_path, duration_sec)
            trimmed_files.append(out_path)
            print(f"✅ Trimmed: {out_name}")
        except Exception as e:
            print(f"⚠️ Skipped {file}: {e}")

    return trimmed_files


def merge_with_crossfade(files: List[str], output_file: str, crossfade_ms: int = 2500) -> None:
    """Merge audio files with crossfade, optimized for memory"""
    print("\nMerging files with smooth crossfades...")

    if not files:
        raise RuntimeError("No audio files available to merge")

    # Start with first file normalized
    final_audio = normalize(AudioSegment.from_file(files[0]))

    # Merge remaining files with adaptive crossfade
    for f in files[1:]:
        segment = normalize(AudioSegment.from_file(f))
        # Adaptive crossfade based on segment lengths
        effective_fade = min(crossfade_ms, len(final_audio) // 2, len(segment) // 2)
        final_audio = final_audio.append(segment, crossfade=effective_fade)

    final_audio.export(output_file, format="mp3", bitrate="192k")
    print(f"✅ Final mashup created: {output_file}")
