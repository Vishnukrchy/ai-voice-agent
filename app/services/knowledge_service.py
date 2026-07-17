from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.chroma_client import add_chunks, delete_file_chunks
from app.knowledge.chunker import chunk_text, extract_text
from app.models.knowledge_file import FileStatus, KnowledgeFile
from app.repositories.base import BaseRepository
from app.utils.logger import logger

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
UPLOAD_DIR = Path("uploads")


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BaseRepository(KnowledgeFile, db)

    async def upload_and_index(self, agent_id: str, file: UploadFile) -> KnowledgeFile:
        extension = (file.filename or "").rsplit(".", 1)[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '.{extension}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
            )

        agent_dir = UPLOAD_DIR / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        # Prefix with a UUID so two uploads sharing the same original filename
        # never overwrite each other on disk; the original name is preserved
        # in the DB record for display purposes.
        stored_name = f"{uuid4().hex}_{file.filename}"
        dest_path = agent_dir / stored_name

        contents = await file.read()
        dest_path.write_bytes(contents)

        record = await self.repo.create(
            agent_id=agent_id,
            filename=file.filename,
            file_path=str(dest_path),
            file_type=extension,
            status=FileStatus.processing,
        )

        try:
            text = extract_text(str(dest_path), extension)
            chunks = chunk_text(text)
            add_chunks(agent_id=agent_id, file_id=record.id, chunks=chunks)
            record = await self.repo.update(record, chunk_count=len(chunks), status=FileStatus.indexed)
            logger.info(f"Indexed '{file.filename}' for agent {agent_id}: {len(chunks)} chunks")
        except Exception:
            logger.exception(f"Failed to index knowledge file '{file.filename}' for agent {agent_id}")
            record = await self.repo.update(record, status=FileStatus.failed)

        return record

    async def delete_file(self, file_id: str) -> None:
        record = await self.repo.get(file_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge file not found")
        delete_file_chunks(record.agent_id, record.id)
        await self.repo.delete(file_id)
