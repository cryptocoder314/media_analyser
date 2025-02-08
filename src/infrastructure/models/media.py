import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import uuid
from sqlalchemy import (
    Column,
    String,
    TIMESTAMP,
    ForeignKey,
    func,
    Integer, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base
from src.common.configuration import get_configuration

SCHEMA = get_configuration("env")


class Media(Base):
    __tablename__ = "media"
    __table_args__ = {"schema": SCHEMA}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.source.id"), nullable=False)
    media_type = Column(String, nullable=False)
    content_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.content.id"), nullable=False)
    name = Column(String, nullable=False)
    codec = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    bitrate_mode = Column(String, nullable=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    framerate_mode = Column(String, nullable=True)
    framerate = Column(Integer, nullable=False)
    bitdepth = Column(Integer, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_extension = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
