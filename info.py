import yt_dlp
import re
from difflib import get_close_matches

def get_channel(url):
    yt_args = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(yt_args) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("channel") or info.get("uploader")

def check_artist(name):
    test_for = [
        "lyrics", "lyric", "audio", "mix", "nightcore",
        "topic", "records", "label", "music", "official audio"]

    return not any(s in name.lower() for s in test_for)

def clean_name(name):
    name = name.lower()
    remove = ["vevo", "official", "topic", "records", "label", "music", "(", ")", "lyric", "video"]
    for r in remove:
        name = re.sub(rf"(?i){re.escape(r)}", "", name)
    name = re.sub(r"\s{2,}", " ", name)
    return name.strip()

def check_existing_artist(name, cache):
    for artist in cache.values():
        if name == artist:
            return True
    return False

def check_existing_song(name, album, artist, cache):
    songs = cache[album]["tracks"]
    if name in songs:
        return True
    else:
        return False

def find_close_artist(candidate, cache, cutoff=0.7):
    artists = list(cache.values())
    matches = get_close_matches(candidate, artists, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def find_close_album(candidate, cache, cutoff=0.7):
    albums = list(cache.keys())
    matches = get_close_matches(candidate, albums, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def find_artist(name, cache):
    name = clean_name(name)

    existing = check_existing_artist(name, cache)
    if existing:
        return existing

    close = find_close_artist(name, cache)
    if close is not None:
        return close
    else:
        return name