import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("files")

async def save_file_to_disk(file: UploadFile, user_id: int) -> tuple[str, str, int]:
    """Helper function to generate a random name and save the file to disk."""
    #unique 32-character string _ path name 
    random_filename = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    dest = user_dir / random_filename
    
    content = await file.read()
    dest.write_bytes(content)
    
    return random_filename, str(dest), len(content)