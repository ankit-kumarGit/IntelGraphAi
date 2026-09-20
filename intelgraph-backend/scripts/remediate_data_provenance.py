import os
import json
import logging
from pathlib import Path
from app.database import db_manager
from app.services.neo4j_service import neo4j_graph
from app.rag.qdrant_store import qdrant_store
from app.rag.vector_store import vector_store
from app.models.document import DocumentChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("remediate_provenance")

def remediate():
    db_manager.connect()
    db = db_manager.db
    logger.info("Starting Strict Data Provenance Remediation...")

    # =========================================================================
    # 1. REMEDIATE TEST-PUMP-REAL-001 Process Flowsheet
    # =========================================================================
    tp_doc = db.documents.find_one({"document_id": "TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet"})
    if tp_doc:
        true_related = ["TEST-PUMP-REAL-001B", "D-450", "E-450A", "T-450", "FSLL-450A", "PDSH-450A", "HV-450A", "HV-450B"]
        db.documents.update_one(
            {"document_id": "TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet"},
            {"$set": {
                "related_asset_tags": true_related,
                "document_scope": "ASSET",
                "primary_asset_tags": ["TEST-PUMP-REAL-001"]
            }}
        )
        db.document_chunks.update_many(
            {"document_id": "TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet"},
            {"$set": {
                "related_asset_tags": true_related,
                "document_scope": "ASSET",
                "primary_asset_tags": ["TEST-PUMP-REAL-001"]
            }}
        )
        logger.info("Remediated TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet: purged false related tags (T-200, P-194A/B).")

    # =========================================================================
    # 2. REMEDIATE Unit 2 Process P&ID Flowsheet (genuine shared document for P-101 & P-102)
    # =========================================================================
    for doc_id, clean_title in [
        ("P-101_Unit2_Process_PID_Flowsheet", "Unit 2 Process P&ID Flowsheet"),
        ("P-101_Unit2_Visual_Engineering_PID", "Unit 2 Visual Engineering P&ID")
    ]:
        doc = db.documents.find_one({"document_id": doc_id})
        if doc:
            db.documents.update_one(
                {"document_id": doc_id},
                {"$set": {
                    "primary_asset_tags": ["P-101", "P-102"],
                    "document_scope": "SYSTEM",
                    "title": clean_title
                }}
            )
            db.document_chunks.update_many(
                {"document_id": doc_id},
                {"$set": {
                    "primary_asset_tags": ["P-101", "P-102"],
                    "document_scope": "SYSTEM",
                    "title": clean_title
                }}
            )
            logger.info(f"Remediated {doc_id}: set primary_asset_tags=['P-101', 'P-102'], scope=SYSTEM, title='{clean_title}'")

    # =========================================================================
    # 2b. PURGE ORPHANED TEST CHUNKS
    # =========================================================================
    del_res = db.document_chunks.delete_many({"document_id": "P-101_test_override_p101_doc"})
    if del_res.deleted_count > 0:
        logger.info(f"Purged {del_res.deleted_count} orphaned test chunk(s) from document_chunks.")
    # Clean contaminated relationships in neo4j_graph.json
    unwanted_pairs = [
        ("asset_T_200", "doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet"),
        ("doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet", "asset_T_200"),
        ("asset_P_194A", "doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet"),
        ("doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet", "asset_P_194A"),
        ("asset_P_194B", "doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet"),
        ("doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet", "asset_P_194B"),
    ]

    initial_rel_count = len(neo4j_graph.relationships)
    neo4j_graph.relationships = [
        r for r in neo4j_graph.relationships
        if not any(r.get("from") == p[0] and r.get("to") == p[1] for p in unwanted_pairs)
    ]
    removed_rels = initial_rel_count - len(neo4j_graph.relationships)
    logger.info(f"Removed {removed_rels} contaminated relationships from local neo4j_graph.json")

    # Ensure doc_P-101_Unit2_Process_PID_Flowsheet applies to asset_P_102
    has_p102_link = any(
        (r.get("from") == "doc_P-101_Unit2_Process_PID_Flowsheet" and r.get("to") == "asset_P_102")
        or (r.get("from") == "asset_P_102" and r.get("to") == "doc_P-101_Unit2_Process_PID_Flowsheet")
        for r in neo4j_graph.relationships
    )
    if not has_p102_link:
        neo4j_graph.relationships.append({
            "from": "doc_P-101_Unit2_Process_PID_Flowsheet",
            "to": "asset_P_102",
            "type": "APPLIES_TO",
            "properties": {"relationship": "APPLIES_TO", "system": "Unit 2 Fluid Processing"}
        })
        logger.info("Linked doc_P-101_Unit2_Process_PID_Flowsheet -[:APPLIES_TO]-> asset_P_102 in local graph")

    neo4j_graph.save_local_graph()

    # Remediate Live Neo4j Aura if connected
    if neo4j_graph.connected_to_live_neo4j and neo4j_graph.driver:
        try:
            with neo4j_graph.driver.session() as session:
                logger.info("Executing remediation on live Neo4j Aura cluster...")
                session.run(
                    """
                    MATCH (a {id: 'asset_T_200'})-[r]-(d {id: 'doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet'})
                    DELETE r
                    """
                )
                session.run(
                    """
                    MATCH (a {id: 'asset_P_194A'})-[r]-(d {id: 'doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet'})
                    DELETE r
                    """
                )
                session.run(
                    """
                    MATCH (a {id: 'asset_P_194B'})-[r]-(d {id: 'doc_TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet'})
                    DELETE r
                    """
                )
                session.run(
                    """
                    MATCH (d {id: 'doc_P-101_Unit2_Process_PID_Flowsheet'}), (a {id: 'asset_P_102'})
                    MERGE (d)-[r:APPLIES_TO]->(a)
                    SET r.system = 'Unit 2 Fluid Processing'
                    """
                )
                logger.info("Live Neo4j Aura remediation Cypher executed successfully.")
        except Exception as e:
            logger.warning(f"Live Neo4j Aura remediation encountered notice: {e}")

    # =========================================================================
    # 4. REINDEX MODIFIED CHUNKS IN QDRANT & FAISS
    # =========================================================================
    logger.info("Re-indexing modified documents in local/remote Qdrant & FAISS stores...")
    affected_doc_ids = [
        "TEST-PUMP-REAL-001_TPREAL001_Process_Flowsheet",
        "P-101_Unit2_Process_PID_Flowsheet",
        "P-101_Unit2_Visual_Engineering_PID"
    ]
    reindexed_chunks = []
    for doc_id in affected_doc_ids:
        raw_chunks = list(db.document_chunks.find({"document_id": doc_id}))
        for rc in raw_chunks:
            chunk_obj = DocumentChunk(**rc)
            reindexed_chunks.append(chunk_obj)

    if reindexed_chunks:
        # Update local FAISS / metadata store
        vector_store.add_chunks(reindexed_chunks)
        # Update Qdrant store
        qdrant_store.add_chunks(reindexed_chunks)
        logger.info(f"Re-indexed {len(reindexed_chunks)} chunks in Vector Store & Qdrant.")

    logger.info("Strict Data Provenance Remediation Completed Successfully!")

if __name__ == "__main__":
    remediate()
