import re
from typing import Dict, Any, List, Optional

class EntityResolutionService:
    KNOWN_TAG_ALIASES = {
        "P-101": ["P101", "PUMP 101", "PUMP-101", "CENTRIFUGAL PUMP 101", "TAG-P101"],
        "P-102": ["P102", "PUMP 102", "PUMP-102", "TAG-P102"],
        "C-201": ["C201", "COMPRESSOR 201", "COMP-201", "TAG-C201"],
        "M-301": ["M301", "MOTOR 301", "INDUCTION MOTOR 301", "TAG-M301"],
        "P-205": ["P205", "PUMP 205", "SLURRY PUMP 205", "TAG-P205"]
    }

    @classmethod
    def resolve_asset_tag(cls, raw_input: str) -> Dict[str, Any]:
        """
        Normalizes equipment tag variations and calculates match confidence.
        If confidence < 0.90, marks as requiring human confirmation.
        """
        clean_input = re.sub(r"[^\w\s-]", "", raw_input).strip().upper()
        
        # Direct exact match
        for canonical, aliases in cls.KNOWN_TAG_ALIASES.items():
            if clean_input == canonical:
                return {
                    "canonical_tag": canonical,
                    "confidence": 1.0,
                    "match_type": "exact",
                    "requires_confirmation": False
                }
            if clean_input in [a.upper() for a in aliases]:
                return {
                    "canonical_tag": canonical,
                    "confidence": 0.95,
                    "match_type": "alias_exact",
                    "requires_confirmation": False
                }

        # Substring / fuzzy heuristic
        for canonical, aliases in cls.KNOWN_TAG_ALIASES.items():
            core_digits = re.findall(r"\d+", canonical)
            input_digits = re.findall(r"\d+", clean_input)
            if core_digits and input_digits and core_digits[0] == input_digits[0]:
                return {
                    "canonical_tag": canonical,
                    "confidence": 0.82,
                    "match_type": "heuristic_digits",
                    "requires_confirmation": True
                }

        # Fallback
        return {
            "canonical_tag": clean_input if clean_input else "UNKNOWN",
            "confidence": 0.40,
            "match_type": "unmatched",
            "requires_confirmation": True
        }

entity_resolution = EntityResolutionService()
