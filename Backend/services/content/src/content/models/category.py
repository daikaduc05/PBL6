import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "content"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
