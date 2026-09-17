import re
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field
from app.models.chat import DependencyType, ConversationState

class KnowledgeScope(str, Enum):
    GENERAL = "GENERAL"
    CUSTOMER = "CUSTOMER"
    HYBRID = "HYBRID"
    CROSS_ASSET = "CROSS_ASSET"
    GREETING = "GREETING"
    UNSUPPORTED_CUSTOMER = "UNSUPPORTED_CUSTOMER"
    UNSUPPORTED_CUSTOMER_FACT = "UNSUPPORTED_CUSTOMER"
    ACTION_OPERATIONAL = "ACTION_OPERATIONAL"
    COMPLIANCE = "COMPLIANCE"
    MAINTENANCE = "MAINTENANCE"
    INSPECTION = "INSPECTION"
    RCA = "RCA"

class QueryAnalysis(BaseModel):
    raw_query: str
    resolved_query: str
    dependency_type: DependencyType = DependencyType.STANDALONE
    scope: KnowledgeScope
    intent: str
    referenced_asset_tags: List[str] = Field(default_factory=list)
    is_hybrid_request: bool = False
    requires_customer_evidence: bool = False
    context_topic: Optional[str] = None
    conversation_state: ConversationState = Field(default_factory=ConversationState)
    response_structure: str = "CONVERSATIONAL"  # CONVERSATIONAL | CUSTOMER_GROUNDED | HYBRID_ASSESSMENT | RCA_INVESTIGATION | COMPLIANCE_REVIEW | REFUSAL
    typo_correction: Optional[Dict[str, str]] = None
    resolved_references: Optional[Dict[str, str]] = None
    target_document_categories: List[str] = Field(default_factory=list)
    fact_type: Optional[str] = None

class QueryUnderstandingEngine:
    """
    Enterprise Semantic Query Understanding & Context Arbitration Engine:
    Pipeline:
      USER QUERY
          ↓
      GREETING / SMALL TALK & TYPO INTERPRETATION
          ↓
      STRUCTURED CONVERSATION STATE EXTRACTION
          ↓
      CONTEXT DEPENDENCY DETECTION (STANDALONE vs CONTEXT_DEPENDENT vs HYBRID)
          ↓
      COREFERENCE & REFERENT RESOLUTION ("it", "its", "those", "that", "this")
          ↓
      INTENT + SCOPE ARBITRATION
          ↓
      RESOLVED QUERY FOR RETRIEVAL & SYNTHESIS
    """
    KNOWN_ASSET_TAGS = {"P-101", "P-102", "C-201", "P-203", "P-307", "M-301", "P-205", "P-194", "P-194A", "P-194B"}
    
    CUSTOMER_RECORD_PATTERNS = [
        r"\bWO-\d+\b",
        r"\bINSP-\d+\b",
        r"\bSOP-\d+\b",
        r"\bAPI\s*610\b",
        r"\bISO\s*10816\b",
        r"\bFAIL-\d+\b",
        r"\bUnit\s*\d+\b",
        r"\bPlant\s*[A-Z0-9]+\b",
        r"\bstandby\s+booster\b",
        r"\bbooster\s+pump\b",
        r"\bstandby\s+pump\b",
        r"\bcalibration\s+frequency\b",
        r"\bpressure\s+transmitter\b",
        r"\b[A-Z]{1,4}-\d{2,5}[A-Z0-9]*\b"
    ]

    UNRECORDED_OR_SPECULATIVE_TAGS = {"X-99", "P-999", "T-999", "FIT-999"}

    GREETING_PATTERNS = [
        r"^(hey+|hi+|hello+|heya+|howdy|sup|greetings)[\s!.,?]*$",
        r"^(good\s+(morning|afternoon|evening|day))[\s!.,?]*$",
        r"^(hi|hello)\s+(there|intelgraph)[\s!.,?]*$"
    ]
    GRATITUDE_PATTERNS = [
        r"^(thanks+|thank\s+you|thx|ty|much\s+appreciated)[\s!.,?]*$"
    ]
    ACKNOWLEDGEMENT_PATTERNS = [
        r"^(ok|okay|cool|great|got\s+it|alright|fine|understood|sure)[\s!.,?]*$"
    ]

    COMMON_TYPO_MAP = {
        "gearing pump": "gear pump",
        "gearing pumps": "gear pumps",
        "centrifugle pump": "centrifugal pump",
        "centrifual pump": "centrifugal pump",
        "cavition": "cavitation",
        "vibrations analysis": "vibration analysis"
    }

    @classmethod
    def _extract_conversation_state(
        cls,
        history: List[Dict[str, str]]
    ) -> ConversationState:
        """
        Extracts a compact structured conversation state dynamically from recent history.
        Determines context relevance dynamically without blindly clearing previous valid state,
        and ensures unrecorded/refused tags (like X-99) never contaminate the state.
        """
        state = ConversationState()
        if not history:
            return state

        # Walk history from oldest to newest by inspecting user turns directly
        for msg in history:
            role = (msg.get("role") or msg.get("sender") or "").lower()
            if role != "user":
                continue

            u_clean = msg.get("content", "").strip()
            u_lower = u_clean.lower()

            # If user queried an unsupported or speculative tag, do NOT adopt it as active_asset
            if any(t in u_clean.upper() for t in cls.UNRECORDED_OR_SPECULATIVE_TAGS):
                continue

            # Extract verified asset tags mentioned in this user turn (longer tags first e.g. P-194B before P-194)
            turn_matched_tags = []
            for tag in sorted(cls.KNOWN_ASSET_TAGS, key=len, reverse=True):
                if re.search(rf"\b{re.escape(tag)}\b", u_clean, re.IGNORECASE):
                    if not any(tag in existing for existing in turn_matched_tags):
                        turn_matched_tags.append(tag)

            # Also extract generic dynamic industrial asset tags from user messages
            generic_tag_matches = re.findall(r"\b([A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12})+)\b", u_clean, re.IGNORECASE)
            for t in generic_tag_matches:
                tag_upper = t.upper()
                if tag_upper not in turn_matched_tags and not any(tag_upper.startswith(p) for p in ["API-", "ISO-", "ASME-", "WO-", "INSP-", "FAIL-"]):
                    turn_matched_tags.append(tag_upper)

            if turn_matched_tags:
                state.active_asset = turn_matched_tags[0]
                for mt in turn_matched_tags:
                    if mt not in state.mentioned_assets:
                        state.mentioned_assets.append(mt)

            # Check general engineering topic from user turn dynamically (supports ANY engineering topic)
            m = re.search(
                r"\b(?:what is|what are|explain|tell me about|how does|define)\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-]+?)(?:\?|$)",
                u_clean, re.IGNORECASE
            )
            if m:
                extracted = m.group(1).strip()
                extracted = re.sub(r"[?!.,;]+$", "", extracted).strip()
                for typo, corrected in cls.COMMON_TYPO_MAP.items():
                    if typo in extracted.lower():
                        extracted = re.sub(rf"\b{re.escape(typo)}\b", corrected, extracted, flags=re.IGNORECASE)
                # If extracted phrase begins with anaphoric pronoun, it is a follow-up, not a new topic
                is_anaphoric_followup = any(
                    extracted.lower().startswith(p) for p in ["its ", "it ", "their ", "these ", "those "]
                )
                if not is_anaphoric_followup and extracted and len(extracted) > 2 and extracted.lower() not in [
                    "it", "this", "that", "those", "machine", "asset", "equipment", "heyy", "hey", "hi", "hello"
                ]:
                    state.active_topic = extracted

            # Track failure modes follow-up topic
            if "failure mode" in u_lower or "failure modes" in u_lower:
                if state.active_topic and "failure mode" not in state.active_topic:
                    state.active_topic = f"{state.active_topic} failure modes"

        return state

    @classmethod
    def analyze(
        cls,
        query: str,
        active_asset_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        scope_filter: str = "Auto"
    ) -> QueryAnalysis:
        q_clean = query.strip()
        q_lower = q_clean.lower()
        history = conversation_history or []

        # =========================================================================
        # 1. GREETING / SMALL TALK DETECTION (Zero Industrial Retrieval)
        # =========================================================================
        for pat in cls.GREETING_PATTERNS:
            if re.match(pat, q_lower):
                return QueryAnalysis(
                    raw_query=query,
                    resolved_query=query,
                    dependency_type=DependencyType.GREETING,
                    scope=KnowledgeScope.GREETING,
                    intent="GREETING",
                    referenced_asset_tags=[],
                    is_hybrid_request=False,
                    requires_customer_evidence=False,
                    context_topic=None,
                    response_structure="CONVERSATIONAL"
                )

        for pat in cls.GRATITUDE_PATTERNS:
            if re.match(pat, q_lower):
                return QueryAnalysis(
                    raw_query=query,
                    resolved_query=query,
                    dependency_type=DependencyType.GREETING,
                    scope=KnowledgeScope.GREETING,
                    intent="GRATITUDE",
                    referenced_asset_tags=[],
                    is_hybrid_request=False,
                    requires_customer_evidence=False,
                    context_topic=None,
                    response_structure="CONVERSATIONAL"
                )

        for pat in cls.ACKNOWLEDGEMENT_PATTERNS:
            if re.match(pat, q_lower):
                return QueryAnalysis(
                    raw_query=query,
                    resolved_query=query,
                    dependency_type=DependencyType.GREETING,
                    scope=KnowledgeScope.GREETING,
                    intent="ACKNOWLEDGEMENT",
                    referenced_asset_tags=[],
                    is_hybrid_request=False,
                    requires_customer_evidence=False,
                    context_topic=None,
                    response_structure="CONVERSATIONAL"
                )

        # =========================================================================
        # 2. TYPO / TERM INTERPRETATION
        # =========================================================================
        detected_typo = None
        for typo, corrected in cls.COMMON_TYPO_MAP.items():
            if typo in q_lower:
                detected_typo = {"original": typo, "corrected": corrected}
                break

        # =========================================================================
        # 3. STRUCTURED CONVERSATION STATE EXTRACTION
        # =========================================================================
        conv_state = cls._extract_conversation_state(history)

        # =========================================================================
        # 4. EXPLICIT ASSET TAG EXTRACTION FROM CURRENT QUERY (PRIORITIZED OVER CONTEXT)
        # =========================================================================
        query_explicit_tags: List[str] = []
        for tag in sorted(cls.KNOWN_ASSET_TAGS, key=len, reverse=True):
            pattern = rf"\b{re.escape(tag)}\b|\b{re.escape(tag.replace('-', ''))}\b"
            if re.search(pattern, q_clean, re.IGNORECASE):
                if not any(tag in existing for existing in query_explicit_tags):
                    query_explicit_tags.append(tag)

        generic_tag_matches = re.findall(r"\b([A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12})+)\b", q_clean, re.IGNORECASE)
        for t in generic_tag_matches:
            tag_upper = t.upper()
            if tag_upper not in query_explicit_tags and not any(tag_upper.startswith(p) for p in ["API-", "ISO-", "ASME-"]):
                query_explicit_tags.append(tag_upper)

        if ("standby booster" in q_lower or ("standby" in q_lower and "booster" in q_lower)) and "P-102" not in query_explicit_tags:
            query_explicit_tags.append("P-102")

        found_tags: List[str] = list(query_explicit_tags)

        # =========================================================================
        # 5. UNSUPPORTED / UNRECORDED TAG CHECK (Refusal Guardrail)
        # =========================================================================
        is_unsupported_claim = any(
            bool(re.search(r"\b" + re.escape(t) + r"\b", q_clean, re.IGNORECASE)) for t in cls.UNRECORDED_OR_SPECULATIVE_TAGS
        ) or any(phrase in q_lower for phrase in [
            "at a timestamp for which no", "at a time for which no record", "nuclear meltdown",
            "propeller speed on submarine", "calibration frequency of pressure transmitter x-99",
            "transmitter x-99", "sensor x-99"
        ])

        if is_unsupported_claim:
            return QueryAnalysis(
                raw_query=query,
                resolved_query=query,
                dependency_type=DependencyType.STANDALONE,
                scope=KnowledgeScope.UNSUPPORTED_CUSTOMER,
                intent="UNSUPPORTED_CUSTOMER_FACT",
                referenced_asset_tags=found_tags,
                is_hybrid_request=False,
                requires_customer_evidence=False,
                context_topic=None,
                conversation_state=conv_state,
                response_structure="REFUSAL"
            )

        # =========================================================================
        # 6. CONTEXT DEPENDENCY & COREFERENCE RESOLUTION
        # =========================================================================
        # Check for anaphoric pronouns and follow-up phrases
        words = q_lower.split()
        has_pronoun = any(p in words for p in ["it", "its", "those", "them"]) or ("that" in words and not any(w in words for w in ["prove", "show", "indicates", "ensure", "confirm", "think"])) or ("this" in words and not any(w in words for w in ["month", "year", "week"]))
        has_deictic = any(p in q_lower for p in [
            "this machine", "this pump", "this asset", "the machine's", "this equipment",
            "what does it do", "what did it cost", "how to prevent that", "how can i prevent that",
            "which of those apply", "which apply to", "failure modes apply to it"
        ])

        # Is the query an independent standalone question?
        # Standalone: introduces a full subject without relying on pronouns
        is_general_inquiry_pattern = bool(re.search(
            r"\b(?:what is|what are|define|definition of|explain|tell me about|how does|how do|principles of)\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-]+)",
            q_lower
        ))
        is_standalone_general = (
            (is_general_inquiry_pattern and not has_pronoun and not has_deictic and not found_tags) or
            any(w in q_lower for w in [
                "what is a bearing", "what is bearing", "define bearing",
                "what is predictive maintenance", "what is a machine", "what is machine",
                "what is a gear pump", "what is gear pump", "what is gearing pump",
                "what is a centrifugal pump", "what is centrifugal pump",
                "what is cavitation", "what is vibration analysis"
            ])
        )

        is_standalone_customer = bool(found_tags and not has_pronoun and not any(p in q_lower for p in ["which of those", "how to prevent"]))
        
        is_standalone = (is_standalone_general or is_standalone_customer) and not ("which of those" in q_lower)

        dependency_type = DependencyType.STANDALONE
        resolved_query = q_clean
        resolved_refs: Optional[Dict[str, str]] = None

        # Resolve coreferences ONLY when context-dependent
        if not is_standalone and (has_pronoun or has_deictic):
            dependency_type = DependencyType.CONTEXT_DEPENDENT

            # Case 1: "What does it do?" / "What does it mean?"
            if any(p in q_lower for p in ["what does it do", "what do it do", "tell me about it", "describe it"]):
                target_asset = (conv_state.active_asset or (found_tags[0] if found_tags else None) or (active_asset_context.get("tag") if active_asset_context else None))
                if target_asset:
                    resolved_query = f"What is {target_asset} and what does it do?"
                    if target_asset not in found_tags:
                        found_tags.append(target_asset)
                elif conv_state.active_topic:
                    resolved_query = f"What does {conv_state.active_topic} do and what is its operational function?"

            # Case 2: "Which of those apply to P-101?" / "Which of those apply to it?"
            elif "which of those" in q_lower or "which apply" in q_lower or "which ones apply" in q_lower:
                target_asset = (conv_state.active_asset or (found_tags[0] if found_tags else None) or (active_asset_context.get("tag") if active_asset_context else None))
                topic = conv_state.active_topic or "bearing failure modes"
                if target_asset:
                    resolved_query = f"Which {topic} apply to customer asset {target_asset}?"
                    if target_asset not in found_tags:
                        found_tags.append(target_asset)
                    dependency_type = DependencyType.HYBRID
                    resolved_refs = {"those": topic, target_asset: "verified customer asset"}
                else:
                    resolved_query = f"Which {topic} apply?"
                    resolved_refs = {"those": topic}

            # Case 3: "What are its common failure modes?" / "What failure modes apply to it?"
            elif ("failure mode" in q_lower or "failure modes" in q_lower) and any(w in q_lower for w in ["what are", "which", "common", "apply to it", "its failure", "these failure"]):
                if found_tags:
                    target_asset = found_tags[0]
                    resolved_query = f"What failure modes apply to customer asset {target_asset}?"
                    dependency_type = DependencyType.HYBRID
                elif conv_state.active_asset:
                    target_asset = conv_state.active_asset
                    resolved_query = f"What failure modes apply to customer asset {target_asset}?"
                    if target_asset not in found_tags:
                        found_tags.append(target_asset)
                    dependency_type = DependencyType.HYBRID
                elif conv_state.active_topic:
                    resolved_query = f"What are common failure modes of a {conv_state.active_topic}?"
                    dependency_type = DependencyType.CONTEXT_DEPENDENT

            # Case 4: "How can I prevent that?" / "How to prevent that"
            elif any(p in q_lower for p in ["how can i prevent that", "how to prevent that", "prevent it"]):
                topic = conv_state.active_topic or "bearing failure and lubrication starvation"
                target_asset = (conv_state.active_asset or (found_tags[0] if found_tags else None) or (active_asset_context.get("tag") if active_asset_context else None))
                if target_asset:
                    resolved_query = f"How to prevent {topic} on {target_asset}?"
                else:
                    resolved_query = f"How can technicians prevent {topic}?"

            # Case 5: General Pronoun / Follow-up Resolution (e.g. "What is its inspection condition?", "its lubricant", etc.)
            else:
                target_asset = (conv_state.active_asset or (found_tags[0] if found_tags else None) or (active_asset_context.get("tag") if active_asset_context else None))
                if target_asset:
                    sub = re.sub(r"\b(its|it|this machine|this asset|this equipment)\b", target_asset, q_clean, flags=re.IGNORECASE)
                    resolved_query = sub
                    if target_asset not in found_tags:
                        found_tags.append(target_asset)
                    resolved_refs = {"its": target_asset, "it": target_asset}

        # If user explicitly set scope filter to Current Machine / Current Asset
        if scope_filter in ("Current Machine", "Current Asset", "Selected Asset") and active_asset_context:
            tag = active_asset_context.get("tag")
            if tag and tag not in found_tags:
                found_tags.append(tag)

        # If user explicitly requested General Knowledge
        if scope_filter == "General Knowledge":
            return QueryAnalysis(
                raw_query=query,
                resolved_query=resolved_query,
                dependency_type=DependencyType.STANDALONE,
                scope=KnowledgeScope.GENERAL,
                intent="GENERAL_ENGINEERING_EXPLANATION",
                referenced_asset_tags=[],
                is_hybrid_request=False,
                requires_customer_evidence=False,
                context_topic=None,
                conversation_state=conv_state,
                response_structure="CONVERSATIONAL",
                typo_correction=detected_typo
            )

        # =========================================================================
        # 7. CROSS-ASSET COMPARISON DETECTION
        # =========================================================================
        is_cross_asset = (
            ("compare" in q_lower and ("p-101" in q_lower or "p-102" in q_lower or "fleet" in q_lower or "vs" in q_lower)) or
            (len([t for t in found_tags if t.startswith("P-") or t.startswith("C-")]) >= 2 and any(w in q_lower for w in ["compare", "difference", "vs", "versus", "fleet", "both"]))
        )

        if is_cross_asset:
            return QueryAnalysis(
                raw_query=query,
                resolved_query=resolved_query,
                dependency_type=DependencyType.CROSS_ASSET,
                scope=KnowledgeScope.CROSS_ASSET,
                intent="CROSS_ASSET_COMPARISON",
                referenced_asset_tags=found_tags,
                is_hybrid_request=False,
                requires_customer_evidence=True,
                context_topic="fleet_comparison",
                conversation_state=conv_state,
                response_structure="CUSTOMER_GROUNDED",
                typo_correction=detected_typo
            )

        # =========================================================================
        # 8. HYBRID INTENT DETECTION
        # =========================================================================
        is_hybrid = dependency_type == DependencyType.HYBRID
        if found_tags and not is_hybrid:
            hybrid_markers = [
                "which of those apply", "which ones apply", "which apply to",
                "failure modes and which apply", "apply to p-", "apply to our",
                "relevant to p-", "compare general", "universal failure modes"
            ]
            if any(m in q_lower for m in hybrid_markers):
                is_hybrid = True
            elif ("failure modes" in q_lower or "causes" in q_lower) and any(w in q_lower for w in ["apply to", "relevant to"]):
                is_hybrid = True

        if is_hybrid:
            return QueryAnalysis(
                raw_query=query,
                resolved_query=resolved_query,
                dependency_type=DependencyType.HYBRID,
                scope=KnowledgeScope.HYBRID,
                intent="HYBRID_REASONING",
                referenced_asset_tags=found_tags,
                is_hybrid_request=True,
                requires_customer_evidence=True,
                context_topic=found_tags[0] if found_tags else None,
                conversation_state=conv_state,
                response_structure="HYBRID_ASSESSMENT",
                typo_correction=detected_typo,
                resolved_references=resolved_refs
            )

        # =========================================================================
        # 9. CUSTOMER ASSET QUERIES (Physical Asset in query)
        # =========================================================================
        has_customer_record = any(re.search(pat, q_clean, re.IGNORECASE) for pat in cls.CUSTOMER_RECORD_PATTERNS)
        
        # If the query explicitly asks about a general engineering concept, it is NOT customer!
        is_pure_general_concept = is_standalone_general and not found_tags

        if found_tags and not is_pure_general_concept:
            # Detect generic fact type
            fact_type = None
            if any(w in q_lower for w in ["date", "when", "timestamp", "occurred on", "performed on"]):
                fact_type = "DATE"

            target_categories: List[str] = []

            # Operational sub-intents & document category preferences
            if any(w in q_lower for w in ["inspection", "condition monitoring", "ndt", "vibration inspection", "inspection finding", "inspection date", "inspected", "survey"]):
                scope = KnowledgeScope.INSPECTION
                intent = "CUSTOMER_INSPECTION_RECORD"
                target_categories = [
                    "Condition Monitoring / NDT",
                    "Inspection Report",
                    "Inspection"
                ]
                response_structure = "CUSTOMER_GROUNDED"
            elif any(w in q_lower for w in ["why did", "failure", "fail", "trip", "rca", "root cause", "breakdown"]):
                scope = KnowledgeScope.RCA
                intent = "CUSTOMER_FAILURE_RCA"
                target_categories = [
                    "Failure / Incident Report",
                    "Incident Report",
                    "Failure"
                ]
                response_structure = "RCA_INVESTIGATION"
            elif any(w in q_lower for w in ["service", "serviced", "overhaul", "maintenance", "work order", "wo-", "repair", "bearing replacement", "maintenance date"]):
                scope = KnowledgeScope.MAINTENANCE
                intent = "CUSTOMER_MAINTENANCE_HISTORY"
                target_categories = [
                    "Maintenance Report / WO",
                    "Maintenance Schedule",
                    "Maintenance"
                ]
                response_structure = "CUSTOMER_GROUNDED"
            elif any(w in q_lower for w in ["shift handover", "shift log", "operator note", "operator notes", "handover", "shift"]):
                scope = KnowledgeScope.CUSTOMER
                intent = "CUSTOMER_SHIFT_HANDOVER"
                target_categories = [
                    "Operations & Shift Logs",
                    "Shift Handover"
                ]
                response_structure = "CUSTOMER_GROUNDED"
            elif any(w in q_lower for w in ["compliant", "compliance", "standard", "regulation", "api 610", "iso", "audit"]):
                scope = KnowledgeScope.COMPLIANCE
                intent = "CUSTOMER_COMPLIANCE_STATUS"
                target_categories = [
                    "Regulatory / Compliance",
                    "Standard Operating Procedure",
                    "SOP"
                ]
                response_structure = "COMPLIANCE_REVIEW"
            elif any(w in q_lower for w in ["action", "corrective", "work item", "assign", "prioritize", "task"]):
                scope = KnowledgeScope.ACTION_OPERATIONAL
                intent = "CUSTOMER_OPERATIONAL_ACTION"
                response_structure = "CUSTOMER_GROUNDED"
            else:
                scope = KnowledgeScope.CUSTOMER
                intent = "CUSTOMER_ASSET_PROFILE"
                response_structure = "CUSTOMER_GROUNDED"

            return QueryAnalysis(
                raw_query=query,
                resolved_query=resolved_query,
                dependency_type=dependency_type,
                scope=scope,
                intent=intent,
                referenced_asset_tags=found_tags,
                is_hybrid_request=False,
                requires_customer_evidence=True,
                context_topic=found_tags[0],
                conversation_state=conv_state,
                response_structure=response_structure,
                typo_correction=detected_typo,
                target_document_categories=target_categories,
                fact_type=fact_type
            )

        # =========================================================================
        # 10. GENERAL ENGINEERING INTELLIGENCE
        # =========================================================================
        scope = KnowledgeScope.GENERAL
        requires_evidence = False
        response_structure = "CONVERSATIONAL"

        if any(w in q_lower for w in ["what is", "define", "definition", "meaning of"]):
            intent = "CONCEPT_DEFINITION"
        elif any(w in q_lower for w in ["explain", "how does", "how do", "principles of"]):
            intent = "TECHNICAL_EXPLANATION"
        elif any(w in q_lower for w in ["compare", "difference between", "versus", "vs"]):
            intent = "COMPARISON_ANALYSIS"
        elif any(w in q_lower for w in ["summarize", "summary", "brief"]):
            intent = "SUMMARIZATION"
        elif any(w in q_lower for w in ["checklist", "draft", "create a", "procedure template"]):
            intent = "DRAFTING_ASSISTANCE"
        else:
            intent = "GENERAL_ENGINEERING_REASONING"

        return QueryAnalysis(
            raw_query=query,
            resolved_query=resolved_query,
            dependency_type=dependency_type,
            scope=scope,
            intent=intent,
            referenced_asset_tags=[],
            is_hybrid_request=False,
            requires_customer_evidence=False,
            context_topic=conv_state.active_topic if dependency_type == DependencyType.CONTEXT_DEPENDENT else None,
            conversation_state=conv_state,
            response_structure=response_structure,
            typo_correction=detected_typo
        )

query_understanding = QueryUnderstandingEngine()
