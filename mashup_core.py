import sys
import os
import shutil
import random
from yt_dlp import YoutubeDL
from advanced_mashup import trim_all_mid, merge_with_crossfade
from mongodb_helper import mongo_handler

DOWNLOAD_DIR = "downloads"
TRIM_DIR = "trimmed"
ARTIST_INFO = {}
CURRENT_SESSION_ID = None

def prepare_dirs():
    """Efficiently clear and recreate directories with retry logic"""
    for path in (DOWNLOAD_DIR, TRIM_DIR):
        if os.path.exists(path):
            for attempt in range(3):
                try:
                    shutil.rmtree(path)
                    break
                except PermissionError:
                    if attempt == 2:
                        print(f"Warning: Using existing {path} due to access permissions.")
        os.makedirs(path, exist_ok=True)

def download_videos(singer, n):
    """Download videos with optimized search and storage"""
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

    query = f"ytsearch{n * 3}:{singer} songs"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        # Filter valid entries in one pass
        entries = [e for e in (info.get("entries") or []) if e and e.get("webpage_url")]
        
        if not entries:
            raise RuntimeError("No videos found for the artist.")

        # Sample or use all entries
        selected = random.sample(entries, min(n, len(entries))) if len(entries) > n else entries

        # Store artist info from first video
        global ARTIST_INFO
        ARTIST_INFO = {
            "thumbnail": selected[0].get("thumbnail", ""),
            "title": selected[0].get("title", singer),
            "uploader": selected[0].get("uploader", singer),
        }
        print(f"Artist info captured: {ARTIST_INFO['title']}")

        # Download all selected videos
        for entry in selected:
            if url := entry.get("webpage_url"):
                ydl.download([url])
        
        # Store downloaded songs in MongoDB (single directory scan)
        if mongo_handler.connected and CURRENT_SESSION_ID:
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    mongo_handler.store_song(filepath, singer, CURRENT_SESSION_ID)

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
        trimmed = trim_all_mid(duration)
        merge_with_crossfade(trimmed, output)
        print("\n✅ Mashup completed successfully")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        

def run_mashup(singer, n, duration, output, user_email=None):
    """Main mashup generation function with MongoDB integration"""
    global CURRENT_SESSION_ID
    
    # Start MongoDB session
    if mongo_handler.connected and user_email:
        CURRENT_SESSION_ID = mongo_handler.start_new_session(singer, user_email)
    
    prepare_dirs()
    download_videos(singer, n)
    trimmed = trim_all_mid(duration)
    merge_with_crossfade(trimmed, output)
    
    return CURRENT_SESSION_ID


if __name__ == "__main__":
    main()