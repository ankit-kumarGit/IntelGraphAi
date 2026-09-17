from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseIndustrialAgent(ABC):
    """
    Abstract Base Class for Industrial Intelligence Agents.
    Enforces deterministic evidence grounding and prevents hallucination.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def process_query(
        self,
        query: str,
        graphrag_context: Dict[str, Any],
        asset_context: Optional[Dict[str, Any]] = None,
        user_role: str = "Maintenance Engineer"
    ) -> Dict[str, Any]:
        pass
