"""
Ascend Engine - Data Models
Core data structures for the financial decision engine.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Callable
from enum import Enum
import uuid


class Horizon(Enum):
    """Time horizon for financial actions."""
    IMMEDIATE = "immediate"      # 0-1 month
    SHORT = "short"              # 1-6 months
    MEDIUM = "medium"            # 6-24 months
    LONG = "long"                # 2-10 years
    EXTENDED = "extended"        # 10+ years


class RiskLevel(Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = 1
    MODERATE_CONSERVATIVE = 2
    MODERATE = 3
    MODERATE_AGGRESSIVE = 4
    AGGRESSIVE = 5


class DependencyType(Enum):
    """Types of dependencies between actions."""
    HARD = "hard"          # Must be completed before
    SOFT = "soft"          # Recommended before, but not required
    PARALLEL = "parallel"  # Can be done together
    EXCLUSIVE = "exclusive"  # Cannot be done together


class LifeStage(Enum):
    """Life stages for contextual recommendations."""
    EARLY_CAREER = "early_career"       # 18-29
    CAREER_GROWTH = "career_growth"     # 30-44
    PEAK_EARNING = "peak_earning"       # 45-54
    PRE_RETIREMENT = "pre_retirement"   # 55-64
    EARLY_RETIREMENT = "early_retirement"  # 65-74
    LATE_RETIREMENT = "late_retirement"    # 75+


class FinancialHealth(Enum):
    """Overall financial health assessment."""
    CRITICAL = 1      # High debt, no savings
    STRESSED = 2      # Struggling
    STABLE = 3        # Getting by
    HEALTHY = 4       # Good position
    THRIVING = 5      # Excellent position


@dataclass
class Dependency:
    """Represents a dependency between financial actions."""
    target_action_id: str
    dependency_type: DependencyType
    strength: float = 1.0  # 0-1, how strong the dependency is
    condition: Optional[str] = None  # Condition expression for conditional deps


@dataclass
class Condition:
    """
    A condition that must be met for an action to be applicable.
    Uses a simple expression language for evaluation.
    """
    expression: str  # e.g., "debt_ratio > 0.3", "age >= 50"
    description: str
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against a context dictionary."""
        try:
            # Safe evaluation with limited namespace
            allowed_names = {
                "abs": abs, "min": min, "max": max,
                "len": len, "sum": sum, "any": any, "all": all,
                "True": True, "False": False, "None": None
            }
            allowed_names.update(context)
            return bool(eval(self.expression, {"__builtins__": {}}, allowed_names))
        except Exception:
            return False


@dataclass
class FinancialAction:
    """
    Represents a financial action/recommendation node in the DAG.
    This is the core unit of the recommendation engine.
    """
    id: str
    name: str
    description: str
    horizon: Horizon
    
    # Categorization
    category: str  # e.g., "debt", "savings", "investment", "protection"
    subcategory: str  # e.g., "emergency_fund", "retirement", "insurance"
    tags: List[str] = field(default_factory=list)
    
    # Dependencies
    dependencies: List[Dependency] = field(default_factory=list)
    
    # Conditions for applicability
    conditions: List[Condition] = field(default_factory=list)
    
    # Scoring parameters
    base_priority: float = 50.0  # Base priority score (0-100)
    risk_level: RiskLevel = RiskLevel.MODERATE
    expected_return: float = 0.0  # Expected annual return (decimal)
    volatility: float = 0.0  # Standard deviation of returns
    liquidity: float = 1.0  # 0-1, how liquid the action is
    
    # Effort and complexity
    effort_hours: float = 1.0  # Estimated hours to implement
    complexity: float = 0.5  # 0-1, how complex to understand/execute
    recurring: bool = False  # Is this a one-time or recurring action?
    
    # Impact factors (0-1 scale)
    debt_impact: float = 0.0       # Positive = reduces debt burden
    savings_impact: float = 0.0    # Positive = increases savings
    income_impact: float = 0.0     # Positive = increases income
    protection_impact: float = 0.0  # Positive = increases financial protection
    growth_impact: float = 0.0     # Positive = increases wealth growth
    
    # Parameterization (for dynamic calculations)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Computed fields (set during engine run)
    computed_score: float = 0.0
    is_applicable: bool = True
    applicability_reasons: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, FinancialAction):
            return self.id == other.id
        return False


@dataclass
class UserProfile:
    """User's financial profile - one-time input."""
    # Demographics
    age_range: str  # "18-24", "25-29", etc.
    location: str  # City or postal code
    
    # Assets
    property_value: str  # Range or "prefer_not_to_say"
    vehicle_value: str
    investments: str
    
    # Liabilities
    debt: str
    
    # Income
    monthly_salary: str
    
    # Normalized values (computed)
    normalized_age: float = 0.0
    normalized_property: float = 0.0
    normalized_vehicle: float = 0.0
    normalized_investments: float = 0.0
    normalized_debt: float = 0.0
    normalized_salary: float = 0.0
    
    # Derived metrics (computed)
    debt_to_income_ratio: float = 0.0
    savings_rate: float = 0.0
    net_worth: float = 0.0
    life_stage: LifeStage = LifeStage.EARLY_CAREER
    financial_health: FinancialHealth = FinancialHealth.STABLE
    
    # Additional context
    has_dependents: bool = False
    is_homeowner: bool = False
    has_emergency_fund: bool = False
    employment_stability: float = 0.5  # 0-1


@dataclass
class QueryInput:
    """Per-query input from user."""
    risk_tolerance: str  # "risky", "medium", "reliable"
    current_situation: str  # Free text
    goal: str  # Free text
    
    # Normalized
    normalized_risk: RiskLevel = RiskLevel.MODERATE
    
    # Extracted features (from text analysis)
    situation_keywords: List[str] = field(default_factory=list)
    goal_keywords: List[str] = field(default_factory=list)
    urgency_score: float = 0.5  # 0-1
    goal_category: str = "general"  # Detected goal category


@dataclass
class ScoringWeights:
    """Configurable weights for the scoring algorithm."""
    # Profile factors
    age_weight: float = 0.15
    risk_tolerance_weight: float = 0.20
    financial_health_weight: float = 0.15
    
    # Action factors
    base_priority_weight: float = 0.10
    goal_alignment_weight: float = 0.20
    dependency_weight: float = 0.10
    
    # Outcome factors
    expected_return_weight: float = 0.05
    risk_adjusted_return_weight: float = 0.05
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "age": self.age_weight,
            "risk_tolerance": self.risk_tolerance_weight,
            "financial_health": self.financial_health_weight,
            "base_priority": self.base_priority_weight,
            "goal_alignment": self.goal_alignment_weight,
            "dependency": self.dependency_weight,
            "expected_return": self.expected_return_weight,
            "risk_adjusted_return": self.risk_adjusted_return_weight
        }


@dataclass
class Recommendation:
    """A single recommendation with full context."""
    action: FinancialAction
    score: float
    rank: int
    horizon: Horizon
    
    # Explanation
    reasoning: List[str] = field(default_factory=list)
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Dependencies
    prerequisites: List[str] = field(default_factory=list)
    enables: List[str] = field(default_factory=list)
    
    # Personalization
    personalized_description: str = ""
    estimated_impact: Dict[str, float] = field(default_factory=dict)


@dataclass
class EngineOutput:
    """Complete output from the Ascend Engine."""
    # Horizon-based recommendations
    immediate: List[Recommendation] = field(default_factory=list)
    short_term: List[Recommendation] = field(default_factory=list)
    medium_term: List[Recommendation] = field(default_factory=list)
    long_term: List[Recommendation] = field(default_factory=list)
    extended_term: List[Recommendation] = field(default_factory=list)
    
    # Sequential path (topologically sorted)
    sequential_path: List[Recommendation] = field(default_factory=list)
    
    # Metadata
    profile_summary: Dict[str, Any] = field(default_factory=dict)
    total_actions_considered: int = 0
    total_actions_applicable: int = 0
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        def rec_to_dict(r: Recommendation) -> Dict:
            return {
                "action_id": r.action.id,
                "name": r.action.name,
                "description": r.personalized_description or r.action.description,
                "category": r.action.category,
                "score": round(r.score, 2),
                "rank": r.rank,
                "reasoning": r.reasoning,
                "score_breakdown": {k: round(v, 3) for k, v in r.score_breakdown.items()},
                "prerequisites": r.prerequisites,
                "estimated_impact": r.estimated_impact
            }
        
        return {
            "immediate": [rec_to_dict(r) for r in self.immediate],
            "short_term": [rec_to_dict(r) for r in self.short_term],
            "medium_term": [rec_to_dict(r) for r in self.medium_term],
            "long_term": [rec_to_dict(r) for r in self.long_term],
            "extended_term": [rec_to_dict(r) for r in self.extended_term],
            "sequential_path": [rec_to_dict(r) for r in self.sequential_path],
            "metadata": {
                "profile_summary": self.profile_summary,
                "total_actions_considered": self.total_actions_considered,
                "total_actions_applicable": self.total_actions_applicable,
                "processing_time_ms": round(self.processing_time_ms, 2)
            }
        }
