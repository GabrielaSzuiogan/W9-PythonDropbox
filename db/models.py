from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    func,
    ForeignKey,
)

#to easily access a user's files
from sqlalchemy.orm import relationship
from db.database import Base

class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    password_hash = Column(String, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    files = relationship("FileRecord", back_populates="owner")


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    #links this file to a specific user's ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    
    filename = Column(String, nullable=False)      
    stored_filename = Column(String, nullable=False) 
    file_path = Column(String, nullable=False)       
    content_type = Column(String, nullable=False)  
    size = Column(Integer, nullable=False)          
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # links back to the UserRecord
    owner = relationship("UserRecord", back_populates="files")