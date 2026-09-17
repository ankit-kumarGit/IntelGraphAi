#!/usr/bin/env python3
"""
F-01 Stale Data Cleanup Script
================================
PROOF: F-01 asset record contains fabricated data from the OLD commented-out
code block in doc_service.py. Evidence:

    specs.air_flow_m3_h: 45000.0   <- exact value from old code line 295
    specs.motor_kw: 55.0            <- exact value from old code line 295
    components[0].name: "Fan Impeller Blades"  <- from old code line 292
    components[0].part_number: "BLD-F-01"      <- from old code line 292
    components[1].name: "Drive Motor"          <- from old code line 293
    components[1].part_number: "MOT-55KW"      <- from old code line 293
    asset_type: "Process Fan"                  <- from old code
    name: "F-01 Induced Draft Fan"             <- from old code

The OISD document (uploaded 2026-09-16 01:02) correctly linked to F-01 
(the document IS about furnace F-01), but the asset profile shows fabricated 
fan data because the asset was pre-populated by the old code.

WHAT THIS SCRIPT DOES:
- Verifies the F-01 asset matches the known stale pattern
- Deletes ONLY the stale F-01 asset record (NOT the linked OISD document)
- Updates the linked document to require re-association review
- Removes the F-01 node from the local Neo4j fallback graph
- Does NOT touch P-101, P-194, or any other assets

IMPORTANT: This script is SAFE. Run it only after confirming with this team.
DO NOT AUTORUN. Execute explicitly: python3 scripts/cleanup_stale_f01.py --confirm
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STALE_ASSET_TAG = "F-01"
STALE_INDICATORS = {
    "name": "F-01 Induced Draft Fan",
    "asset_type": "Process Fan",
    "specs.air_flow_m3_h": 45000.0,
    "specs.motor_kw": 55.0,
}

def run_dry_run(db):
    """Print what would be deleted/modified without actually doing it."""
    print("=== DRY RUN — NO CHANGES MADE ===")
    print()
    
    asset = db.assets.find_one({"tag": STALE_ASSET_TAG})
    if not asset:
        print(f"RESULT: {STALE_ASSET_TAG} asset not found in MongoDB. Nothing to clean.")
        return False
    
    print(f"FOUND asset in MongoDB: _id={asset['_id']}")
    print(f"  tag: {asset.get('tag')}")
    print(f"  name: {asset.get('name')}")
    print(f"  asset_type: {asset.get('asset_type')}")
    print(f"  specs: {asset.get('specs')}")
    print(f"  components: {[c.get('name') for c in asset.get('components', [])]}")
    
    # Verify this matches the stale pattern
    is_stale = (
        asset.get("name") == STALE_INDICATORS["name"] or
        (asset.get("specs", {}).get("air_flow_m3_h") == STALE_INDICATORS["specs.air_flow_m3_h"] and
         asset.get("specs", {}).get("motor_kw") == STALE_INDICATORS["specs.motor_kw"])
    )
    
    print()
    print(f"STALE PATTERN MATCH: {is_stale}")
    if not is_stale:
        print("WARNING: Asset does not match known stale pattern. Refusing to delete.")
        return False
    
    docs = list(db.documents.find({"asset_tag": STALE_ASSET_TAG}))
    print()
    print(f"LINKED DOCUMENTS: {len(docs)}")
    for d in docs:
        print(f"  doc_id: {d.get('document_id')}, filename: {d.get('filename')}, uploaded: {d.get('upload_date')}")
    
    chunks_count = db.document_chunks.count_documents({"asset_tag": STALE_ASSET_TAG})
    print(f"LINKED CHUNKS: {chunks_count}")
    
    graph_file = os.path.join(os.path.dirname(__file__), "../../storage/neo4j_graph.json")
    graph_file = os.path.normpath(graph_file)
    if os.path.exists(graph_file):
        with open(graph_file) as f:
            graph = json.load(f)
        f01_nodes = [k for k in graph.get("nodes", {}) if "f_01" in k.lower()]
        print(f"LOCAL GRAPH NODES: {f01_nodes}")
    
    print()
    print("PLAN:")
    print(f"  1. DELETE: db.assets where tag='{STALE_ASSET_TAG}' AND name='{STALE_INDICATORS['name']}'")
    print(f"     (Preserves OISD document — it is NOT deleted)")
    print(f"  2. UPDATE: db.documents where asset_tag='{STALE_ASSET_TAG}'")
    print(f"     -> Set association_status='NEEDS_REVIEW', cleared from stale asset")
    print(f"  3. UPDATE: db.document_chunks where asset_tag='{STALE_ASSET_TAG}'")
    print(f"     -> Set asset_tag='UNASSIGNED' so chunks are not lost")
    print(f"  4. REMOVE: Local graph node 'asset_F_01'")
    print()
    print("Re-run with --confirm to execute these changes.")
    return True


def run_cleanup(db):
    """Execute the actual cleanup."""
    print("=== EXECUTING CLEANUP ===")
    
    # 1. Verify stale pattern before deleting
    asset = db.assets.find_one({"tag": STALE_ASSET_TAG})
    if not asset:
        print("ERROR: F-01 asset not found. Aborting.")
        return
    
    is_stale = (
        asset.get("name") == STALE_INDICATORS["name"] or
        (asset.get("specs", {}).get("air_flow_m3_h") == STALE_INDICATORS["specs.air_flow_m3_h"] and
         asset.get("specs", {}).get("motor_kw") == STALE_INDICATORS["specs.motor_kw"])
    )
    
    if not is_stale:
        print("ERROR: F-01 asset does not match stale pattern. Aborting cleanup for safety.")
        print(f"  name={asset.get('name')} (expected: {STALE_INDICATORS['name']})")
        return
    
    # 2. Delete the stale F-01 asset
    result = db.assets.delete_one({"tag": STALE_ASSET_TAG, "name": STALE_INDICATORS["name"]})
    print(f"DELETED assets: {result.deleted_count} records for {STALE_ASSET_TAG} (stale pattern)")
    
    # 3. Mark linked documents as NEEDS_REVIEW (do NOT delete them)
    doc_result = db.documents.update_many(
        {"asset_tag": STALE_ASSET_TAG},
        {"$set": {
            "association_status": "NEEDS_REVIEW",
            "association_note": (
                f"Auto-association to {STALE_ASSET_TAG} was based on body text references in an OISD "
                f"case study. The {STALE_ASSET_TAG} asset record was stale (created by old code). "
                f"Please re-assign this document to the correct asset via the upload workflow."
            )
        }}
    )
    print(f"UPDATED documents to NEEDS_REVIEW: {doc_result.modified_count} document(s)")
    
    # 4. Mark chunks as UNASSIGNED (so they are not lost)
    chunk_result = db.document_chunks.update_many(
        {"asset_tag": STALE_ASSET_TAG},
        {"$set": {"asset_tag": "UNASSIGNED", "asset_tag_original": STALE_ASSET_TAG}}
    )
    print(f"UPDATED document_chunks: {chunk_result.modified_count} chunks marked UNASSIGNED")
    
    # 5. Remove from local Neo4j graph
    graph_file = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../storage/neo4j_graph.json")
    )
    if os.path.exists(graph_file):
        with open(graph_file) as f:
            graph = json.load(f)
        
        nodes = graph.get("nodes", {})
        removed_nodes = []
        for k in list(nodes.keys()):
            if "f_01" in k.lower():
                removed_nodes.append(k)
                del nodes[k]
        
        rels = graph.get("relationships", [])
        removed_rels = [r for r in rels if "f_01" in r.get("source", "").lower() or "f_01" in r.get("target", "").lower()]
        graph["relationships"] = [r for r in rels if r not in removed_rels]
        
        with open(graph_file, "w") as f:
            json.dump(graph, f, indent=2)
        
        print(f"REMOVED local graph nodes: {removed_nodes}")
        print(f"REMOVED local graph relationships: {len(removed_rels)}")
    
    print()
    print("CLEANUP COMPLETE.")
    print()
    print("NEXT STEPS:")
    print("  1. Restart the backend to reload the local graph store.")
    print("  2. Re-upload the OISD document, selecting the correct asset tag or 'NEEDS_REVIEW'.")
    print("  3. The document chunks are preserved in Qdrant/FAISS — RAG will still work.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up stale F-01 asset data")
    parser.add_argument("--confirm", action="store_true",
                        help="Execute actual cleanup. Without this flag, runs in dry-run mode.")
    args = parser.parse_args()
    
    from app.database import get_db, db_manager
    db_manager.connect()
    db = get_db()
    
    if db is None:
        print("ERROR: Cannot connect to MongoDB.")
        sys.exit(1)
    
    if args.confirm:
        run_cleanup(db)
    else:
        run_dry_run(db)
