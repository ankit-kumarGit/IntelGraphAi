#!/usr/bin/env python3
import os
import sys
import zipfile
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import openpyxl
from pypdf import PdfWriter, PdfReader
import io

OUTPUT_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_p194_package")
NEG_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_negative_package")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NEG_DIR.mkdir(parents=True, exist_ok=True)

print(f"Generating test package in {OUTPUT_DIR}...")

# 1. P-194_Process_Flowsheet.txt
txt_path = OUTPUT_DIR / "P-194_Process_Flowsheet.txt"
with open(txt_path, "w") as f:
    f.write("""UNIT 2 FLUID PROCESSING TRAIN - PROCESS FLOWSHEET
Asset Tag: P-194
Equipment Description: Primary Hydrocarbon Transfer & Process Pump
Design Duty: Centrifugal Heavy-Duty Pump Model CP-194

PIPING & INSTRUMENTATION LOOPS:
Suction Line: Line 194-A-10 (10-inch Schedule 40 Carbon Steel)
Discharge Line: Line 194-B-8 (8-inch Schedule 80 Carbon Steel)
Instrumentation:
- PT-194: Suction and Discharge Pressure Transmitters (Operating at 18.2 bar)
- FT-194: Ultrasonic Flow Transmitter (Rated 140 m3/h)
- TT-194: Dual RTD Bearing Temperature Sensors (Drive-End and Non-Drive-End)
- PSV-194: Pressure Safety Relief Valve set at 18.5 bar with direct vent to flare header

CONTROL & INTERLOCKS:
Automated trip at discharge pressure > 22.0 bar or bearing temperature > 95.0 deg C.
Standby auto-rotation scheduled bi-weekly.
""")

# 2. P-194_Shift_Handover.eml
eml_path = OUTPUT_DIR / "P-194_Shift_Handover.eml"
with open(eml_path, "w") as f:
    f.write("""From: Marcus Vance <m.vance@industrialops.example.com>
To: reliability-team@industrialops.example.com, shift-lead@industrialops.example.com
Subject: Shift Handover - P-194 Pump Operations and Vibration Monitoring
Date: Wed, 11 Mar 2026 06:45:00 -0600
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Team,

Here is the operational handover summary for the Unit 2 Process Train:

1. Centrifugal Process Pump P-194 has been running continuously overnight at steady throughput (138 m3/h).
2. Drive-End bearing temperature was logged at 68.0 deg C, which is well within normal operating envelope.
3. Vibration survey performed at 04:00 showed 2.2 mm/s RMS, demonstrating stable hydrodynamic performance.
4. Lube oil level was checked and topped up with approved ISO VG 46 mineral turbine oil (approx 250 ml added).
5. Discharge pressure transmitter PT-194 holds steady at 18.2 bar.
6. Mechanical seal BURG-M7N barrier pressure is nominal with zero weepage.

Day shift: Please continue routine walkdown and monitor TT-194 during peak afternoon ambient temperature.

Regards,
Marcus Vance
Senior Operations & Reliability Lead
Unit 2 Fluid Processing
""")

# 3. P-194_Site_Upload_Package.zip
zip_path = OUTPUT_DIR / "P-194_Site_Upload_Package.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("P-194_Electrical_Single_Line.txt", """ELECTRICAL SYSTEM SPECIFICATION - P-194
Driver: 55 kW 415V 3-Phase Squirrel Cage Induction Motor
Full Load Current: 96 A
Rated Speed: 2950 RPM
Insulation Class: Class H (VFD Rated)
Feeder Breaker: 125A MCC-2-B4
Grounding: Redundant 70mm2 copper earthing strap verified.
""")
    zf.writestr("P-194_Lubrication_Spec.txt", """LUBRICATION MATRIX & PROTOCOL - P-194
Primary Lubricant: ISO VG 46 Mineral Turbine Oil
Reservoir Sump Volume: 4.5 Liters
Relubrication Frequency: Every 2,000 Operating Hours
Oil Analysis Interval: Quarterly
Target Particle Count: ISO 16/14/11
""")
    zf.writestr("P-194_Spare_Parts_Catalog.csv", """Part_Number,Description,Manufacturer,Stock_Qty,Criticality
SKF-6314-2Z,Drive-End Deep Groove Ball Bearing,SKF,4,High
SKF-NU-314,Non-Drive-End Cylindrical Roller Bearing,SKF,3,High
BURG-M7N,Single Cartridge Mechanical Seal 50mm,Burgmann,2,High
O-RING-VITON-194,Viton O-Ring Casing Gasket Set,Parker,6,Medium
""")

# Helper for PDF generation using fitz
def create_pdf(path: Path, title: str, sections: list):
    doc = fitz.open()
    page = doc.new_page()
    
    # Header
    page.insert_text((50, 60), title, fontsize=15, fontname="helv", color=(0.1, 0.2, 0.4))
    page.draw_line((50, 75), (550, 75), color=(0.2, 0.4, 0.7), width=1.5)
    
    y = 100
    for heading, body in sections:
        page.insert_text((50, y), heading, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.2))
        y += 18
        for line in body.split("\n"):
            page.insert_text((60, y), line, fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
            y += 14
        y += 10
    
    doc.save(str(path))
    doc.close()

# 4. P-194_Failure_Incident_Report.pdf
create_pdf(
    OUTPUT_DIR / "P-194_Failure_Incident_Report.pdf",
    "INCIDENT INVESTIGATION REPORT: ASSET P-194",
    [
        ("1. Incident Summary", 
         "Asset Tag: P-194 (Centrifugal Heavy-Duty Process Pump)\n"
         "Incident Date: 2026-02-14\n"
         "Failure Mode: Bearing Thermal Distress & High Vibration Trip\n"
         "Unplanned Downtime: 4.2 hours\n"
         "Assigned Work Order: WO-9412"),
        ("2. Sequence of Events & Root Cause Analysis",
         "At 14:15, vibration telemetry on P-194 spiked to 9.8 mm/s RMS (trip setpoint 7.1 mm/s).\n"
         "Drive-end bearing temperature reached 92.4 deg C.\n"
         "Immediate emergency shutdown prevented catastrophic impeller seizure.\n"
         "Root Cause: Oil seal degradation permitted boundary weepage and progressive lubricant starvation.\n"
         "Metal-to-metal contact generated localized micro-spalling on the inner raceway."),
        ("3. Corrective Actions & Resolution",
         "Work Order WO-9412 executed emergency bearing replacement.\n"
         "Fitted new SKF-6314-2Z drive-end bearing and renewed BURG-M7N mechanical seal.\n"
         "Laser alignment verified to within 0.03 mm precision tolerance.\n"
         "Pump recommissioned successfully with baseline vibration at 2.1 mm/s RMS.")
    ]
)

# 5. P-194_Inspection_Report.pdf
create_pdf(
    OUTPUT_DIR / "P-194_Inspection_Report.pdf",
    "CONDITION MONITORING & NDT INSPECTION REPORT: P-194",
    [
        ("1. Inspection Overview",
         "Asset Tag: P-194\n"
         "Inspection Date: 2026-03-02\n"
         "Inspector / Technician: Lead Reliability Specialist\n"
         "Document Reference: INSP-P194\n"
         "Operating Hours at Inspection: 3,420 hours"),
        ("2. NDT & Vibration Survey Findings",
         "Overall Vibration Velocity: 2.1 mm/s RMS (ISO 10816-3 Class II Satisfactory Zone).\n"
         "Drive-End Bearing Operating Temperature: 68.0 deg C (Continuous limit: 85.0 deg C).\n"
         "Non-Drive-End Bearing Temperature: 64.5 deg C.\n"
         "Ultrasonic Acoustic Emission: Decibel baseline 18 dBuV with no high-frequency impact peaks.\n"
         "Shaft Laser Alignment: Radial offset 0.02 mm, angular offset 0.01 deg (well within tolerance)."),
        ("3. Regulatory & Safety Compliance Verification",
         "OISD-STD-119 periodic inspection requirement satisfied.\n"
         "The Factories Act 1948 Section 21 machinery coupling guard securely locked.\n"
         "Overpressure relief valve PSV-194 setpoint validated at 18.5 bar.\n"
         "Final Condition Assessment: Satisfactory Baseline Survey.")
    ]
)

# 6. P-194_Maintenance_Report.pdf
create_pdf(
    OUTPUT_DIR / "P-194_Maintenance_Report.pdf",
    "CORRECTIVE MAINTENANCE WORK ORDER COMPLETION REPORT: P-194",
    [
        ("1. Work Order Metadata",
         "Work Order Number: WO-9412\n"
         "Asset Tag: P-194\n"
         "Completion Date: 2026-02-18\n"
         "Technician: David Mercer (Senior Rotating Equipment Specialist)\n"
         "Operating Hours: 3,200 hours\n"
         "Status: Completed & Verified"),
        ("2. Scope of Maintenance Executed",
         "- Complete disassembly of pump bearing housing and seal chamber.\n"
         "- Replaced Drive-End bearing with new SKF-6314-2Z deep groove ball bearing.\n"
         "- Inspected Non-Drive-End SKF-NU-314 roller bearing (verified in excellent condition).\n"
         "- Installed new BURG-M7N cartridge mechanical seal with Viton secondary elastomers.\n"
         "- Flushed lube reservoir and charged with 4.5 liters of fresh ISO VG 46 turbine oil.\n"
         "- Precision laser alignment completed with soft-foot check under 0.02 mm."),
        ("3. Sign-off & Quality Acceptance",
         "Post-maintenance solo run and coupled run vibration measured 1.9 mm/s RMS.\n"
         "Thermal stabilization reached 66 deg C after 4 hours continuous full-load run.\n"
         "Signed off by Lead Mechanical Engineer.")
    ]
)

# 7. P-194_Maintenance_Schedule.xlsx
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Maintenance_Schedule"
ws.append(["Asset_Tag", "Component", "Task_Description", "Frequency_Hours", "Last_Completed", "Next_Due", "Lubricant_Spec"])
ws.append(["P-194", "Drive-End Bearing", "Lubrication Drain & Refill", 2000, "2026-02-18", "2026-05-15", "ISO VG 46 Turbine Oil"])
ws.append(["P-194", "Non-Drive-End Bearing", "Acoustic Grease Regrease", 2000, "2026-02-18", "2026-05-15", "Polyurea EP2 Grease"])
ws.append(["P-194", "Mechanical Seal", "Barrier Fluid Pressure & Leak Check", 500, "2026-03-02", "2026-03-23", "Propylene Glycol Barrier"])
ws.append(["P-194", "Motor Coupling", "Laser Alignment & Rubber Element NDT", 8000, "2026-02-18", "2026-11-30", "N/A"])
ws.append(["P-194", "Impeller & Casing", "Major Overhaul & Wear Ring Clearance", 16000, "2025-01-10", "2027-04-01", "N/A"])
ws.append(["P-194", "Safety Relief Valve", "PSV-194 Bench Calibration Pop Test", 8760, "2025-10-15", "2026-10-15", "N/A"])
wb.save(str(OUTPUT_DIR / "P-194_Maintenance_Schedule.xlsx"))

# 8. P-194_OEM_Manual.pdf
create_pdf(
    OUTPUT_DIR / "P-194_OEM_Manual.pdf",
    "OEM TECHNICAL OPERATING MANUAL: MODEL CP-194 PROCESS PUMP",
    [
        ("1. Technical Specifications",
         "Manufacturer: FlowServe Industrial Pumps Ltd\n"
         "Model: CP-194 Heavy-Duty Single-Stage Process Centrifugal Pump\n"
         "Rated Volumetric Flow: 140 m3/h (Normal operating range: 110 - 165 m3/h)\n"
         "Rated Total Differential Head: 92 meters\n"
         "Operating Rotational Speed: 2950 RPM\n"
         "Electric Driver: 55 kW 415V 50Hz 3-phase electric motor\n"
         "Impeller Diameter: 245 mm closed dynamic balanced impeller"),
        ("2. Bearing Assembly & Lubrication Limits",
         "Drive-End Bearing: SKF-6314-2Z Deep Groove Ball Bearing\n"
         "Non-Drive-End Bearing: SKF-NU-314 Cylindrical Roller Bearing\n"
         "Recommended Lubricant: ISO VG 46 high-demulsibility mineral turbine oil\n"
         "Maximum Continuous Operating Temperature: 85.0 deg C\n"
         "High Temperature Alarm: 90.0 deg C | High-High Emergency Trip: 95.0 deg C\n"
         "Vibration Baseline Norm: ISO 10816-3 Class II (Rigid Foundation: Alarm 4.5 mm/s, Trip 7.1 mm/s)"),
        ("3. Mechanical Seal Operation",
         "Cartridge Mechanical Seal: BURG-M7N balanced single seal with plan 11 flush piping.\n"
         "Seal face materials: Silicon Carbide vs Reaction Bonded Tungsten Carbide.")
    ]
)

# 9. P-194_PID_Diagram.png
img_pid = Image.new("RGB", (1000, 700), color=(255, 255, 255))
draw_pid = ImageDraw.Draw(img_pid)

# Draw borders and title block
draw_pid.rectangle([(20, 20), (980, 680)], outline=(20, 40, 80), width=3)
draw_pid.rectangle([(20, 20), (980, 80)], fill=(230, 240, 255), outline=(20, 40, 80), width=2)
draw_pid.text((40, 35), "P&ID FLOWSHEET - UNIT 2 HYDROCARBON PROCESS TRAIN", fill=(10, 30, 70))
draw_pid.text((40, 55), "DRAWING NO: PID-U2-194-REV2 | PRIMARY ASSET: P-194", fill=(50, 50, 50))

# Draw Piping Lines
draw_pid.line([(100, 350), (400, 350)], fill=(0, 100, 200), width=5) # Suction
draw_pid.text((150, 325), "SUCTION LINE 194-A-10", fill=(0, 60, 150))

# Draw Centrifugal Pump Symbol
draw_pid.ellipse([(400, 270), (560, 430)], outline=(10, 30, 80), width=4, fill=(240, 245, 255))
draw_pid.line([(400, 350), (560, 350)], fill=(10, 30, 80), width=2)
draw_pid.polygon([(480, 270), (520, 350), (440, 350)], outline=(10, 30, 80), fill=(20, 120, 220))
draw_pid.text((440, 380), "P-194", fill=(10, 20, 80))
draw_pid.text((420, 400), "PRIMARY PUMP", fill=(40, 40, 40))

# Draw Discharge Line
draw_pid.line([(480, 270), (480, 200)], fill=(0, 100, 200), width=5)
draw_pid.line([(480, 200), (900, 200)], fill=(0, 100, 200), width=5)
draw_pid.text((540, 175), "DISCHARGE LINE 194-B-8", fill=(0, 60, 150))

# Instrumentation bubbles
# PT-194 (Pressure)
draw_pid.ellipse([(620, 100), (700, 180)], outline=(150, 0, 0), width=3, fill=(255, 245, 245))
draw_pid.line([(660, 180), (660, 200)], fill=(150, 0, 0), width=2)
draw_pid.text((635, 130), "PT-194", fill=(150, 0, 0))

# FT-194 (Flow)
draw_pid.ellipse([(740, 100), (820, 180)], outline=(0, 120, 50), width=3, fill=(245, 255, 245))
draw_pid.line([(780, 180), (780, 200)], fill=(0, 120, 50), width=2)
draw_pid.text((755, 130), "FT-194", fill=(0, 120, 50))

# TT-194 (Temp)
draw_pid.ellipse([(300, 420), (380, 500)], outline=(180, 90, 0), width=3, fill=(255, 250, 240))
draw_pid.line([(380, 460), (420, 400)], fill=(180, 90, 0), width=2)
draw_pid.text((315, 450), "TT-194", fill=(180, 90, 0))

# PSV-194 (Pressure Safety Valve)
draw_pid.ellipse([(520, 480), (600, 560)], outline=(180, 0, 0), width=3, fill=(255, 235, 235))
draw_pid.line([(560, 480), (560, 200)], fill=(180, 0, 0), width=2)
draw_pid.text((530, 510), "PSV-194", fill=(180, 0, 0))
draw_pid.text((515, 570), "SET: 18.5 BAR", fill=(100, 0, 0))

img_pid.save(str(OUTPUT_DIR / "P-194_PID_Diagram.png"))

# 10. P-194_Scanned_Field_Checklist.png
img_check = Image.new("RGB", (900, 600), color=(250, 250, 250))
draw_check = ImageDraw.Draw(img_check)
draw_check.rectangle([(15, 15), (885, 585)], outline=(100, 100, 100), width=2)
draw_check.text((30, 30), "OPERATOR DAILY FIELD INSPECTION CHECKLIST - P-194", fill=(20, 20, 20))
draw_check.text((30, 60), "Inspection Date: 2026-03-08 | Shift: Day Shift A | Inspector: Operator J. Miller", fill=(50, 50, 50))
draw_check.line([(30, 90), (870, 90)], fill=(150, 150, 150), width=2)

items = [
    ("1. Lube Oil Level & Color", "Normal - Amber clarity - Sump level at 80% gauge mark", "[PASS]"),
    ("2. Mechanical Seal Leakage", "Zero liquid weepage observed at BURG-M7N gland", "[PASS]"),
    ("3. Handheld Vibration Check", "2.2 mm/s RMS on Drive-End bearing housing", "[PASS]"),
    ("4. Bearing Skin Temperature", "67.4 deg C measured with calibrated IR thermometer", "[PASS]"),
    ("5. Suction & Discharge Pressure", "Suction: 1.8 bar | Discharge PT-194: 18.2 bar", "[PASS]"),
    ("6. Coupling Safety Guarding", "Factories Act Sec 21 safety cage bolted and intact", "[PASS]"),
    ("7. Abnormal Noise / Cavitation", "Smooth continuous rotodynamic hum, no cracking noise", "[PASS]")
]

y_pos = 110
for title_item, note, status in items:
    draw_check.text((40, y_pos), title_item, fill=(10, 10, 10))
    draw_check.text((300, y_pos), note, fill=(60, 60, 60))
    draw_check.text((800, y_pos), status, fill=(0, 120, 0))
    draw_check.line([(30, y_pos + 25), (870, y_pos + 25)], fill=(220, 220, 220), width=1)
    y_pos += 45

draw_check.text((40, 520), "Signed off: J. Miller (Process Operator #402)", fill=(30, 30, 30))
img_check.save(str(OUTPUT_DIR / "P-194_Scanned_Field_Checklist.png"))

# 11. P-194_Telemetry.csv
telemetry_path = OUTPUT_DIR / "P-194_Telemetry.csv"
with open(telemetry_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "asset_tag", "vibration_rms", "bearing_temp_c", "discharge_pressure_bar", "rpm", "operating_hours"])
    timestamps = [
        "2026-03-10 00:00", "2026-03-10 04:00", "2026-03-10 08:00", "2026-03-10 12:00", "2026-03-10 16:00",
        "2026-03-10 20:00", "2026-03-11 00:00", "2026-03-11 04:00", "2026-03-11 08:00", "2026-03-11 12:00",
        "2026-03-11 16:00", "2026-03-11 20:00", "2026-03-12 00:00", "2026-03-12 04:00", "2026-03-12 08:00"
    ]
    vibs = [2.1, 2.15, 2.2, 2.25, 2.3, 2.2, 2.15, 2.1, 2.2, 2.35, 2.4, 2.25, 2.15, 2.2, 2.2]
    temps = [66.5, 66.8, 67.5, 69.2, 71.0, 68.5, 67.0, 66.4, 68.0, 71.5, 72.0, 69.5, 67.2, 66.8, 68.0]
    pressures = [18.2, 18.3, 18.2, 18.5, 18.6, 18.4, 18.3, 18.2, 18.3, 18.5, 18.6, 18.4, 18.3, 18.2, 18.4]
    hrs = 3420.0
    for t, v, te, p in zip(timestamps, vibs, temps, pressures):
        writer.writerow([t, "P-194", v, te, p, 2950.0, hrs])
        hrs += 4.0

# 12. SOP-P194-01-Operation.pdf
create_pdf(
    OUTPUT_DIR / "SOP-P194-01-Operation.pdf",
    "STANDARD OPERATING PROCEDURE: SOP-P194-01",
    [
        ("1. Scope & Regulatory Framework",
         "Procedure Title: Standard Operating Procedure for Hydrocarbon Process Pump P-194\n"
         "Asset Identifier: P-194 | Unit: Fluid Processing Train 2\n"
         "Governance Version: v2.0 | Governance Status: Approved\n"
         "Governing Regulations:\n"
         "- OISD-STD-119: Process Piping & Machinery Operational Inspection Guidelines\n"
         "- The Factories Act 1948 Section 21: Rotating machinery fencing & protective interlocking\n"
         "- PESO Rule 33: Hydrocarbon Pressure Piping and Vessel statutory compliance"),
        ("2. Pre-Start Verification Checklist",
         "1. Verify suction line 194-A valve is 100% open and locked in open position.\n"
         "2. Verify seal barrier fluid pressure is pressurized to 2.5 bar above suction pressure.\n"
         "3. Verify lube oil reservoir contains ISO VG 46 turbine oil at minimum 65% glass level.\n"
         "4. Confirm mechanical coupling safety cage is securely latched.\n"
         "5. Confirm emergency stop push button is reset and control interlocks are healthy."),
        ("3. Normal Running & Stop Sequence",
         "Start 55 kW driver and observe pressure build-up on PT-194 to 18.2 bar.\n"
         "Gradually crack open discharge control valve V-194 until FT-194 indicates 140 m3/h flow.\n"
         "In the event of vibration exceeding 7.1 mm/s RMS or temperature exceeding 95 deg C, automated trip initiates.")
    ]
)

print("12 P-194 files generated successfully!")

# NOW GENERATE NEGATIVE TEST FILES
print(f"Generating negative test suite in {NEG_DIR}...")

# 1. Unsupported .exe
with open(NEG_DIR / "bad_unsupported.exe", "wb") as f:
    f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00FakeWindowsExecutablePayload")

# 2. Corrupted PDF
with open(NEG_DIR / "corrupted_sample.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n%CORRUPTED_BINARY_DATA_TRUNCATED_EOF_ERROR\x00\xff\xfe\x12\x34\x56")

# 3. Empty file (0 bytes)
with open(NEG_DIR / "empty_file.txt", "wb") as f:
    pass

# 4. Oversized ZIP (> 50 MB uncompressed)
oversized_zip = NEG_DIR / "oversized_sample.zip"
with zipfile.ZipFile(oversized_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    # 52 MB of uncompressed zeroes (compresses to ~50 KB)
    zf.writestr("huge_payload.txt", b"0" * (52 * 1024 * 1024))

# 5. Malicious Zip Slip archive
zipslip_zip = NEG_DIR / "malicious_zipslip.zip"
with zipfile.ZipFile(zipslip_zip, "w") as zf:
    zf.writestr("../../etc/cron.d/malicious", "malicious payload\n")

# 6. ZIP with executable
zip_exe = NEG_DIR / "zip_with_executable.zip"
with zipfile.ZipFile(zip_exe, "w") as zf:
    zf.writestr("harmless.txt", "Harmless content\n")
    zf.writestr("malicious_tool.exe", b"MZexecutable")

# 7. Password-protected PDF
writer = PdfWriter()
writer.add_blank_page(width=200, height=200)
writer.encrypt("topsecret123")
with open(NEG_DIR / "password_protected.pdf", "wb") as f:
    writer.write(f)

print("All negative test files generated successfully!")
