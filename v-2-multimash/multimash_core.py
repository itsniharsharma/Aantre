import os
import random
import re
import subprocess
from array import array
from collections import deque
from typing import Dict, List, Optional, Tuple

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize
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
) -> Tuple[Dict[str, Tuple[str, str]], List[str]]:
    prefix = safe_slug(query)
    if os.path.exists(DOWNLOAD_DIR):
        before_files = {entry.name for entry in os.scandir(DOWNLOAD_DIR) if entry.is_file()}
    else:
        before_files = set()

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

    if os.path.exists(DOWNLOAD_DIR):
        after_files = {entry.name for entry in os.scandir(DOWNLOAD_DIR) if entry.is_file()}
    else:
        after_files = set()
    new_files = sorted(after_files - before_files)

    mapped: Dict[str, Tuple[str, str]] = {}
    new_paths: List[str] = []
    for filename in new_files:
        if not filename.startswith(prefix + "-"):
            continue
        base_name, _ = os.path.splitext(filename)
        mapped[base_name] = (filename, query)
        new_paths.append(os.path.join(DOWNLOAD_DIR, filename))

        if mongo_handler.connected and session_id:
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                mongo_handler.store_song(
                    filepath,
                    query,
                    session_id,
                    file_type="download",
                )

    return mapped, new_paths


def trim_all_mid(
    duration_sec: int,
    meta_by_base: Dict[str, Tuple[str, str]],
) -> Tuple[List[str], Dict[str, Tuple[str, str]]]:
    ensure_ffmpeg_tools()
    trimmed_files: List[str] = []
    trimmed_meta: Dict[str, Tuple[str, str]] = {}

    for entry in os.scandir(DOWNLOAD_DIR):
        if not entry.is_file():
            continue

        file = entry.name
        path = entry.path

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


def _find_loudest_start_streaming(path: str, window_ms: int, step_ms: int = 500) -> int:
    """Find loudest window start without loading full audio into memory."""
    ensure_ffmpeg_tools()
    if window_ms <= 0:
        return 0

    sample_rate = 22050
    step_samples = max(1, int(sample_rate * step_ms / 1000))
    step_bytes = step_samples * 2
    window_steps = max(1, window_ms // step_ms)

    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        path,
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "s16le",
        "-",
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if not proc.stdout:
        return 0

    energies = deque()
    sum_energy = 0.0
    best_sum = -1.0
    best_end_idx = -1
    step_idx = 0

    try:
        while True:
            data = proc.stdout.read(step_bytes)
            if not data or len(data) < step_bytes:
                break

            samples = array("h")
            samples.frombytes(data)
            if not samples:
                break

            # Energy per step; sliding sum finds the loudest window.
            energy = sum(s * s for s in samples) / len(samples)
            energies.append(energy)
            sum_energy += energy

            if len(energies) > window_steps:
                sum_energy -= energies.popleft()

            if len(energies) == window_steps and sum_energy > best_sum:
                best_sum = sum_energy
                best_end_idx = step_idx

            step_idx += 1
    finally:
        proc.stdout.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    if best_end_idx < 0:
        return 0

    best_start_step = best_end_idx - window_steps + 1
    return max(0, best_start_step * step_ms)


def _trim_chunk_at_start(path: str, out_path: str, start_sec: float, duration_sec: int) -> None:
    ensure_ffmpeg_tools()
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start_sec:.3f}",
            "-i",
            path,
            "-t",
            str(duration_sec),
            "-vn",
            "-acodec",
            "libmp3lame",
            "-b:a",
            "192k",
            out_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=90,
    )


def trim_loudest_chunks_from_files(
    duration_sec: int,
    files: List[str],
    meta_by_base: Dict[str, Tuple[str, str]],
) -> Tuple[List[str], Dict[str, Tuple[str, str]]]:
    ensure_ffmpeg_tools()
    trimmed_files: List[str] = []
    trimmed_meta: Dict[str, Tuple[str, str]] = {}
    window_ms = duration_sec * 1000

    for path in files:
        if not os.path.isfile(path):
            continue

        file = os.path.basename(path)

        base_name, _ = os.path.splitext(file)
        out_name = base_name + ".mp3"
        out_path = os.path.join(TRIM_DIR, out_name)

        try:
            start_ms = _find_loudest_start_streaming(path, window_ms)
            _trim_chunk_at_start(path, out_path, start_ms / 1000.0, duration_sec)
            trimmed_files.append(out_path)
            if base_name in meta_by_base:
                trimmed_meta[base_name] = meta_by_base[base_name]
        except Exception:
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


def trim_loudest_chunks(
    duration_sec: int,
    meta_by_base: Dict[str, Tuple[str, str]],
) -> Tuple[List[str], Dict[str, Tuple[str, str]]]:
    files = [entry.path for entry in os.scandir(DOWNLOAD_DIR) if entry.is_file()]
    return trim_loudest_chunks_from_files(duration_sec, files, meta_by_base)


def _resample_stereo(segment: AudioSegment) -> AudioSegment:
    return segment.set_frame_rate(44100).set_channels(2)


def _apply_eq_bands(segment: AudioSegment) -> AudioSegment:
    low = segment.low_pass_filter(200).apply_gain(-1.5)
    mud = segment.low_pass_filter(400).high_pass_filter(200).apply_gain(-3.0)
    mid = segment.low_pass_filter(2000).high_pass_filter(400)
    presence = segment.low_pass_filter(5000).high_pass_filter(2000).apply_gain(2.0)
    high = segment.high_pass_filter(5000).apply_gain(0.5)

    combined = low.overlay(mud)
    combined = combined.overlay(mid)
    combined = combined.overlay(presence)
    combined = combined.overlay(high)
    return combined


def _multiband_compress(segment: AudioSegment) -> AudioSegment:
    low = compress_dynamic_range(segment.low_pass_filter(200), threshold=-22.0, ratio=3.0, attack=5, release=80)
    mid = compress_dynamic_range(segment.high_pass_filter(200).low_pass_filter(3000), threshold=-20.0, ratio=3.5, attack=5, release=60)
    high = compress_dynamic_range(segment.high_pass_filter(3000), threshold=-24.0, ratio=2.5, attack=3, release=50)
    combined = low.overlay(mid)
    combined = combined.overlay(high)
    return combined


def _limit_and_normalize(segment: AudioSegment, target_dbfs: float = -14.0) -> AudioSegment:
    limited = compress_dynamic_range(segment, threshold=-6.0, ratio=10.0, attack=2, release=50)
    if limited.dBFS != float("-inf"):
        limited = limited.apply_gain(-1.0 - limited.max_dBFS)
        delta = target_dbfs - limited.dBFS
        limited = limited.apply_gain(delta)
    return limited


def merge_rotating_premium(
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
        seg = _resample_stereo(segment)
        seg = normalize(seg)
        return seg

    prepared = [prep(AudioSegment.from_file(f)[:duration_ms]) for f in files]

    slice_ms = max(10000, min(14000, duration_ms // 2))

    def make_scratch(source: AudioSegment, bpm_value: int) -> AudioSegment:
        beat_ms = int(60000 / bpm_value)
        burst_ms = max(80, beat_ms // 4)
        total_ms = beat_ms * 2
        src = source[:total_ms].apply_gain(-4)

        bursts: List[AudioSegment] = []
        pos = 0
        forward = True
        while pos + burst_ms <= len(src):
            chunk = src[pos:pos + burst_ms]
            bursts.append(chunk if forward else chunk.reverse())
            forward = not forward
            pos += burst_ms

        if not bursts:
            return AudioSegment.silent(duration=0)

        scratch = bursts[0]
        for part in bursts[1:]:
            scratch = scratch.append(part, crossfade=10)

        return scratch.apply_gain(-3)

    def low_pass_sweep(segment: AudioSegment) -> AudioSegment:
        chunks = []
        steps = 8
        step_ms = max(100, len(segment) // steps)
        for i in range(steps):
            cut = 800 + i * 900
            part = segment[i * step_ms:(i + 1) * step_ms].low_pass_filter(cut)
            chunks.append(part)
        return sum(chunks)

    def high_pass_sweep(segment: AudioSegment) -> AudioSegment:
        chunks = []
        steps = 8
        step_ms = max(100, len(segment) // steps)
        for i in range(steps):
            cut = 40 + i * 120
            part = segment[i * step_ms:(i + 1) * step_ms].high_pass_filter(cut)
            chunks.append(part)
        return sum(chunks)

    offsets = [0 for _ in prepared]
    rotated_parts: List[AudioSegment] = []

    while True:
        progressed = False
        for idx, segment in enumerate(prepared):
            if offsets[idx] >= len(segment):
                continue

            progressed = True
            slice_part = segment[offsets[idx]:offsets[idx] + slice_ms]
            offsets[idx] += slice_ms
            rotated_parts.append(slice_part)

        if not progressed:
            break

    if not rotated_parts:
        raise RuntimeError("Unable to assemble mashup")

    base_mix = rotated_parts[0]
    for part in rotated_parts[1:]:
        fade = min(effective_fade, len(base_mix) // 2, len(part) // 2)
        base_mix = base_mix.append(part, crossfade=fade)

    total_ms = len(base_mix)
    ratios = [0.12, 0.16, 0.16, 0.16, 0.1, 0.16]
    min_section = 4000
    remaining = total_ms
    lengths = []
    for ratio in ratios:
        length = max(min_section, int(total_ms * ratio))
        length = min(length, remaining)
        lengths.append(length)
        remaining -= length
    lengths.append(max(min_section, remaining))

    positions = [0]
    for length in lengths[:-1]:
        positions.append(positions[-1] + length)

    def replace_section(audio: AudioSegment, start: int, end: int, effect_fn) -> AudioSegment:
        if end <= start:
            return audio
        return audio[:start] + effect_fn(audio[start:end]) + audio[end:]

    intro_start, build_start, hook_start, drop_start, switch_start, peak_start, outro_start = positions[:7]
    intro_end = build_start
    build_end = hook_start
    hook_end = drop_start
    drop_end = switch_start
    switch_end = peak_start
    peak_end = outro_start

    print("\nMashup structure plan: Intro → Build → Hook → Drop → Switch → Peak → Outro")

    base_mix = replace_section(base_mix, intro_start, intro_end, low_pass_sweep)
    base_mix = replace_section(base_mix, build_start, build_end, high_pass_sweep)

    scratch = make_scratch(base_mix[hook_start:hook_end], bpm)

    if drop_start < total_ms:
        base_mix = base_mix.overlay(scratch, position=drop_start)
    if switch_start < total_ms:
        base_mix = base_mix.overlay(scratch, position=switch_start)

    base_mix = base_mix.fade_out(800)

    processed = _resample_stereo(base_mix)
    processed = processed.high_pass_filter(40)
    processed = _apply_eq_bands(processed)
    processed = _multiband_compress(processed)
    processed = _limit_and_normalize(processed, target_dbfs=-14.0)

    processed.export(output_file, format="mp3", bitrate="320k")


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
    downloaded_paths: List[str] = []
    for query, count in zip(queries, counts):
        meta, new_paths = download_videos_for_query(query, count, session_id, mode)
        meta_by_base.update(meta)
        downloaded_paths.extend(new_paths)

    trimmed_files, trimmed_meta = trim_loudest_chunks_from_files(
        duration,
        downloaded_paths,
        meta_by_base,
    )

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

    merge_rotating_premium(trimmed_files, output, duration)

    return session_id
