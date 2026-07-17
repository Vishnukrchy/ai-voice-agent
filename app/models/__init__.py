"""
Import every model here so that Base.metadata sees all tables.
This is required for both `init_models()` (dev convenience create_all)
and Alembic's autogenerate to work correctly.
"""
from app.models.agent import Agent
from app.models.call import Call, CallDirection, CallStatus
from app.models.call_recording import CallRecording
from app.models.call_summary import CallSummary
from app.models.campaign import Campaign, CampaignStatus
from app.models.conversation_message import ConversationMessage, Speaker
from app.models.customer import Customer
from app.models.extracted_information import ExtractedInformation
from app.models.knowledge_file import FileStatus, KnowledgeFile
from app.models.settings import Setting
from app.models.user import User, UserRole

__all__ = [
    "Agent",
    "Call",
    "CallDirection",
    "CallStatus",
    "CallRecording",
    "CallSummary",
    "Campaign",
    "CampaignStatus",
    "ConversationMessage",
    "Speaker",
    "Customer",
    "ExtractedInformation",
    "FileStatus",
    "KnowledgeFile",
    "Setting",
    "User",
    "UserRole",
]
