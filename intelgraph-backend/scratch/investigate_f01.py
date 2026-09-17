"""Investigation script: Probe MongoDB and Neo4j for F-01 data provenance."""
import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, db_manager

db_manager.connect()
db = get_db()

if db is None:
    print("DB NOT CONNECTED")
    sys.exit(1)

print("=" * 60)
print("SECTION 1: F-01 ASSET RECORD IN MONGODB")
print("=" * 60)

asset = db.assets.find_one({"tag": "F-01"})
if asset:
    asset["_id"] = str(asset.get("_id"))
    print(json.dumps(asset, indent=2, default=str))
else:
    print("F-01 asset NOT FOUND in MongoDB")

print()
print("=" * 60)
print("SECTION 2: ALL F- PREFIX ASSETS IN MONGODB")
print("=" * 60)

f_assets = list(db.assets.find({"tag": {"$regex": "^F-"}}))
if f_assets:
    for a in f_assets:
        a["_id"] = str(a.get("_id"))
        print(json.dumps(a, indent=2, default=str))
        print("---")
else:
    print("No F- prefix assets found in MongoDB")

print()
print("=" * 60)
print("SECTION 3: DOCUMENTS LINKED TO F-01")
print("=" * 60)

docs = list(db.documents.find({"asset_tag": "F-01"}))
if docs:
    for d in docs:
        d["_id"] = str(d.get("_id"))
        safe_d = {k: v for k, v in d.items() if k not in ["summary", "extracted_entities"]}
        print(json.dumps(safe_d, indent=2, default=str))
        print("---")
else:
    print("No documents linked to F-01")

print()
print("=" * 60)
print("SECTION 4: DOCUMENT CHUNKS FOR F-01")
print("=" * 60)

chunks = list(db.document_chunks.find({"asset_tag": "F-01"}).limit(3))
print(f"Total chunks for F-01: {db.document_chunks.count_documents({'asset_tag': 'F-01'})}")
for c in chunks:
    c["_id"] = str(c.get("_id"))
    print(json.dumps({k: v for k, v in c.items() if k != "content"}, indent=2, default=str))
    print("---")

print()
print("=" * 60)
print("SECTION 5: ALL ASSETS IN MONGODB (tags only)")
print("=" * 60)

all_assets = list(db.assets.find({}, {"tag": 1, "name": 1, "asset_type": 1, "tenant_id": 1}))
for a in all_assets:
    a["_id"] = str(a.get("_id"))
    print(f"  tag={a.get('tag')} | name={a.get('name')} | type={a.get('asset_type')} | tenant={a.get('tenant_id')}")

print()
print("=" * 60)
print("SECTION 6: RECENT DOCUMENTS (last 5 uploads)")
print("=" * 60)

recent_docs = list(db.documents.find({}, {"document_id": 1, "filename": 1, "asset_tag": 1, "upload_date": 1, "document_category": 1, "category": 1}).sort("upload_date", -1).limit(5))
for d in recent_docs:
    d["_id"] = str(d.get("_id"))
    print(json.dumps(d, indent=2, default=str))
    print("---")
