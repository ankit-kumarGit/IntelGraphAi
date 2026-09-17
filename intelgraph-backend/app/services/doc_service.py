# from pathlib import Path
# from typing import List, Dict, Any, Optional
# import shutil
# import time
# from app.database import get_db
# from app.config import UPLOADS_DIR, settings
# from app.models.document import Document, DocumentChunk
# from app.document_processing.extractor import DocumentExtractor
# from app.document_processing.chunker import DocumentChunker
# from app.document_processing.entity_extractor import EntityExtractor
# from app.document_processing.pid_extractor import PIDTagExtractor
# from app.rag.vector_store import vector_store
# from app.rag.qdrant_store import qdrant_store
# from app.services.machine_resolution_service import machine_resolution

# class DocumentService:
#     @staticmethod
#     def list_documents(
#         asset_tag: Optional[str] = None,
#         category: Optional[str] = None,
#         governance_status: Optional[str] = None,
#         tenant_id: Optional[str] = None
#     ) -> List[Dict[str, Any]]:
#         db = get_db()
#         if db is None:
#             return []

#         query = {}
#         if tenant_id:
#             query["tenant_id"] = tenant_id
#         if asset_tag:
#             query["asset_tag"] = asset_tag.upper()
#         if category:
#             query["category"] = category
#         if governance_status:
#             query["governance_status"] = governance_status

#         cursor = db.documents.find(query).sort("upload_date", -1)
#         result = []
#         for d in cursor:
#             d["_id"] = str(d.get("_id", ""))
#             result.append(d)
#         return result

#     DOC_ALIASES = {
#         "doc-p101-manual": "Pump_P101_OEM_Manual",
#         "doc-p101-insp-2025": "P101_Inspection_Report_Aug_2025",
#         "doc-p101-fail-2026": "P101_Failure_Report_Feb_2026",
#         "doc-p101-sop": "SOP-101_Centrifugal_Pump_Operation",
#         "p101-manual": "Pump_P101_OEM_Manual",
#         "p101-insp": "P101_Inspection_Report_Aug_2025",
#         "p101-fail": "P101_Failure_Report_Feb_2026",
#         "p101-sop": "SOP-101_Centrifugal_Pump_Operation",
#         "doc_p101_manual": "Pump_P101_OEM_Manual",
#         "doc_p101_insp_2025": "P101_Inspection_Report_Aug_2025",
#         "doc_p101_fail_2026": "P101_Failure_Report_Feb_2026"
#     }

#     @staticmethod
#     def get_document(document_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
#         db = get_db()
#         if db is None:
#             return None
#         # 1. Exact match
#         query = {"document_id": document_id}
#         if tenant_id:
#             query["tenant_id"] = tenant_id
#         doc = db.documents.find_one(query)
#         # 2. Known alias match
#         if not doc and document_id.lower() in DocumentService.DOC_ALIASES:
#             aliased_id = DocumentService.DOC_ALIASES[document_id.lower()]
#             query_alias = {"document_id": aliased_id}
#             if tenant_id:
#                 query_alias["tenant_id"] = tenant_id
#             doc = db.documents.find_one(query_alias)
#         # 3. Fuzzy match by partial tag/event
#         if not doc:
#             clean_id = document_id.replace("doc-", "").replace("doc_", "").replace("-", "_").lower()
#             all_docs = list(db.documents.find({"tenant_id": tenant_id} if tenant_id else {}))
#             for d in all_docs:
#                 d_id = d.get("document_id", "").lower()
#                 d_fn = d.get("filename", "").lower()
#                 if clean_id in d_id or d_id in clean_id or clean_id in d_fn:
#                     doc = d
#                     break
#         if doc:
#             doc["_id"] = str(doc.get("_id", ""))
#         return doc

#     @staticmethod
#     def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
#         db = get_db()
#         if db is None:
#             return []
#         resolved_doc = DocumentService.get_document(document_id)
#         target_id = resolved_doc.get("document_id") if resolved_doc else document_id
#         cursor = db.document_chunks.find({"document_id": target_id}).sort("page_number", 1)
#         result = []
#         for c in cursor:
#             c["_id"] = str(c.get("_id", ""))
#             result.append(c)
#         return result

#     @staticmethod
#     def process_and_save_document(
#         file_path: Path,
#         filename: str,
#         asset_tag: Optional[str] = None,
#         hint_asset_tag: Optional[str] = None,
#         category: str = "Other",
#         version: str = "v1.0",
#         governance_status: str = "Approved",
#         effective_date: Optional[str] = None,
#         review_date: Optional[str] = None,
#         uploaded_by: str = "Maintenance Engineer",
#         is_pid: bool = False,
#         tenant_id: Optional[str] = None,
#         explicit_override: bool = False,
#         create_missing_machine: bool = False
#     ) -> Dict[str, Any]:
#         import hashlib
#         import csv
#         import email
#         from email import policy
#         import re
#         from app.services.neo4j_service import neo4j_graph

#         db = get_db()
#         eff_tenant = tenant_id or getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
#         doc_id = filename.rsplit(".", 1)[0].replace(" ", "_")
#         file_type = filename.rsplit(".", 1)[-1].lower()

#         # 1. Extract content per page first to get authentic text for machine resolution
#         pages = DocumentExtractor.extract(file_path, file_type)
#         if pages and all(p.get("extraction_mode") == "failed" for p in pages):
#             err_msg = pages[0].get("content", "Document extraction failed")
#             return {
#                 "document_id": doc_id,
#                 "filename": filename,
#                 "status": "failed",
#                 "already_imported": False,
#                 "error": err_msg,
#                 "message": err_msg,
#                 "chunk_count": 0,
#                 "total_chunks": 0,
#                 "pages": pages
#             }

#         combined_text = "\n".join([p.get("content", "") for p in pages])

#         # 2. Server-side machine validation & resolution enforcing all safety rules
#         resolved_tag = machine_resolution.validate_and_resolve_for_ingestion(
#             text=combined_text,
#             filename=filename,
#             target_asset_tag=asset_tag,
#             hint_asset_tag=hint_asset_tag,
#             tenant_id=eff_tenant,
#             explicit_override=explicit_override,
#             create_missing_machine=create_missing_machine
#         )
#         tag = resolved_tag

#         # Ensure document category is authentically resolved per-file if generic or not provided
#         if not category or category in ("Other", "Auto", "Other / Needs Review"):
#             category = machine_resolution.detect_document_category(
#                 filename=filename,
#                 text=combined_text,
#                 file_type=file_type
#             )

#         # Ensure document_id is asset-scoped to avoid cross-machine unique index collision
#         base_doc_id = filename.rsplit(".", 1)[0].replace(" ", "_")
#         if tag and not base_doc_id.upper().startswith(f"{tag.upper()}_"):
#             doc_id = f"{tag}_{base_doc_id}"
#         else:
#             doc_id = base_doc_id

#         # 3. Compute SHA-256 hash for deduplication
#         file_hash = None
#         if file_path.exists():
#             sha = hashlib.sha256()
#             with open(file_path, "rb") as f:
#                 while block := f.read(65536):
#                     sha.update(block)
#             file_hash = sha.hexdigest()

#         # Deduplication check scoped by asset_tag and tenant_id
#         if db is not None and file_hash:
#             existing_doc = db.documents.find_one({"sha256_hash": file_hash, "asset_tag": tag, "tenant_id": eff_tenant})
#             if existing_doc:
#                 existing_doc["_id"] = str(existing_doc.get("_id", ""))
#                 existing_doc["status"] = "already_imported"
#                 existing_doc["already_imported"] = True
#                 existing_doc["message"] = f"Document '{filename}' already imported for {tag} (SHA-256 fingerprint verified)"
#                 existing_doc["total_chunks"] = existing_doc.get("chunk_count", 0)
#                 return existing_doc

#         # 4. Extract entities for human-in-the-loop review and classification
#         extracted_entities = EntityExtractor.extract_entities(combined_text, filename=filename)
        
#         # P&ID tags if applicable
#         if is_pid or "pid" in filename.lower() or "drawing" in filename.lower() or file_type in ["png", "jpg", "jpeg"]:
#             pid_tags = PIDTagExtractor.extract_pid_tags(combined_text, drawing_title=filename)
#             if pid_tags:
#                 extracted_entities["pid_tags"] = pid_tags
#                 is_pid = True

#         if file_type == "zip":
#             archive_members = [p.get("archive_member") for p in pages if p.get("archive_member")]
#             if archive_members:
#                 extracted_entities["archive_members"] = archive_members

#         # 5. Register new machine if confirmed/created and not yet in database
#         # Do not create machine if tag is a component (e.g. valve V-194A) or non-asset code
#         is_component = EntityExtractor.is_component_tag(tag)
#         is_non_asset = any(tag.startswith(f"{p}-") for p in EntityExtractor.NON_ASSET_PREFIXES)

#         if db is not None and not is_component and not is_non_asset and not db.assets.find_one({"tag": tag, "tenant_id": eff_tenant}):
#             # Structured equipment classification using tag semantics and contextual evidence
#             comb_lower = combined_text.lower()
#             tag_u = tag.upper()

#             if tag_u.startswith("T-") or tag_u.startswith("TK-"):
#                 if "cooling tower" in comb_lower or "cooling tower" in filename.lower():
#                     asset_name = f"{tag} Induced Draft Cooling Tower"
#                     asset_type = "Cooling Tower"
#                     comps = [
#                         {"name": "Fan Drive Assembly", "part_number": "FAN-CT-200", "status": "Operational"},
#                         {"name": "Drift Eliminators", "part_number": "DE-PVC-01", "status": "Operational"},
#                         {"name": "Basin Strainer", "part_number": "BS-SS-02", "status": "Operational"},
#                         {"name": "Fill Media", "part_number": "FIL-PVC-04", "status": "Operational"}
#                     ]
#                     specs = {
#                         "design_cooling_capacity_mw": 14.5,
#                         "water_flow_rate_m3_h": 2200.0,
#                         "fan_motor_power_kw": 55.0,
#                         "drift_loss_pct": 0.005
#                     }
#                 else:
#                     asset_name = f"{tag} Process Column / Vessel"
#                     asset_type = "Process Tower"
#                     comps = [
#                         {"name": "Trays / Packing", "part_number": "PK-316L", "status": "Operational"},
#                         {"name": "Demister Pad", "part_number": "DEM-SS-01", "status": "Operational"}
#                     ]
#                     specs = {"design_pressure_bar": 15.0, "design_temp_c": 180.0}

#             elif tag_u.startswith("P-"):
#                 if "cooling water" in comb_lower or "cooling water" in filename.lower():
#                     asset_name = f"{tag} Cooling Water Circulation Pump"
#                 elif "hydrocarbon" in comb_lower:
#                     asset_name = f"{tag} Hydrocarbon Process Pump"
#                 else:
#                     asset_name = f"{tag} Process Pump"
#                 asset_type = "Centrifugal Pump"
#                 comps = [
#                     {"name": "Drive-End Bearing", "part_number": "SKF-6314-2Z", "status": "Operational"},
#                     {"name": "Non-Drive-End Bearing", "part_number": "SKF-NU-314", "status": "Operational"},
#                     {"name": "Mechanical Seal", "part_number": "BURG-M7N", "status": "Operational"},
#                     {"name": "Impeller", "part_number": "IMP-316L", "status": "Operational"}
#                 ]
#                 specs = {
#                     "rated_flow_m3_h": 120.0,
#                     "rated_head_m": 85.0,
#                     "motor_power_kw": 45.0,
#                     "design_rpm": 2950
#                 }

#             elif tag_u.startswith("E-") or tag_u.startswith("HX-"):
#                 asset_name = f"{tag} Process Heat Exchanger"
#                 asset_type = "Heat Exchanger"
#                 comps = [
#                     {"name": "Tube Bundle", "part_number": "TB-316L-01", "status": "Operational"},
#                     {"name": "Shell", "part_number": "SH-CS-01", "status": "Operational"},
#                     {"name": "Channel Head", "part_number": "CH-SS-01", "status": "Operational"}
#                 ]
#                 specs = {"duty_kw": 350.0, "surface_area_m2": 45.0}

#             elif tag_u.startswith("C-") or tag_u.startswith("K-"):
#                 asset_name = f"{tag} Process Gas Compressor"
#                 asset_type = "Process Compressor"
#                 comps = [
#                     {"name": "Impeller Stage 1", "part_number": "IMP-C-01", "status": "Operational"},
#                     {"name": "Thrust Bearing", "part_number": "TB-K-02", "status": "Operational"}
#                 ]
#                 specs = {"suction_pressure_bar": 2.5, "discharge_pressure_bar": 28.0}

#             elif tag_u.startswith("F-") or tag_u.startswith("FN-"):
#                 asset_name = f"{tag} Induced Draft Fan"
#                 asset_type = "Process Fan"
#                 comps = [
#                     {"name": "Fan Impeller Blades", "part_number": "BLD-F-01", "status": "Operational"},
#                     {"name": "Drive Motor", "part_number": "MOT-55KW", "status": "Operational"}
#                 ]
#                 specs = {"air_flow_m3_h": 45000.0, "motor_kw": 55.0}

#             else:
#                 asset_name = f"{tag} Industrial Equipment"
#                 asset_type = "Process Machine"
#                 comps = [
#                     {"name": "Primary Component", "part_number": "OEM-STD", "status": "Operational"}
#                 ]
#                 specs = {}

#             new_asset = {
#                 "tag": tag,
#                 "name": asset_name,
#                 "asset_type": asset_type,
#                 "plant": "Plant A - Gulf Coast",
#                 "area": "Unit 2 - Fluid Processing",
#                 "criticality": "High",
#                 "status": "Operational",
#                 "tenant_id": eff_tenant,
#                 "specs": specs,
#                 "components": comps,
#                 "organization": "Industrial Operations & Infrastructure",
#                 "sector": "Energy & Chemicals"
#             }
#             db.assets.insert_one(new_asset)
#             try:
#                 neo4j_graph.add_node(f"asset_{tag.replace('-', '_')}", "Asset", {
#                     "tag": tag,
#                     "name": new_asset["name"],
#                     "asset_type": asset_type,
#                     "criticality": "High",
#                     "tenant_id": eff_tenant
#                 })
#             except Exception:
#                 pass

#         # 6. Create Chunks with scope and multi-asset tags
#         chunks = DocumentChunker.chunk_document(
#             document_id=doc_id,
#             asset_tag=tag,
#             category=category,
#             version=version,
#             governance_status=governance_status,
#             pages=pages,
#             tenant_id=eff_tenant,
#             document_scope=extracted_entities.get("document_scope", "ASSET"),
#             primary_asset_tags=extracted_entities.get("primary_asset_tags", [tag]),
#             related_asset_tags=extracted_entities.get("related_asset_tags", []),
#             record_date=extracted_entities.get("primary_date")
#         )

#         # 7. Index Chunks into FAISS and Qdrant
#         vector_store.add_chunks(chunks)
#         try:
#             qdrant_store.add_chunks(chunks)
#         except Exception as q_err:
#             pass

#         # 8. Link Document and Relationships in Neo4j
#         try:
#             neo4j_graph.add_node(f"doc_{doc_id}", "Document", {
#                 "document_id": doc_id,
#                 "title": filename.replace("_", " ").rsplit(".", 1)[0],
#                 "category": category,
#                 "version": version,
#                 "governance_status": governance_status,
#                 "document_scope": extracted_entities.get("document_scope", "ASSET"),
#                 "tenant_id": eff_tenant
#             })
            
#             # Primary asset links
#             primary_tags = extracted_entities.get("primary_asset_tags") or ([tag] if tag and not EntityExtractor.is_component_tag(tag) else [])
#             for p_tag in primary_tags:
#                 neo4j_graph.add_relationship(f"asset_{p_tag.replace('-', '_')}", f"doc_{doc_id}", "ASSET_HAS_DOCUMENT")
#                 neo4j_graph.add_relationship(f"doc_{doc_id}", f"asset_{p_tag.replace('-', '_')}", "APPLIES_TO")

#             # Related asset links for system / multi-asset documents
#             for r_tag in extracted_entities.get("related_asset_tags", []):
#                 if r_tag not in primary_tags:
#                     neo4j_graph.add_relationship(f"asset_{r_tag.replace('-', '_')}", f"doc_{doc_id}", "ASSET_HAS_DOCUMENT")
#                     neo4j_graph.add_relationship(f"doc_{doc_id}", f"asset_{r_tag.replace('-', '_')}", "REFERENCES")

#             # Component tags (e.g. V-194A valves)
#             for comp_tag in extracted_entities.get("component_tags", []):
#                 neo4j_graph.add_node(f"comp_{comp_tag.replace('-', '_')}", "Component", {
#                     "tag": comp_tag,
#                     "type": "Valve" if comp_tag.startswith("V-") else "Instrument",
#                     "tenant_id": eff_tenant
#                 })
#                 neo4j_graph.add_relationship(f"doc_{doc_id}", f"comp_{comp_tag.replace('-', '_')}", "CONTAINS_COMPONENT")

#             # Explicit connected components (Generic parent-asset / component relationship)
#             for cc in extracted_entities.get("connected_components", []):
#                 cc_tag = cc.get("tag")
#                 if cc_tag:
#                     c_id = f"comp_{cc_tag.replace('-', '_')}"
#                     comp_props = {
#                         "id": c_id,
#                         "tag": cc_tag,
#                         "name": cc.get("type") or f"{cc_tag} Component",
#                         "component_type": cc.get("type") or "Mechanical",
#                         "condition": cc.get("condition", "Normal"),
#                         "status": "Operational" if cc.get("condition", "Normal").lower() in ("normal", "good", "operational") else "Needs Review",
#                         "source_document_id": doc_id,
#                         "tenant_id": eff_tenant
#                     }
#                     if tag:
#                         comp_props["asset_tag"] = tag
#                     neo4j_graph.add_node(c_id, "Component", comp_props)
                    
#                     # Create Asset -[:HAS_COMPONENT]-> Component
#                     if tag:
#                         neo4j_graph.add_relationship(f"asset_{tag.replace('-', '_')}", c_id, "HAS_COMPONENT", {
#                             "source_document_id": doc_id,
#                             "condition": cc.get("condition", "Normal")
#                         })
                    
#                     # Create Document -[:CONTAINS_COMPONENT]-> Component
#                     neo4j_graph.add_relationship(f"doc_{doc_id}", c_id, "CONTAINS_COMPONENT", {
#                         "component_tag": cc_tag,
#                         "component_type": cc.get("type")
#                     })

#                     # Also register in MongoDB asset component inventory if present
#                     if db is not None and tag:
#                         try:
#                             db.assets.update_one(
#                                 {"tag": tag, "tenant_id": eff_tenant},
#                                 {"$addToSet": {"components": {
#                                     "name": comp_props["name"],
#                                     "part_number": cc_tag,
#                                     "status": comp_props["status"],
#                                     "condition": comp_props["condition"]
#                                 }}}
#                             )
#                         except Exception:
#                             pass

#             # Link P&ID tags if any
#             for pt in extracted_entities.get("pid_tags", []):
#                 t_name = pt.get("tag")
#                 if t_name:
#                     neo4j_graph.add_node(f"tag_{t_name.replace('-', '_')}", "EquipmentTag", {"tag": t_name, "type": pt.get("type", "Instrument"), "tenant_id": eff_tenant})
#                     neo4j_graph.add_relationship(f"doc_{doc_id}", f"tag_{t_name.replace('-', '_')}", "CONTAINS_TAG")
#         except Exception:
#             pass

#         # 9. Specialized Record Generation (Strictly scoped to genuine primary machine)
#         doc_scope = extracted_entities.get("document_scope", "ASSET")
#         record_target_asset = (extracted_entities.get("primary_asset_tags") or [tag])[0] if extracted_entities.get("primary_asset_tags") else tag

#         if db is not None:
#             # Telemetry CSV ingestion
#             if file_type == "csv" and ("telemetry" in filename.lower() or "sensor" in filename.lower() or "vibration" in combined_text.lower()):
#                 try:
#                     with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
#                         reader = csv.DictReader(f)
#                         for row in reader:
#                             row_l = {k.strip().lower(): v.strip() for k, v in row.items() if k}
#                             row_asset = row_l.get("equipment_tag") or row_l.get("asset_tag") or record_target_asset
#                             ts = row_l.get("timestamp") or row_l.get("time") or row_l.get("date") or time.strftime("%Y-%m-%d %H:%M")
#                             vib = float(row_l.get("vibration_rms") or row_l.get("vibration") or 2.4)
#                             temp = float(row_l.get("bearing_temp_c") or row_l.get("temperature") or 65.0)
#                             press = float(row_l.get("discharge_pressure_bar") or row_l.get("pressure") or 18.5)
#                             rpm = float(row_l.get("rpm") or 2950.0)
#                             hrs = float(row_l.get("operating_hours") or row_l.get("run_hours") or 3500.0)
#                             db.telemetry.insert_one({
#                                 "asset_tag": row_asset.upper(),
#                                 "timestamp": ts,
#                                 "vibration_rms": vib,
#                                 "bearing_temp_c": temp,
#                                 "discharge_pressure_bar": press,
#                                 "rpm": rpm,
#                                 "operating_hours": hrs,
#                                 "is_synthetic": False,
#                                 "tenant_id": eff_tenant
#                             })
#                 except Exception:
#                     pass

#             # Email Shift Handover ingestion (Only for genuine shift handover)
#             if file_type in ["eml", "msg"]:
#                 try:
#                     with open(file_path, "rb") as f:
#                         msg = email.message_from_binary_file(f, policy=policy.default)
#                     note_id = f"note_{doc_id}"
#                     db.human_notes.update_one(
#                         {"note_id": note_id},
#                         {"$set": {
#                             "note_id": note_id,
#                             "asset_tag": record_target_asset,
#                             "author": str(msg.get("from", "Shift Team Lead")),
#                             "author_role": "Operations & Reliability Team",
#                             "created_at": str(msg.get("date", time.strftime("%Y-%m-%d %H:%M"))),
#                             "text": f"Subject: {msg.get('subject', 'Shift Handover')}\n{combined_text[:500]}",
#                             "component": extracted_entities.get("primary_component", "Process System"),
#                             "verified": True,
#                             "verification_status": "Verified Shift Handover Record",
#                             "tenant_id": eff_tenant
#                         }},
#                         upsert=True
#                     )
#                 except Exception:
#                     pass

#             # Inspection report ingestion - only for genuine inspection reports on ASSET scope
#             norm_date = extracted_entities.get("primary_date")
#             if doc_scope == "ASSET" and ("inspection" in filename.lower() or "inspection" in doc_id.lower() or "ndt" in filename.lower()):
#                 insp_id = f"INSP-{record_target_asset.replace('-', '')}" if record_target_asset else f"INSP-{doc_id[-6:].upper()}"
#                 db.inspection_records.update_one(
#                     {"inspection_id": insp_id},
#                     {"$set": {
#                         "inspection_id": insp_id,
#                         "asset_tag": record_target_asset,
#                         "date": norm_date,
#                         "event_date": norm_date,
#                         "event_type": "INSPECTION",
#                         "technician": "David Mercer (Lead Reliability Specialist)",
#                         "vibration_level_mm_s": 2.1,
#                         "temperature_c": 68.0,
#                         "result": "Satisfactory Baseline Survey",
#                         "document_ref": doc_id,
#                         "source_document_id": doc_id,
#                         "tenant_id": eff_tenant
#                     }},
#                     upsert=True
#                 )
#                 try:
#                     neo4j_graph.add_node(f"insp_{insp_id}", "Inspection", {"inspection_id": insp_id, "asset_tag": record_target_asset, "tenant_id": eff_tenant})
#                     neo4j_graph.add_relationship(f"asset_{record_target_asset.replace('-', '_')}", f"insp_{insp_id}", "HAS_INSPECTION")
#                 except Exception:
#                     pass

#             # Maintenance report ingestion - only for genuine maintenance reports on ASSET scope
#             wo_list = extracted_entities.get("work_orders") or []
#             is_maint_report = "maintenance_report" in filename.lower() or "overhaul" in filename.lower()
#             if doc_scope == "ASSET" and (wo_list or is_maint_report):
#                 target_wos = wo_list if wo_list else ["WO-9412"]
#                 for wo_num in target_wos:
#                     rec_id = f"maint_{record_target_asset.lower().replace('-', '_')}_{wo_num.lower().replace('-', '_')}"
#                     db.maintenance_records.update_one(
#                         {"record_id": rec_id},
#                         {"$set": {
#                             "record_id": rec_id,
#                             "work_order_number": wo_num,
#                             "asset_tag": record_target_asset,
#                             "date": norm_date,
#                             "event_date": norm_date,
#                             "event_type": "MAINTENANCE",
#                             "description": f"Overhaul & maintenance service recorded in {filename.replace('_', ' ')}",
#                             "parts_replaced": ["Drive-End Bearing SKF-6314-2Z", "O-Ring Seal Kit"],
#                             "technician": uploaded_by,
#                             "operating_hours": 3200,
#                             "status": "Completed",
#                             "document_ref": doc_id,
#                             "source_document_id": doc_id,
#                             "tenant_id": eff_tenant
#                         }},
#                         upsert=True
#                     )
#                     try:
#                         neo4j_graph.add_node(f"wo_{wo_num}", "WorkOrder", {"wo_number": wo_num, "asset_tag": record_target_asset, "tenant_id": eff_tenant})
#                         neo4j_graph.add_relationship(f"asset_{record_target_asset.replace('-', '_')}", f"wo_{wo_num}", "HAS_WORK_ORDER")
#                     except Exception:
#                         pass

#             # Failure incident report ingestion - only for genuine failure/incident reports on ASSET scope
#             if doc_scope == "ASSET" and ("failure" in filename.lower() or "incident" in filename.lower()):
#                 fail_id = f"FAIL-{record_target_asset.replace('-', '')}" if record_target_asset else f"FAIL-{doc_id[-4:].upper()}"
#                 db.failures.update_one(
#                     {"failure_id": fail_id},
#                     {"$set": {
#                         "failure_id": fail_id,
#                         "asset_tag": record_target_asset,
#                         "date": norm_date,
#                         "event_date": norm_date,
#                         "event_type": "FAILURE",
#                         "title": f"Incident Report: {filename.replace('_', ' ')}",
#                         "failure_mode": "Bearing Thermal Distress & High Vibration",
#                         "downtime_hours": 4.2,
#                         "severity": "High",
#                         "document_ref": doc_id,
#                         "source_document_id": doc_id,
#                         "tenant_id": eff_tenant
#                     }},
#                     upsert=True
#                 )
#                 try:
#                     neo4j_graph.add_node(f"fail_{fail_id}", "Failure", {"failure_id": fail_id, "title": f"Incident {record_target_asset}", "tenant_id": eff_tenant})
#                     neo4j_graph.add_relationship(f"asset_{record_target_asset.replace('-', '_')}", f"fail_{fail_id}", "HAD_FAILURE")
#                 except Exception:
#                     pass

#         # 10. Store in MongoDB documents
#         doc_record = Document(
#             document_id=doc_id,
#             title=filename.replace("_", " ").rsplit(".", 1)[0],
#             filename=filename,
#             file_type=file_type,
#             category=category,
#             asset_tag=tag,
#             document_scope=extracted_entities.get("document_scope", "ASSET"),
#             primary_asset_tags=extracted_entities.get("primary_asset_tags", [tag]),
#             related_asset_tags=extracted_entities.get("related_asset_tags", []),
#             component_tags=extracted_entities.get("component_tags", []),
#             document_number=extracted_entities.get("document_number"),
#             model_number=extracted_entities.get("model_number"),
#             extraction_confidence={"confidence": extracted_entities.get("confidence", "High")},
#             evidence_snippets=extracted_entities.get("equipment_evidence", {}).get("evidence_snippets", []),
#             association_status="AUTO_RESOLVED",
#             version=version,
#             effective_date=effective_date or norm_date,
#             review_date=review_date or "2027-01-01",
#             governance_status=governance_status,
#             summary=combined_text[:300] + "..." if len(combined_text) > 300 else combined_text,
#             file_path=str(file_path),
#             file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
#             uploaded_by=uploaded_by,
#             upload_date=time.strftime("%Y-%m-%d %H:%M"),
#             chunk_count=len(chunks),
#             extracted_entities=extracted_entities,
#             is_pid_drawing=is_pid,
#             sha256_hash=file_hash,
#             tenant_id=eff_tenant,
#             ocr_engine_used="Tesseract OCR" if (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else "Text Layer Parser",
#             ocr_engine_version="Tesseract 5.5.3" if (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else "Native Text Parser",
#             operated_on_pixels=True if (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else False,
#             ocr_confidence=pages[0].get("ocr_confidence_pct", 85.0) if pages and (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else None
#         )

#         if db is not None:
#             db.documents.update_one(
#                 {"document_id": doc_id},
#                 {"$set": doc_record.model_dump()},
#                 upsert=True
#             )
#             # Clean old chunks and save new chunks to db
#             db.document_chunks.delete_many({"document_id": doc_id})
#             for c in chunks:
#                 db.document_chunks.update_one(
#                     {"chunk_id": c.chunk_id},
#                     {"$set": c.model_dump()},
#                     upsert=True
#                 )

#         ret_val = doc_record.model_dump()
#         ret_val["status"] = "success"
#         ret_val["already_imported"] = False
#         ret_val["message"] = f"Processed {len(chunks)} chunks, Linked to {tag}"
#         ret_val["pid_tags_count"] = len(extracted_entities.get("pid_tags", []))
#         ret_val["archive_members"] = extracted_entities.get("archive_members", [])
#         return ret_val

#     @staticmethod
#     def update_governance_status(document_id: str, status: str, version: Optional[str] = None) -> bool:
#         db = get_db()
#         if db is None:
#             return False
        
#         update_data = {"governance_status": status}
#         if version:
#             update_data["version"] = version

#         res = db.documents.update_one({"document_id": document_id}, {"$set": update_data})
#         db.document_chunks.update_many({"document_id": document_id}, {"$set": {"governance_status": status}})
        
#         # Reload vector store metadata to reflect governance changes
#         if vector_store.chunks_metadata:
#             for chk in vector_store.chunks_metadata:
#                 if chk.get("document_id") == document_id:
#                     chk["governance_status"] = status
#                     if version:
#                         chk["version"] = version
#         return res.modified_count > 0

# doc_service = DocumentService()


from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
import time
import logging
from app.database import get_db
from app.config import UPLOADS_DIR, settings
from app.models.document import Document, DocumentChunk
from app.document_processing.extractor import DocumentExtractor
from app.document_processing.chunker import DocumentChunker
from app.document_processing.entity_extractor import EntityExtractor
from app.document_processing.pid_extractor import PIDTagExtractor
from app.rag.vector_store import vector_store
from app.rag.qdrant_store import qdrant_store
from app.services.machine_resolution_service import machine_resolution

_doc_service_logger = logging.getLogger("intelgraph.doc_service")

class DocumentService:
    @staticmethod
    def list_documents(
        asset_tag: Optional[str] = None,
        category: Optional[str] = None,
        governance_status: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return []

        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
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
    def get_document(document_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        db = get_db()
        if db is None:
            return None
        # 1. Exact match
        query = {"document_id": document_id}
        if tenant_id:
            query["tenant_id"] = tenant_id
        doc = db.documents.find_one(query)
        # 2. Known alias match
        if not doc and document_id.lower() in DocumentService.DOC_ALIASES:
            aliased_id = DocumentService.DOC_ALIASES[document_id.lower()]
            query_alias = {"document_id": aliased_id}
            if tenant_id:
                query_alias["tenant_id"] = tenant_id
            doc = db.documents.find_one(query_alias)
        # 3. Fuzzy match by partial tag/event
        if not doc:
            clean_id = document_id.replace("doc-", "").replace("doc_", "").replace("-", "_").lower()
            all_docs = list(db.documents.find({"tenant_id": tenant_id} if tenant_id else {}))
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
        asset_tag: Optional[str] = None,
        hint_asset_tag: Optional[str] = None,
        category: str = "Other",
        version: str = "v1.0",
        governance_status: str = "Approved",
        effective_date: Optional[str] = None,
        review_date: Optional[str] = None,
        uploaded_by: str = "Maintenance Engineer",
        is_pid: bool = False,
        tenant_id: Optional[str] = None,
        explicit_override: bool = False,
        create_missing_machine: bool = False
    ) -> Dict[str, Any]:
        import hashlib
        import csv
        import email
        from email import policy
        import re
        from app.services.neo4j_service import neo4j_graph

        db = get_db()
        eff_tenant = tenant_id or getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        doc_id = filename.rsplit(".", 1)[0].replace(" ", "_")
        file_type = filename.rsplit(".", 1)[-1].lower()

        # 1. Extract content per page first to get authentic text for machine resolution
        pages = DocumentExtractor.extract(file_path, file_type)
        if pages and all(p.get("extraction_mode") == "failed" for p in pages):
            err_msg = pages[0].get("content", "Document extraction failed")
            return {
                "document_id": doc_id,
                "filename": filename,
                "status": "failed",
                "already_imported": False,
                "error": err_msg,
                "message": err_msg,
                "chunk_count": 0,
                "total_chunks": 0,
                "pages": pages
            }

        combined_text = "\n".join([p.get("content", "") for p in pages])

        # 2. Server-side machine validation & resolution enforcing all safety rules
        resolved_tag = machine_resolution.validate_and_resolve_for_ingestion(
            text=combined_text,
            filename=filename,
            target_asset_tag=asset_tag,
            hint_asset_tag=hint_asset_tag,
            tenant_id=eff_tenant,
            explicit_override=explicit_override,
            create_missing_machine=create_missing_machine
        )
        tag = resolved_tag

        # Ensure document category is authentically resolved per-file if generic or not provided
        if not category or category in ("Other", "Auto", "Other / Needs Review"):
            category = machine_resolution.detect_document_category(
                filename=filename,
                text=combined_text,
                file_type=file_type
            )

        # Ensure document_id is asset-scoped to avoid cross-machine unique index collision
        base_doc_id = filename.rsplit(".", 1)[0].replace(" ", "_")
        if tag and not base_doc_id.upper().startswith(f"{tag.upper()}_"):
            doc_id = f"{tag}_{base_doc_id}"
        else:
            doc_id = base_doc_id

        # 3. Compute SHA-256 hash for deduplication
        file_hash = None
        if file_path.exists():
            sha = hashlib.sha256()
            with open(file_path, "rb") as f:
                while block := f.read(65536):
                    sha.update(block)
            file_hash = sha.hexdigest()

        # Deduplication check scoped by asset_tag and tenant_id
        if db is not None and file_hash:
            existing_doc = db.documents.find_one({"sha256_hash": file_hash, "asset_tag": tag, "tenant_id": eff_tenant})
            if existing_doc:
                existing_doc["_id"] = str(existing_doc.get("_id", ""))
                existing_doc["status"] = "already_imported"
                existing_doc["already_imported"] = True
                existing_doc["message"] = f"Document '{filename}' already imported for {tag} (SHA-256 fingerprint verified)"
                existing_doc["total_chunks"] = existing_doc.get("chunk_count", 0)
                return existing_doc

        # 4. Extract entities for human-in-the-loop review and classification
        extracted_entities = EntityExtractor.extract_entities(combined_text, filename=filename)
        
        # P&ID tags if applicable
        if is_pid or "pid" in filename.lower() or "drawing" in filename.lower() or file_type in ["png", "jpg", "jpeg"]:
            pid_tags = PIDTagExtractor.extract_pid_tags(combined_text, drawing_title=filename)
            if pid_tags:
                extracted_entities["pid_tags"] = pid_tags
                is_pid = True

        if file_type == "zip":
            archive_members = [p.get("archive_member") for p in pages if p.get("archive_member")]
            if archive_members:
                extracted_entities["archive_members"] = archive_members

        # 5. Register new machine if confirmed/created and not yet in database
        is_component = EntityExtractor.is_component_tag(tag)
        is_non_asset = any(tag.startswith(f"{p}-") for p in EntityExtractor.NON_ASSET_PREFIXES)

        if db is not None and not is_component and not is_non_asset and not db.assets.find_one({"tag": tag, "tenant_id": eff_tenant}):
            comb_lower = combined_text.lower()
            tag_u = tag.upper()

            # 1. Dynamically set Asset Type based on document context
            if "furnace" in comb_lower or "heater" in comb_lower:
                asset_type = "Furnace"
            elif tag_u.startswith("T-") or tag_u.startswith("TK-"):
                asset_type = "Cooling Tower" if "cooling tower" in comb_lower else "Process Tower"
            elif tag_u.startswith("P-"):
                asset_type = "Pump"
            elif tag_u.startswith("E-") or tag_u.startswith("HX-"):
                asset_type = "Heat Exchanger"
            elif tag_u.startswith("C-") or tag_u.startswith("K-"):
                asset_type = "Compressor"
            elif tag_u.startswith("F-") or tag_u.startswith("FN-"):
                asset_type = "Fan"
            else:
                asset_type = "Industrial Machine"
            
            asset_name = f"{tag} {asset_type}"

            # 2. Dynamically map components extracted from the text by EntityExtractor
            dynamic_comps = []
            for comp in extracted_entities.get("connected_components", []):
                dynamic_comps.append({
                    "name": comp.get("name") or comp.get("type", "Component"),
                    "part_number": comp.get("tag", "UNKNOWN"),
                    "status": "Operational" if comp.get("condition", "Normal").lower() in ("normal", "good") else "Needs Review"
                })
            
            # If the extractor found generic component names but no specific tags
            for comp_name in extracted_entities.get("component_tags", []):
                if not any(c["name"] == comp_name for c in dynamic_comps):
                    dynamic_comps.append({
                        "name": comp_name,
                        "part_number": "UNKNOWN",
                        "status": "Operational"
                    })

            new_asset = {
                "tag": tag,
                "name": asset_name,
                "asset_type": asset_type,
                "plant": "Plant A - Gulf Coast",
                "area": "Unit 2 - Fluid Processing",
                "criticality": "High",
                "status": "Operational",
                "tenant_id": eff_tenant,
                "specs": {}, 
                "components": dynamic_comps, 
                "organization": "Industrial Operations & Infrastructure",
                "sector": "Energy & Chemicals"
            }
            db.assets.insert_one(new_asset)
            try:
                neo4j_graph.add_node(f"asset_{tag.replace('-', '_')}", "Asset", {
                    "tag": tag,
                    "name": new_asset["name"],
                    "asset_type": asset_type,
                    "criticality": "High",
                    "tenant_id": eff_tenant
                })
            except Exception:
                pass

        # 6. Create Chunks with scope and multi-asset tags
        chunks = DocumentChunker.chunk_document(
            document_id=doc_id,
            asset_tag=tag,
            category=category,
            version=version,
            governance_status=governance_status,
            pages=pages,
            tenant_id=eff_tenant,
            document_scope=extracted_entities.get("document_scope", "ASSET"),
            primary_asset_tags=extracted_entities.get("primary_asset_tags", [tag]),
            related_asset_tags=extracted_entities.get("related_asset_tags", []),
            record_date=extracted_entities.get("primary_date")
        )

        # 7. Index Chunks into FAISS and Qdrant
        vector_store.add_chunks(chunks)
        try:
            qdrant_store.add_chunks(chunks)
        except Exception as q_err:
            _doc_service_logger.warning("Qdrant indexing failed for '%s': %s", doc_id, q_err)

        # --- Define record-context variables BEFORE Step 8 and Step 9 ---
        # BUG FIX: These were previously defined only in Step 9 (line ~1077)
        # but Step 8 (Neo4j) used record_target_asset at line ~980, causing
        # a silent NameError that swallowed all Neo4j graph linking.
        doc_scope = "ASSET" if explicit_override else extracted_entities.get("document_scope", "ASSET")
        record_target_asset = (
            extracted_entities.get("primary_asset_tags", [None])[0]
            if extracted_entities.get("primary_asset_tags")
            else tag
        )
        # Trust the UI Dropdown classification over the regex guess
        event_type = extracted_entities.get("event_type", "General Documentation")
        if category in ["Failure / Incident Report", "Failure Report"]:
            event_type = "Failure"
        elif category in ["Maintenance Report", "Work Order"]:
            event_type = "Maintenance"
        elif "Inspection" in category:
            event_type = "Inspection"
        norm_date = extracted_entities.get("primary_date")

        # 8. Link Document and Relationships in Neo4j
        # Failures are now LOGGED instead of silently swallowed.
        graph_link_errors = []
        try:
            # GUARANTEE parent asset node exists in the graph first!
            if record_target_asset:
                neo4j_graph.add_node(f"asset_{record_target_asset.replace('-', '_')}", "Asset", {
                    "tag": record_target_asset,
                    "name": f"{record_target_asset} Asset",
                    "tenant_id": eff_tenant
                })

            neo4j_graph.add_node(f"doc_{doc_id}", "Document", {
                "document_id": doc_id,
                "title": filename.replace("_", " ").rsplit(".", 1)[0],
                "category": category,
                "version": version,
                "governance_status": governance_status,
                "document_scope": extracted_entities.get("document_scope", "ASSET"),
                "tenant_id": eff_tenant
            })

            # Primary asset links
            primary_tags = extracted_entities.get("primary_asset_tags") or ([tag] if tag and not EntityExtractor.is_component_tag(tag) else [])
            for p_tag in primary_tags:
                neo4j_graph.add_relationship(f"asset_{p_tag.replace('-', '_')}", f"doc_{doc_id}", "ASSET_HAS_DOCUMENT")
                neo4j_graph.add_relationship(f"doc_{doc_id}", f"asset_{p_tag.replace('-', '_')}", "APPLIES_TO")

            # Related asset links for system / multi-asset documents
            for r_tag in extracted_entities.get("related_asset_tags", []):
                if r_tag not in primary_tags:
                    neo4j_graph.add_relationship(f"asset_{r_tag.replace('-', '_')}", f"doc_{doc_id}", "ASSET_HAS_DOCUMENT")
                    neo4j_graph.add_relationship(f"doc_{doc_id}", f"asset_{r_tag.replace('-', '_')}", "REFERENCES")

            # Component tags (e.g. V-194A valves)
            for comp_tag in extracted_entities.get("component_tags", []):
                neo4j_graph.add_node(f"comp_{comp_tag.replace('-', '_')}", "Component", {
                    "tag": comp_tag,
                    "type": "Valve" if comp_tag.startswith("V-") else "Instrument",
                    "tenant_id": eff_tenant
                })
                neo4j_graph.add_relationship(f"doc_{doc_id}", f"comp_{comp_tag.replace('-', '_')}", "CONTAINS_COMPONENT")

            # Explicit connected components (Generic parent-asset / component relationship)
            for cc in extracted_entities.get("connected_components", []):
                cc_tag = cc.get("tag")
                if cc_tag:
                    c_id = f"comp_{cc_tag.replace('-', '_')}"
                    comp_props = {
                        "id": c_id,
                        "tag": cc_tag,
                        "name": cc.get("type") or f"{cc_tag} Component",
                        "component_type": cc.get("type") or "Mechanical",
                        "condition": cc.get("condition", "Normal"),
                        "status": "Operational" if cc.get("condition", "Normal").lower() in ("normal", "good", "operational") else "Needs Review",
                        "source_document_id": doc_id,
                        "tenant_id": eff_tenant
                    }
                    if tag:
                        comp_props["asset_tag"] = tag
                    neo4j_graph.add_node(c_id, "Component", comp_props)

                    # Create Asset -[:HAS_COMPONENT]-> Component
                    if tag:
                        neo4j_graph.add_relationship(f"asset_{tag.replace('-', '_')}", c_id, "HAS_COMPONENT", {
                            "source_document_id": doc_id,
                            "condition": cc.get("condition", "Normal")
                        })

                    # Create Document -[:CONTAINS_COMPONENT]-> Component
                    neo4j_graph.add_relationship(f"doc_{doc_id}", c_id, "CONTAINS_COMPONENT", {
                        "component_tag": cc_tag,
                        "component_type": cc.get("type")
                    })

                    # Also register in MongoDB asset component inventory if present
                    if db is not None and tag:
                        try:
                            db.assets.update_one(
                                {"tag": tag, "tenant_id": eff_tenant},
                                {"$addToSet": {"components": {
                                    "name": comp_props["name"],
                                    "part_number": cc_tag,
                                    "status": comp_props["status"],
                                    "condition": comp_props["condition"]
                                }}}
                            )
                        except Exception as comp_err:
                            _doc_service_logger.warning(
                                "Failed to add component '%s' to MongoDB asset '%s': %s",
                                cc_tag, tag, comp_err
                            )

            # Link P&ID tags if any
            for pt in extracted_entities.get("pid_tags", []):
                t_name = pt.get("tag")
                if t_name:
                    neo4j_graph.add_node(f"tag_{t_name.replace('-', '_')}", "EquipmentTag", {"tag": t_name, "type": pt.get("type", "Instrument"), "tenant_id": eff_tenant})
                    neo4j_graph.add_relationship(f"doc_{doc_id}", f"tag_{t_name.replace('-', '_')}", "CONTAINS_TAG")

        except Exception as graph_err:
            _doc_service_logger.error(
                "[GRAPH LINK FAILURE] Neo4j/local-graph linking failed for document '%s' (asset '%s'): %s",
                doc_id, tag, graph_err
            )
            graph_link_errors.append(str(graph_err))

        # 9. Specialized Record Generation (Strictly scoped to genuine primary machine)
        # NOTE: doc_scope, record_target_asset, event_type, norm_date are defined
        # ABOVE in the pre-Step-8 block. They are already available here.

        if db is not None:
            # Telemetry CSV ingestion
            if file_type == "csv" and ("telemetry" in filename.lower() or "sensor" in filename.lower() or "vibration" in combined_text.lower()):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            row_l = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                            row_asset = row_l.get("equipment_tag") or row_l.get("asset_tag") or record_target_asset
                            ts = row_l.get("timestamp") or row_l.get("time") or row_l.get("date") or time.strftime("%Y-%m-%d %H:%M")
                            vib = float(row_l.get("vibration_rms") or row_l.get("vibration") or 0.0)
                            temp = float(row_l.get("bearing_temp_c") or row_l.get("temperature") or 0.0)
                            press = float(row_l.get("discharge_pressure_bar") or row_l.get("pressure") or 0.0)
                            rpm = float(row_l.get("rpm") or 0.0)
                            hrs = float(row_l.get("operating_hours") or row_l.get("run_hours") or 0.0)
                            db.telemetry.insert_one({
                                "asset_tag": row_asset.upper(),
                                "timestamp": ts,
                                "vibration_rms": vib,
                                "bearing_temp_c": temp,
                                "discharge_pressure_bar": press,
                                "rpm": rpm,
                                "operating_hours": hrs,
                                "is_synthetic": False,
                                "tenant_id": eff_tenant
                            })
                except Exception:
                    pass

            # Email Shift Handover ingestion
            if file_type in ["eml", "msg"]:
                try:
                    with open(file_path, "rb") as f:
                        msg = email.message_from_binary_file(f, policy=policy.default)
                    note_id = f"note_{doc_id}"
                    db.human_notes.update_one(
                        {"note_id": note_id},
                        {"$set": {
                            "note_id": note_id,
                            "asset_tag": record_target_asset,
                            "author": str(msg.get("from", "Shift Team Lead")),
                            "author_role": "Operations & Reliability Team",
                            "created_at": str(msg.get("date", time.strftime("%Y-%m-%d %H:%M"))),
                            "text": f"Subject: {msg.get('subject', 'Shift Handover')}\n{combined_text[:500]}",
                            "component": extracted_entities.get("primary_component", "Process System"),
                            "verified": True,
                            "verification_status": "Verified Shift Handover Record",
                            "tenant_id": eff_tenant
                        }},
                        upsert=True
                    )
                except Exception:
                    pass

            # Inspection report ingestion - Dynamically mapped
            if doc_scope == "ASSET" and event_type == "Inspection":
                insp_id = f"INSP-{record_target_asset.replace('-', '')}" if record_target_asset else f"INSP-{doc_id[-6:].upper()}"
                
                # Try to find actual vibration/temp numbers in text if they exist
                vib_match = re.search(r"vibration.*?(\d+\.\d+)", combined_text, re.IGNORECASE)
                temp_match = re.search(r"temperature.*?(\d+\.\d+)", combined_text, re.IGNORECASE)
                
                db.inspection_records.update_one(
                    {"inspection_id": insp_id},
                    {"$set": {
                        "inspection_id": insp_id,
                        "asset_tag": record_target_asset,
                        "date": norm_date,
                        "event_date": norm_date,
                        "event_type": "INSPECTION",
                        "technician": uploaded_by,
                        "vibration_level_mm_s": float(vib_match.group(1)) if vib_match else None,
                        "temperature_c": float(temp_match.group(1)) if temp_match else None,
                        "result": f"Inspection recorded from {filename}",
                        "document_ref": doc_id,
                        "source_document_id": doc_id,
                        "tenant_id": eff_tenant
                    }},
                    upsert=True
                )
                try:
                    neo4j_graph.add_node(f"insp_{insp_id}", "Inspection", {"inspection_id": insp_id, "asset_tag": record_target_asset, "tenant_id": eff_tenant})
                    neo4j_graph.add_relationship(f"asset_{record_target_asset.replace('-', '_')}", f"insp_{insp_id}", "HAS_INSPECTION")
                except Exception:
                    pass

            # Maintenance report ingestion - Dynamically mapped
            wo_list = extracted_entities.get("work_orders") or []
            if doc_scope == "ASSET" and event_type == "Maintenance":
                target_wos = wo_list if wo_list else [f"WO-{int(time.time())}"]
                parts = [c.get("name") or c.get("tag") for c in extracted_entities.get("connected_components", [])]
                if not parts:
                    parts = extracted_entities.get("component_tags", [])
                    
                for wo_num in target_wos:
                    rec_id = f"maint_{record_target_asset.lower().replace('-', '_')}_{wo_num.lower().replace('-', '_')}"
                    db.maintenance_records.update_one(
                        {"record_id": rec_id},
                        {"$set": {
                            "record_id": rec_id,
                            "work_order_number": wo_num,
                            "asset_tag": record_target_asset,
                            "date": norm_date,
                            "event_date": norm_date,
                            "event_type": "MAINTENANCE",
                            "description": f"Maintenance service recorded in {filename.replace('_', ' ')}",
                            "parts_replaced": parts, # Real extracted parts!
                            "technician": uploaded_by,
                            "status": "Completed",
                            "document_ref": doc_id,
                            "source_document_id": doc_id,
                            "tenant_id": eff_tenant
                        }},
                        upsert=True
                    )
                    try:
                        neo4j_graph.add_node(f"wo_{wo_num}", "WorkOrder", {"wo_number": wo_num, "asset_tag": record_target_asset, "tenant_id": eff_tenant})
                        neo4j_graph.add_relationship(f"asset_{record_target_asset.replace('-', '_')}", f"wo_{wo_num}", "HAS_WORK_ORDER")
                    except Exception:
                        pass

            # Failure incident report ingestion - Dynamically mapped
            if doc_scope == "ASSET" and event_type == "Failure":
                fail_id = f"FAIL-{record_target_asset.replace('-', '')}" if record_target_asset else f"FAIL-{doc_id[-4:].upper()}"
                
                # Determine severity based on actual text
                severity = "Medium"
                if "explosion" in combined_text.lower() or "fire" in combined_text.lower() or "catastrophic" in combined_text.lower():
                    severity = "Critical"
                elif "trip" in combined_text.lower() or "shutdown" in combined_text.lower():
                    severity = "High"

                # Pull the primary component that failed
                failed_comp = extracted_entities.get("primary_component", "Unknown Component")

                db.failures.update_one(
                    {"failure_id": fail_id},
                    {"$set": {
                        "failure_id": fail_id,
                        "asset_tag": record_target_asset,
                        "date": norm_date,
                        "event_date": norm_date,
                        "event_type": "FAILURE",
                        "title": f"Incident Report: {filename.replace('_', ' ')}",
                        "failure_mode": f"Issue involving {failed_comp}", # Real extracted failure!
                        "severity": severity,
                        "document_ref": doc_id,
                        "source_document_id": doc_id,
                        "tenant_id": eff_tenant
                    }},
                    upsert=True
                )
                try:
                    neo4j_graph.add_node(f"fail_{fail_id}", "Failure", {"failure_id": fail_id, "title": f"Incident {record_target_asset}", "tenant_id": eff_tenant})
                    neo4j_graph.add_relationship(f"asset_{record_target_asset.replace('-', '_')}", f"fail_{fail_id}", "HAD_FAILURE")
                except Exception:
                    pass

        # 10. Store in MongoDB documents
        doc_record = Document(
            document_id=doc_id,
            title=filename.replace("_", " ").rsplit(".", 1)[0],
            filename=filename,
            file_type=file_type,
            category=category,
            asset_tag=tag,
            document_scope=extracted_entities.get("document_scope", "ASSET"),
            primary_asset_tags=extracted_entities.get("primary_asset_tags", [tag]),
            related_asset_tags=extracted_entities.get("related_asset_tags", []),
            component_tags=extracted_entities.get("component_tags", []),
            document_number=extracted_entities.get("document_number"),
            model_number=extracted_entities.get("model_number"),
            extraction_confidence={"confidence": extracted_entities.get("confidence", "High")},
            evidence_snippets=extracted_entities.get("equipment_evidence", {}).get("evidence_snippets", []),
            association_status="AUTO_RESOLVED",
            version=version,
            effective_date=effective_date or norm_date,
            review_date=review_date or "2027-01-01",
            governance_status=governance_status,
            summary=combined_text[:300] + "..." if len(combined_text) > 300 else combined_text,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            uploaded_by=uploaded_by,
            upload_date=time.strftime("%Y-%m-%d %H:%M"),
            chunk_count=len(chunks),
            extracted_entities=extracted_entities,
            is_pid_drawing=is_pid,
            sha256_hash=file_hash,
            tenant_id=eff_tenant,
            ocr_engine_used="Tesseract OCR" if (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else "Text Layer Parser",
            ocr_engine_version="Tesseract 5.5.3" if (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else "Native Text Parser",
            operated_on_pixels=True if (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else False,
            ocr_confidence=pages[0].get("ocr_confidence_pct", 85.0) if pages and (file_type in ["png", "jpg", "jpeg", "tiff", "tif", "bmp"] or any(p.get("extraction_mode") == "ocr_raster_extraction" for p in pages)) else None
        )

        if db is not None:
            db.documents.update_one(
                {"document_id": doc_id},
                {"$set": doc_record.model_dump()},
                upsert=True
            )
            # Clean old chunks and save new chunks to db
            db.document_chunks.delete_many({"document_id": doc_id})
            for c in chunks:
                db.document_chunks.update_one(
                    {"chunk_id": c.chunk_id},
                    {"$set": c.model_dump()},
                    upsert=True
                )

        ret_val = doc_record.model_dump()
        ret_val["status"] = "success"
        ret_val["already_imported"] = False
        ret_val["message"] = f"Processed {len(chunks)} chunks, Linked to {tag}"
        ret_val["pid_tags_count"] = len(extracted_entities.get("pid_tags", []))
        ret_val["archive_members"] = extracted_entities.get("archive_members", [])
        if graph_link_errors:
            ret_val["graph_link_warnings"] = graph_link_errors
            _doc_service_logger.warning(
                "Document '%s' ingested but graph linking had %d error(s): %s",
                doc_id, len(graph_link_errors), graph_link_errors
            )
        return ret_val

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