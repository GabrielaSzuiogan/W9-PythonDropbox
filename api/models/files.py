from datetime import datetime
from pydantic import BaseModel

class FileMetadataResponse(BaseModel):
    id: int
    original_name: str
    content_type: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}

class FileChunkResponse(BaseModel):
    id: int
    text_content: str
    # Note: We do NOT return the embedding array because it is 2048 numbers long and would crash the browser!
    
    model_config = {"from_attributes": True}

class SearchResultResponse(BaseModel):
    rank: float
    file: FileMetadataResponse
    chunk: FileChunkResponse