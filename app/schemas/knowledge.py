from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    filename: str
    file_type: str
    chunk_count: int
    status: str
    created_at: datetime
