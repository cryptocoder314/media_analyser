import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from src.infrastructure.connection import (
    engine,
    get_session
)
from src.infrastructure.models import ALL_MODELS
from src.infrastructure.query import (
    get_source_by_name,
    insert_source
)
from src.common.configuration import get_configuration

SCHEMA = get_configuration("env")

def create_infrastructure() -> None:
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))

    with engine.begin() as conn:
        for model in ALL_MODELS:
            model.metadata.create_all(conn, checkfirst=True)

    with get_session() as session:
        sync_database_with_json(session)

def sync_database_with_json(session):
    def load_json_file(path):
        with open(path, mode='r') as file:
            content = file.read()
            return json.loads(content)

    sync_source_from_json(session, load_json_file("./src/infrastructure/json/source.json"))


def sync_source_from_json(session, data):
    for item in data:
        row = get_source_by_name(session, item['name'])

        if row:
            continue

        insert_source(
            session,
            name=item["name"]
        )
