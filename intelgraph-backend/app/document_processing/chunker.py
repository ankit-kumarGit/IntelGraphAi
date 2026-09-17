from typing import List, Dict, Any, Optional
from app.models.document import DocumentChunk

class DocumentChunker:
    @staticmethod
    def chunk_document(
        document_id: str,
        asset_tag: str,
        category: str,
        version: str,
        governance_status: str,
        pages: List[Dict[str, Any]],
        chunk_size: int = 350,
        chunk_overlap: int = 50,
        tenant_id: Optional[str] = "tenant_default",
        document_scope: str = "ASSET",
        primary_asset_tags: Optional[List[str]] = None,
        related_asset_tags: Optional[List[str]] = None,
        record_date: Optional[str] = None
    ) -> List[DocumentChunk]:
        chunks = []
        chunk_counter = 1
        p_tags = primary_asset_tags or ([asset_tag] if asset_tag else [])
        r_tags = related_asset_tags or []

        for p in pages:
            page_num = p.get("page", 1)
            section = p.get("section", "General")
            text = p.get("content", "").strip()

            if not text:
                continue

            words = text.split()
            if len(words) <= chunk_size:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}_chk_{chunk_counter:03d}",
                        document_id=document_id,
                        asset_tag=asset_tag,
                        document_scope=document_scope,
                        primary_asset_tags=p_tags,
                        related_asset_tags=r_tags,
                        page_number=page_num,
                        section_title=section,
                        content=text,
                        record_date=record_date,
                        category=category,
                        version=version,
                        governance_status=governance_status,
                        tenant_id=tenant_id
                    )
                )
                chunk_counter += 1
            else:
                # Sliding window chunking
                idx = 0
                while idx < len(words):
                    chunk_words = words[idx:idx + chunk_size]
                    chunk_text = " ".join(chunk_words)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{document_id}_chk_{chunk_counter:03d}",
                            document_id=document_id,
                            asset_tag=asset_tag,
                            document_scope=document_scope,
                            primary_asset_tags=p_tags,
                            related_asset_tags=r_tags,
                            page_number=page_num,
                            section_title=section,
                            content=chunk_text,
                            record_date=record_date,
                            category=category,
                            version=version,
                            governance_status=governance_status,
                            tenant_id=tenant_id
                        )
                    )
                    chunk_counter += 1
                    idx += (chunk_size - chunk_overlap)

        return chunks
