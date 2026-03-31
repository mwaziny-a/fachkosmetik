from typing import List, Dict, Any
from models.schemas import RecommendationItem, InterventionLevel

INTERVENTION_ORDER = {
    InterventionLevel.NONE: 0, InterventionLevel.LOW: 1,
    InterventionLevel.MEDIUM: 2, InterventionLevel.HIGH: 3,
    InterventionLevel.SPECIALIST: 4,
}


class RecommendationEngine:
    def rank_recommendations(self, items: List[RecommendationItem]) -> List[RecommendationItem]:
        return sorted(items, key=lambda r: (INTERVENTION_ORDER.get(r.intervention_level, 99), r.priority))

    def rank_all_categories(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        rec_fields = [
            "skincare_recommendations", "grooming_recommendations", "hairstyle_recommendations",
            "beard_recommendations", "makeup_recommendations", "non_invasive_options",
            "injectables_to_discuss", "procedural_surgical_consultation",
        ]
        for field in rec_fields:
            if field in report_data and isinstance(report_data[field], list):
                items = []
                for item in report_data[field]:
                    try:
                        items.append(RecommendationItem(**item) if isinstance(item, dict) else item)
                    except Exception:
                        pass
                report_data[field] = [r.dict() for r in self.rank_recommendations(items)]
        return report_data