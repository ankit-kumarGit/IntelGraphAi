import os
import sys
import tempfile
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import db_manager, get_db
from app.services.asset_service import asset_service
from app.services.doc_service import doc_service
from app.models.asset import AssetCreate, Component

TEST_TAG = "TEST-GENERIC-94721"

def create_generic_test_asset():
    print(f"=== Creating Generic Test Asset: {TEST_TAG} ===")
    db_manager.connect()
    db = get_db()
    if db is None:
        print("Error: Could not connect to MongoDB.")
        sys.exit(1)

    # 1. Register Asset in MongoDB
    components = [
        Component(
            id=f"{TEST_TAG}-DE",
            name="Drive-End Bearing (SKF 7315 BECBM)",
            component_type="Bearing",
            part_number="SKF-7315-BECBM",
            status="Operational",
            description="Angular contact ball bearing for thrust absorption"
        ),
        Component(
            id=f"{TEST_TAG}-NDE",
            name="Non-Drive-End Bearing (SKF NU 218 ECP)",
            component_type="Bearing",
            part_number="SKF-NU-218-ECP",
            status="Operational",
            description="Cylindrical roller bearing accommodating thermal shaft float"
        ),
        Component(
            id=f"{TEST_TAG}-SEAL",
            name="Mechanical Seal Cartridge",
            component_type="Mechanical Seal",
            part_number="JC-5620-DUAL",
            status="Operational",
            description="Dual pressurized cartridge seal (API Plan 53A)"
        )
    ]

    asset_data = AssetCreate(
        tag=TEST_TAG,
        name="Heavy-Duty Slurry Feed Process Pump",
        asset_type="Centrifugal Process Pump",
        manufacturer="FlowTech Dynamics",
        model="FT-500-HD",
        serial_number="FT-2025-94721",
        organization="Apex Industrial Energy",
        sector="Chemicals & Processing",
        plant="Plant C - Northern Complex",
        area="Unit 4 - Slurry Fractionation",
        status="Operational",
        criticality="Critical",
        description="High-reliability multi-stage slurry charge pump operating under ISO 10816-3 surveillance.",
        tenant_id="tenant_default",
        components=components
    )

    registered_asset = asset_service.create_asset(asset_data)
    print(f"Asset registered in MongoDB: {registered_asset.get('tag')} ({registered_asset.get('name')})")

    # Clean prior documents for this tag to force fresh indexing
    db.documents.delete_many({"asset_tag": TEST_TAG})
    db.document_chunks.delete_many({"asset_tag": TEST_TAG})

    # 2. Documents to Ingest
    docs_to_create = [
        # Document 1: Engineering Datasheet (OEM Manual)
        (
            f"{TEST_TAG}_Datasheet.txt",
            "OEM Manual",
            f"""FLOWTECH DYNAMICS — MODEL FT-500-HD TECHNICAL DATASHEET & MANUAL
Equipment Tag: {TEST_TAG}
Equipment Name: Heavy-Duty Slurry Feed Process Pump
Manufacturer: FlowTech Dynamics | Model: FT-500-HD | Serial Number: FT-2025-94721
Installation Location: Plant C - Northern Complex, Unit 4 - Slurry Fractionation

1. DESIGN & OPERATING SPECIFICATIONS:
- Design Flow Rate: 320 m³/h
- Total Dynamic Differential Head: 110 meters
- Rated Operating Speed: 1780 RPM
- Drive Motor: 200 kW 3-Phase Induction Motor (415V, 50Hz, Class F insulation)
- Impeller Diameter: 380 mm (High Chrome A05 Alloy)
- Approved Lubricant: ISO VG 46 Premium Mineral Turbine Oil (Capacity: 3.5 Liters)
- Continuous Bearing Housing Temperature Limit: 78°C (Alarm Trip at 85°C)
- Vibration Baseline: ISO 10816-3 Class II (Normal: < 2.8 mm/s RMS, Warning: 4.5 mm/s RMS, Shutdown: 7.1 mm/s RMS)

2. BEARING & SHAFT ARRANGEMENT:
- Drive-End (DE) Bearing: SKF 7315 BECBM Angular Contact Ball Bearing (Duplex Back-to-Back)
- Non-Drive-End (NDE) Bearing: SKF NU 218 ECP Cylindrical Roller Bearing
- Radial Internal Clearance: 0.04 mm to 0.07 mm
- Maximum Permissible Dynamic Shaft Runout: 0.025 mm TIR at seal chamber face
- Mechanical Seal: John Crane Type 5620 Dual Cartridge Seal with Plan 53A barrier fluid loop
"""
        ),

        # Document 2: Inspection Survey Report
        (
            f"{TEST_TAG}_Inspection.txt",
            "Inspection",
            f"""CONDITION MONITORING & VIBRATION SURVEY REPORT
Asset Tag: {TEST_TAG}
Survey Date: 2025-08-14
Survey Type: Comprehensive Vibration & Thermal Diagnostic Screening
Certified Vibration Analyst: Marcus Vance (ISO 18436 Category III)
Governance Status: Approved

1. MEASURED PARAMETERS & OBSERVATIONS:
- Survey Inspection Date: 2025-08-14
- Drive-End (DE) Vibration: 2.1 mm/s RMS Velocity (Horizontal) — ISO Class I/II Acceptable
- Drive-End (DE) Axial Vibration: 1.4 mm/s RMS Velocity
- Non-Drive-End (NDE) Vibration: 1.8 mm/s RMS Velocity
- Peak Bearing Temperature: DE 62.4°C, NDE 58.1°C (Well within 78°C limit)
- Fast Fourier Transform (FFT) Spectral Analysis: 1X rotational peak dominant at 29.6 Hz (1780 RPM); zero high-frequency demodulated bearing defect frequencies (BPFO/BPFI).
- Lubricant Appearance: Clear, amber, zero particulate foaming or water emulsification.
- Overall Condition Assessment: Machine condition is Normal and approved for continuous unconstrained duty.
"""
        ),

        # Document 3: Maintenance Record
        (
            f"{TEST_TAG}_Maintenance.txt",
            "Maintenance",
            f"""PREVENTIVE & CORRECTIVE MAINTENANCE WORK ORDER RECORD
Asset Tag: {TEST_TAG}
Work Order Number: WO-94721-M1
Maintenance Execution Date: 2025-07-10
Lead Maintenance Engineer: David Chen
Governance Status: Approved

1. WORK ORDER SUMMARY & EXECUTED TASKS:
- Maintenance Date: 2025-07-10
- Sump Oil Flush & Replenishment: Drained old lubricant, flushed reservoir with Mobil Pegasus, and refilled with 3.5 Liters of fresh ISO VG 46 mineral turbine oil.
- Laser Shaft Alignment: Verified cold alignment between 200 kW motor and pump shaft. Horizontal angularity adjusted to 0.02 mm/100mm, parallel offset to 0.03 mm TIR.
- Seal Barrier Fluid Servicing: Barrier reservoir pressurized to 3.2 bar with synthetic barrier fluid; zero leakage detected.
- Fastener Torque Verification: Casing stud torque verified to 140 Nm; bearing housing cap bolts torqued to 95 Nm per FlowTech specifications.
"""
        ),

        # Document 4: Failure & Incident History
        (
            f"{TEST_TAG}_Failure.txt",
            "Incident",
            f"""INCIDENT INVESTIGATION & ROOT CAUSE ANALYSIS (RCA) REPORT
Asset Tag: {TEST_TAG}
Incident Date: 2024-11-03
Report Number: RCA-94721-01
Lead Investigator: Dr. Aris Thorne (Reliability Engineering)
Governance Status: Approved

1. INCIDENT TIMELINE & FAILURE MODE:
- Incident Date: 2024-11-03
- Failure Mode: Mechanical seal face catastrophic thermal cracking and high-pressure process slurry leakage.
- Unplanned Plant Downtime: 14.5 hours.

2. ROOT CAUSE ANALYSIS (RCA) FINDINGS:
- Direct Cause: Severe thermal dry running of the inner seal silicon carbide faces.
- Root Cause: Upstream particulate clogging in the 6 mm seal flush plan orifice restricted cooling barrier flow. The lack of flow differential instrumentation allowed heat build-up to go unnoticed until seal face failure.

3. CORRECTIVE & PREVENTATIVE ACTIONS:
- Replaced failed mechanical seal cartridge with John Crane Type 5620 dual cartridge assembly.
- Upgraded flush piping to 316SS with dual cyclone abrasive separators.
- Installed Rosemount differential pressure transmitter across flush loop with safety interlock alarm at 1.5 bar differential.
"""
        ),

        # Document 5: Telemetry CSV (Notice: 50 repetitive rows where TEST-GENERIC-94721 occurs on every line!)
        (
            f"{TEST_TAG}_Telemetry.csv",
            "Telemetry",
            "\n".join([
                "timestamp,equipment_tag,vibration_rms,bearing_temp_c,discharge_pressure_bar,rpm,operating_hours"
            ] + [
                f"2025-09-01T{h:02d}:00:00Z,{TEST_TAG},{round(2.10 + (h % 5) * 0.05, 2)},{round(61.0 + (h % 6) * 0.4, 1)},{round(8.2 + (h % 3) * 0.1, 1)},1780,{4200 + h}"
                for h in range(50)
            ])
        )
    ]

    for filename, cat, content in docs_to_create:
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, mode="w", delete=False) as tf:
            tf.write(content)
            tmp_path = Path(tf.name)

        print(f"Ingesting {filename} (Category: {cat})...")
        res = doc_service.process_and_save_document(
            file_path=tmp_path,
            filename=filename,
            asset_tag=TEST_TAG,
            category=cat,
            version="v1.0",
            governance_status="Approved",
            tenant_id="tenant_default",
            explicit_override=True,
            create_missing_machine=True
        )
        print(f"-> Result: {res.get('status')} | Chunks: {res.get('chunk_count')} | Doc ID: {res.get('document_id')}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    print(f"\nAll 5 documents successfully indexed for generic asset: {TEST_TAG}")

if __name__ == "__main__":
    create_generic_test_asset()
