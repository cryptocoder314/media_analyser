import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.common.configuration import get_configuration

engine = create_engine(
    get_configuration("database"),
    echo=False
)

SessionFactory = sessionmaker(
    engine,
    expire_on_commit=False
)

def get_session():
    return SessionFactory()
