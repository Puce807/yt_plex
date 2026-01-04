from config import *
from info import *
import re
import json
import subprocess
import os
import yt_dlp


def read(filePath):
    with open(filePath, "r") as file:
        return json.load(file)


def clean_files():
    for f in ("output.mp4", "video.mp4", "video.webm", "audio.mp3"):
        if os.path.exists(f):
            os.remove(f)


def cleanup(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()


def video_opts():
    out = {
        "outtmpl": "video.%(ext)s",
        "format": "bestvideo",
        "noplaylist": True,
        "quiet": quiet,
        "ignoreerrors": True,
        "no_warnings": True,
    }
    if ffmpeg_location != "PATH":
        out["ffmpeg_location"] = ffmpeg_location
    return out


def audio_opts():
    out = {
        "outtmpl": "audio.%(ext)s",
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": quiet,
        "ignoreerrors": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(audio_bitrate),
        }],
    }
    if ffmpeg_location != "PATH":
        out["ffmpeg_location"] = ffmpeg_location
    return out


def merge_audio():
    try:
        subprocess.run(
            ["ffmpeg", "-i", "video.mp4", "-i", "audio.mp3",
             "-c:v", "copy", "-c:a", "aac", f"output.{video_file_type}"],
            check=True
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            ["ffmpeg", "-i", "video.webm", "-i", "audio.mp3",
             "-c:v", "copy", "-c:a", "aac", f"output.{video_file_type}"],
            check=True
        )

    for f in ("video.mp4", "video.webm", "audio.mp3"):
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    user_input = input("Enter song name/URL: ")

    is_playlist = ("youtube" in user_input and "playlist" in user_input)

    # ---- Resolve entries ----
    if is_playlist:
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            playlist_info = ydl.extract_info(user_input, download=False)

        print(f"You selected {user_input} (PLAYLIST)")
        video_entries = playlist_info["entries"]

    else:
        if "youtube.com" in user_input or "youtu.be" in user_input:
            URL = user_input
            print(f"You selected: {user_input} (URL)")
        else:
            URL = f"ytsearch1:{user_input}"
            print(f"You selected: {user_input} (SEARCH)")
            print(f"URL: {URL}")

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(URL, download=False)

        video_entries = [{"url": URL, "title": info["title"]}]

    include_video = input("Include video? [y/n] ").lower() == "y"

    # ---- Process entries ----
    for entry in video_entries:
        URL = entry["url"]
        title = entry.get("title", "unknown_title")
        safe_title = cleanup(title)

        print(f"\n--- Processing: {title} ---")
        clean_files()

        if include_video:
            print("Downloading video...")
            with yt_dlp.YoutubeDL(video_opts()) as ydl:
                ydl.download([URL])

            print("Downloading audio...")
            with yt_dlp.YoutubeDL(audio_opts()) as ydl:
                ydl.download([URL])

            if not separate_audio:
                merge_audio()
                final_name = f"{safe_title}.{video_file_type}"
                os.rename(f"output.{video_file_type}", final_name)
                print(f"Saved as: {final_name}")

        else:
            print("Downloading audio only...")
            with yt_dlp.YoutubeDL(audio_opts()) as ydl:
                ydl.extract_info(URL, download=True)

            final_name = f"{safe_title}.mp3"
            if os.path.exists("audio.mp3"):
                os.rename("audio.mp3", final_name)
                print(f"Saved as: {final_name}")
            else:
                print("ERROR: audio.mp3 was not created")

    clean_files()
    print("--- Finished Processing ---")
