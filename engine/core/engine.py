"""
Ascend Engine - Main Orchestrator
Coordinates all engine components to generate recommendations.
"""

import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    UserProfile, QueryInput, EngineOutput, ScoringWeights,
    FinancialAction, Recommendation
)
from .normalizer import InputNormalizer, ProfileAnalyzer
from .action_registry import ActionRegistry, ActionGenerator
from .scorer import MultiFactorScorer, AdaptiveScorer
from .dag_builder import DAGBuilder, DAGOptimizer
from .recommender import (
    RecommendationEngine, RecommendationPersonalizer, RecommendationFilter
)


class AscendEngine:
    """
    Main engine class that orchestrates all components.
    
    Usage:
        engine = AscendEngine()
        result = engine.process(profile, query)
    """
    
    def __init__(
        self,
        actions_config_path: Optional[str] = None,
        scoring_weights: Optional[ScoringWeights] = None,
        enable_adaptive_scoring: bool = False
    ):
        """
        Initialize the Ascend Engine.
        
        Args:
            actions_config_path: Path to actions JSON config
            scoring_weights: Custom scoring weights
            enable_adaptive_scoring: Whether to use adaptive scorer
        """
        # Initialize components
        self.normalizer = InputNormalizer()
        self.registry = ActionRegistry(actions_config_path)
        
        if enable_adaptive_scoring:
            self.scorer = AdaptiveScorer(scoring_weights)
        else:
            self.scorer = MultiFactorScorer(scoring_weights)
        
        self.recommender = RecommendationEngine()
        
        # State
        self._last_profile: Optional[UserProfile] = None
        self._last_context: Optional[Dict[str, Any]] = None
    
    def process(
        self,
        profile: UserProfile,
        query: QueryInput,
        max_recommendations: int = 20
    ) -> EngineOutput:
        """
        Process a user query and generate recommendations.
        
        Args:
            profile: User's financial profile
            query: Current query with goals and situation
            max_recommendations: Maximum total recommendations
            
        Returns:
            Complete recommendation output
        """
        start_time = time.time()
        
        # Step 1: Normalize inputs
        normalized_profile = self.normalizer.normalize_profile(profile)
        normalized_query = self.normalizer.normalize_query(query)
        
        # Step 2: Create evaluation context
        context = self.normalizer.create_evaluation_context(
            normalized_profile, normalized_query
        )
        
        # Step 3: Compute priorities
        priorities = ProfileAnalyzer.compute_financial_priorities(
            normalized_profile, normalized_query
        )
        
        # Step 4: Filter applicable actions
        applicable_actions = self.registry.filter_applicable_actions(context)
        
        # Step 5: Generate dynamic actions based on profile
        dynamic_actions = self._generate_dynamic_actions(
            normalized_profile, normalized_query
        )
        applicable_actions.extend(dynamic_actions)
        
        # Step 6: Score all actions
        scores = {}
        breakdowns = {}
        
        for action in applicable_actions:
            score, breakdown = self.scorer.score_action(
                action, normalized_profile, normalized_query, priorities, context
            )
            scores[action.id] = score
            breakdowns[action.id] = breakdown
            action.computed_score = score
        
        # Step 7: Generate recommendations
        output = self.recommender.generate_recommendations(
            applicable_actions,
            scores,
            breakdowns,
            normalized_profile,
            normalized_query,
            priorities
        )
        
        # Step 8: Add personalization
        output = self._personalize_output(output, normalized_profile)
        
        # Record timing
        output.processing_time_ms = (time.time() - start_time) * 1000
        
        # Store state for potential follow-up
        self._last_profile = normalized_profile
        self._last_context = context
        
        return output
    
    def _generate_dynamic_actions(
        self,
        profile: UserProfile,
        query: QueryInput
    ) -> List[FinancialAction]:
        """Generate additional dynamic actions based on profile."""
        dynamic = []
        
        # Generate savings goal action if user has a specific goal
        if query.goal_category == "home_ownership" and not profile.is_homeowner:
            # Estimate down payment needed
            avg_home_price = 400000  # Could be location-based
            down_payment = avg_home_price * 0.20
            monthly_savings = profile.normalized_salary * 0.15
            
            dynamic.append(ActionGenerator.generate_savings_goal_action(
                "Home Down Payment",
                down_payment,
                monthly_savings,
                priority=75
            ))
        
        if query.goal_category == "major_purchase":
            # Generic savings goal
            dynamic.append(ActionGenerator.generate_savings_goal_action(
                "Major Purchase",
                10000,  # Default target
                profile.normalized_salary * 0.10,
                priority=55
            ))
        
        return dynamic
    
    def _personalize_output(
        self,
        output: EngineOutput,
        profile: UserProfile
    ) -> EngineOutput:
        """Add personalization to the output."""
        # Personalize each recommendation
        all_recs = (
            output.immediate + output.short_term + output.medium_term +
            output.long_term + output.extended_term
        )
        
        for rec in all_recs:
            RecommendationPersonalizer.add_estimated_timeline(rec, profile)
        
        return output
    
    def get_quick_wins(self, output: EngineOutput) -> List[Recommendation]:
        """Get quick win recommendations from output."""
        all_recs = (
            output.immediate + output.short_term + output.medium_term
        )
        return RecommendationFilter.filter_quick_wins(all_recs)
    
    def get_action_details(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific action."""
        action = self.registry.get_action(action_id)
        if not action:
            return None
        
        return {
            "id": action.id,
            "name": action.name,
            "description": action.description,
            "category": action.category,
            "subcategory": action.subcategory,
            "horizon": action.horizon.value,
            "risk_level": action.risk_level.value,
            "expected_return": action.expected_return,
            "effort_hours": action.effort_hours,
            "complexity": action.complexity,
            "parameters": action.parameters,
            "impacts": {
                "debt": action.debt_impact,
                "savings": action.savings_impact,
                "income": action.income_impact,
                "protection": action.protection_impact,
                "growth": action.growth_impact
            }
        }
    
    def record_feedback(
        self,
        action_id: str,
        was_helpful: bool
    ) -> None:
        """Record user feedback for adaptive scoring."""
        if isinstance(self.scorer, AdaptiveScorer) and self._last_context:
            self.scorer.record_feedback(action_id, was_helpful, self._last_context)
    
    def export_config(self) -> Dict[str, Any]:
        """Export current engine configuration."""
        return {
            "weights": self.scorer.weights.to_dict() if self.scorer.weights else {},
            "action_count": len(self.registry.actions),
            "categories": self.registry.get_categories(),
            "tags": self.registry.get_tags()
        }


class AscendEngineBuilder:
    """
    Builder pattern for constructing AscendEngine with custom configuration.
    """
    
    def __init__(self):
        self._actions_path: Optional[str] = None
        self._weights: Optional[ScoringWeights] = None
        self._adaptive: bool = False
        self._custom_actions: List[FinancialAction] = []
    
    def with_actions_config(self, path: str) -> 'AscendEngineBuilder':
        """Set custom actions configuration path."""
        self._actions_path = path
        return self
    
    def with_weights(self, weights: ScoringWeights) -> 'AscendEngineBuilder':
        """Set custom scoring weights."""
        self._weights = weights
        return self
    
    def with_adaptive_scoring(self, enabled: bool = True) -> 'AscendEngineBuilder':
        """Enable/disable adaptive scoring."""
        self._adaptive = enabled
        return self
    
    def add_custom_action(self, action: FinancialAction) -> 'AscendEngineBuilder':
        """Add a custom action to the engine."""
        self._custom_actions.append(action)
        return self
    
    def build(self) -> AscendEngine:
        """Build and return the configured engine."""
        engine = AscendEngine(
            actions_config_path=self._actions_path,
            scoring_weights=self._weights,
            enable_adaptive_scoring=self._adaptive
        )
        
        # Add custom actions
        for action in self._custom_actions:
            engine.registry.add_custom_action(action)
        
        return engine


# Convenience functions

def create_profile(
    age_range: str,
    location: str = "Unknown",
    property_value: str = "prefer_not_to_say",
    vehicle_value: str = "prefer_not_to_say",
    investments: str = "prefer_not_to_say",
    debt: str = "prefer_not_to_say",
    monthly_salary: str = "prefer_not_to_say",
    has_dependents: bool = False,
    employment_stability: float = 0.7
) -> UserProfile:
    """Convenience function to create a user profile."""
    return UserProfile(
        age_range=age_range,
        location=location,
        property_value=property_value,
        vehicle_value=vehicle_value,
        investments=investments,
        debt=debt,
        monthly_salary=monthly_salary,
        has_dependents=has_dependents,
        employment_stability=employment_stability
    )


def create_query(
    risk_tolerance: str,
    current_situation: str,
    goal: str
) -> QueryInput:
    """Convenience function to create a query input."""
    return QueryInput(
        risk_tolerance=risk_tolerance,
        current_situation=current_situation,
        goal=goal
    )


def quick_recommend(
    age_range: str,
    monthly_salary: str,
    debt: str,
    investments: str,
    risk_tolerance: str,
    goal: str,
    situation: str = ""
) -> Dict[str, Any]:
    """
    Quick one-liner to get recommendations.
    
    Example:
        result = quick_recommend(
            age_range="25-29",
            monthly_salary="$4k-$5k",
            debt="$25k-$50k",
            investments="$5k-$10k",
            risk_tolerance="medium",
            goal="Pay off student loans and start investing"
        )
    """
    profile = create_profile(
        age_range=age_range,
        monthly_salary=monthly_salary,
        debt=debt,
        investments=investments
    )
    
    query = create_query(
        risk_tolerance=risk_tolerance,
        current_situation=situation or "General financial planning",
        goal=goal
    )
    
    engine = AscendEngine()
    output = engine.process(profile, query)
    
    return output.to_dict()
