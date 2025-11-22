
from config import *
from typing import Any
import subprocess
import os
import yt_dlp

if __name__ == '__main__':
    user_input = input("Enter song name/URL: ")
    if "youtube.com" in user_input: # URL
        print(f"You selected: {user_input} (URL)")
        URL = user_input
    else: # Search
        URL = f"ytsearch1:{user_input}"
        print(f"You selected: {user_input} (SEARCH)")
        print(f"URL: {URL}")
    user_input = input("Include video? [y/n] ").lower()
    include_video = True if user_input == "y" else False

    if os.path.exists("output.mp4"): os.remove("output.mp4")
    if os.path.exists("video.mp4"): os.remove("video.mp4")
    if os.path.exists("video.webm"): os.remove("video.webm")
    if os.path.exists("audio.mp3"): os.remove("audio.mp3")

    if include_video:
        # Download video and audio separately
        ydl_opts_video = {
            "outtmpl": "video.%(ext)s",
            "format": "bestvideo",
            "noplaylist": True,
            "quiet": quiet,
            "ignoreerrors": True,
            "no_warnings": True,
        }

        ydl_opts_audio = {
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
            ydl_opts_video["ffmpeg_location"] = ffmpeg_location
            ydl_opts_audio["ffmpeg_location"] = ffmpeg_location

        print("Downloading video...")
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([URL])

        print("Downloading audio...")
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([URL])

        if not separate_audio:
            cmd = [
                "ffmpeg",
                "-i", "video.mp4",
                "-i", "audio.mp3",
                "-c:v", "copy",
                "-c:a", "aac",
                f"output.{video_file_type}"
            ]

            try: subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                cmd = [
                    "ffmpeg",
                    "-i", "video.webm",
                    "-i", "audio.mp3",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    f"output.{video_file_type}"
                ]
                subprocess.run(cmd, check=True)
            os.remove("video.mp4")
            os.remove("audio.mp3")
            print("Video and audio merged successfully")

    else:
        # Audio-only mode
        ydl_opts = {
            "outtmpl": output_template,
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": quiet,
            "ignoreerrors": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_file_type,
                "preferredquality": str(audio_bitrate),
            }],
        }

        if ffmpeg_location != "PATH":
            ydl_opts["ffmpeg_location"] = ffmpeg_location

        print("Downloading audio only...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(URL, download=True)
            filename = ydl.prepare_filename(info_dict)
            print(f"Saved as: {filename}")


