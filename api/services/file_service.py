from pathlib import Path
from typing import Union
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import FileContentRecord, FileRecord


class FileService:
    # Fixed the type hint here using Union for Python 3.9 compatibility
    def __init__(self, base_dir: Union[Path, str] = "files") -> None:
        self.base_dir = Path(base_dir)

    def get_upload_dir(self, user_id: int) -> Path:
        """Return the upload directory for a given user (without creating it)."""
        return self.base_dir / str(user_id)

    async def store(self, file: UploadFile, user_id: int) -> dict:
        """Store an uploaded file on disk under files/{user_id}/ and return metadata (including raw bytes)."""

        original_name = Path(file.filename or "").name
        ext = Path(original_name).suffix

        random_name = f"{uuid4().hex}{ext}"

        user_dir = self.get_upload_dir(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        dest = user_dir / random_name

        content = await file.read()
        dest.write_bytes(content)

        return {
            "filename": original_name,
            "stored_filename": random_name,
            "content_type": file.content_type or "application/octet-stream",
            "size": len(content),
            "path": str(dest),
            "raw_bytes": content,
        }

    async def store_and_record(
        self,
        *,
        file: UploadFile,
        user_id: int,
        db: Session,
    ) -> FileRecord:
        """Store file on disk and create a FileRecord in the database."""

        # 1. Store file on disk
        stored = await self.store(file=file, user_id=user_id)

        # 2. Store file metadata in DB
        record = FileRecord(
            original_name=stored["filename"],
            random_name=stored["stored_filename"],
            content_type=stored["content_type"],
            size=stored["size"],
            path=stored["path"],
            user_id=user_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
      
        # 3. Store file content as tsvector in DB
        
        raw_bytes = stored.get("raw_bytes", b"")
        try:
            text_content = raw_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text_content = ""

        if text_content:
            content_record = FileContentRecord(
                file_id=record.id,
                content_tsv=func.to_tsvector("english", text_content),
            )
            db.add(content_record)

        db.commit()
        db.refresh(record)

        return record
    
    def search_content(
            self,
            *,
            query: str,
            user_id: int,
            db: Session,
            limit: int = 20,
            offset: int = 0,
    ) -> list[dict]:
        q = (query or "").strip()
        if not q:
            return []
        
        tsquery = func.websearch_to_tsquery("english", q)
        rank = func.ts_rank_cd(FileContentRecord.content_tsv, tsquery).label("rank")

        rows = (
            db.query(FileRecord, rank)
            .join(FileContentRecord, FileContentRecord.file_id == FileRecord.id)
            .filter(FileRecord.user_id == user_id)
            .filter(FileContentRecord.content_tsv.op("@@")(tsquery))
            .order_by(rank.desc(), FileRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        results: list[dict] = []
        for file_record, file_rank in rows:
            results.append(
                {
                    "rank": float(file_rank or 0.0),
                    "file" : {
                        "id": file_record.id,
                        "original_name": file_record.original_name,
                        "random_name": file_record.content_type,
                        "size": file_record.size,
                        "user_id": file_record.user_id,
                        "created_at": file_record.created_at,
                        "path": file_record.path,

                    },
                }
            )
        return results


def get_file_service() -> FileService:
    """FastAPI dependency to provide a FileService instance."""
    return FileService()