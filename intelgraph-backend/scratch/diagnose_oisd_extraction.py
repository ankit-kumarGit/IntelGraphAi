"""Diagnose: What does the entity extractor do with an OISD furnace document that references F-01?"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.document_processing.entity_extractor import EntityExtractor
from app.services.machine_resolution_service import MachineResolutionService

# Simulate OISD-style incident report text (furnace incident narrative mentioning F-01 in body)
SAMPLE_OISD_TEXT = """
This Case Study is based on the Investigation report done by OISD and published
in the OISD Safety Case Studies.

CASE STUDY: FIRE IN A REFINERY FURNACE

Incident Summary:
On 15th October 2024, a fire broke out in the furnace section of a petroleum
refinery. The furnace F-01 was in operation when abnormal vibration was detected
in the combustion chamber. The furnace, designated F-01, was processing heavy
crude feedstock at approximately 380 degrees C.

Root Cause Analysis:
The investigation identified that furnace F-01 had a tube failure due to high
temperature oxidation. The furnace F-01 had been operating for 18 months
without a scheduled inspection.

Process Description:
The fired heater F-01 processes crude feedstock. The outlet temperature of
F-01 is controlled by burner management system (BMS).

Recommendations:
1. All fired heaters similar to F-01 should undergo annual tube thickness measurement.
2. Implement online monitoring for F-01 type furnaces.

OISD Standard Reference: OISD-STD-116 (Process Design and Operating Philosophies)
"""

print("=" * 60)
print("ENTITY EXTRACTION TEST: OISD FURNACE DOCUMENT")
print("=" * 60)

# Test 1: What does extract_document_equipment_evidence return?
evidence = EntityExtractor.extract_document_equipment_evidence(
    SAMPLE_OISD_TEXT,
    filename="1736421689_bf2c01e78c6a523ee694.pdf"
)
print("\n--- extract_document_equipment_evidence() ---")
print(f"document_scope: {evidence['document_scope']}")
print(f"primary_asset_tags: {evidence['primary_asset_tags']}")
print(f"related_asset_tags: {evidence['related_asset_tags']}")
print(f"component_tags: {evidence['component_tags']}")
print(f"confidence: {evidence['confidence']}")
print(f"detection_method: {evidence['detection_method']}")
print(f"evidence_snippets: {evidence['evidence_snippets']}")
print(f"distinct_tags: {evidence['distinct_tags']}")

print()
print("--- Machine Resolution ---")
resolution = MachineResolutionService.resolve_machine_association(
    text=SAMPLE_OISD_TEXT,
    filename="1736421689_bf2c01e78c6a523ee694.pdf",
    hint_tag=None,
    tenant_id="tenant_default"
)
print(f"status: {resolution['status']}")
print(f"resolved_tag: {resolution.get('resolved_tag')}")
print(f"detected_tags: {resolution.get('detected_tags')}")
print(f"confidence: {resolution.get('confidence')}")
print(f"message: {resolution.get('message')}")
print(f"requires_review: {resolution.get('requires_review')}")

# Test 2: What about clean_tag on "F-01"?
print()
print("--- clean_tag tests ---")
print(f"clean_tag('F-01'): {EntityExtractor.clean_tag('F-01')}")
print(f"is_component_tag('F-01'): {EntityExtractor.is_component_tag('F-01')}")
print(f"'F' in NON_ASSET_PREFIXES: {'F' in EntityExtractor.NON_ASSET_PREFIXES}")

# Test 3: What tags does body extraction find?
print()
print("--- Body tag extraction ---")
import re
body_matches = re.findall(r"\b([A-Z]{1,10}(?:-[A-Z]{1,10})*-\d{1,5}[A-Z0-9]*)\b", SAMPLE_OISD_TEXT, re.IGNORECASE)
print(f"Raw body matches: {body_matches}")
for b in body_matches:
    cleaned = EntityExtractor.clean_tag(b)
    is_comp = EntityExtractor.is_component_tag(b.upper()) if cleaned else False
    print(f"  '{b}' -> clean='{cleaned}', is_component={is_comp}")
