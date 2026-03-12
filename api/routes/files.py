from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.models import FileMetadataResponse
from db.database import get_db
from db.models import UserRecord, FileRecord 

# Import your auth AND file tools cleanly from utils!
from utils import get_current_user, save_file_to_disk

router = APIRouter(prefix="/files", tags=["files"])

@router.post("", response_model=FileMetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # 1. Use the utility function from utils/files.py!
    random_name, file_path, file_size = await save_file_to_disk(file, current_user.id)

    # 2. Save metadata to database
    new_file_record = FileRecord(
        user_id=current_user.id,
        filename=file.filename,
        stored_filename=random_name,
        file_path=file_path,
        content_type=file.content_type or "application/octet-stream",
        size=file_size
    )
    
    db.add(new_file_record)
    db.commit()
    db.refresh(new_file_record)

    return new_file_record


@router.get("", response_model=List[FileMetadataResponse])
def list_files(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files = db.query(FileRecord).filter(FileRecord.user_id == current_user.id).all()
    return files


@router.get("/{file_id}", response_model=FileMetadataResponse)
def retrieve_file_metadata(
    file_id: int,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(FileRecord).filter(
        FileRecord.id == file_id, 
        FileRecord.user_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    return file_record


@router.get("/{file_id}/content")
def retrieve_file_content(
    file_id: int,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(FileRecord).filter(
        FileRecord.id == file_id, 
        FileRecord.user_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing from disk")

    return FileResponse(
        path=file_path, 
        filename=file_record.filename, 
        media_type=file_record.content_type
    )