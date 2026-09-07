from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
import time
from app.database import get_db
from app.config import UPLOADS_DIR
from app.models.document import Document, DocumentChunk
from app.document_processing.extractor import DocumentExtractor
from app.document_processing.chunker import DocumentChunker
from app.document_processing.entity_extractor import EntityExtractor
from app.document_processing.pid_extractor import PIDTagExtractor
from app.rag.vector_store import vector_store

class DocumentService:
    @staticmethod
    def list_documents(
        asset_tag: Optional[str] = None,
        category: Optional[str] = None,
        governance_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return []

        query = {}
        if asset_tag:
            query["asset_tag"] = asset_tag.upper()
        if category:
            query["category"] = category
        if governance_status:
            query["governance_status"] = governance_status

        cursor = db.documents.find(query).sort("upload_date", -1)
        result = []
        for d in cursor:
            d["_id"] = str(d.get("_id", ""))
            result.append(d)
        return result

    DOC_ALIASES = {
        "doc-p101-manual": "Pump_P101_OEM_Manual",
        "doc-p101-insp-2025": "P101_Inspection_Report_Aug_2025",
        "doc-p101-fail-2026": "P101_Failure_Report_Feb_2026",
        "doc-p101-sop": "SOP-101_Centrifugal_Pump_Operation",
        "p101-manual": "Pump_P101_OEM_Manual",
        "p101-insp": "P101_Inspection_Report_Aug_2025",
        "p101-fail": "P101_Failure_Report_Feb_2026",
        "p101-sop": "SOP-101_Centrifugal_Pump_Operation",
        "doc_p101_manual": "Pump_P101_OEM_Manual",
        "doc_p101_insp_2025": "P101_Inspection_Report_Aug_2025",
        "doc_p101_fail_2026": "P101_Failure_Report_Feb_2026"
    }

    @staticmethod
    def get_document(document_id: str) -> Optional[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return None
        # 1. Exact match
        doc = db.documents.find_one({"document_id": document_id})
        # 2. Known alias match
        if not doc and document_id.lower() in DocumentService.DOC_ALIASES:
            aliased_id = DocumentService.DOC_ALIASES[document_id.lower()]
            doc = db.documents.find_one({"document_id": aliased_id})
        # 3. Fuzzy match by partial tag/event
        if not doc:
            clean_id = document_id.replace("doc-", "").replace("doc_", "").replace("-", "_").lower()
            all_docs = list(db.documents.find())
            for d in all_docs:
                d_id = d.get("document_id", "").lower()
                d_fn = d.get("filename", "").lower()
                if clean_id in d_id or d_id in clean_id or clean_id in d_fn:
                    doc = d
                    break
        if doc:
            doc["_id"] = str(doc.get("_id", ""))
        return doc

    @staticmethod
    def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return []
        resolved_doc = DocumentService.get_document(document_id)
        target_id = resolved_doc.get("document_id") if resolved_doc else document_id
        cursor = db.document_chunks.find({"document_id": target_id}).sort("page_number", 1)
        result = []
        for c in cursor:
            c["_id"] = str(c.get("_id", ""))
            result.append(c)
        return result

    @staticmethod
    def process_and_save_document(
        file_path: Path,
        filename: str,
        asset_tag: str,
        category: str = "Other",
        version: str = "v1.0",
        governance_status: str = "Approved",
        effective_date: Optional[str] = None,
        review_date: Optional[str] = None,
        uploaded_by: str = "Maintenance Engineer",
        is_pid: bool = False
    ) -> Dict[str, Any]:
        db = get_db()
        doc_id = filename.rsplit(".", 1)[0].replace(" ", "_")
        file_type = filename.rsplit(".", 1)[-1].lower()

        # 1. Extract content per page
        pages = DocumentExtractor.extract(file_path, file_type)
        combined_text = "\n".join([p["content"] for p in pages])

        # 2. Extract entities for human-in-the-loop review
        extracted_entities = EntityExtractor.extract_entities(combined_text)
        
        # P&ID tags if applicable
        if is_pid or "pid" in filename.lower() or "drawing" in filename.lower():
            pid_tags = PIDTagExtractor.extract_pid_tags(combined_text, drawing_title=filename)
            extracted_entities["pid_tags"] = pid_tags

        # 3. Create Chunks
        chunks = DocumentChunker.chunk_document(
            document_id=doc_id,
            asset_tag=asset_tag.upper(),
            category=category,
            version=version,
            governance_status=governance_status,
            pages=pages
        )

        # 4. Index Chunks into FAISS
        vector_store.add_chunks(chunks)

        # 5. Store in MongoDB
        doc_record = Document(
            document_id=doc_id,
            title=filename.replace("_", " ").rsplit(".", 1)[0],
            filename=filename,
            file_type=file_type,
            category=category,
            asset_tag=asset_tag.upper(),
            version=version,
            effective_date=effective_date or time.strftime("%Y-%m-%d"),
            review_date=review_date or "2027-01-01",
            governance_status=governance_status,
            summary=combined_text[:300] + "..." if len(combined_text) > 300 else combined_text,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            uploaded_by=uploaded_by,
            upload_date=time.strftime("%Y-%m-%d %H:%M"),
            chunk_count=len(chunks),
            extracted_entities=extracted_entities,
            is_pid_drawing=is_pid
        )

        if db is not None:
            db.documents.update_one(
                {"document_id": doc_id},
                {"$set": doc_record.model_dump()},
                upsert=True
            )
            # Save chunks to db
            for c in chunks:
                db.document_chunks.update_one(
                    {"chunk_id": c.chunk_id},
                    {"$set": c.model_dump()},
                    upsert=True
                )

        return doc_record.model_dump()

    @staticmethod
    def update_governance_status(document_id: str, status: str, version: Optional[str] = None) -> bool:
        db = get_db()
        if db is None:
            return False
        
        update_data = {"governance_status": status}
        if version:
            update_data["version"] = version

        res = db.documents.update_one({"document_id": document_id}, {"$set": update_data})
        db.document_chunks.update_many({"document_id": document_id}, {"$set": {"governance_status": status}})
        
        # Reload vector store metadata to reflect governance changes
        if vector_store.chunks_metadata:
            for chk in vector_store.chunks_metadata:
                if chk.get("document_id") == document_id:
                    chk["governance_status"] = status
                    if version:
                        chk["version"] = version
        return res.modified_count > 0

doc_service = DocumentService()
