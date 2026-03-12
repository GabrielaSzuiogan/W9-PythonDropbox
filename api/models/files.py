from datetime import datetime
from pydantic import BaseModel

class FileMetadataResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}