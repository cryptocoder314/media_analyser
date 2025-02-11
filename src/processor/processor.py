import subprocess
import json
import shutil
from pathlib import Path
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

FORCED_KEYWORDS = ["forced", "forçada", "forcednarrative"]
ALLOWED_AUDIO_LANGUAGES = {"japanese", "english", "portuguese"}
ALLOWED_SUBTITLE_LANGUAGES = {"portuguese", "english"}


def process_file(session, file_path, jellyfin_folder=False):
    if jellyfin_folder:
        moved = move_file_to_plex(file_path)

        if moved:
            print(f"File moved from Jellyfin to Plex: {file_path}")
            return

    debug_mode = True if get_configuration('debug_mode') == 'active' else False
    result = process_and_clean_media_info(file_path, debug_mode)

    if debug_mode:
        return

    if result:
        extract_media_info(session, file_path)
        completed = move_file_to_jellyfin(file_path)

        if completed:
            print(f"All process completed for: {file_path}")

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
    overall_bitrate = general_track.get("OverallBitRate", 0)

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
                 framerate_mode, framerate, bitdepth, file_size, file_extension, overall_bitrate)

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


def process_and_clean_media_info(file_path, debug_mode):
    result = subprocess.run([
        "mediainfo", "--Language=raw", "--Output=JSON", file_path
    ], capture_output=True, text=True)

    json_result = json.loads(result.stdout) if result.stdout else {}

    track_ids_to_remove = []
    tracks_to_edit = []

    is_anime = True if "Processing" in str(file_path) and "Anime" in str(file_path) else False
    default_audio = "japanese" if is_anime else "portuguese"
    default_subtitle = "portuguese" if is_anime else None

    for track in json_result.get("media", {}).get("track", []):
        track_id = track.get("UniqueID")
        track_type = track.get("@type")
        lang = detect_language(track.get("Language", "und"))

        if track_type == "Audio":
            title = track.get("Title", "")
            print(f"Detected language for audio: {lang} of title {title} for {track_type}")
            if lang in ALLOWED_AUDIO_LANGUAGES:
                edit_params = {"name": lang.capitalize()}
                if lang == default_audio:
                    edit_params["flag-default"] = 1
                tracks_to_edit.append((track_id, edit_params))
            else:
                if lang == "unknown" and debug_mode != 'active':
                    print(f"Language unknown for file: {file_path}")
                    return False
                track_ids_to_remove.append(track_id)

        elif track_type == "Text":
            title = track.get("Title", "")
            print(f"Detected language for subtitle: {lang} of title {title} for {track_type}")
            if lang in ALLOWED_SUBTITLE_LANGUAGES:
                title = lang.capitalize()
                edit_params = {"name": title}

                if any(keyword in track.get("Title", "").lower() for keyword in FORCED_KEYWORDS):
                    edit_params["flag-forced"] = 1
                    edit_params["name"] += " (Forced)"

                if lang == default_subtitle:
                    edit_params["flag-default"] = 1

                tracks_to_edit.append((track_id, edit_params))
            else:
                if lang == "unknown" and debug_mode != 'active':
                    print(f"Language unknown for file: {file_path}")
                    return False
                track_ids_to_remove.append(track_id)

    print("Editing properties")

    for track_id, edit_params in tracks_to_edit:
        mkv_edit_cmd = f"mkvpropedit \"{str(file_path)}\""
        for param, value in edit_params.items():
            mkv_edit_cmd += f" --edit track:={track_id} --set {param}=\"{value}\""
        try:
            if debug_mode:
                print("Debug mode active. Will not overwrite file")
                continue

            subprocess.run(mkv_edit_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Error on track {track_id}: {e}")
            return False

    return True


def move_file_to_jellyfin(file_path):
    new_path_parts = list(file_path.parts)
    new_path_parts[new_path_parts.index('Processing')] = 'Jellyfin'
    new_path = Path(*new_path_parts)

    new_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(file_path), str(new_path))

    if new_path.exists():
        return True
    return False


def move_file_to_plex(file_path):
    new_path_parts = list(file_path.parts)
    new_path_parts[new_path_parts.index('Jellyfin')] = 'Plex'
    new_path = Path(*new_path_parts)

    new_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(file_path), str(new_path))

    if new_path.exists():
        return True
    return False
