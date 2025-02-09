from pathlib import Path
from src.common.configuration import get_configuration
from src.infrastructure.connection import get_session
from src.infrastructure.query import (
    get_media_by_name
)
from src.infrastructure.infrastructure import create_infrastructure
from src.processor.processor import process_file


def process_folder(session, folder_path):
    folder_path = Path(folder_path)
    process_queue = []

    for file_path in folder_path.rglob("*"):
        if (file_path.is_file()
                and not file_path.name.startswith(".")
                and file_path.suffix.lower().lstrip('.') in {"mp4", "mkv"}):

            result = get_media_by_name(session, file_path.name)

            if not result:
                process_queue.append(file_path)

    if len(process_queue) > 0:
        print(f"{len(process_queue)} files need to be processed on folder {folder_path}")

    for file_path in process_queue:
        process_file(session, file_path)

def main():
    try:
        create_infrastructure()

        print("Starting processor")

        folders = [
            "processing_anime_show_folder",
            "processing_anime_movie_folder",
            "processing_cartoon_folder",
            "processing_movie_folder",
            "processing_show_folder"
        ]

        for folder in folders:
            with get_session() as session:
                process_folder(session, get_configuration(folder))
    except Exception as e:
        print(f"An exception occurred during execution. {str(e)}")

if __name__ == "__main__":
    main()
