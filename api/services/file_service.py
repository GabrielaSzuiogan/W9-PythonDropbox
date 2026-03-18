from pathlib import Path
from typing import Union
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

#from db.models import FileContentRecord, FileRecord

from api.services.chunk_service import chunk_text, get_embeddings
from db.models import FileChunkRecord, FileRecord, FileContentRecord 


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
            #chunk the text content
            # chunks = chunk_by_char(text_content, chunk_size=150, chunk_overlap=20)
        except Exception:
            text_content = ""

        # if text_content:
        #     content_record = FileContentRecord(
        #         file_id=record.id,
        #         content_tsv=func.to_tsvector("english", text_content),
        #     )
        #     db.add(content_record)

        if text_content.strip():
            # 1. Use your new service to chunk the text
            chunks = chunk_text(text_content, chunk_size=500, chunk_overlap=50)
            
            if chunks:
                # 2. Use your new service to get the Voyage embeddings
                embeddings = get_embeddings(chunks)

                # 3. Save to database
                for i, chunk_text_str in enumerate(chunks):
                    chunk_record = FileChunkRecord(
                        file_id=record.id,
                        text_content=chunk_text_str,
                        content_tsv=func.to_tsvector("english", chunk_text_str),
                        embedding=embeddings[i]
                    )
                    db.add(chunk_record)

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
        
        # 1. Ask Voyage AI to turn the user's search query into an embedding
        from api.services.chunk_service import get_embeddings # Import your voyage function
        query_embeddings = get_embeddings([q])
        query_vector = query_embeddings[0]

        # 2. Tell pgvector to calculate the Cosine Distance between the search query and the file chunks
        # Cosine distance measures how similar the meaning of the texts are.
        distance = FileChunkRecord.embedding.cosine_distance(query_vector).label("distance")

        # 3. Query the database, joining the chunks to their parent files
        rows = (
            db.query(FileRecord, FileChunkRecord, distance)
            .join(FileChunkRecord, FileChunkRecord.file_id == FileRecord.id)
            .filter(FileRecord.user_id == user_id)
            .order_by(distance) # Smallest distance means closest match!
            .offset(offset)
            .limit(limit)
            .all()
        )

        # 4. Format the results for Postman
        results: list[dict] = []
        for file_record, chunk_record, dist in rows:
            # We convert "distance" into a "similarity score" (1.0 is a perfect match)
            similarity_score = 1.0 - float(dist) 
            
            results.append(
                {
                    "rank": similarity_score,
                    "file" : {
                        "id": file_record.id,
                        "original_name": file_record.original_name,
                        "content_type": file_record.content_type,
                        "size": file_record.size,
                        "created_at": file_record.created_at,
                    },
                    "chunk": {
                        "id": chunk_record.id,
                        "text_content": chunk_record.text_content
                    }
                }
            )
        return results


def get_file_service() -> FileService:
    """FastAPI dependency to provide a FileService instance."""
    return FileService()