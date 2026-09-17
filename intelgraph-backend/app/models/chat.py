from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DependencyType(str, Enum):
    STANDALONE = "STANDALONE"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    GREETING = "GREETING"
    HYBRID = "HYBRID"
    CROSS_ASSET = "CROSS_ASSET"

class ConversationState(BaseModel):
    active_topic: Optional[str] = None
    active_asset: Optional[str] = None
    mentioned_assets: List[str] = Field(default_factory=list)
    last_intent: Optional[str] = None
    last_scope: Optional[str] = None
    entities: List[str] = Field(default_factory=list)
    referents: Dict[str, str] = Field(default_factory=dict)
    last_answer_subject: Optional[str] = None
    context_confidence: float = 1.0

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
    context_asset_tag: Optional[str] = None  # non-authoritative: currently selected UI machine, for pronoun resolution only
    tenant_id: Optional[str] = None
    user_role: str = "Maintenance Engineer"
    trusted_sources_only: bool = True
    conversation_history: List[dict] = Field(default_factory=list)
    scope_filter: str = "Auto"  # Auto | Current Asset | Selected Asset | Plant | Organization | General Knowledge
    active_asset_context: Optional[dict] = None

class ChatResponse(BaseModel):
    answer: str
    scope: str = "GENERAL"  # GENERAL | CUSTOMER | HYBRID | CROSS_ASSET | MAINTENANCE | RCA | COMPLIANCE | UNSUPPORTED
    response_format: str = "CONVERSATIONAL"  # CONVERSATIONAL | CUSTOMER_GROUNDED | HYBRID_ASSESSMENT | RCA_INVESTIGATION | COMPLIANCE_REVIEW | REFUSAL
    dependency_type: str = "STANDALONE"
    resolved_query: Optional[str] = None
    confidence: Optional[str] = None  # High | Medium | Low | None (None for General queries)
    evidence_summary: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    safety_disclaimer: str = (
        "AI-generated guidance. Verify against approved procedure, OEM documentation, "
        "and applicable site safety requirements before performing work."
    )
    refused: bool = False
    query_latency_ms: float = 0.0
    agent_name: str = "IntelGraph AI"
    traversal_hops: Optional[List[dict]] = Field(default_factory=list)
    latency_breakdown: Optional[dict] = Field(default_factory=dict)

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
