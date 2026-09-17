#!/usr/bin/env python3
"""
Generate realistic test fixtures for real-world user acceptance test.
Creates:
1. USER_TEST_001_Maintenance_Report.pdf (WO-8812, Maintenance Report / WO)
2. USER_TEST_001_OEM_Manual.pdf (Model UT-100 Centrifugal Pump, OEM Technical Manual)
3. USER_TEST_001_Telemetry.csv (Sensor Telemetry & Time Series)
4. USER_TEST_001_Maintenance_Schedule.xlsx (Maintenance Report / WO)
5. USER_TEST_001_PID_Drawing.png (Engineering Drawing / P&ID)
6. USER_TEST_001_Shift_Handover.eml (Operations & Shift Logs)
7. USER_TEST_002_Inspection.pdf (for TEST C - Wrong Machine)
8. MULTI_USER_TEST_001_002.pdf (for TEST D - Multiple Machines)
9. UNKNOWN_USER_TEST_999.pdf (for TEST E - Unknown Machine)
10. NO_TAG_General_Guide.pdf (for TEST F - No Machine Evidence)
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import openpyxl
from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path("/Users/ankitkumar/Desktop/IntelGraphAI/test_fixtures_user_test")
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

def create_pdf(filepath: Path, title: str, lines: list):
    doc = SimpleDocTemplate(str(filepath), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e293b")
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    story = [
        Paragraph(title, title_style),
        Spacer(1, 12)
    ]
    for line in lines:
        if line == "---":
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 4))
    doc.build(story)

# 1. USER_TEST_001_Maintenance_Report.pdf
create_pdf(
    FIXTURES_DIR / "USER_TEST_001_Maintenance_Report.pdf",
    "WORK ORDER EXECUTION & OVERHAUL REPORT — USER-TEST-001",
    [
        "<b>Work Order Number:</b> WO-8812",
        "<b>Equipment Tag:</b> USER-TEST-001",
        "<b>Equipment Name:</b> User Test Pump (Centrifugal Process Pump)",
        "<b>Facility / Area:</b> Gulf Coast Refining — Unit 2 Fluid Transfer",
        "<b>Maintenance Date:</b> 2026-08-24",
        "<b>Technician:</b> Marcus Vance (Lead Mechanical Reliability Specialist)",
        "---",
        "<b>Executive Summary:</b>",
        "Comprehensive overhaul and corrective maintenance performed on centrifugal pump USER-TEST-001 following scheduled preventative maintenance trigger.",
        "<b>Detailed Scope of Work:</b>",
        "1. Isolated pump USER-TEST-001 mechanically and electrically via lockout/tagout protocol LOTO-4491.",
        "2. Disassembled drive-end and non-drive-end bearing housings.",
        "3. Removed degraded bearings and replaced with genuine SKF-6314-2Z deep groove ball bearing (DE) and SKF-NU-314 cylindrical roller bearing (NDE).",
        "4. Inspected mechanical seal cartridge BURG-M7N; replaced elastomeric secondary O-rings and flushed seal faces.",
        "5. Reassembled pump casing and performed precision laser shaft alignment. Angular misalignment was adjusted from 0.12 mm down to 0.02 mm (well within OEM tolerance of 0.05 mm).",
        "6. Charged bearing cavity with 180 grams of Mobil SHC Polyrex 462 synthetic grease.",
        "<b>Final Test Run & Handover:</b>",
        "Restarted pump USER-TEST-001 under full process load (145 m3/h at 2950 RPM). Overall vibration RMS measured 1.45 mm/s at drive end, significantly below ISO 10816-3 alert limit of 4.5 mm/s. Bearing temperatures stabilized at 62.4 C.",
        "Pump USER-TEST-001 certified for continuous unconstrained service."
    ]
)

# 2. USER_TEST_001_OEM_Manual.pdf
create_pdf(
    FIXTURES_DIR / "USER_TEST_001_OEM_Manual.pdf",
    "OEM TECHNICAL MANUAL & OPERATING SPECIFICATIONS — MODEL UT-100",
    [
        "<b>Manufacturer:</b> FlowDynamics Industrial Equipment Corp.",
        "<b>Equipment Identification:</b> USER-TEST-001 (User Test Pump)",
        "<b>Model Designation:</b> UT-100-CP Heavy Duty Process Centrifugal Pump",
        "<b>Publication Document No:</b> OEM-MAN-UT100-REV4",
        "<b>Classification:</b> OEM Technical Manual & Engineering Reference",
        "---",
        "<b>Section 1: Operating Specifications & Technical Limits:</b>",
        "• <b>Rated Volumetric Flow:</b> 145.0 m3/h (Normal operating range: 110 - 165 m3/h)",
        "• <b>Total Dynamic Head (TDH):</b> 92.0 meters liquid column",
        "• <b>Design Operating Speed:</b> 2,950 RPM (50 Hz synchronous 2-pole direct drive)",
        "• <b>Motor Nameplate Power:</b> 55.0 kW, 400V 3-phase, TEFC Class F insulation",
        "• <b>Maximum Allowable Working Pressure (MAWP):</b> 25.0 bar gauge at 120 C",
        "• <b>NPSH Required (NPSHr):</b> 3.2 meters at rated flow",
        "---",
        "<b>Section 2: Component Part Numbers & Tolerances:</b>",
        "• Drive-End (DE) Bearing: SKF-6314-2Z (C3 clearance)",
        "• Non-Drive-End (NDE) Bearing: SKF-NU-314 (cylindrical roller)",
        "• Mechanical Shaft Seal: Burgmann M7N single cartridge seal with silicon carbide / carbon faces",
        "• Lubricant Specification: ISO VG 46 high-performance synthetic hydraulic oil or polyurea grease",
        "---",
        "<b>Section 3: Alarm & Trip Setpoints for USER-TEST-001:</b>",
        "• Bearing Temperature Warning Alarm: 75.0 C",
        "• Bearing Temperature Emergency Trip: 85.0 C",
        "• Overall Vibration Velocity (RMS) Warning: 4.5 mm/s",
        "• Overall Vibration Velocity (RMS) Emergency Trip: 7.1 mm/s",
        "Any questions regarding pump USER-TEST-001 should be directed to FlowDynamics Technical Services."
    ]
)

# 3. USER_TEST_001_Telemetry.csv
csv_path = FIXTURES_DIR / "USER_TEST_001_Telemetry.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("timestamp,asset_tag,vibration_rms,bearing_temp_c,discharge_pressure_bar,rpm,operating_hours\n")
    data_rows = [
        ("2026-09-01 08:00:00", "USER-TEST-001", "1.42", "61.2", "18.4", "2950", "4100.0"),
        ("2026-09-01 12:00:00", "USER-TEST-001", "1.45", "62.0", "18.5", "2950", "4104.0"),
        ("2026-09-01 16:00:00", "USER-TEST-001", "1.48", "62.8", "18.3", "2950", "4108.0"),
        ("2026-09-01 20:00:00", "USER-TEST-001", "1.46", "62.3", "18.4", "2950", "4112.0"),
        ("2026-09-02 00:00:00", "USER-TEST-001", "1.44", "61.8", "18.5", "2950", "4116.0"),
        ("2026-09-02 04:00:00", "USER-TEST-001", "1.43", "61.5", "18.6", "2950", "4120.0"),
        ("2026-09-02 08:00:00", "USER-TEST-001", "1.47", "62.5", "18.4", "2950", "4124.0"),
        ("2026-09-02 12:00:00", "USER-TEST-001", "1.50", "63.1", "18.3", "2950", "4128.0"),
        ("2026-09-02 16:00:00", "USER-TEST-001", "1.52", "63.7", "18.2", "2950", "4132.0"),
        ("2026-09-02 20:00:00", "USER-TEST-001", "1.49", "62.9", "18.4", "2950", "4136.0"),
    ]
    for row in data_rows:
        f.write(",".join(row) + "\n")

# 4. USER_TEST_001_Maintenance_Schedule.xlsx
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Maintenance Schedule"
headers = ["Task ID", "Equipment Tag", "Equipment Name", "Scheduled Date", "Maintenance Activity", "Interval", "Assigned Lead", "Status"]
ws.append(headers)
schedule_rows = [
    ["TSK-901", "USER-TEST-001", "User Test Pump", "2026-09-15", "Vibration baseline survey & spectrum analysis", "Monthly", "D. Mercer", "Scheduled"],
    ["TSK-902", "USER-TEST-001", "User Test Pump", "2026-10-01", "Lube oil sample extraction & wear metal analysis", "Quarterly", "M. Vance", "Pending"],
    ["TSK-903", "USER-TEST-001", "User Test Pump", "2026-11-15", "Laser shaft alignment verification & coupling check", "Semi-Annual", "M. Vance", "Planned"],
    ["TSK-904", "USER-TEST-001", "User Test Pump", "2027-02-20", "Annual mechanical seal inspection & flush plan overhaul", "Annual", "R. Chen", "Planned"]
]
for r in schedule_rows:
    ws.append(r)
wb.save(str(FIXTURES_DIR / "USER_TEST_001_Maintenance_Schedule.xlsx"))

# 5. USER_TEST_001_PID_Drawing.png
img = Image.new("RGB", (1200, 800), color=(15, 23, 42)) # slate-900 background
draw = ImageDraw.Draw(img)
# Draw borders and title box
draw.rectangle([(20, 20), (1180, 780)], outline=(51, 65, 85), width=2)
draw.rectangle([(800, 680), (1170, 770)], outline=(71, 85, 105), width=2, fill=(30, 41, 59))
draw.text((815, 690), "GULF COAST REFINERY — UNIT 2", fill=(241, 245, 249))
draw.text((815, 715), "PROCESS PIPING & INSTRUMENTATION DIAGRAM", fill=(148, 163, 184))
draw.text((815, 740), "EQUIPMENT: USER-TEST-001 CENTRIFUGAL PUMP", fill=(56, 189, 248))

# Draw Process piping
draw.line([(80, 350), (450, 350)], fill=(56, 189, 248), width=5) # suction line
draw.line([(550, 350), (1100, 350)], fill=(56, 189, 248), width=5) # discharge line

# Draw Pump Symbol
draw.ellipse([(450, 300), (550, 400)], outline=(56, 189, 248), width=4, fill=(15, 23, 42))
draw.polygon([(470, 320), (470, 380), (530, 350)], outline=(56, 189, 248), fill=(56, 189, 248))
draw.text((460, 415), "USER-TEST-001", fill=(255, 255, 255))
draw.text((440, 435), "USER TEST PUMP", fill=(148, 163, 184))

# Draw Instruments
draw.ellipse([(300, 220), (360, 280)], outline=(250, 204, 21), width=2)
draw.line([(330, 280), (330, 350)], fill=(250, 204, 21), width=2)
draw.text((315, 245), "PI-881", fill=(250, 204, 21))

draw.ellipse([(700, 220), (760, 280)], outline=(250, 204, 21), width=2)
draw.line([(730, 280), (730, 350)], fill=(250, 204, 21), width=2)
draw.text((715, 245), "TI-881", fill=(250, 204, 21))

img.save(str(FIXTURES_DIR / "USER_TEST_001_PID_Drawing.png"))

# 6. USER_TEST_001_Shift_Handover.eml
eml_content = """From: operator.lead@gulfcoast-refinery.com
To: shift-handover@gulfcoast-refinery.com
Subject: Shift Handover Log — Unit 2 USER-TEST-001 Operational Status
Date: Wed, 02 Sep 2026 06:30:00 -0500
Message-ID: <shift-log-20260902-USER-TEST-001@refinery.internal>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

SHIFT HANDOVER LOGBOOK RECORD — UNIT 2
==================================================
Date / Time: September 2, 2026 — 06:30 AM Shift Change
Lead Operator: Frank Reynolds (Day Shift Lead)
Relieving Operator: Sarah Jenkins (Night Shift Lead)

PRIMARY ASSET STATUS: USER-TEST-001
Equipment: User Test Pump (Centrifugal Process Pump)
Current Operating Mode: Continuous Duty (Automated Cascade Control)

1. PROCESS PARAMETERS:
- Operating Speed: 2,950 RPM
- Suction Pressure: 2.3 bar
- Discharge Pressure: 18.4 bar
- Flow Rate: 144.5 m3/h

2. CONDITION MONITORING:
- Bearing Drive-End Temp: 62.8 C (Normal, threshold is 75 C)
- Vibration RMS: 1.48 mm/s (Smooth, ISO Class I acceptable)
- Mechanical Seal Flush: Plan 11 active, zero gland leakage noted

3. SHIFT ACTIVITIES & REMARKS:
- Pump USER-TEST-001 completed 24-hour post-overhaul run under WO-8812.
- All operating parameters remain within OEM Model UT-100 specifications.
- No active alarms or process interlocks tripped during shift.
- Handing over custody to Sarah Jenkins.
"""
with open(FIXTURES_DIR / "USER_TEST_001_Shift_Handover.eml", "w", encoding="utf-8") as f:
    f.write(eml_content)

# 7. USER_TEST_002_Inspection.pdf (for TEST C)
create_pdf(
    FIXTURES_DIR / "USER_TEST_002_Inspection.pdf",
    "CONDITION MONITORING & VIBRATION SURVEY — USER-TEST-002",
    [
        "<b>Survey Type:</b> Baseline NDT Vibration Survey",
        "<b>Equipment Tag:</b> USER-TEST-002",
        "<b>Equipment Name:</b> Secondary Booster Pump",
        "<b>Survey Date:</b> 2026-08-30",
        "<b>Inspector:</b> David Mercer (Vibration Analyst Level III)",
        "---",
        "<b>Vibration Summary for USER-TEST-002:</b>",
        "Non-drive end peak velocity measured 2.8 mm/s at 1x RPM running speed.",
        "Harmonic spectral peaks indicate healthy bearing condition for USER-TEST-002.",
        "Next scheduled survey for USER-TEST-002 set for November 2026."
    ]
)

# 8. MULTI_USER_TEST_001_002.pdf (for TEST D)
create_pdf(
    FIXTURES_DIR / "MULTI_USER_TEST_001_002.pdf",
    "CROSS-TRAIN FLUID TRANSFER REPORT — USER-TEST-001 & USER-TEST-002",
    [
        "<b>Document Subject:</b> Dual Asset Inspection & Performance Comparison",
        "<b>Primary Equipment Tags:</b> USER-TEST-001 and USER-TEST-002",
        "<b>Facility:</b> Main Pumping Complex — Unit 2",
        "<b>Inspection Date:</b> 2026-09-05",
        "---",
        "<b>Executive Findings:</b>",
        "This shared operational audit covers both USER-TEST-001 (Lead User Test Pump) and USER-TEST-002 (Standby Booster Pump).",
        "During parallel transfer operations, USER-TEST-001 delivered 145 m3/h while USER-TEST-002 delivered 138 m3/h.",
        "Pressure differential between USER-TEST-001 and USER-TEST-002 remained under 0.4 bar.",
        "Both USER-TEST-001 and USER-TEST-002 require synchronized maintenance shutdown."
    ]
)

# 9. UNKNOWN_USER_TEST_999.pdf (for TEST E)
create_pdf(
    FIXTURES_DIR / "UNKNOWN_USER_TEST_999.pdf",
    "NEW ASSET COMMISSIONING CERTIFICATE — USER-TEST-999",
    [
        "<b>Commissioning Notice:</b> Initial Factory Acceptance Testing",
        "<b>Equipment Tag:</b> USER-TEST-999",
        "<b>Description:</b> Unregistered High-Pressure Injection Skid",
        "<b>Date:</b> 2026-09-10",
        "---",
        "<b>Status:</b>",
        "Skid package USER-TEST-999 delivered to site from manufacturer.",
        "USER-TEST-999 is currently unregistered in plant asset database.",
        "Requires management review and formal onboarding before energization."
    ]
)

# 10. NO_TAG_General_Guide.pdf (for TEST F)
create_pdf(
    FIXTURES_DIR / "NO_TAG_General_Guide.pdf",
    "GENERAL INDUSTRIAL PUMP LUBRICATION & MAINTENANCE GUIDELINES",
    [
        "<b>Document Purpose:</b> General Safety & Operating Best Practices",
        "<b>Target Audience:</b> All Plant Maintenance Technicians",
        "<b>Document Code:</b> GEN-SOP-LUBE-2026",
        "---",
        "<b>General Guidelines:</b>",
        "1. Always de-energize and lock out equipment prior to entering pump volute or bearing housing.",
        "2. Ensure clean grease gun tips to avoid introducing particulate contamination into ball or roller bearings.",
        "3. Monitor casing skin temperature using infrared thermography during initial two hours after startup.",
        "4. Replace mechanical seal face gaskets whenever the gland plate is loosened.",
        "This is a general guideline document and does not specify any particular equipment asset."
    ]
)

print("SUCCESS: All 10 realistic test fixtures generated in", FIXTURES_DIR)
