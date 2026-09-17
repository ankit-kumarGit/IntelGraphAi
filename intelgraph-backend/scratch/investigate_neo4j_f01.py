"""Investigation: Query Neo4j for F-01 relationships and properties."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.neo4j_service import neo4j_kg

print("=" * 60)
print("NEO4J F-01 INVESTIGATION")
print("=" * 60)

try:
    with neo4j_kg.driver.session() as session:
        # 1. Check if F-01 asset node exists
        result = session.run(
            "MATCH (n {tag: $tag}) RETURN n, labels(n) as labels",
            tag="F-01"
        )
        records = list(result)
        if records:
            for r in records:
                print(f"Node found: labels={r['labels']}")
                print(f"Properties: {dict(r['n'])}")
        else:
            print("F-01 node NOT FOUND in Neo4j")

        print()
        print("--- F-01 RELATIONSHIPS ---")
        result2 = session.run(
            """MATCH (n)-[r]-(m) 
               WHERE n.tag = $tag OR m.tag = $tag
               RETURN n.tag as from_tag, type(r) as rel_type, m.tag as to_tag, 
                      labels(n) as from_labels, labels(m) as to_labels
               LIMIT 30""",
            tag="F-01"
        )
        rels = list(result2)
        if rels:
            for r in rels:
                print(f"  ({r['from_tag']}) -[{r['rel_type']}]-> ({r['to_tag']})")
        else:
            print("No relationships for F-01 in Neo4j")

        print()
        print("--- ALL ASSET NODES IN NEO4J ---")
        result3 = session.run(
            "MATCH (n:Asset) RETURN n.tag as tag, n.name as name LIMIT 50"
        )
        for r in result3:
            print(f"  tag={r['tag']} | name={r['name']}")

        print()
        print("--- DOCUMENT NODES IN NEO4J ---")
        result4 = session.run(
            "MATCH (n:Document) RETURN n.document_id as doc_id, n.category as cat LIMIT 20"
        )
        for r in result4:
            print(f"  doc_id={r['doc_id']} | category={r['cat']}")

except Exception as e:
    print(f"Neo4j query error: {e}")
    import traceback
    traceback.print_exc()
