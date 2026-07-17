from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.knowledge import KnowledgeFileResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])


@router.post("/upload", response_model=KnowledgeFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_file(
    agent_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Uploads a PDF/DOCX/TXT file, extracts text, chunks it, and indexes
    it into the agent's ChromaDB collection for retrieval-augmented answers."""
    return await KnowledgeService(db).upload_and_index(agent_id, file)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await KnowledgeService(db).delete_file(file_id)
