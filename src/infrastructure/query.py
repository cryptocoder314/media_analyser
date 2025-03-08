import uuid

from sqlalchemy import (
    select
)
from src.infrastructure.models.source import Source
from src.infrastructure.models.media import Media
from src.infrastructure.models.content import Content
from src.infrastructure.models.audio import Audio
from src.infrastructure.models.subtitle import Subtitle


def get_source_by_name(session, source_name: str):
    query = select(Source).where(Source.name == source_name)
    result = session.execute(query)
    result = result.scalar_one_or_none()
    return result


def get_content_by_name(session, content_name: str):
    query = select(Content).where(Content.name == content_name)
    result = session.execute(query)
    result = result.scalar_one_or_none()
    return result


def get_media_by_name(session, name: str):
    query = select(Media).where(Media.name == name)
    result = session.execute(query)
    result = result.scalar_one_or_none()
    return result


def get_audio_by_media_id_title_and_language(session, media_id: uuid.uuid4, title: str, language: str):
    query = select(Audio).where(Audio.media_id == media_id, Audio.title == title, Audio.language == language)
    result = session.execute(query)
    result = result.scalar_one_or_none()
    return result


def get_subtitle_by_media_id_title_and_language(session, media_id: uuid.uuid4, title: str, language: str):
    query = select(Subtitle).where(Subtitle.media_id == media_id, Subtitle.title == title, Subtitle.language == language)
    result = session.execute(query)
    result = result.scalar_one_or_none()
    return result


def insert_source(session, name: str):
    new_data = Source(name=name)
    session.add(new_data)
    session.commit()
    session.refresh(new_data)
    return new_data


def insert_content(session, name: str, category: str):
    new_data = Content(name=name, category=category)
    session.add(new_data)
    session.commit()
    session.refresh(new_data)
    return new_data


def insert_media(session, source_name, media_type, content_id, name, codec, duration, bitrate_mode, width, height, framerate_mode, framerate, bitdepth, file_size, file_extension, overall_bitrate):
    result = session.execute(
        select(Source.id).where(Source.name == source_name)
    )
    source_id = result.scalar_one_or_none()

    new_data = Media(source_id=source_id, media_type=media_type, content_id=content_id, name=name, codec=codec, duration=duration, bitrate_mode=bitrate_mode, width=width, height=height, framerate_mode=framerate_mode, framerate=framerate, bitdepth=bitdepth, file_size=file_size, file_extension=file_extension, overall_bitrate=overall_bitrate)
    session.add(new_data)
    session.commit()
    session.refresh(new_data)
    return new_data


def insert_audio(session, media_id, format, channels, title, language):
    new_data = Audio(media_id=media_id, format=format, channels=channels, title=title, language=language)
    session.add(new_data)
    session.commit()
    session.refresh(new_data)
    return new_data


def insert_subtitle(session, media_id, title, language, is_forced):
    new_data = Subtitle(media_id=media_id, title=title, language=language, is_forced=is_forced)
    session.add(new_data)
    session.commit()
    session.refresh(new_data)
    return new_data
