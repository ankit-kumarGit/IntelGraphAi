from typing import Dict, Any, List
from app.database import get_db

class KnowledgeMapService:
    @staticmethod
    def get_asset_knowledge_map(asset_tag: str) -> Dict[str, Any]:
        """
        Builds the visible interactive knowledge graph representing:
        Asset -> Component -> Document -> Maintenance -> Inspection -> Failure -> Procedure
        """
        db = get_db()
        if db is None:
            return {"nodes": [], "links": []}

        asset = db.assets.find_one({"tag": asset_tag.upper()})
        if not asset:
            return {"nodes": [], "links": []}

        nodes = []
        links = []
        node_ids = set()

        def add_node(nid: str, label: str, ntype: str, status: str = "normal", details: str = "", metadata: dict = None):
            if nid not in node_ids:
                node_ids.add(nid)
                nodes.append({
                    "id": nid,
                    "label": label,
                    "type": ntype,
                    "status": status,
                    "details": details,
                    "metadata": metadata or {}
                })

        def add_link(source: str, target: str, rel: str):
            if source in node_ids and target in node_ids:
                links.append({
                    "source": source,
                    "target": target,
                    "relationship": rel
                })

        # 1. Root Asset Node
        root_id = f"asset_{asset['tag']}"
        add_node(
            nid=root_id,
            label=f"{asset['tag']} ({asset.get('name', 'Asset')})",
            ntype="asset",
            status=asset.get("status", "Operational"),
            details=f"{asset.get('manufacturer')} {asset.get('model')} - {asset.get('plant')}",
            metadata={"tag": asset["tag"], "type": asset.get("asset_type")}
        )

        # 2. Components
        components = asset.get("components", [])
        for c in components:
            cid = f"comp_{c.get('id', c.get('name'))}"
            add_node(
                nid=cid,
                label=c.get("name", "Component"),
                ntype="component",
                status=c.get("status", "Operational"),
                details=c.get("description", "Mechanical component"),
                metadata=c
            )
            add_link(root_id, cid, "has_component")

        # 3. Documents
        docs = list(db.documents.find({"asset_tag": asset["tag"]}))
        for d in docs:
            d["_id"] = str(d.get("_id", ""))
            did = f"doc_{d['document_id']}"
            is_proc = d.get("category") in ["SOP", "Safety", "Operating Procedure"]
            ntype = "procedure" if is_proc else "document"
            add_node(
                nid=did,
                label=f"{d.get('title', d['document_id'])} ({d.get('version', 'v1.0')})",
                ntype=ntype,
                status=d.get("governance_status", "Approved"),
                details=f"{d.get('category')} - Effective: {d.get('effective_date', 'N/A')}",
                metadata={"document_id": d["document_id"], "version": d.get("version"), "category": d.get("category")}
            )
            rel = "governed_by_procedure" if is_proc else "has_document"
            add_link(root_id, did, rel)

        # 4. Maintenance Records
        maints = list(db.maintenance_records.find({"asset_tag": asset["tag"]}))
        for m in maints:
            m["_id"] = str(m.get("_id", ""))
            mid = f"maint_{m['record_id']}"
            add_node(
                nid=mid,
                label=f"{m['work_order_number']} ({m.get('date')})",
                ntype="maintenance",
                status=m.get("status", "Completed"),
                details=m.get("description", "Maintenance event"),
                metadata={"work_order_number": m.get("work_order_number"), "date": m.get("date"), "description": m.get("description")}
            )
            add_link(root_id, mid, "has_maintenance")
            
            # Connect to replaced components
            for rep in m.get("components_replaced", []):
                for c in components:
                    if rep.lower() in c.get("name", "").lower():
                        cid = f"comp_{c.get('id', c.get('name'))}"
                        add_link(mid, cid, "replaced_component")

        # 5. Inspection Records
        insps = list(db.inspection_records.find({"asset_tag": asset["tag"]}))
        for insp in insps:
            insp["_id"] = str(insp.get("_id", ""))
            iid = f"insp_{insp['inspection_id']}"
            add_node(
                nid=iid,
                label=f"{insp['inspection_id']} ({insp.get('date')})",
                ntype="inspection",
                status=insp.get("result", "Passed"),
                details=insp.get("observations", "Inspection record"),
                metadata={"inspection_id": insp.get("inspection_id"), "date": insp.get("date"), "result": insp.get("result")}
            )
            add_link(root_id, iid, "has_inspection")

        # 6. Failures
        fails = list(db.failures.find({"asset_tag": asset["tag"]}))
        for f in fails:
            f["_id"] = str(f.get("_id", ""))
            fid = f"fail_{f['failure_id']}"
            add_node(
                nid=fid,
                label=f"Failure: {f.get('title', f.get('failure_mode'))}",
                ntype="failure",
                status=f.get("severity", "High"),
                details=f"{f.get('failure_mode')} - Downtime: {f.get('downtime_hours', 0)}h",
                metadata={"failure_id": f.get("failure_id"), "date": f.get("date"), "failure_mode": f.get("failure_mode")}
            )
            add_link(root_id, fid, "experienced_failure")
            
            # Link failure to specific component if matches
            for c in components:
                if f.get("component", "").lower() in c.get("name", "").lower():
                    cid = f"comp_{c.get('id', c.get('name'))}"
                    add_link(fid, cid, "failed_component")

        return {
            "asset_tag": asset["tag"],
            "nodes": nodes,
            "links": links
        }

knowledge_map_service = KnowledgeMapService()
