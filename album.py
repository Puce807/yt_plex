from config import *
from info import *
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
import re
import json
import subprocess
import os
import yt_dlp


def read(filepath):
    with open(filepath, "r") as file:
        return json.load(file)

def write(filepath, to_write):
    with open(filepath, "w") as file:
        if "json" in filepath:
            json_string = json.dumps(to_write, indent=4)
            file.write(json_string)
        else:
            file.write(to_write)

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


def set_meta(filename, meta, value):
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    audio = File(filename, easy=True)

    if audio is None:
        raise ValueError(f"Unsupported or unreadable audio format: {filename}")

    # Mutagen Easy mode expects a list of strings.
    # If it's already a list, we use it. If it's a string, we wrap it in a list.
    if isinstance(value, str):
        value = [value]

    # Ensure all items in the list are strings and cleaned of extra list-formatting characters
    # if they were accidentally passed in as a string-representation of a list.
    audio[meta] = value

    audio.save()
    print(f"Metadata successfully updated for {filename}: {meta} >>> {value}")

if __name__ == "__main__":
    if os.path.isfile("data.json"):
        data = read("data.json")
    else:
        write("data.json", {})
        data = {}

    user_input = input("Enter playlist URL: ")

    is_playlist = ("youtube" in user_input and "playlist" in user_input)

    # ---- Resolve entries ----
    if is_playlist:
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            playlist_info = ydl.extract_info(user_input, download=False)

        print(f"You selected {user_input} (PLAYLIST)")
        video_entries = playlist_info["entries"]

    else:
        #print("THIS FILE IS PLAYLIST ONLY")
        #raise ValueError
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
    artist = ""
    album = input("Enter album name: ")
    for D_artist, D_album in data.items():
        if D_album == album:
            answer = input(f"Is {album}'s artist {D_artist}? [y/n] ")
            if answer == "y":
                artist = album

    if artist == "":
        artist = input(f"Enter artist for {album}: ")
    print(f"Album: {album} Artist: {artist}")
    answer = input("Would you like to proceed? [y/n] ").lower()
    if answer == "n" or answer == "no":
        raise ValueError

    total_entries = len(video_entries)
    entry_num = 0
    #os.mkdir(album)

    # ---- Process entries ----
    for entry in video_entries:
        entry_num += 1
        URL = entry["url"]
        title = entry.get("title", "unknown_title")
        safe_title = cleanup(title)

        print(f"\n--- Processing: {title} {entry_num}/{total_entries }---")
        clean_files()

        local_folder = os.path.join(artist, album)
        album_folder = os.path.join(OUTPUT_DESTINATION, local_folder)
        os.makedirs(album_folder, exist_ok=True)

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
                final_path = os.path.join(album_folder, final_name)
                os.rename(f"output.{video_file_type}", final_name)
                print(f"Saved as: {final_name}")

        else:
            print("Downloading audio only...")
            with yt_dlp.YoutubeDL(audio_opts()) as ydl:
                ydl.extract_info(URL, download=True)

            final_name = f"{safe_title}.mp3"
            final_path = os.path.join(album_folder, final_name)

            if os.path.exists("audio.mp3"):
                os.rename("audio.mp3", final_path)
                print(f"Saved as: {final_path}")
            else:
                print("ERROR: audio.mp3 was not created")

            try:
                set_meta(final_path, "title", safe_title)
                set_meta(final_path, "artist", artist)
                set_meta(final_path, "album", album)
                set_meta(final_path, "albumartist", artist)
                set_meta(final_path, "tracknumber", str(entry_num))
            except (FileNotFoundError, ValueError):
                print("Metadata unsuccessful")

    clean_files()
    print("--- Finished Processing ---")
