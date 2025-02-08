import subprocess
import json
from src.infrastructure.query import (
    get_content_by_name,
    insert_content,
    insert_media,
    get_audio_by_media_id_title_and_language,
    get_subtitle_by_media_id_title_and_language,
    insert_audio,
    insert_subtitle
)
from src.common.common import (
    normalize_codec,
    detect_language
)
from src.common.configuration import get_configuration


def process_file(session, file_path):
    extract_media_info(session, file_path)


def extract_media_info(session, file_path):
    result = subprocess.run(
        ["mediainfo", "--Language=raw", "--Output=JSON", file_path],
        capture_output=True, text=True
    )
    json_result = json.loads(result.stdout) if result.stdout else {}

    content_name = file_path.name.split(" - ", 1)[1].rsplit(".", 1)[0] if "Movie" in str(file_path) else file_path.parent.parent.name
    content = get_content_by_name(session, content_name)

    if not content:
        content = insert_content(session, content_name)
        content_id = content.id
    else:
        content_id = content.id

    extract_and_insert_media_info(session, json_result, file_path, content_id)


def extract_and_insert_media_info(session, json_result, file_path, content_id):
    source = file_path.name.split("] ")[0][1:] if "] " in file_path.name else "Unknown"
    general_track = next((track for track in json_result.get("media", {}).get("track", []) if track.get("@type") == "General"),
                         {})
    file_size = general_track.get("FileSize")
    file_extension = general_track.get("FileExtension")

    video_track = next((track for track in json_result.get("media", {}).get("track", []) if track.get("@type") == "Video"), {})
    codec = normalize_codec(video_track.get("Format"))
    duration = int(float(video_track.get("Duration", 0))) if video_track.get("Duration") else None
    bitrate_mode = video_track.get("BitRate_Mode")
    width = int(video_track.get("Width", 0)) if video_track.get("Width") else None
    height = int(video_track.get("Height", 0)) if video_track.get("Height") else None
    framerate_mode = video_track.get("FrameRate_Mode")
    framerate = float(video_track.get("FrameRate", 0)) if video_track.get("FrameRate") else None
    bitdepth = int(video_track.get("BitDepth", 0)) if video_track.get("BitDepth") else None

    media_type = None
    if "Season" in file_path.parent.name:
        media_type = 'Season Episode'
    elif "Specials" in file_path.parent.name:
        media_type = 'Special Episode'
    elif "Movie" in file_path.parent.name:
        media_type = 'Movie'

    media = insert_media(session, source, media_type, content_id, file_path.name, codec, duration, bitrate_mode, width, height,
                 framerate_mode, framerate, bitdepth, file_size, file_extension)

    if media:
        for track in json_result.get("media", {}).get("track", []):
            if track.get("@type") == "Audio":
                audio = get_audio_by_media_id_title_and_language(session, media.id, track.get("Title"), track.get("Language"))

                if not audio:
                    insert_audio(session, media.id, track.get("Format"), int(track.get("Channels", 0)), track.get("Title"), detect_language(track.get("Language", "")), track.get("Default") == "Yes")
            elif track.get("@type") == "Text":
                subtitle = get_subtitle_by_media_id_title_and_language(session, media.id, track.get("Title"),
                                                                 track.get("Language"))

                if not subtitle:
                    insert_subtitle(session, media.id, track.get("Title"),
                        detect_language(track.get("Language", "")),
                        track.get("Default") == "Yes", track.get("Forced") == "Yes")

    print(f"Processed: {file_path.name}")