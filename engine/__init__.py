"""
Ascend Engine - Deterministic Financial Decision Engine
A robust, graph-based recommendation system for personalized financial planning.

Features:
- DAG-based action dependency management
- Multi-factor scoring with configurable weights
- Profile normalization and derived metrics
- Goal and situation text analysis
- ML-based profile clustering
- Adaptive scoring from feedback
- Horizon-based recommendation grouping

Quick Start:
    from engine import AscendEngine, create_profile, create_query
    
    engine = AscendEngine()
    
    profile = create_profile(
        age_range="25-29",
        monthly_salary="$4k-$5k",
        debt="$25k-$50k",
        investments="$5k-$10k"
    )
    
    query = create_query(
        risk_tolerance="medium",
        current_situation="Just started a new job, want to get finances in order",
        goal="Pay off student loans and start building wealth"
    )
    
    result = engine.process(profile, query)
    print(result.to_dict())

One-liner:
    from engine import quick_recommend
    
    result = quick_recommend(
        age_range="30-34",
        monthly_salary="$5k-$6k",
        debt="$10k-$25k",
        investments="$25k-$50k",
        risk_tolerance="medium",
        goal="Save for a house down payment"
    )
"""

__version__ = "1.0.0"
__author__ = "Ascend Engine Team"

# Core classes
from .core.engine import (
    AscendEngine,
    AscendEngineBuilder,
    create_profile,
    create_query,
    quick_recommend
)

# Models
from .models import (
    UserProfile,
    QueryInput,
    FinancialAction,
    Recommendation,
    EngineOutput,
    Horizon,
    RiskLevel,
    LifeStage,
    FinancialHealth,
    ScoringWeights,
    Condition,
    Dependency,
    DependencyType
)

# Core components (for advanced usage)
from .core.normalizer import InputNormalizer, ProfileAnalyzer
from .core.action_registry import ActionRegistry, ActionGenerator
from .core.scorer import MultiFactorScorer, AdaptiveScorer
from .core.dag_builder import DAGBuilder, DAGOptimizer
from .core.recommender import (
    RecommendationEngine,
    RecommendationPersonalizer,
    RecommendationFilter
)

# ML components
from .ml import (
    ProfileVectorizer,
    KMeansCluster,
    ProfileClusterEngine,
    SimilarityEngine,
    GoalSimilarityEngine,
    RecommendationLearner
)

# Utilities
from .utils import (
    KeywordExtractor,
    FinancialMath,
    RangeParser,
    ConfigLoader,
    GraphUtils,
    SimilarityUtils
)

__all__ = [
    # Main engine
    "AscendEngine",
    "AscendEngineBuilder",
    "create_profile",
    "create_query",
    "quick_recommend",
    
    # Models
    "UserProfile",
    "QueryInput",
    "FinancialAction",
    "Recommendation",
    "EngineOutput",
    "Horizon",
    "RiskLevel",
    "LifeStage",
    "FinancialHealth",
    "ScoringWeights",
    "Condition",
    "Dependency",
    "DependencyType",
    
    # Core components
    "InputNormalizer",
    "ProfileAnalyzer",
    "ActionRegistry",
    "ActionGenerator",
    "MultiFactorScorer",
    "AdaptiveScorer",
    "DAGBuilder",
    "DAGOptimizer",
    "RecommendationEngine",
    "RecommendationPersonalizer",
    "RecommendationFilter",
    
    # ML components
    "ProfileVectorizer",
    "KMeansCluster",
    "ProfileClusterEngine",
    "SimilarityEngine",
    "GoalSimilarityEngine",
    "RecommendationLearner",
    
    # Utilities
    "KeywordExtractor",
    "FinancialMath",
    "RangeParser",
    "ConfigLoader",
    "GraphUtils",
    "SimilarityUtils"
]
