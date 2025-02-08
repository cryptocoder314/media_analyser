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
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base
from src.common.configuration import get_configuration

SCHEMA = get_configuration("env")


class Subtitle(Base):
    __tablename__ = "subtitle"
    __table_args__ = {"schema": SCHEMA}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.media.id"), nullable=False)
    title = Column(String, nullable=True)
    language = Column(String, nullable=False)
    is_default = Column(Boolean, nullable=False)
    is_forced = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
