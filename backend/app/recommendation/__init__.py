"""
Phase 8: Recommendation Agent — Module Init
"""

from app.recommendation.models import (
    SupplierCandidate,
    RecommendationResult,
    ProcurementNote,
    MCDMCriteria,
)
from app.recommendation.topsis import TOPSISSolver
from app.recommendation.cosine_sim import CosineSimilarityMatcher
from app.recommendation.mcdm import MCDMEngine
from app.recommendation.ranker import RecommendationRanker
from app.recommendation.explainer import RecommendationExplainer
from app.recommendation.pipeline import RecommendationPipeline

__all__ = [
    "SupplierCandidate",
    "RecommendationResult",
    "ProcurementNote",
    "MCDMCriteria",
    "TOPSISSolver",
    "CosineSimilarityMatcher",
    "MCDMEngine",
    "RecommendationRanker",
    "RecommendationExplainer",
    "RecommendationPipeline",
]
