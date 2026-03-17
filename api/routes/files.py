from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session #connects your code to the database
from api.models import FileMetadataResponse
from api.services.file_service import FileService, get_file_service
from db.database import get_db
from db.models import FileContentRecord, UserRecord, FileRecord 
from utils import get_current_user

router = APIRouter(prefix="/files", tags=["files"])

@router.post("", response_model=FileMetadataResponse, status_code=status.HTTP_201_CREATED) #return data matching the FileMetadataResponse shape
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserRecord = Depends(get_current_user), #check who is logged in. If they aren't logged in, FastAPI stops them right here
    file_service: FileService = Depends(get_file_service),
    db: Session = Depends(get_db) 
):
    """Upload a file. Stored under files/{user_id}/ and record metadata in DB."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    record = await file_service.store_and_record(
        file=file,
        user_id=current_user.id,
        db=db,
    )

    return record

#fetches a list of all files a user owns
@router.get("", response_model=List[FileMetadataResponse])
def list_files(
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #a user can never see another user's files
    files = db.query(FileRecord).filter(FileRecord.user_id == current_user.id).all()
    return files



@router.get("/search_content")
def search_content(
    q: str,
    limit: int = 20,
    offset: int = 0,
    current_user: UserRecord = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
    db: Session = Depends(get_db)
):
    """
    Search for files by text. 
    Matches ONLY against the extracted file content.
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Search query 'q' cannot be empty"
        )
    
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    results = file_service.search_content(
        query=q,
        user_id=current_user.id,
        db=db,
        limit=limit,
        offset=offset,
    )

    return{ 
        "query" : q,
        "limit":limit,
        "offset":offset,
        "results" : results
    }

    # # Use a standard join since we only want files that actually have extracted text content
    # matched_records = db.query(FileRecord).join(FileContentRecord).filter(
    #     FileRecord.user_id == current_user.id,
    #     FileContentRecord.content_tsv.op("@@")(func.plainto_tsquery("english", q))
    # ).all()

    # return matched_records


#gets the details of a specific file
@router.get("/{file_id}", response_model=FileMetadataResponse)
def retrieve_file_metadata(
    file_id: int,
    current_user: UserRecord = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    #searches the database for a file that matches the requested file_id and is owned by the  first current_user
    file_record = db.query(FileRecord).filter(
        FileRecord.id == file_id, 
        FileRecord.user_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")   
    return file_record


#downloads or displays the file
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
        
    file_path = Path(file_record.path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing from disk")


    #file from the hard drive and securely stream it to the user's browser, 
    #giving it its original name and telling the browser what kind of file it is
    return FileResponse(
        path=file_path, 
        filename=file_record.original_name, 
        media_type=file_record.content_type
    )

