import os
import random
import re
from typing import Dict, List, Optional, Tuple

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize
from pydub.generators import Sine
from yt_dlp import YoutubeDL

from advanced_mashup import ensure_ffmpeg_tools, trim_mid_chunk
from mashup_core import DOWNLOAD_DIR, TRIM_DIR, prepare_dirs
from mongodb_helper import mongo_handler


def safe_slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return (cleaned[:40] or "query").lower()


def _build_ydl(prefix: str) -> YoutubeDL:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{prefix}-%(title)s.%(ext)s"),
        "quiet": False,
        "noplaylist": True,
        "skip_unavailable_fragments": True,
        "retries": 5,
        "fragment_retries": 3,
        "socket_timeout": 15,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "extract_flat": False,
        "match_filters": "!is_live & !is_upcoming",
        "js_runtimes": {"node": {}},
    }
    return YoutubeDL(ydl_opts)


def download_videos_for_query(
    query: str,
    count: int,
    session_id: Optional[str],
    mode: str,
) -> Dict[str, Tuple[str, str]]:
    prefix = safe_slug(query)
    before_files = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()

    with _build_ydl(prefix) as ydl:
        search_suffix = "songs" if mode == "singer" else "audio"
        search = f"ytsearch{count * 3}:{query} {search_suffix}"
        info = ydl.extract_info(search, download=False)
        entries = [e for e in (info.get("entries") or []) if e and e.get("webpage_url")]

        if not entries:
            raise RuntimeError(f"No videos found for: {query}")

        selected = random.sample(entries, min(count, len(entries))) if len(entries) > count else entries

        for entry in selected:
            url = entry.get("webpage_url")
            if url:
                ydl.download([url])

    after_files = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()
    new_files = sorted(after_files - before_files)

    mapped: Dict[str, Tuple[str, str]] = {}
    for filename in new_files:
        if not filename.startswith(prefix + "-"):
            continue
        base_name, _ = os.path.splitext(filename)
        mapped[base_name] = (filename, query)

        if mongo_handler.connected and session_id:
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                mongo_handler.store_song(
                    filepath,
                    query,
                    session_id,
                    file_type="download",
                )

    return mapped


def trim_all_mid(
    duration_sec: int,
    meta_by_base: Dict[str, Tuple[str, str]],
) -> Tuple[List[str], Dict[str, Tuple[str, str]]]:
    ensure_ffmpeg_tools()
    trimmed_files: List[str] = []
    trimmed_meta: Dict[str, Tuple[str, str]] = {}

    for file in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, file)
        if not os.path.isfile(path):
            continue

        base_name, _ = os.path.splitext(file)
        out_name = base_name + ".mp3"
        out_path = os.path.join(TRIM_DIR, out_name)

        try:
            trim_mid_chunk(path, out_path, duration_sec)
            trimmed_files.append(out_path)
            if base_name in meta_by_base:
                trimmed_meta[base_name] = meta_by_base[base_name]
        except Exception:
            continue

    return trimmed_files, trimmed_meta


def _find_loudest_start(segment: AudioSegment, window_ms: int, step_ms: int = 1000) -> int:
    if len(segment) <= window_ms:
        return 0

    best_start = 0
    best_score = -1.0
    for start in range(0, len(segment) - window_ms + 1, step_ms):
        window = segment[start:start + window_ms]
        score = window.rms
        if score > best_score:
            best_score = score
            best_start = start

    return best_start


def trim_loudest_chunks(
    duration_sec: int,
    meta_by_base: Dict[str, Tuple[str, str]],
) -> Tuple[List[str], Dict[str, Tuple[str, str]]]:
    ensure_ffmpeg_tools()
    trimmed_files: List[str] = []
    trimmed_meta: Dict[str, Tuple[str, str]] = {}
    window_ms = duration_sec * 1000

    for file in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, file)
        if not os.path.isfile(path):
            continue

        base_name, _ = os.path.splitext(file)
        out_name = base_name + ".mp3"
        out_path = os.path.join(TRIM_DIR, out_name)

        try:
            segment = AudioSegment.from_file(path)
            start_ms = _find_loudest_start(segment, window_ms)
            chunk = segment[start_ms:start_ms + window_ms]
            chunk.export(out_path, format="mp3", bitrate="192k")
            trimmed_files.append(out_path)
            if base_name in meta_by_base:
                trimmed_meta[base_name] = meta_by_base[base_name]
        except Exception:
            continue

    return trimmed_files, trimmed_meta


def build_beat_track(duration_ms: int, bpm: int) -> AudioSegment:
    interval = max(1, int(60000 / bpm))
    kick = Sine(60).to_audio_segment(duration=90).apply_gain(-6).fade_in(4).fade_out(50)
    click = Sine(180).to_audio_segment(duration=40).apply_gain(-12).fade_in(2).fade_out(15)

    track = AudioSegment.silent(duration=duration_ms, frame_rate=44100).set_channels(2)
    for pos in range(0, duration_ms, interval):
        track = track.overlay(kick, position=pos)
        off = pos + interval // 2
        if off < duration_ms:
            track = track.overlay(click, position=off)

    return track.apply_gain(-14)


def merge_with_beat(
    files: List[str],
    output_file: str,
    crossfade_ms: int = 3000,
    bpm: int = 96,
) -> None:
    if not files:
        raise RuntimeError("No audio files available to merge")

    def prep(segment: AudioSegment) -> AudioSegment:
        seg = segment.set_frame_rate(44100).set_channels(2)
        seg = normalize(seg)
        seg = compress_dynamic_range(seg, threshold=-20.0, ratio=4.0, attack=5, release=50)
        return seg.fade_in(60).fade_out(60)

    final_audio = prep(AudioSegment.from_file(files[0]))

    for f in files[1:]:
        segment = prep(AudioSegment.from_file(f))
        effective_fade = min(crossfade_ms, len(final_audio) // 2, len(segment) // 2)
        final_audio = final_audio.append(segment, crossfade=effective_fade)

    beat = build_beat_track(len(final_audio), bpm)
    final_audio = final_audio.overlay(beat)
    final_audio = normalize(final_audio)

    final_audio.export(output_file, format="mp3", bitrate="320k")


def merge_rotating_with_beat(
    files: List[str],
    output_file: str,
    duration_sec: int,
    crossfade_ms: int = 2400,
    bpm: int = 96,
) -> None:
    if not files:
        raise RuntimeError("No audio files available to merge")

    duration_ms = duration_sec * 1000
    beat_interval = int(60000 / bpm)
    effective_fade = min(crossfade_ms, beat_interval * 2)

    def prep(segment: AudioSegment) -> AudioSegment:
        seg = segment.set_frame_rate(44100).set_channels(2)
        seg = normalize(seg)
        seg = compress_dynamic_range(seg, threshold=-20.0, ratio=4.0, attack=5, release=50)
        return seg

    prepared = [prep(AudioSegment.from_file(f)[:duration_ms]) for f in files]

    slice_ms = max(4000, min(8000, duration_ms // 3))
    rotated = None
    offsets = [0 for _ in prepared]

    while True:
        progressed = False
        for idx, segment in enumerate(prepared):
            if offsets[idx] >= len(segment):
                continue

            progressed = True
            slice_part = segment[offsets[idx]:offsets[idx] + slice_ms]
            offsets[idx] += slice_ms

            if rotated is None:
                rotated = slice_part
            else:
                fade = min(effective_fade, len(rotated) // 2, len(slice_part) // 2)
                rotated = rotated.append(slice_part, crossfade=fade)

        if not progressed:
            break

    if rotated is None:
        raise RuntimeError("Unable to assemble mashup")

    beat = build_beat_track(len(rotated), bpm)
    final_audio = rotated.overlay(beat)
    final_audio = normalize(final_audio)

    final_audio.export(output_file, format="mp3", bitrate="320k")


def _split_counts(total: int, buckets: int) -> List[int]:
    base = max(2, total // buckets)
    counts = [base for _ in range(buckets)]
    remainder = total - base * buckets

    idx = 0
    while remainder > 0:
        counts[idx] += 1
        remainder -= 1
        idx = (idx + 1) % buckets

    return counts


def run_multi_mashup(
    queries: List[str],
    total_videos: Optional[int],
    duration: int,
    output: str,
    user_email: Optional[str] = None,
    mode: str = "singer",
) -> Optional[str]:
    if not queries:
        raise RuntimeError("Please provide at least one singer or song.")

    if len(queries) > 5:
        raise RuntimeError("You can add up to 5 singers or songs.")

    mode = mode if mode in ("singer", "song") else "singer"

    if mode == "singer":
        if total_videos is None:
            raise RuntimeError("Total videos is required for singer mashups.")
        if total_videos < max(10, len(queries) * 2):
            raise RuntimeError("Total videos must be at least 10 and allow 2 per entry.")
    else:
        total_videos = len(queries)

    session_id = None
    if mongo_handler.connected and user_email:
        session_id = mongo_handler.start_new_session(", ".join(queries), user_email)

    prepare_dirs()
    if mode == "song":
        counts = [1 for _ in queries]
    else:
        counts = _split_counts(total_videos, len(queries))

    meta_by_base: Dict[str, Tuple[str, str]] = {}
    for query, count in zip(queries, counts):
        meta_by_base.update(download_videos_for_query(query, count, session_id, mode))

    trimmed_files, trimmed_meta = trim_loudest_chunks(duration, meta_by_base)

    if mongo_handler.connected and session_id:
        for trimmed_path in trimmed_files:
            trimmed_name = os.path.basename(trimmed_path)
            base_name, _ = os.path.splitext(trimmed_name)
            source_filename, query = trimmed_meta.get(base_name, (None, None))
            mongo_handler.store_song(
                trimmed_path,
                query or "multi",
                session_id,
                file_type="trimmed",
                source_filename=source_filename,
            )

    merge_rotating_with_beat(trimmed_files, output, duration)

    return session_id
