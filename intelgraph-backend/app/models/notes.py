from typing import Optional
from pydantic import BaseModel

class HumanNote(BaseModel):
    note_id: str
    asset_tag: str
    author: str
    author_role: str
    created_at: str
    text: str
    component: Optional[str] = None
    attachment_name: Optional[str] = None
    verified: bool = False
    verification_status: str = "Unverified Operator Note"
