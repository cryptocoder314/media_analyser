import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import uuid
from sqlalchemy import (
    Column,
    String,
    TIMESTAMP,
    func
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base
from src.common.configuration import get_configuration

SCHEMA = get_configuration("env")


class Content(Base):
    __tablename__ = "content"
    __table_args__ = {"schema": SCHEMA}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
