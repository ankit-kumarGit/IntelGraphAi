import logging
from pymongo import MongoClient
from pymongo.database import Database
from app.config import settings

logger = logging.getLogger("intelgraph.database")

class MongoDBManager:
    client: MongoClient = None
    db: Database = None

    def connect(self):
        try:
            self.client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info("Connected to MongoDB successfully at %s", settings.MONGO_URI)
            self._ensure_indexes()
        except Exception as e:
            logger.warning("MongoDB connection warning: %s. Using local in-memory fallback for transient storage.", e)
            self.client = None
            self.db = None

    def _ensure_indexes(self):
        if self.db is not None:
            self.db.assets.create_index("tag", unique=True)
            self.db.documents.create_index("document_id", unique=True)
            self.db.documents.create_index("asset_tag")
            self.db.document_chunks.create_index([("document_id", 1), ("chunk_id", 1)])
            self.db.maintenance_records.create_index("record_id", unique=True)
            self.db.audit_logs.create_index("timestamp")

    def get_collection(self, name: str):
        if self.db is not None:
            return self.db[name]
        return None

db_manager = MongoDBManager()

def get_db():
    if db_manager.db is None:
        db_manager.connect()
    return db_manager.db
