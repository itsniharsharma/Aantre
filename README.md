# MashMix 🎧

**Professional YouTube Audio Mashup Generator** — Create Spotify-grade mashups from YouTube videos in minutes.

## Features

✨ **Smart Search**: Fetches top tracks by artist from YouTube  
🎯 **Precision Trim**: Extracts clips from the middle of songs for smooth transitions  
🎚️ **Clean Stitch**: Crossfaded merging with normalization for seamless playback  
📧 **Auto Email**: Delivers mashups directly to your inbox as ZIP files  
🎨 **Spotify-Inspired UI**: Professional dark theme with gradient accents

## Installation

### Prerequisites
- Python 3.8+
- ffmpeg (with ffprobe)

### Setup

```bash
# Install Python dependencies
pip install flask yt-dlp pydub python-dotenv

# Install ffmpeg (Windows)
# Option 1: Chocolatey
choco install ffmpeg

# Option 2: Download from https://ffmpeg.org/download.html
```

## Configuration

Create a `.env` file in the project directory:

```dotenv
MASHMIX_EMAIL="your_email@gmail.com"
MASHMIX_APP_PASSWORD="your_gmail_app_password"
```

**How to get Gmail App Password:**
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → App passwords
3. Select "Mail" and "Windows" → Generate
4. Copy the 16-character password to `.env`

## Usage

### Web Interface (Flask)
```bash
python app.py
```
Opens at `http://127.0.0.1:5000`

### Command Line
```bash
python 102303012.py "Artist Name" 12 25 mashup.mp3
```
- `Artist Name`: Singer to search for
- `12`: Number of videos to download (must be > 10)
- `25`: Duration in seconds per clip (must be > 20)
- `mashup.mp3`: Output file name

## Project Structure

```
mashup/
├── app.py                    # Flask web app
├── mashup_core.py           # Main mashup orchestration
├── advanced_mashup.py       # Advanced trimming & merging logic
├── 102303012.py             # CLI entry point
├── test_email.py            # Email connectivity test
├── .env                     # Configuration (not in git)
└── README.md
```

## How It Works

1. **Download**: YouTube search fetches top non-live videos
2. **Trim**: Extracts middle section from each clip (avoids intro/outro silence)
3. **Normalize**: Balances loudness across all clips
4. **Crossfade**: 2.5-second smooth transitions between clips
5. **Export**: High-quality MP3 output
6. **Email**: Sends ZIP to your inbox automatically

## Troubleshooting

### Email not sending?
Run: `python test_email.py` to diagnose

### FFmpeg not found?
```bash
# Add ffmpeg to PATH or reinstall:
pip install pydub
```

### Download stuck on live streams?
Already fixed! Videos are filtered with `!is_live & !is_upcoming`

### Audio quality issues?
- Increase duration (try 30-40 seconds instead of 25)
- More videos = better variety (try 15+ instead of 12)

## Files Generated

- `downloads/` — Downloaded audio files (temporary)
- `trimmed/` — Trimmed clips (temporary)
- `result.mp3` — Final mashup
- `result.zip` — Packaged for email delivery

## Requirements

- yt-dlp
- flask
- pydub
- python-dotenv

Install all: `pip install flask yt-dlp pydub python-dotenv`

## License

Created for educational & personal mashup generation.
