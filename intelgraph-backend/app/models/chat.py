from typing import Optional, List
from pydantic import BaseModel, Field

class Citation(BaseModel):
    document_name: str
    document_id: str
    page_number: int = 1
    section_title: str = "General"
    record_date: Optional[str] = None
    version: str = "v1.0"
    governance_status: str = "Approved"
    excerpt: str

class ChatRequest(BaseModel):
    query: str
    asset_tag: Optional[str] = None
    user_role: str = "Maintenance Engineer"  # Maintenance Engineer | Quality / Compliance User | Plant Manager
    trusted_sources_only: bool = True

class ChatResponse(BaseModel):
    answer: str
    confidence: str = "High"  # High | Medium | Low
    evidence_summary: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    safety_disclaimer: str = (
        "AI-generated guidance. Verify against approved procedure, OEM documentation, "
        "and applicable site safety requirements before performing work."
    )
    refused: bool = False
    query_latency_ms: float = 0.0

class BenchmarkQuestion(BaseModel):
    id: str
    category: str
    asset_tag: str
    question: str
    expected_answer_keywords: List[str]
    expected_document_ids: List[str]
    expected_pages: List[int]
    is_refusal_expected: bool = False

class BenchmarkResult(BaseModel):
    total_questions: int
    passed_count: int
    answer_accuracy_pct: float
    retrieval_accuracy_pct: float
    citation_accuracy_pct: float
    refusal_accuracy_pct: float
    avg_latency_ms: float
    manual_search_estimated_time_s: float
    platform_speedup_factor: float
    details: List[dict]
