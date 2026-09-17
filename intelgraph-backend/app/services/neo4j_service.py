import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

logger = logging.getLogger("intelgraph.neo4j")

class Neo4jKnowledgeGraph:
    """
    Industrial Knowledge Graph Service.
    Connects to Neo4j database if available, or falls back to an embedded
    persistent Cypher-compatible graph store to ensure 100% offline availability.
    """
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "intelgraph2026")
        self.driver = None
        self.connected_to_live_neo4j = False
        
        # Local persistent fallback graph store
        self.storage_file = Path(__file__).resolve().parent.parent.parent / "storage" / "neo4j_graph.json"
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []

        self.initialize_connection()

    def initialize_connection(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()["test"] == 1:
                    self.connected_to_live_neo4j = True
                    logger.info("Connected successfully to active Neo4j cluster at %s", self.uri)
                    return
        except Exception as e:
            logger.info("Live Neo4j instance not reachable (%s). Utilizing embedded persistent graph engine.", str(e))
            self.connected_to_live_neo4j = False

        self.load_local_graph()

    def load_local_graph(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r") as f:
                    data = json.load(f)
                    self.nodes = data.get("nodes", {})
                    self.relationships = data.get("relationships", [])
            except Exception as e:
                logger.error("Failed to load local graph store: %s", e)

    def save_local_graph(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump({
                    "nodes": self.nodes,
                    "relationships": self.relationships
                }, f, indent=2)
        except Exception as e:
            logger.error("Failed to persist local graph store: %s", e)

    def add_node(self, node_id: str, label: str, properties: Dict[str, Any]):
        if self.connected_to_live_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    props_cypher = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
                    cypher = f"MERGE (n:{label} {{id: $node_id}}) ON CREATE SET {props_cypher} ON MATCH SET {props_cypher}"
                    params = dict(properties, node_id=node_id)
                    session.run(cypher, params)
                    return
            except Exception as e:
                logger.warning("Neo4j node write failed, falling back to local: %s", e)

        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "properties": properties
        }
        self.save_local_graph()

    def delete_node(self, node_id: str):
        if self.connected_to_live_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    cypher = "MATCH (n {id: $node_id}) DETACH DELETE n"
                    session.run(cypher, node_id=node_id)
            except Exception as e:
                logger.warning("Neo4j node delete failed: %s", e)

        if node_id in self.nodes:
            del self.nodes[node_id]
        self.relationships = [r for r in self.relationships if r["from"] != node_id and r["to"] != node_id]
        self.save_local_graph()

    def count_subgraph(self, asset_tag: str) -> Dict[str, int]:
        clean_tag = asset_tag.upper()
        clean_tag_norm = clean_tag.replace("-", "_")
        asset_id_candidates = {
            f"asset_{clean_tag_norm}",
            f"asset_{clean_tag}",
            clean_tag
        }
        for nid, node in self.nodes.items():
            if node.get("label") == "Asset" and node.get("properties", {}).get("tag", "").upper() == clean_tag:
                asset_id_candidates.add(nid)

        connected_nodes = set()
        connected_rels = 0
        for r in self.relationships:
            if r["from"] in asset_id_candidates or r["to"] in asset_id_candidates:
                connected_rels += 1
                target = r["to"] if r["from"] in asset_id_candidates else r["from"]
                connected_nodes.add(target)
        for aid in asset_id_candidates:
            if aid in self.nodes:
                connected_nodes.add(aid)
        return {
            "node_count": len(connected_nodes),
            "edge_count": connected_rels
        }

    def delete_asset_subgraph(self, asset_tag: str) -> Dict[str, int]:
        clean_tag = asset_tag.upper()
        clean_tag_norm = clean_tag.replace("-", "_")
        asset_id_candidates = {
            f"asset_{clean_tag_norm}",
            f"asset_{clean_tag}",
            clean_tag
        }
        
        # Also find any Asset node with matching tag property
        for nid, node in list(self.nodes.items()):
            if node.get("label") == "Asset" and node.get("properties", {}).get("tag", "").upper() == clean_tag:
                asset_id_candidates.add(nid)

        # 1. Identify relationships directly attached to these asset candidates
        adjacent_node_ids = set()
        for r in self.relationships:
            if r["from"] in asset_id_candidates:
                adjacent_node_ids.add(r["to"])
            elif r["to"] in asset_id_candidates:
                adjacent_node_ids.add(r["from"])
        
        # 2. Identify which adjacent nodes are exclusive to this asset vs shared/ontology
        nodes_to_delete = set(asset_id_candidates)
        for nid in adjacent_node_ids:
            if nid not in self.nodes:
                continue
            node = self.nodes[nid]
            label = node.get("label", "")
            props = node.get("properties", {})
            
            # Strict protection: do NOT delete global ontology concepts or standards
            if label in ["OntologyConcept", "Standard", "Regulation", "EquipmentClass", "Manufacturer"]:
                continue
            if props.get("is_global") or props.get("is_ontology"):
                continue
            
            # Strict protection: do NOT delete nodes linked to other assets
            has_other_relationships = any(
                (r["from"] == nid and r["to"] not in asset_id_candidates) or
                (r["to"] == nid and r["from"] not in asset_id_candidates)
                for r in self.relationships
            )
            if has_other_relationships:
                continue
            
            # Node belongs exclusively to this asset
            if (
                props.get("asset_tag") == clean_tag or
                props.get("asset_tag") == clean_tag_norm or
                props.get("document_id", "").startswith(clean_tag) or
                nid.startswith(f"doc_{clean_tag}") or
                nid.startswith(f"doc_{clean_tag_norm}") or
                nid.startswith(f"wo_{clean_tag}") or
                nid.startswith(f"insp_{clean_tag}") or
                nid.startswith(f"fail_{clean_tag}") or
                nid == f"tag_{clean_tag}" or
                not has_other_relationships
            ):
                nodes_to_delete.add(nid)

        # Execute Live Neo4j cleanup if connected
        if self.connected_to_live_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    for aid in asset_id_candidates:
                        session.run("MATCH (a {id: $asset_id})-[r]-() DELETE r", asset_id=aid)
                        session.run("MATCH (a {id: $asset_id}) DELETE a", asset_id=aid)
                    for nid in nodes_to_delete:
                        if nid not in asset_id_candidates:
                            session.run("MATCH (n {id: $nid}) DETACH DELETE n", nid=nid)
            except Exception as e:
                logger.warning("Neo4j subgraph deletion failed: %s", e)

        # Remove local nodes
        deleted_node_count = 0
        for nid in nodes_to_delete:
            if nid in self.nodes:
                del self.nodes[nid]
                deleted_node_count += 1
        
        # Remove all relationships connected to deleted nodes or asset candidates
        initial_rel_count = len(self.relationships)
        self.relationships = [
            r for r in self.relationships
            if r["from"] not in nodes_to_delete and r["to"] not in nodes_to_delete and
               r["from"] not in asset_id_candidates and r["to"] not in asset_id_candidates
        ]
        deleted_rel_count = initial_rel_count - len(self.relationships)
        self.save_local_graph()
        
        return {
            "deleted_nodes": deleted_node_count,
            "deleted_relationships": deleted_rel_count
        }

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        props = properties or {}
        if self.connected_to_live_neo4j and self.driver:
            try:
                with self.driver.session() as session:
                    cypher = (
                        f"MATCH (a {{id: $from_id}}), (b {{id: $to_id}}) "
                        f"MERGE (a)-[r:{rel_type}]->(b) "
                        f"SET r += $props"
                    )
                    session.run(cypher, from_id=from_id, to_id=to_id, props=props)
                    return
            except Exception as e:
                logger.warning("Neo4j relationship write failed: %s", e)

        # Local graph relationship
        existing = any(
            r["from"] == from_id and r["to"] == to_id and r["type"] == rel_type
            for r in self.relationships
        )
        if not existing:
            self.relationships.append({
                "from": from_id,
                "to": to_id,
                "type": rel_type,
                "properties": props
            })
            self.save_local_graph()

    def get_subgraph(self, asset_tag: str, max_depth: int = 2, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves directional subgraph centered around an asset.
        """
        asset_id = f"asset_{asset_tag.upper().replace('-', '_')}"
        if asset_id not in self.nodes:
            # Check if raw tag exists
            for nid, n in self.nodes.items():
                if n["properties"].get("tag", "").upper() == asset_tag.upper():
                    asset_id = nid
                    break

        # Check tenant match on target asset
        default_tenant = getattr(settings, "DEFAULT_TENANT_ID", "tenant_default")
        if asset_id in self.nodes and tenant_id:
            node_tenant = self.nodes[asset_id]["properties"].get("tenant_id", default_tenant)
            if node_tenant != tenant_id and node_tenant != "global":
                return {
                    "asset_tag": asset_tag,
                    "connected_to_neo4j": self.connected_to_live_neo4j,
                    "nodes": [],
                    "edges": [],
                    "node_count": 0,
                    "edge_count": 0
                }

        matched_node_ids = {asset_id} if asset_id in self.nodes else set()
        matched_links = []

        # Depth 1 traversal
        current_level = set(matched_node_ids)
        visited_rel_keys = set()
        for _ in range(max_depth):
            next_level = set()
            for r in self.relationships:
                rel_key = (r["from"], r["to"], r["type"])
                if rel_key in visited_rel_keys:
                    continue
                if r["from"] in current_level:
                    matched_links.append(r)
                    visited_rel_keys.add(rel_key)
                    next_level.add(r["to"])
                elif r["to"] in current_level:
                    matched_links.append(r)
                    visited_rel_keys.add(rel_key)
                    next_level.add(r["from"])
            matched_node_ids.update(next_level)
            current_level = next_level

        nodes_list = [self.nodes[nid] for nid in matched_node_ids if nid in self.nodes]
        if tenant_id:
            nodes_list = [
                n for n in nodes_list
                if n["properties"].get("tenant_id", default_tenant) in [tenant_id, "global"]
                or n.get("label") in ["OntologyConcept", "Standard", "Regulation", "EquipmentClass", "Manufacturer"]
            ]

        return {
            "asset_tag": asset_tag,
            "connected_to_neo4j": self.connected_to_live_neo4j,
            "nodes": nodes_list,
            "edges": matched_links,
            "node_count": len(nodes_list),
            "edge_count": len(matched_links)
        }

    def multi_hop_evidence_traversal(
        self,
        asset_tag: str,
        target_component: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        GraphRAG dynamic multi-hop traversal:
        Asset -> HAS_COMPONENT -> Component -> HAD_FAILURE -> Failure
        Component -> HAS_INSPECTION -> Inspection
        Component -> HAS_WORK_ORDER -> WorkOrder
        Asset -> GOVERNED_BY -> Procedure / OEM Manual
        """
        asset_subgraph = self.get_subgraph(asset_tag, max_depth=2, tenant_id=tenant_id)
        nodes_by_id = {n["id"]: n for n in asset_subgraph["nodes"]}
        evidence_chains = []

        for edge in asset_subgraph["edges"]:
            source_node = nodes_by_id.get(edge["from"])
            target_node = nodes_by_id.get(edge["to"])
            if not source_node or not target_node:
                continue

            rel_type = edge["type"]
            chain = {
                "source": {
                    "id": source_node["id"],
                    "label": source_node["label"],
                    "name": source_node["properties"].get("name") or source_node["properties"].get("title") or source_node["id"]
                },
                "relationship": rel_type,
                "target": {
                    "id": target_node["id"],
                    "label": target_node["label"],
                    "name": target_node["properties"].get("name") or target_node["properties"].get("title") or target_node["id"]
                },
                "properties": edge["properties"]
            }
            evidence_chains.append(chain)

        return evidence_chains

    def get_fleet_cross_asset_links(self, component_type: str = "Bearing") -> List[Dict[str, Any]]:
        """
        Discovers cross-asset patterns across P-101, P-102, P-203, P-307
        sharing similar failure modes or component issues.
        """
        pattern_matches = []
        for r in self.relationships:
            if r["type"] in ["HAD_FAILURE", "FAILED_COMPONENT", "SIMILAR_FAILURE"]:
                from_node = self.nodes.get(r["from"], {})
                to_node = self.nodes.get(r["to"], {})
                pattern_matches.append({
                    "relationship": r["type"],
                    "source": from_node.get("properties", {}),
                    "target": to_node.get("properties", {}),
                    "properties": r["properties"]
                })
        return pattern_matches

neo4j_graph = Neo4jKnowledgeGraph()
neo4j_kg = neo4j_graph
