"""
Laboratory Resolver Service Interface
"""
from typing import List
from backend.app.schemas.labs import ExtractedLabItem, ResolvedLabItem
from backend.app.agents.lab_resolver.loinc_resolver import resolve_lab_item

class LabResolverService:
    @staticmethod
    def resolve_items(items: List[ExtractedLabItem]) -> List[ResolvedLabItem]:
        return [resolve_lab_item(item) for item in items]

lab_resolver_service = LabResolverService()
