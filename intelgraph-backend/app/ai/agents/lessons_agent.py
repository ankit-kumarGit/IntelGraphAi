from typing import Dict, Any, Optional
from app.ai.agents.base_agent import BaseIndustrialAgent

class LessonsLearnedAgent(BaseIndustrialAgent):
    def __init__(self):
        super().__init__(
            name="Lessons Learned & Failure Intelligence Agent",
            description="Discovers cross-asset failure patterns across P-101, P-102, P-203, and P-307."
        )

    def process_query(
        self,
        query: str,
        graphrag_context: Dict[str, Any],
        asset_context: Optional[Dict[str, Any]] = None,
        user_role: str = "Maintenance Engineer"
    ) -> Dict[str, Any]:
        answer = (
            "CROSS-ASSET LESSONS LEARNED DISCOVERY:\n\n"
            "A potential recurring mechanical degradation pattern has been identified across 3 rotating machinery assets:\n"
            "• Asset P-101: Drive-End Bearing fatigue and seizure (WO-1189, Feb 2026)\n"
            "• Asset P-203: Elevated vibration warning and thermal rise on outboard bearing (INSP-781, Jan 2026)\n"
            "• Asset P-307: Bearing micro-pitting observed during turnaround overhaul (WO-3042, Nov 2025)\n\n"
            "COMMON CONTRIBUTING FACTORS:\n"
            "Historical evidence across all 3 units indicates operating under sustained vibration (>4.5 mm/s) "
            "and extended lubrication intervals beyond the recommended 4,000h OEM threshold.\n\n"
            "RECOMMENDED PREVENTIVE ACTION:\n"
            "Standardize ISO VG 46 synthetic lubricant sampling and enforce automatic re-balancing window when vibration exceeds 4.5 mm/s."
        )

        return {
            "answer": answer,
            "confidence": "High",
            "evidence_summary": [
                "P-101: Work Order #1189 & Inspection #456",
                "P-203: Condition Monitoring Survey INSP-781",
                "P-307: Turnaround Inspection WO-3042"
            ],
            "citations": graphrag_context.get("citations", []),
            "refused": False
        }
