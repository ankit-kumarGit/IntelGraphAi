import json
import time
from pathlib import Path
from bson import json_util
from app.database import db_manager

db_manager.connect()
db = db_manager.db

backup_dir = Path("storage/backups") / f"backup_provenance_{int(time.time())}"
backup_dir.mkdir(parents=True, exist_ok=True)

print(f"Backing up MongoDB collections to {backup_dir}...")

collections = ["assets", "documents", "document_chunks", "maintenance_records"]
for col in collections:
    docs = list(db[col].find({}))
    out_file = backup_dir / f"{col}.json"
    with open(out_file, "w") as f:
        f.write(json_util.dumps(docs, indent=2))
    print(f" - Backed up {len(docs)} documents from {col} to {out_file}")

# Backup neo4j_graph.json
neo_src = Path("storage/neo4j_graph.json")
if neo_src.exists():
    import shutil
    neo_dst = backup_dir / "neo4j_graph.json"
    shutil.copy(neo_src, neo_dst)
    print(f" - Backed up {neo_src} to {neo_dst}")

print("Backup complete!")
