from typing import List, Dict, Any
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
        chunk_overlap: int = 50
    ) -> List[DocumentChunk]:
        chunks = []
        chunk_counter = 1

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
                        page_number=page_num,
                        section_title=section,
                        content=text,
                        category=category,
                        version=version,
                        governance_status=governance_status
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
                            page_number=page_num,
                            section_title=section,
                            content=chunk_text,
                            category=category,
                            version=version,
                            governance_status=governance_status
                        )
                    )
                    chunk_counter += 1
                    idx += (chunk_size - chunk_overlap)

        return chunks
