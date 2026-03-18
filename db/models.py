from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    func,
    ForeignKey,
    Index
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from db.database import Base
from pgvector.sqlalchemy import Vector

class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    password_hash = Column(String, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    files = relationship("FileRecord", back_populates="user", cascade="all, delete-orphan")


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    #permanently links this file to a specific user's ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    original_name = Column(String, nullable=False)
    random_name = Column(String, nullable=False, index=True)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String, nullable=False)        
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # links back to the UserRecord
    user = relationship("UserRecord", back_populates="files")
    content = relationship(
        "FileContentRecord",
        back_populates="file",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # <-- UPDATED RELATIONSHIP: One file now has MANY chunks -->
    chunks = relationship(
        "FileChunkRecord",
        back_populates="file",
        cascade="all, delete-orphan",
    )



class FileContentRecord(Base):
    __tablename__ = "file_content"

    file_id = Column(Integer, ForeignKey("files.id"), primary_key=True)
    # Use a GIN index in Postgres for efficient full-text search.
    # We declare the index explicitly instead of using index=True to avoid a default btree index,
    # which can hit Postgres row-size limits for large tsvectors.
    content_tsv = Column(TSVECTOR, nullable=False)

    __table_args__ = (
        Index(
            "ix_file_content_content_tsv",
            "content_tsv",
            postgresql_using="gin",
        ),
    )

    file = relationship("FileRecord", back_populates="content")

class FileChunkRecord(Base):
    __tablename__ = "file_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    
    # We store the actual text of the chunk so we can show it to the user in the search results
    text_content = Column(String, nullable=False)
    
    # Full-text search (keyword match)
    content_tsv = Column(TSVECTOR, nullable=False)
    
    # Semantic search (Embedding match). Voyage-4 uses 2048 dimensions!
    embedding = Column(Vector(2048), nullable=False)

    __table_args__ = (
        # GIN index for fast full-text keyword search
        Index("ix_file_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
    )

    file = relationship("FileRecord", back_populates="chunks")