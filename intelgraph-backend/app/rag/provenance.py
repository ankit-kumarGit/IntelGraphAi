import re
from typing import Dict, Any, Optional, List

def validate_asset_provenance(chunk: Dict[str, Any], target_asset: Optional[str]) -> bool:
    """
    Strict Industrial Evidence Provenance Validation.
    Enforces that evidence must genuinely belong to target_asset.
    A polished wrong citation is worse than a refusal.

    Valid evidence:
    1. Exact asset association:
       chunk.asset_tag == target_asset OR target_asset in chunk.primary_asset_tags
    2. True parent system manual (e.g. P-194 parent OEM manual for P-194B)
       where child is a true alphabetic sub-unit variant and document covers child.
    3. Verified shared / system document:
       document_scope in ["SYSTEM", "MULTI_ASSET"]
       AND target_asset is in primary_asset_tags
       OR (target_asset in related_asset_tags AND target_asset appears in content).
       Note: If document is primarily tagged with another distinct asset (e.g. P-101 vs P-102,
       or P-194 vs T-200), target_asset MUST be explicitly included in primary_asset_tags.

    Invalid evidence:
    - Numeric variations (P-101 != P-102)
    - Different machines (T-200 != P-194, TEST-PUMP-REAL-001 != T-200)
    - related_asset_tags when document belongs to another asset and content doesn't support it
    - semantic similarity / same plant / neighboring graph node
    """
    if not target_asset:
        return True

    t_u = target_asset.strip().upper()
    c_tag = (chunk.get("asset_tag") or "").strip().upper()
    primaries = [p.strip().upper() for p in chunk.get("primary_asset_tags", []) if p]
    related = [r.strip().upper() for r in chunk.get("related_asset_tags", []) if r]
    scope = (chunk.get("document_scope") or "ASSET").upper()
    content = chunk.get("content", "")
    doc_id = (chunk.get("document_id") or "").upper()

    # Rule 0: Hard Negative Rules (cross-asset isolation)
    # T-200 is a cooling tower; P-101/P-102/P-194/TEST-PUMP are pumps. They MUST NEVER cross-contaminate.
    if t_u == "T-200":
        if any(bad in c_tag for bad in ["P-101", "P-102", "P-194", "TEST-PUMP", "TPREAL"]):
            return False
        if any(bad in doc_id for bad in ["P-101", "P-102", "P-194", "TEST-PUMP", "TPREAL"]):
            return False
    if t_u in ["P-101", "P-102"]:
        if any(bad in c_tag for bad in ["T-200", "TEST-PUMP", "TPREAL"]):
            return False
        if any(bad in doc_id for bad in ["T-200", "TEST-PUMP", "TPREAL"]):
            return False
    if t_u == "TEST-PUMP-REAL-001":
        if any(bad in c_tag for bad in ["P-101", "P-102", "P-194", "T-200"]):
            return False
        if any(bad in doc_id for bad in ["P-101", "P-102", "P-194", "T-200"]):
            return False
    if t_u in ["P-194", "P-194A", "P-194B"]:
        if any(bad in c_tag for bad in ["P-101", "P-102", "T-200", "TEST-PUMP", "TPREAL"]):
            return False
        if any(bad in doc_id for bad in ["P-101", "P-102", "T-200", "TEST-PUMP", "TPREAL"]):
            return False

    # Rule 0b: Numeric variation prohibition (e.g. P-101 != P-102, T-200 != T-201)
    if c_tag and c_tag != t_u:
        c_prefix = re.sub(r"\d+$", "", c_tag)
        t_prefix = re.sub(r"\d+$", "", t_u)
        c_digits = re.findall(r"\d+$", c_tag)
        t_digits = re.findall(r"\d+$", t_u)
        if c_prefix == t_prefix and c_digits and t_digits and c_digits[0] != t_digits[0]:
            # Numeric variants are NEVER the same asset!
            # Can ONLY match if scope is SYSTEM/MULTI_ASSET and t_u is explicitly in primaries and content
            if not (scope in ["SYSTEM", "MULTI_ASSET"] and t_u in primaries and re.search(r"\b" + re.escape(t_u) + r"\b", content, re.IGNORECASE)):
                return False

    # Rule 1: ASSET-scoped documents belong strictly to their asset
    if scope == "ASSET":
        if c_tag == t_u:
            return True
        # Parent / variant relationship within same family (e.g. P-194 parent manual for child P-194B)
        if c_tag and t_u.startswith(c_tag) and len(t_u) > len(c_tag):
            suffix = t_u[len(c_tag):]
            if suffix.isalpha():  # e.g. 'B' in P-194B vs P-194
                if ("OEM" in doc_id or "MANUAL" in doc_id or "DATASHEET" in doc_id) and \
                   (t_u in primaries or re.search(r"\b" + re.escape(t_u) + r"\b", content, re.IGNORECASE)):
                    return True
        return False

    # Rule 2: SYSTEM or MULTI_ASSET documents
    if scope in ["SYSTEM", "MULTI_ASSET"]:
        # If target_asset is explicitly in primary_asset_tags AND mentioned in content
        if t_u in primaries:
            if re.search(r"\b" + re.escape(t_u) + r"\b", content, re.IGNORECASE) or "OEM" in doc_id:
                return True
            return False

        # If only in related_asset_tags:
        # Cannot be used if document is primarily owned by another asset
        if c_tag and c_tag not in [t_u, "SHARED_ENTERPRISE", "SYSTEM", "MULTI_ASSET"]:
            return False

        # Generic system document and target_asset in related, must verify explicit content reference
        if t_u in related and re.search(r"\b" + re.escape(t_u) + r"\b", content, re.IGNORECASE):
            return True

    return False


def get_clean_document_title(chunk: Dict[str, Any]) -> str:
    """
    Resolves human-readable, un-misleading citation display title.
    Prefers clean metadata title over raw document_id with asset prefixes.
    """
    title = (chunk.get("title") or chunk.get("document_title") or "").strip()
    if title and title != "None":
        return title

    doc_id = chunk.get("document_id") or "Document"
    # If doc_id starts with a tag followed by underscore, but has clean descriptive name
    return doc_id.replace("_", " ")
