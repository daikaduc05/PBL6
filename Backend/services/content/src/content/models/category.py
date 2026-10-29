import uuid

from pbl6_common.db import Base
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "content"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("content.categories.id"), nullable=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    sort_order = Column(Integer, default=0)

    children = relationship("Category", backref="parent", remote_side=[id])
