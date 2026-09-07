import os
from pathlib import Path
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.config import SAMPLE_FILES_DIR, UPLOADS_DIR
from app.database import get_db, db_manager
from app.services.doc_service import doc_service
from app.services.asset_service import asset_service
from app.services.audit_service import audit_service
from app.models.asset import AssetCreate, Component
from app.models.maintenance import MaintenanceRecord, InspectionRecord, FailureRecord, Finding, TelemetryPoint
from app.models.compliance import ComplianceRequirement
from app.models.notes import HumanNote

def create_pdf(filepath: Path, title: str, pages_content: list[tuple[str, list[str]]]):
    c = canvas.Canvas(str(filepath), pagesize=letter)
    width, height = letter
    for page_title, lines in pages_content:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(54, height - 54, title)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(54, height - 76, f"Section: {page_title}")
        c.setLineWidth(0.5)
        c.line(54, height - 82, width - 54, height - 82)
        
        c.setFont("Helvetica", 10)
        y = height - 105
        for line in lines:
            c.drawString(54, y, line)
            y -= 15
            if y < 60:
                break
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(54, 35, "CONFIDENTIAL & PROPRIETARY - APEX INDUSTRIAL ENERGY OPERATIONS")
        c.showPage()
    c.save()

def seed_database():
    db_manager.connect()
    db = get_db()
    if db is None:
        print("Warning: MongoDB not reachable during seed.")
        return

    print("Clearing collections...")
    db.assets.delete_many({})
    db.documents.delete_many({})
    db.document_chunks.delete_many({})
    db.maintenance_records.delete_many({})
    db.inspection_records.delete_many({})
    db.failures.delete_many({})
    db.findings.delete_many({})
    db.telemetry.delete_many({})
    db.compliance_requirements.delete_many({})
    db.human_notes.delete_many({})
    db.audit_logs.delete_many({})

    # 1. Generate Synthetic PDF Files
    print("Generating synthetic industrial documents...")

    # P-101 OEM Manual
    oem_pdf = SAMPLE_FILES_DIR / "Pump_P101_OEM_Manual.pdf"
    create_pdf(
        oem_pdf,
        "ABC PUMPS - MODEL XYZ-200 TECHNICAL MANUAL",
        [
            ("1. Technical Specifications", [
                "Equipment Tag: P-101 (Centrifugal Water Injection Pump)",
                "Manufacturer: ABC Pumps Inc. | Model: XYZ-200 Heavy Duty",
                "Design Flow Rate: 180 m3/h | Total Dynamic Head: 45 meters",
                "Operating Speed: 2950 RPM | Impeller Diameter: 240 mm",
                "Drive Motor: 75 kW Induction Motor (3-phase, 415V, 50Hz)",
                "Installation Location: Plant A, Unit 2 - Fluid Processing Line"
            ]),
            ("2. Bearing Specifications & Clearances", [
                "Drive-End (DE) Bearing: Deep Groove Ball Bearing SKF 6312 C3",
                "Non-Drive-End (NDE) Bearing: Cylindrical Roller Bearing NU 312",
                "Recommended Radial Internal Clearance: 0.05 mm to 0.08 mm",
                "Maximum Permissible Axial Float: 0.12 mm",
                "Shaft Runout Tolerance: Less than 0.03 mm TIR at coupling hub",
                "Torque Limits: Casing bolts 120 Nm, Bearing housing bolts 85 Nm"
            ]),
            ("3. Lubrication & Operating Limits", [
                "Approved Lubricant: ISO VG 46 Premium Synthetic Turbine Oil",
                "Lubrication Sump Capacity: 2.4 Liters",
                "Relubrication Interval: Every 4,000 operating hours or 6 months",
                "Maximum Continuous Bearing Housing Temperature: 82°C (180°F)",
                "Vibration Limit Baseline: ISO 10816-3 Class II pumps",
                "Vibration Warning Threshold: 4.5 mm/s RMS (Velocity)",
                "Vibration Trip / Shutdown Threshold: 9.0 mm/s RMS (Velocity)"
            ])
        ]
    )

    # P-101 SOP
    sop_pdf = SAMPLE_FILES_DIR / "SOP-101_Centrifugal_Pump_Operation.pdf"
    create_pdf(
        sop_pdf,
        "STANDARD OPERATING PROCEDURE: PUMP P-101",
        [
            ("1. Purpose & Scope", [
                "Document ID: SOP-101 | Version: v3.0 (Approved)",
                "Effective Date: 15 January 2023 | Review Date: 15 January 2027",
                "Applies to: P-101 and P-102 Centrifugal Pumps in Unit 2",
                "Mandatory PPE: Safety Glasses, Steel-Toe Boots, Hearing Protection, Nomex Coveralls"
            ]),
            ("2. Pre-Start Checks & Safety LOTO", [
                "Step 1: Verify Lockout/Tagout (LOTO) isolation status before opening casing.",
                "Step 2: Inspect bearing housing oil level in sight glass (center of red mark).",
                "Step 3: Confirm lubricant is clean ISO VG 46 oil free from moisture emulsification.",
                "Step 4: Rotate pump shaft by hand to verify smooth rotation without binding.",
                "Step 5: Ensure suction isolation valve is 100% OPEN before motor energization."
            ]),
            ("3. Alignment Verification Procedure", [
                "Step 6: Use dial indicators or laser alignment tool across flexible coupling.",
                "Step 7: Maximum allowable radial angular misalignment: 0.05 mm.",
                "Step 8: Check casing soft foot before tightening foundation anchor bolts.",
                "Step 9: Monitor initial vibration for 30 minutes following restart. Stop if > 4.5 mm/s."
            ])
        ]
    )

    # 2024 Maintenance Report
    maint_2024_pdf = SAMPLE_FILES_DIR / "P101_Maintenance_Report_March_2024.pdf"
    create_pdf(
        maint_2024_pdf,
        "WORK ORDER REPORT #1023 - PREVENTIVE OVERHAUL",
        [
            ("Work Order Details", [
                "Work Order Number: WO-1023 | Asset Tag: P-101",
                "Date Executed: 12 March 2024 | Lead Technician: M. Vance",
                "Operating Hours at Service: 12,450 Hours",
                "Scope: Scheduled 12,000-hour major preventive overhaul and inspection.",
                "Actions Taken: Disassembled pump wet end and bearing cartridge.",
                "Replaced Components: Drive-End Bearing (SKF 6312) and mechanical seal faces.",
                "Installed new synthetic lubricant ISO VG 46 (2.4 L).",
                "Test Run: Baseline vibration measured at 2.2 mm/s RMS. Return to service approved."
            ])
        ]
    )

    # 2025 Inspection Report
    insp_2025_pdf = SAMPLE_FILES_DIR / "P101_Inspection_Report_Aug_2025.pdf"
    create_pdf(
        insp_2025_pdf,
        "CONDITION MONITORING INSPECTION REPORT #456",
        [
            ("Condition Monitoring Log", [
                "Inspection ID: INSP-456 | Asset Tag: P-101",
                "Date: 15 August 2025 | Inspector: R. Jenkins (Reliability Lead)",
                "Inspection Type: Routine Vibration Spectrum & Thermographic Survey",
                "Observations: Abnormal vibration detected on pump drive-end bearing housing.",
                "Measured Vibration Velocity: 6.8 mm/s RMS (exceeds warning threshold of 4.5 mm/s).",
                "Spectral Peak: Prominent 1X and 2X shaft rotational speed harmonics.",
                "Bearing Housing Temperature: 71°C (elevated above 60°C baseline).",
                "Recommendation: Schedule lubrication oil sampling and check shaft alignment at next window."
            ])
        ]
    )

    # 2026 Failure Report
    fail_2026_pdf = SAMPLE_FILES_DIR / "P101_Failure_Report_Feb_2026.pdf"
    create_pdf(
        fail_2026_pdf,
        "FAILURE INCIDENT & CORRECTIVE WORK ORDER #1189",
        [
            ("Incident Breakdown", [
                "Incident ID: INC-78 | Work Order Number: WO-1189 | Asset Tag: P-101",
                "Failure Date: 22 February 2026 | Reported By: Unit 2 Lead Operator",
                "Failure Mode: Drive-End Bearing Seizure and High Vibration Trip.",
                "Root Cause: Chronic vibration elevation (previously noted in INSP-456) caused ball cage fatigue.",
                "Impact: Unscheduled unit shutdown. Downtime: 18.5 hours.",
                "Damage: Drive-end bearing inner race seized, minor scoring on pump shaft collar.",
                "Corrective Action Taken: Emergency bearing replacement (SKF 6312), shaft polished,",
                "laser alignment verified (runout 0.02 mm), oil flushed with fresh ISO VG 46."
            ])
        ]
    )

    # Obsolete SOP (v1.0) for testing governance filtering
    obsolete_pdf = SAMPLE_FILES_DIR / "P101_SOP_Obsolete_v1.0.pdf"
    create_pdf(
        obsolete_pdf,
        "OBSOLETE STANDARD OPERATING PROCEDURE: P-101 (SUPERSEDED)",
        [
            ("Obsolete Protocol", [
                "Document ID: SOP-101-OBSOLETE | Version: v1.0 (SUPERSEDED / OBSOLETE)",
                "Effective Date: 10 May 2018 | Status: Obsolete / Do Not Use",
                "Notice: This procedure specified mineral grease which is no longer approved.",
                "AI Policy: Do not rely on obsolete protocols for current maintenance decisions."
            ])
        ]
    )

    # P-205 New Machine Datasheet
    p205_pdf = SAMPLE_FILES_DIR / "P205_Slurry_Pump_Datasheet.pdf"
    create_pdf(
        p205_pdf,
        "WARMAN SLURRY PUMP MODEL AH-100 - SPECIFICATION",
        [
            ("New Asset Technical Sheet", [
                "Equipment Tag: P-205 (Heavy Slurry Transfer Pump)",
                "Manufacturer: Warman Industrial | Model: AH-100 High Chrome",
                "Serial Number: P205-2026-0012 | Installation Date: 2026-01-10",
                "Location: Plant A, Unit 3 - Solids Handling Facility",
                "Bearing Assembly: Grease-lubricated heavy roller bearings (Lithium EP-2)",
                "Status: Newly Commissioned Asset (Knowledge profile starting from day one)."
            ])
        ]
    )

    # P&ID Text Flowsheet
    pid_txt = SAMPLE_FILES_DIR / "Unit2_Process_PID_Flowsheet.txt"
    with open(pid_txt, "w") as f:
        f.write(
            "========================================================================\n"
            "ENGINEERING DRAWING: P&ID FLOWSHEET - UNIT 2 FLUID HANDLING\n"
            "Drawing Ref: PID-ENG-U2-004 Rev 4 | Area: Fluid Processing\n"
            "========================================================================\n"
            "Line 101-A: Feed Suction -> P-101 (Primary Pump) -> V-102 (Discharge Control Valve)\n"
            "Line 101-B: Pressure Transmitter PT-101 -> Suction Strainer STR-101\n"
            "Line 102-A: Standby Line -> P-102 (Standby Pump) -> V-104 (Check Valve)\n"
            "Line 201-A: Overhead Gas -> C-201 (Reciprocating Compressor) -> T-201 (Separation Drum)\n"
            "Safety Loop: Pressure Safety Valve PSV-101 set at 16.5 bar to Flare Header\n"
            "Electrical Drive: Motor M-301 coupled to C-201 primary drive shaft\n"
            "Instrumentation: Temperature Transmitter TT-101, Flow Transmitter FT-202\n"
        )

    # 2. Ingest Documents into Database & FAISS
    print("Ingesting and indexing documents...")
    doc_service.process_and_save_document(
        file_path=oem_pdf,
        filename="Pump_P101_OEM_Manual.pdf",
        asset_tag="P-101",
        category="OEM Manual",
        version="v2.1",
        governance_status="Approved",
        effective_date="2021-06-01",
        review_date="2027-01-01"
    )
    doc_service.process_and_save_document(
        file_path=sop_pdf,
        filename="SOP-101_Centrifugal_Pump_Operation.pdf",
        asset_tag="P-101",
        category="SOP",
        version="v3.0",
        governance_status="Approved",
        effective_date="2023-01-15",
        review_date="2027-01-15"
    )
    doc_service.process_and_save_document(
        file_path=maint_2024_pdf,
        filename="P101_Maintenance_Report_March_2024.pdf",
        asset_tag="P-101",
        category="Maintenance",
        version="v1.0",
        governance_status="Approved",
        effective_date="2024-03-12",
        review_date="2028-03-12"
    )
    doc_service.process_and_save_document(
        file_path=insp_2025_pdf,
        filename="P101_Inspection_Report_Aug_2025.pdf",
        asset_tag="P-101",
        category="Inspection",
        version="v1.0",
        governance_status="Approved",
        effective_date="2025-08-15",
        review_date="2027-08-15"
    )
    doc_service.process_and_save_document(
        file_path=fail_2026_pdf,
        filename="P101_Failure_Report_Feb_2026.pdf",
        asset_tag="P-101",
        category="Incident",
        version="v1.0",
        governance_status="Approved",
        effective_date="2026-02-22",
        review_date="2028-02-22"
    )
    doc_service.process_and_save_document(
        file_path=obsolete_pdf,
        filename="P101_SOP_Obsolete_v1.0.pdf",
        asset_tag="P-101",
        category="SOP",
        version="v1.0",
        governance_status="Obsolete",
        effective_date="2018-05-10",
        review_date="2021-05-10"
    )
    doc_service.process_and_save_document(
        file_path=p205_pdf,
        filename="P205_Slurry_Pump_Datasheet.pdf",
        asset_tag="P-205",
        category="OEM Manual",
        version="v1.0",
        governance_status="Approved",
        effective_date="2026-01-10",
        review_date="2028-01-10"
    )
    doc_service.process_and_save_document(
        file_path=pid_txt,
        filename="Unit2_Process_PID_Flowsheet.txt",
        asset_tag="P-101",
        category="P&ID",
        version="v4.0",
        governance_status="Approved",
        effective_date="2023-11-20",
        review_date="2027-11-20",
        is_pid=True
    )

    # 3. Seed Assets
    print("Seeding asset records...")
    assets_data = [
        AssetCreate(
            tag="P-101",
            name="Centrifugal Water Injection Pump",
            asset_type="Centrifugal Pump",
            manufacturer="ABC Pumps Inc.",
            model="XYZ-200",
            serial_number="P101-2021-9982",
            organization="Apex Industrial Energy",
            sector="Energy & Chemicals",
            plant="Plant A - Gulf Coast",
            area="Unit 2 - Fluid Processing",
            status="Operational",
            installation_date="2021-06-15",
            criticality="Critical",
            description="Primary water injection booster pump for Unit 2 processing line.",
            aliases=["P101", "PUMP 101", "PUMP-101", "CENTRIFUGAL PUMP 101", "TAG-P101"],
            components=[
                Component(id="comp_p101_de_bearing", name="Drive-End Bearing", part_number="SKF-6312-C3", status="Operational", description="Deep groove ball bearing on motor drive coupling side"),
                Component(id="comp_p101_nde_bearing", name="Non-Drive-End Bearing", part_number="NU-312", status="Operational", description="Cylindrical roller bearing on pump outboard"),
                Component(id="comp_p101_impeller", name="Impeller", part_number="IMP-240-SS", status="Operational", description="240mm enclosed 316L stainless steel impeller"),
                Component(id="comp_p101_shaft", name="Pump Shaft", part_number="SHF-4140-50", status="Operational", description="4140 alloy steel shaft with polished collar"),
                Component(id="comp_p101_mech_seal", name="Mechanical Seal", part_number="SEAL-CART-65", status="Operational", description="Single cartridge balanced mechanical seal"),
                Component(id="comp_p101_motor", name="75kW Electric Motor", part_number="MOT-75KW-4P", status="Operational", description="3-phase 415V 50Hz induction drive motor")
            ]
        ),
        AssetCreate(
            tag="P-102",
            name="Centrifugal Booster Pump (Standby)",
            asset_type="Centrifugal Pump",
            manufacturer="FlowServe",
            model="Mark 3 ISO",
            serial_number="P102-2022-4412",
            organization="Apex Industrial Energy",
            sector="Energy & Chemicals",
            plant="Plant A - Gulf Coast",
            area="Unit 2 - Fluid Processing",
            status="Operational",
            installation_date="2022-04-10",
            criticality="High",
            description="Parallel standby booster pump for Unit 2 line.",
            aliases=["P102", "PUMP 102", "PUMP-102"],
            components=[
                Component(id="comp_p102_bearing", name="Thrust Bearing Set", status="Operational"),
                Component(id="comp_p102_motor", name="75kW Motor", status="Operational")
            ]
        ),
        AssetCreate(
            tag="C-201",
            name="Reciprocating Gas Compressor",
            asset_type="Compressor",
            manufacturer="Dresser-Rand",
            model="3HHE Recip",
            serial_number="CR-2019-1102",
            organization="Apex Industrial Energy",
            sector="Energy & Chemicals",
            plant="Plant B - Sabine River",
            area="Unit 1 - Gas Compression",
            status="Maintenance Due",
            installation_date="2019-11-05",
            criticality="Critical",
            description="3-stage reciprocating compressor for hydrocarbon overhead gas.",
            aliases=["C201", "COMP 201", "COMP-201"],
            components=[
                Component(id="comp_c201_piston", name="High Pressure Piston", status="Warning"),
                Component(id="comp_c201_valves", name="Suction Valves", status="Operational")
            ]
        ),
        AssetCreate(
            tag="M-301",
            name="Main Drive Induction Motor 350kW",
            asset_type="Electric Motor",
            manufacturer="Siemens",
            model="1LA8 High Voltage",
            serial_number="SM-2020-8831",
            organization="Apex Industrial Energy",
            sector="Energy & Chemicals",
            plant="Plant A - Gulf Coast",
            area="Unit 1 - Primary Utilities",
            status="Operational",
            installation_date="2020-08-20",
            criticality="Medium",
            description="High efficiency 350kW induction motor driving compressor train.",
            aliases=["M301", "MOTOR 301", "TAG-M301"],
            components=[
                Component(id="comp_m301_stator", name="Stator Winding", status="Operational"),
                Component(id="comp_m301_rotor", name="Squirrel Cage Rotor", status="Operational")
            ]
        ),
        AssetCreate(
            tag="P-205",
            name="Slurry Transfer Pump",
            asset_type="Slurry Pump",
            manufacturer="Warman Industrial",
            model="AH-100",
            serial_number="P205-2026-0012",
            organization="Apex Industrial Energy",
            sector="Energy & Chemicals",
            plant="Plant A - Gulf Coast",
            area="Unit 3 - Solids Handling",
            status="Operational",
            installation_date="2026-01-10",
            criticality="High",
            description="Brand-new asset registered directly in the platform to build machine history from day one.",
            aliases=["P205", "PUMP 205", "SLURRY PUMP 205"],
            components=[
                Component(id="comp_p205_liner", name="High Chrome Casing Liner", status="Operational"),
                Component(id="comp_p205_impeller", name="Slurry Impeller", status="Operational")
            ]
        )
    ]

    for a in assets_data:
        asset_service.create_asset(a)

    # 4. Seed Maintenance Records
    print("Seeding maintenance work orders...")
    maint_records = [
        MaintenanceRecord(
            record_id="maint_wo_1023",
            asset_tag="P-101",
            work_order_number="WO-1023",
            record_type="Preventive Overhaul",
            date="2024-03-12",
            technician="M. Vance",
            description="Scheduled 12,000h overhaul. Replaced drive-end bearing with SKF 6312. Flushed lubricant with ISO VG 46.",
            components_replaced=["Drive-End Bearing", "Mechanical Seal"],
            hours_spent=14.5,
            findings="Normal wear on bearing balls. Minor carbon deposit on mechanical seal face.",
            document_ref="P101_Maintenance_Report_March_2024",
            status="Completed"
        ),
        MaintenanceRecord(
            record_id="maint_wo_1189",
            asset_tag="P-101",
            work_order_number="WO-1189",
            record_type="Emergency Corrective",
            date="2026-02-22",
            technician="D. Briggs",
            description="Emergency repair following vibration trip and bearing seizure. Replaced drive-end bearing, polished shaft collar, performed laser alignment.",
            components_replaced=["Drive-End Bearing"],
            hours_spent=18.5,
            findings="Severe fatigue spalling on DE bearing inner ring. Shaft runout corrected to 0.02 mm.",
            document_ref="P101_Failure_Report_Feb_2026",
            status="Completed"
        ),
        MaintenanceRecord(
            record_id="maint_wo_2041",
            asset_tag="P-102",
            work_order_number="WO-2041",
            record_type="Condition Monitoring",
            date="2025-11-04",
            technician="M. Vance",
            description="Lubricant replenishment and seal flush check.",
            components_replaced=[],
            hours_spent=3.0,
            findings="Grease discoloration noted.",
            status="Completed"
        )
    ]
    for m in maint_records:
        db.maintenance_records.update_one({"record_id": m.record_id}, {"$set": m.model_dump()}, upsert=True)

    # 5. Seed Inspections
    print("Seeding inspection records...")
    inspections = [
        InspectionRecord(
            inspection_id="INSP-456",
            asset_tag="P-101",
            date="2025-08-15",
            inspector="R. Jenkins (Reliability Lead)",
            inspection_type="Vibration Spectrum Survey",
            parameters_checked=["Overall Vibration", "Bearing High-Frequency Demodulation", "Housing Temperature"],
            observations="Abnormal vibration detected on drive-end bearing housing. Measured 6.8 mm/s RMS vs 4.5 mm/s limit.",
            vibration_level_mm_s=6.8,
            result="Warning",
            document_ref="P101_Inspection_Report_Aug_2025"
        ),
        InspectionRecord(
            inspection_id="INSP-390",
            asset_tag="P-101",
            date="2024-03-13",
            inspector="R. Jenkins",
            inspection_type="Post-Overhaul Baseline",
            parameters_checked=["Vibration", "Shaft Runout", "Temperature"],
            observations="Post-overhaul baseline normal. Measured 2.2 mm/s RMS.",
            vibration_level_mm_s=2.2,
            result="Passed",
            document_ref="P101_Maintenance_Report_March_2024"
        ),
        InspectionRecord(
            inspection_id="INSP-501",
            asset_tag="C-201",
            date="2026-01-14",
            inspector="T. Howell",
            inspection_type="Valve Acoustic Leakage Survey",
            parameters_checked=["Cylinder Head Pressure", "Valve Temperature"],
            observations="Stage 2 suction valve temperature elevated by 14°C. Valve overhaul due.",
            vibration_level_mm_s=4.1,
            result="Warning"
        )
    ]
    for insp in inspections:
        db.inspection_records.update_one({"inspection_id": insp.inspection_id}, {"$set": insp.model_dump()}, upsert=True)

    # 6. Seed Failures & Incidents
    print("Seeding failure incidents...")
    failures = [
        FailureRecord(
            failure_id="FAIL-2026-02",
            asset_tag="P-101",
            date="2026-02-22",
            title="Drive-End Bearing Seizure Trip",
            failure_mode="Bearing Seizure / High Vibration Trip",
            component="Drive-End Bearing",
            severity="Critical",
            root_cause_hypothesis="Lubricant breakdown combined with operating under sustained elevated vibration (>6.8 mm/s).",
            corrective_action="Emergency bearing replacement, shaft dress-up, laser alignment verification.",
            downtime_hours=18.5,
            document_ref="P101_Failure_Report_Feb_2026"
        ),
        FailureRecord(
            failure_id="FAIL-2025-10",
            asset_tag="P-102",
            date="2025-10-18",
            title="Bearing Overheating Alarm",
            failure_mode="High Bearing Temperature",
            component="Thrust Bearing Set",
            severity="Medium",
            root_cause_hypothesis="Grease starvation.",
            corrective_action="Lubricant purged and topped up with ISO VG 46 equivalent.",
            downtime_hours=4.0
        )
    ]
    for f in failures:
        db.failures.update_one({"failure_id": f.failure_id}, {"$set": f.model_dump()}, upsert=True)

    # 7. Seed Action-Oriented Findings
    print("Seeding open findings...")
    findings = [
        Finding(
            finding_id="FIND-P101-01",
            asset_tag="P-101",
            title="Potential Recurring Bearing-Related Issue Detected",
            severity="High",
            status="Open",
            detected_date="2026-02-23",
            evidence_summary="3 related historical records (WO-1023 in 2024, INSP-456 in 2025, WO-1189 in 2026).",
            supporting_records=["WO-1023", "INSP-456", "WO-1189"],
            recommended_action="Review bearing inspection procedure and lubricant sampling frequency per SOP-101 Section 4.2.",
            source_procedure="OEM Manual XYZ-200 / SOP-101",
            owner="Maintenance Lead"
        )
    ]
    for find in findings:
        db.findings.update_one({"finding_id": find.finding_id}, {"$set": find.model_dump()}, upsert=True)

    # 8. Seed Synthetic Telemetry Points for P-101
    print("Seeding synthetic telemetry...")
    telemetry_samples = [
        {"ts": "2024-03-15 10:00", "vib": 2.1, "temp": 52.0, "press": 14.8, "rpm": 2950, "hrs": 12500},
        {"ts": "2024-09-10 14:00", "vib": 2.4, "temp": 54.5, "press": 14.7, "rpm": 2950, "hrs": 14200},
        {"ts": "2025-03-12 11:00", "vib": 3.8, "temp": 59.0, "press": 14.5, "rpm": 2950, "hrs": 16000},
        {"ts": "2025-08-15 09:30", "vib": 6.8, "temp": 71.0, "press": 14.2, "rpm": 2950, "hrs": 18200},  # Warning in INSP-456
        {"ts": "2025-12-05 16:00", "vib": 7.4, "temp": 76.5, "press": 13.9, "rpm": 2950, "hrs": 19800},
        {"ts": "2026-02-21 23:00", "vib": 9.2, "temp": 88.0, "press": 13.5, "rpm": 2940, "hrs": 20900},
        {"ts": "2026-02-22 03:15", "vib": 12.4, "temp": 94.0, "press": 11.2, "rpm": 2880, "hrs": 20920}, # Failure Trip in WO-1189
        {"ts": "2026-02-23 18:00", "vib": 2.2, "temp": 51.0, "press": 14.9, "rpm": 2950, "hrs": 20940},  # Post-repair normal
        {"ts": "2026-03-01 08:00", "vib": 2.3, "temp": 50.5, "press": 15.0, "rpm": 2950, "hrs": 21050}
    ]
    for s in telemetry_samples:
        t_pt = TelemetryPoint(
            asset_tag="P-101",
            timestamp=s["ts"],
            vibration_rms=s["vib"],
            bearing_temp_c=s["temp"],
            discharge_pressure_bar=s["press"],
            rpm=s["rpm"],
            operating_hours=s["hrs"],
            is_synthetic=True
        )
        db.telemetry.insert_one(t_pt.model_dump())

    # 9. Seed Compliance Requirements
    print("Seeding compliance requirements...")
    compliance_reqs = [
        ComplianceRequirement(
            req_id="API-610-VIB",
            title="Annual Vibration Baseline Survey (API 610)",
            regulatory_body="API 610 / ISO 10816",
            requirement_type="Inspection",
            target_asset_types=["Centrifugal Pump", "Slurry Pump"],
            description="Mandatory annual overall velocity vibration survey to ensure operational stability below 4.5 mm/s.",
            required_evidence_type="Condition Monitoring Report",
            frequency_days=365
        ),
        ComplianceRequirement(
            req_id="ISO-14224-REL",
            title="Reliability-Centered Maintenance Overhaul Logging",
            regulatory_body="ISO 14224",
            requirement_type="Overhaul SOP",
            target_asset_types=["All"],
            description="Maintenance documentation must track part replacements, operating hours, and technician sign-off.",
            required_evidence_type="Maintenance Work Order",
            frequency_days=730
        ),
        ComplianceRequirement(
            req_id="OSHA-1910-LOTO",
            title="Lockout/Tagout (LOTO) Energy Isolation Standard",
            regulatory_body="OSHA 1910.147",
            requirement_type="Safety LOTO",
            target_asset_types=["All"],
            description="Verified isolation procedure must be maintained for all rotating equipment before casing intervention.",
            required_evidence_type="Safety Procedure / SOP",
            frequency_days=365
        ),
        ComplianceRequirement(
            req_id="ISA-S51-CALIB",
            title="Pressure Transmitter Annual Calibration Certificate",
            regulatory_body="ISA / IEC 61508",
            requirement_type="Calibration",
            target_asset_types=["Centrifugal Pump", "Compressor"],
            description="Annual 5-point calibration certificate for suction and discharge pressure instrumentation.",
            required_evidence_type="Calibration Certificate",
            frequency_days=365
        )
    ]
    for cr in compliance_reqs:
        db.compliance_requirements.update_one({"req_id": cr.req_id}, {"$set": cr.model_dump()}, upsert=True)

    # 10. Seed Human Notes
    print("Seeding operator human notes...")
    notes = [
        HumanNote(
            note_id="note_001",
            asset_tag="P-101",
            author="J. Martinez",
            author_role="Lead Field Operator",
            created_at="2026-02-18 15:45",
            text="Observed slight acoustic hum and subtle casing vibration during evening shift changeover. Recommended priority review.",
            component="Drive-End Bearing",
            verified=False,
            verification_status="Unverified Operator Observation"
        )
    ]
    for n in notes:
        db.human_notes.update_one({"note_id": n.note_id}, {"$set": n.model_dump()}, upsert=True)

    # 11. Seed Audit Logs
    print("Seeding immutable audit logs...")
    audit_events = [
        ("System Admin", "Administrator", "Document Ingested", "Document", "Pump_P101_OEM_Manual", "Uploaded and chunked OEM manual v2.1 with Approved governance status"),
        ("M. Vance", "Maintenance Engineer", "Maintenance Logged", "Maintenance", "WO-1023", "Recorded 12,000h overhaul and bearing replacement"),
        ("R. Jenkins", "Quality / Compliance User", "Inspection Logged", "Inspection", "INSP-456", "Logged 6.8 mm/s vibration warning on DE bearing"),
        ("D. Briggs", "Maintenance Engineer", "Extraction Confirmed", "Document", "P101_Failure_Report_Feb_2026", "Confirmed extracted failure mode and component tag"),
        ("Safety Officer", "Safety / Compliance", "Governance Updated", "Document", "P101_SOP_Obsolete_v1.0", "Marked old procedure v1.0 as Obsolete")
    ]
    for user, role, act, t_type, t_id, det in audit_events:
        audit_service.log_event(user=user, role=role, action=act, target_type=t_type, target_id=t_id, details=det)

    print("Seed complete! Synthetic assets, documents, FAISS index, and operational records ready.")

if __name__ == "__main__":
    seed_database()
