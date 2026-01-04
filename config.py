
# --- YTDL options ---
ffmpeg_location = "PATH" # if not added to path, r"C:\ffmpeg\ffmpeg-8.0\bin"
quiet = False # Show progress (false = show)

audio_file_type = "mp3" # mp3, m4a, wav, opus, flac, aac
audio_bitrate = "192" # Bitrate in kbps - STRING
video_file_type = "mp4" # mp4, webm
separate_audio = False # False = 1 file, True = 1 video and 1 audio

output_template = "%(title)s.%(ext)s"  # Output filename template

categorise_output = True # Ask user for album and artist, clean title ready for plex