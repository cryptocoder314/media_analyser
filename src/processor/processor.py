import shutil
import json
import subprocess
from collections import defaultdict
import re
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
    detect_language,
    run_media_info,
    run_ffprobe,
    detect_iso_language_code
)

FORCED_KEYWORDS = ["forced", "forçada", "forcednarrative"]


def process_file(session, file_path, plex=False):
    print(f"Processing file: {file_path.name}")

    if plex:
        move_file_to_plex(file_path)
        print(f"File moved from Jellyfin to Plex: {file_path}")
        return

    renamed_file = rename_media_tracks(file_path)

    if renamed_file:
        updated_file = remove_unwanted_tracks(file_path)

        if updated_file:
            collected_file = extract_media_info(session, file_path)

            if collected_file:
                move_file_to_jellyfin(file_path)
                print(f"File moved from Processing to Jellyfin: {file_path.name}")
                print("------------------------------------------------------------------------------------------------")
                return


def rename_media_tracks(file_path):
    media_info = run_media_info(file_path)
    source = extract_source(file_path.name)
    if not source:
        return False

    communication_tracks = extract_communication_tracks(media_info)
    if not communication_tracks:
        return False

    tracks_by_language = classify_tracks(communication_tracks)
    if not tracks_by_language:
        return False

    organized_tracks = resolve_duplicates(tracks_by_language)
    if not organized_tracks:
        return False

    return apply_edits(file_path, organized_tracks)


def extract_source(file_name):
    return file_name.split("] ")[0][1:] if "] " in file_name else None


def extract_communication_tracks(media_info):
    return [track for track in media_info.get("media", {}).get("track", []) if track.get("@type") in ("Audio", "Text")]


def classify_tracks(tracks):
    categorized_tracks = {"audio": defaultdict(list), "text": defaultdict(list)}

    for track in tracks:
        track_info = extract_track_info(track)
        if not track_info:
            return False

        category = "audio" if track_info["type"] == "Audio" else "text"
        categorized_tracks[category][track_info["language"]].append(track_info)

    return categorized_tracks


def extract_track_info(track):
    track_id = track.get("UniqueID")
    track_type = track.get("@type")
    title = track.get("Title", "unknown")
    language = track.get("Language", "unknown")

    if title == "unknown" or language == "unknown":
        manual_review = True

    new_language = detect_language(language)
    new_title = new_language.capitalize()
    language_code = detect_iso_language_code(new_title)

    track_info = {
        "track_id": track_id,
        "type": track_type,
        "language": language,
        "title": title,
        "new_language": new_language,
        "new_title": new_title,
        "language_code": language_code
    }

    if track_type == "Text" and any(keyword in title.lower() for keyword in FORCED_KEYWORDS):
        track_info["forced"] = True
        track_info["new_title"] += " (Forced)"

    new_title = track_info["new_title"]
    print(f"Mapped {track_type}. Original code: {language}. New Code: {language_code}. Code lang: {new_language}. Original title: {title}. New title: {new_title}.")

    return track_info


def resolve_duplicates(tracks_by_language):
    organized_tracks = []

    for track_type, languages in tracks_by_language.items():
        for language, track_list in languages.items():
            forced_tracks = [t for t in track_list if "(Forced)" in t["new_title"]]
            normal_tracks = [t for t in track_list if "(Forced)" not in t["new_title"]]

            if len(normal_tracks) > 1:
                print(f"Duplicate {track_type} tracks found for {language} (Normal):")
                for track in normal_tracks:
                    print(f"ID: {track['track_id']}, Old Title: {track['title']}, New Title: {track['new_title']}")
                keep_id = input("Enter the track ID to keep: ")
                for track in normal_tracks:
                    if track['track_id'] != keep_id:
                        track['new_title'] = "remove"

            if len(forced_tracks) > 1:
                print(f"Duplicate {track_type} tracks found for {language} (Forced):")
                for track in forced_tracks:
                    print(f"ID: {track['track_id']}, Old Title: {track['title']}, New Title: {track['new_title']}")
                keep_id = input("Enter the track ID to keep: ")
                for track in forced_tracks:
                    if track['track_id'] != keep_id:
                        track['new_title'] = "remove"

            organized_tracks.extend(normal_tracks + forced_tracks)

    return organized_tracks


def apply_edits(file_path, tracks):
    for track in tracks:
        edit_params = {"name": track["new_title"], "language": track["language_code"]}
        if track.get("forced"):
            edit_params["flag-forced"] = 1

        mkv_edit_cmd = f"mkvpropedit \"{str(file_path)}\""
        for param, value in edit_params.items():
            mkv_edit_cmd += f" --edit track:={track['track_id']} --set {param}=\"{value}\""

        try:
            subprocess.run(mkv_edit_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Error on track {track['track_id']}: {e}")
            return False

    return True


def remove_unwanted_tracks(mkv_file):
    anime_content = "Processing" in str(mkv_file) and "Anime" in str(mkv_file)

    cmd = ["mkvmerge", "-J", mkv_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error processing {mkv_file}: {result.stderr}")
        return False

    mkv_info = json.loads(result.stdout)
    audio_tracks, subtitle_tracks, removed_tracks = [], [], []

    for track in mkv_info["tracks"]:
        track_id = str(track["id"])
        track_type = track["type"]
        title = track["properties"].get("track_name", "").lower()
        language = track["properties"].get("language", "unknown")

        if 'remove' in title:
            removed_tracks.append(track_id)

        if track_type == "audio":
            if anime_content and title not in {"japanese", "chinese"}:
                print(f"Removing track of title: '{title}' for breaking language rules")
                removed_tracks.append(track_id)
            elif not anime_content and title not in {"english", "portuguese"}:
                print(f"Removing track of title: '{title}' for breaking language rules")
                removed_tracks.append(track_id)
            else:
                audio_tracks.append(track_id)

        elif track_type == "subtitles":
            if not any(title.startswith(lang) for lang in {"english", "portuguese"}):
                print(f"Removing track of title: '{title}' for breaking language rules")
                removed_tracks.append(track_id)
            else:
                subtitle_tracks.append(track_id)

    audio_tracks_after_removal = [t for t in audio_tracks if t not in removed_tracks]

    if anime_content and len(audio_tracks_after_removal) == 0 and any(
            track_id in removed_tracks for track_id in audio_tracks):
        print("There's only one audio track left and it would be removed. Aborting.")
        return False

    if not removed_tracks:
        return True

    temp_file = f"temp_{mkv_file}"
    mkvmerge_cmd = ["mkvmerge", "-o", temp_file, "-a", ",".join(audio_tracks_after_removal),
                    "-s", ",".join(subtitle_tracks), mkv_file]

    result = subprocess.run(mkvmerge_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        subprocess.run(["mv", temp_file, mkv_file])
        print(f"Tracks removed successfully from {mkv_file}")
        return True
    else:
        print(f"Error processing {mkv_file}: {result.stderr}")
        return False


def extract_media_info(session, file_path):
    media_info = run_media_info(file_path)

    anime_content = True if "Processing" in str(file_path) and "Anime" in str(file_path) else False
    content_name = file_path.name.split(" - ", 1)[1].rsplit(".", 1)[0] if "Movie" in str(file_path) else file_path.parent.parent.name

    source = file_path.name.split("] ")[0][1:] if "] " in file_path.name else "Unknown"
    general_track = next((track for track in media_info.get("media", {}).get("track", []) if track.get("@type") == "General"),
                         {})
    file_size = general_track.get("FileSize")
    file_extension = general_track.get("FileExtension")
    overall_bitrate = general_track.get("OverallBitRate", 0)

    video_track = next((track for track in media_info.get("media", {}).get("track", []) if track.get("@type") == "Video"), {})
    codec = normalize_codec(video_track.get("Format"))
    duration = int(float(video_track.get("Duration", 0))) if video_track.get("Duration") else None

    bitrate_mode = video_track.get("BitRate_Mode")
    width = int(video_track.get("Width", 0)) if video_track.get("Width") else None
    height = int(video_track.get("Height", 0)) if video_track.get("Height") else None
    framerate_mode = video_track.get("FrameRate_Mode")
    framerate = float(video_track.get("FrameRate", 0)) if video_track.get("FrameRate") else None
    bitdepth = int(video_track.get("BitDepth", 0)) if video_track.get("BitDepth") else None

    if "Season" in file_path.parent.name:
        media_type = 'Season Episode'
    elif "Specials" in file_path.parent.name:
        media_type = 'Special Episode'
    elif "Movie" in file_path.parent.name and "Anime" in file_path.parent.parent.name:
        media_type = 'Anime Movie'
        category = 'Anime'
    else:
        media_type = 'Movie'
        category = media_type

    if media_type in ('Season Episode', 'Special Episode') and "Anime" in file_path.parent.parent.parent.parent.name:
        category = 'Anime'
    elif media_type in ('Season Episode', 'Special Episode') and "Anime" not in file_path.parent.parent.parent.parent.name:
        category = 'TV Show'

    if not duration or not framerate:
        # Handling rare cases where the .mkv was created without trusted metadata
        ffprobe_result = run_ffprobe(file_path)

        duration = int(float(ffprobe_result["format"]["duration"])) if "format" in ffprobe_result else None
        framerate = 25

    if not duration or not framerate:
        return False

    content = get_content_by_name(session, content_name)
    if not content:
        content = insert_content(session, content_name, category)
        content_id = content.id
    else:
        content_id = content.id

    media = insert_media(session, source, media_type, content_id, file_path.name, codec, duration, bitrate_mode, width, height,
                 framerate_mode, framerate, bitdepth, file_size, file_extension, overall_bitrate)

    if media:
        for track in media_info.get("media", {}).get("track", []):
            if track.get("@type") == "Audio":
                audio = get_audio_by_media_id_title_and_language(session, media.id, track.get("Title"), track.get("Language"))

                if not audio:
                    insert_audio(session, media.id, track.get("Format"), int(track.get("Channels", 0)), track.get("Title"), detect_language(track.get("Language", "")))
            elif track.get("@type") == "Text":
                subtitle = get_subtitle_by_media_id_title_and_language(session, media.id, track.get("Title"),
                                                                 track.get("Language"))

                if not subtitle:
                    insert_subtitle(session, media.id, track.get("Title"),
                        detect_language(track.get("Language", "")),
                        track.get("Forced") == "Yes")

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
