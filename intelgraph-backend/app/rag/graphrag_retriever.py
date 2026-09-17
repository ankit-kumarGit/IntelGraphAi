import re
import logging
from typing import Dict, Any, List, Optional
from app.rag.hybrid_search import hybrid_search
from app.rag.qdrant_store import qdrant_store
from app.services.neo4j_service import neo4j_graph
from app.services.entity_resolution import entity_resolution

logger = logging.getLogger("intelgraph.graphrag")

class GraphRAGRetriever:
    """
    Genuine GraphRAG Retriever:
    Fuses hybrid vector & lexical retrieval (backed by Qdrant & FAISS) with dynamic multi-hop Neo4j graph traversal.
    """

    @staticmethod
    def retrieve(
        query: str,
        asset_tag: Optional[str] = None,
        user_role: str = "Maintenance Engineer",
        trusted_sources_only: bool = True,
        top_k: int = 6,
        tenant_id: Optional[str] = None,
        target_document_categories: Optional[List[str]] = None,
        fact_type: Optional[str] = None
    ) -> Dict[str, Any]:
        q_lower = query.lower()

        # 1. Entity Resolution & Target Asset Detection
        detected_asset = asset_tag
        if not detected_asset:
            tag_resolution = entity_resolution.resolve_asset_tag(query)
            if tag_resolution.get("matched"):
                detected_asset = tag_resolution["canonical_tag"]
            else:
                matches = re.findall(r"\b([A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12})+|[A-Z]-\d{3}|[A-Z]\d{3})\b", query, re.IGNORECASE)
                if matches:
                    detected_asset = matches[0].upper()
                    if "-" not in detected_asset and len(detected_asset) >= 4:
                        detected_asset = f"{detected_asset[0]}-{detected_asset[1:]}"

        # 2. Dynamic Traversal Strategy Classification
        intent = "GENERAL_EXPERT"
        if any(w in q_lower for w in ["inspection", "condition monitoring", "ndt", "survey", "vibration inspection", "inspection date"]):
            intent = "INSPECTION_RECORD"
        elif any(w in q_lower for w in ["failure", "fail", "broke", "seizure", "why did", "root cause", "trip"]):
            intent = "FAILURE_RCA"
        elif any(w in q_lower for w in ["maintenance", "overhaul", "wo-", "work order", "interval", "history"]):
            intent = "MAINTENANCE_HISTORY"
        elif any(w in q_lower for w in ["compliance", "regulation", "osha", "api", "iso", "audit", "gap", "valid"]):
            intent = "COMPLIANCE_AUDIT"
        elif any(w in q_lower for w in ["other asset", "elsewhere", "across fleet", "similar issue", "recurring pattern"]):
            intent = "FLEET_ANOMALY"

        # 3. Hybrid Semantic & Lexical Vector Retrieval (Qdrant & FAISS backed)
        hybrid_candidates = hybrid_search.search(
            query=query,
            asset_tag=detected_asset,
            trusted_sources_only=trusted_sources_only,
            top_k=top_k,
            tenant_id=tenant_id,
            target_categories=target_document_categories,
            fact_type=fact_type
        )

        # 4. Dynamic Neo4j Graph Traversal
        raw_graph_hops = []
        connected_entities = []
        if detected_asset:
            target_tag = detected_asset.upper()
            if intent == "INSPECTION_RECORD":
                sub = neo4j_graph.get_subgraph(target_tag, max_depth=2, tenant_id=tenant_id)
                for edge in sub.get("edges", []):
                    if "INSPECTION" in edge.get("type", "") or "INSP" in edge.get("type", "") or "DOCUMENT" in edge.get("type", ""):
                        raw_graph_hops.append(edge)
                connected_entities.extend(sub.get("nodes", []))
            elif intent == "FAILURE_RCA":
                hops = neo4j_graph.multi_hop_evidence_traversal(target_tag, tenant_id=tenant_id)
                raw_graph_hops.extend(hops)
            elif intent == "MAINTENANCE_HISTORY":
                sub = neo4j_graph.get_subgraph(target_tag, max_depth=2, tenant_id=tenant_id)
                raw_graph_hops.extend(sub.get("edges", []))
                connected_entities.extend(sub.get("nodes", []))
            elif intent == "COMPLIANCE_AUDIT":
                sub = neo4j_graph.get_subgraph(target_tag, max_depth=2, tenant_id=tenant_id)
                for edge in sub.get("edges", []):
                    if "COMPLIANCE" in edge.get("type", "") or "GOVERN" in edge.get("type", ""):
                        raw_graph_hops.append(edge)
                connected_entities.extend(sub.get("nodes", []))
            elif intent == "FLEET_ANOMALY":
                cross_links = neo4j_graph.get_fleet_cross_asset_links("Bearing")
                raw_graph_hops.extend(cross_links)
            else:
                sub = neo4j_graph.get_subgraph(target_tag, max_depth=2, tenant_id=tenant_id)
                raw_graph_hops.extend(sub.get("edges", []))
                connected_entities.extend(sub.get("nodes", []))

        # Format graph evidence to meet the Part 3 structured contract
        nodes_by_id = {n["id"]: n for n in connected_entities}
        graph_hops = []
        seen_hops = set()

        for edge in raw_graph_hops:
            edge_from = edge.get("from") or (edge.get("source", {}).get("id") if isinstance(edge.get("source"), dict) else str(edge.get("source", "")))
            edge_to = edge.get("to") or (edge.get("target", {}).get("id") if isinstance(edge.get("target"), dict) else str(edge.get("target", "")))
            rel_type = edge.get("relationship") or edge.get("type", "")

            hop_key = (edge_from, rel_type, edge_to)
            if hop_key in seen_hops:
                continue
            seen_hops.add(hop_key)

            from_node = nodes_by_id.get(edge_from) or getattr(neo4j_graph, "nodes", {}).get(edge_from, {})
            to_node = nodes_by_id.get(edge_to) or getattr(neo4j_graph, "nodes", {}).get(edge_to, {})

            from_props = from_node.get("properties", {})
            to_props = to_node.get("properties", {})
            edge_props = dict(edge.get("properties") or {})

            from_type = from_node.get("label") or ("Asset" if edge_from.startswith("asset_") else ("Component" if edge_from.startswith("comp_") else ("Document" if edge_from.startswith("doc_") else "Node")))
            to_type = to_node.get("label") or ("Component" if edge_to.startswith("comp_") else ("Document" if edge_to.startswith("doc_") else ("Asset" if edge_to.startswith("asset_") else "Node")))

            source_name = from_props.get("name") or from_props.get("tag") or from_props.get("title") or edge_from
            target_name = to_props.get("name") or to_props.get("tag") or to_props.get("title") or edge_to

            # Determine associated asset tag
            hop_asset_tag = (
                from_props.get("tag") if from_type == "Asset"
                else (to_props.get("tag") if to_type == "Asset"
                else (from_props.get("asset_tag") or to_props.get("asset_tag") or edge_props.get("asset_tag") or detected_asset))
            )

            # Determine associated document ID
            hop_doc_id = (
                from_props.get("document_id")
                or to_props.get("document_id")
                or from_props.get("source_document_id")
                or to_props.get("source_document_id")
                or edge_props.get("source_document_id")
                or (edge_from[4:] if edge_from.startswith("doc_") else (edge_to[4:] if edge_to.startswith("doc_") else None))
            )

            merged_props = {}
            if to_type == "Component":
                if to_props.get("tag"):
                    merged_props["tag"] = to_props["tag"]
                if to_props.get("component_type") or to_props.get("type"):
                    merged_props["type"] = to_props.get("component_type") or to_props.get("type")
                if to_props.get("condition"):
                    merged_props["condition"] = to_props["condition"]
            merged_props.update(edge_props)

            hop = {
                "from": edge_from,
                "from_type": from_type,
                "relationship": rel_type,
                "type": rel_type,
                "to": edge_to,
                "to_type": to_type,
                "properties": merged_props,
                "source_name": source_name,
                "target_name": target_name
            }
            if hop_asset_tag:
                hop["asset_tag"] = hop_asset_tag
            if hop_doc_id:
                hop["document_id"] = hop_doc_id

            graph_hops.append(hop)

        # Prioritize domain/component relationships over document link scaffolding
        rel_priority = {
            "HAS_COMPONENT": 1,
            "CONTAINS_COMPONENT": 2,
            "HAS_INSPECTION": 3,
            "HAS_WORK_ORDER": 4,
            "HAD_FAILURE": 5,
            "GOVERNED_BY": 6,
            "ASSET_HAS_DOCUMENT": 10,
            "APPLIES_TO": 11,
            "REFERENCES": 12,
        }
        graph_hops.sort(key=lambda h: rel_priority.get(h.get("relationship", ""), 20))

        # 5. Extract Citations & Evidence Payload
        citations = []
        seen_docs = set()
        for item in hybrid_candidates[:top_k]:
            chk = item["chunk"]
            doc_id = chk.get("document_id", "DOC")
            if doc_id not in seen_docs:
                citations.append({
                    "document_name": doc_id.replace("_", " "),
                    "document_id": doc_id,
                    "page_number": chk.get("page_number", 1),
                    "section_title": chk.get("section_title", "General"),
                    "record_date": chk.get("effective_date", "2024-2026"),
                    "version": chk.get("version", "v1.0"),
                    "governance_status": chk.get("governance_status", "Approved"),
                    "excerpt": chk.get("content", "")[:200]
                })
                seen_docs.add(doc_id)

        return {
            "query": query,
            "detected_asset": detected_asset,
            "query_intent": intent,
            "vector_chunks": hybrid_candidates,
            "graph_hops": graph_hops,
            "connected_entities": connected_entities,
            "citations": citations,
            "confidence": "High" if len(hybrid_candidates) > 0 or len(graph_hops) > 0 else "Low"
        }

graphrag_retriever = GraphRAGRetriever()
