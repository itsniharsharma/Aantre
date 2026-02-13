import sys
import os
import shutil
import random
from yt_dlp import YoutubeDL
from advanced_mashup import trim_all_mid, merge_with_crossfade

DOWNLOAD_DIR = "downloads"
TRIM_DIR = "trimmed"

def prepare_dirs():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    if os.path.exists(TRIM_DIR):
        shutil.rmtree(TRIM_DIR)

    os.makedirs(DOWNLOAD_DIR)
    os.makedirs(TRIM_DIR)

def download_videos(singer, n):
    print(f"\nDownloading top {n} videos for: {singer}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
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

    search_count = max(n * 3, n)
    query = f"ytsearch{search_count}:{singer} songs"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        entries = []
        if info and "entries" in info:
            entries = [
                e for e in info["entries"]
                if e and e.get("webpage_url")
            ]

        if not entries:
            raise RuntimeError("No videos found for the artist.")

        selected = (
            random.sample(entries, k=min(n, len(entries)))
            if len(entries) > n else entries
        )

        for entry in selected:
            url = entry.get("webpage_url")
            if url:
                ydl.download([url])

def trim_all(duration_sec):
    return trim_all_mid(duration_sec)


def merge_files(files, output_file):
    return merge_with_crossfade(files, output_file)


def validate_args(args):
    if len(args) != 5:
        print("\nUSAGE:")
        print("python <rollno.py> <SingerName> <NumberOfVideos> <DurationSec> <OutputFile>")
        print('Ex: python 102303012.py "Arijit Singh" 12 25 mashup.mp3\n')
        return False

    try:
        n = int(args[2])
        d = int(args[3])
    except:
        print("Error: NumberOfVideos and DurationSec must be integers")
        return False

    if n <= 10:
        print("Error: NumberOfVideos must be > 10")
        return False

    if d <= 20:
        print("Error: DurationSec must be > 20")
        return False

    if not args[4].lower().endswith(".mp3"):
        print("Error: Output file must be .mp3")
        return False

    return True

def main():
    if not validate_args(sys.argv):
        return

    singer = sys.argv[1]
    n = int(sys.argv[2])
    duration = int(sys.argv[3])
    output = sys.argv[4]

    try:
        prepare_dirs()
        download_videos(singer, n)
        trimmed = trim_all(duration)
        merge_files(trimmed, output)

        print("\n Mashup completed successfully")

    except Exception as e:
        print("\n Error occurred:", str(e))
        

def run_mashup(singer, n, duration, output):
    prepare_dirs()
    download_videos(singer, n)
    trimmed = trim_all(duration)
    merge_files(trimmed, output)


if __name__ == "__main__":
    main()