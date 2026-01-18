"""
Ascend Engine - Multi-Factor Scorer
Computes weighted scores for financial actions based on multiple factors.
"""

from typing import Dict, List, Any, Tuple
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    FinancialAction, UserProfile, QueryInput, ScoringWeights,
    RiskLevel, LifeStage, FinancialHealth, Horizon
)
from utils import FinancialMath, SimilarityUtils


class MultiFactorScorer:
    """
    Computes comprehensive scores for financial actions.
    Uses multiple weighted factors to produce a final score.
    """
    
    # Risk-free rate for Sharpe ratio calculations
    RISK_FREE_RATE = 0.04
    
    # Category to priority area mapping
    CATEGORY_PRIORITY_MAP = {
        "debt": "debt_reduction",
        "savings": "emergency_savings",
        "investment": "growth",
        "protection": "protection",
        "income": "income",
        "optimization": "growth"
    }
    
    def __init__(self, weights: ScoringWeights = None):
        """
        Initialize the scorer.
        
        Args:
            weights: Custom scoring weights (uses defaults if not provided)
        """
        self.weights = weights or ScoringWeights()
    
    def score_action(
        self,
        action: FinancialAction,
        profile: UserProfile,
        query: QueryInput,
        priorities: Dict[str, float],
        context: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute the final score for an action.
        
        Args:
            action: The action to score
            profile: User's profile
            query: Current query
            priorities: Computed priority weights
            context: Full evaluation context
            
        Returns:
            (final_score, score_breakdown)
        """
        breakdown = {}
        
        # 1. Base priority score (0-100 normalized to 0-1)
        base_score = action.base_priority / 100
        breakdown["base_priority"] = base_score * self.weights.base_priority_weight
        
        # 2. Risk alignment score
        risk_score = self._compute_risk_alignment(action, query, profile)
        breakdown["risk_alignment"] = risk_score * self.weights.risk_tolerance_weight
        
        # 3. Goal alignment score
        goal_score = self._compute_goal_alignment(action, query)
        breakdown["goal_alignment"] = goal_score * self.weights.goal_alignment_weight
        
        # 4. Financial health alignment
        health_score = self._compute_health_alignment(action, profile)
        breakdown["financial_health"] = health_score * self.weights.financial_health_weight
        
        # 5. Age/life stage alignment
        age_score = self._compute_age_alignment(action, profile)
        breakdown["age_alignment"] = age_score * self.weights.age_weight
        
        # 6. Risk-adjusted return (Sharpe-like ratio normalized)
        return_score = self._compute_risk_adjusted_return(action)
        breakdown["risk_adjusted_return"] = return_score * self.weights.risk_adjusted_return_weight
        
        # 7. Priority area alignment
        priority_score = self._compute_priority_alignment(action, priorities)
        breakdown["priority_alignment"] = priority_score * 0.15  # Extra weight for priorities
        
        # 8. Urgency adjustment
        urgency_multiplier = self._compute_urgency_multiplier(action, query)
        
        # 9. Dependency bonus/penalty
        dependency_score = self._compute_dependency_score(action, context)
        breakdown["dependency"] = dependency_score * self.weights.dependency_weight
        
        # 10. Effort-adjusted score (prefer lower effort for similar outcomes)
        effort_adjustment = self._compute_effort_adjustment(action)
        
        # Compute weighted sum
        total_weight = sum([
            self.weights.base_priority_weight,
            self.weights.risk_tolerance_weight,
            self.weights.goal_alignment_weight,
            self.weights.financial_health_weight,
            self.weights.age_weight,
            self.weights.risk_adjusted_return_weight,
            0.15,  # Priority alignment
            self.weights.dependency_weight
        ])
        
        raw_score = sum(breakdown.values()) / total_weight
        
        # Apply multipliers
        final_score = raw_score * urgency_multiplier * effort_adjustment
        
        # Normalize to 0-100
        final_score = min(100, max(0, final_score * 100))
        
        return final_score, breakdown
    
    def _compute_risk_alignment(
        self,
        action: FinancialAction,
        query: QueryInput,
        profile: UserProfile
    ) -> float:
        """
        Compute how well the action's risk matches user's risk tolerance.
        """
        user_risk = query.normalized_risk.value  # 1-5
        action_risk = action.risk_level.value  # 1-5
        
        # Perfect match = 1.0, decreases with distance
        risk_diff = abs(user_risk - action_risk)
        base_alignment = 1.0 - (risk_diff * 0.2)  # 20% penalty per level
        
        # Bonus for conservative actions when financial health is poor
        if profile.financial_health.value <= FinancialHealth.STRESSED.value:
            if action_risk <= 2:  # Conservative action
                base_alignment += 0.2
            elif action_risk >= 4:  # Risky action
                base_alignment -= 0.2
        
        return max(0, min(1, base_alignment))
    
    def _compute_goal_alignment(
        self,
        action: FinancialAction,
        query: QueryInput
    ) -> float:
        """
        Compute how well the action aligns with the user's stated goal.
        """
        # Goal category to action mapping
        goal_action_map = {
            "debt_freedom": ["debt", "optimization"],
            "emergency_savings": ["savings"],
            "retirement": ["investment"],
            "wealth_building": ["investment", "income"],
            "home_ownership": ["savings", "debt"],
            "income_increase": ["income"],
            "financial_protection": ["protection"],
            "education": ["savings", "investment"],
            "major_purchase": ["savings"]
        }
        
        score = 0.5  # Base score
        
        # Category alignment
        relevant_categories = goal_action_map.get(query.goal_category, [])
        if action.category in relevant_categories:
            score += 0.3
        
        # Keyword alignment
        combined_keywords = set(query.goal_keywords + query.situation_keywords)
        action_keywords = set(action.tags + [action.category, action.subcategory])
        
        overlap = SimilarityUtils.jaccard_similarity(combined_keywords, action_keywords)
        score += overlap * 0.2
        
        # Tag-based alignment
        goal_tags = {
            "debt_freedom": ["debt", "foundation"],
            "retirement": ["retirement", "tax_advantaged"],
            "wealth_building": ["growth", "passive"],
            "financial_protection": ["insurance", "protection", "estate"]
        }
        
        relevant_tags = goal_tags.get(query.goal_category, [])
        tag_overlap = len(set(action.tags) & set(relevant_tags))
        if tag_overlap > 0:
            score += 0.1 * min(tag_overlap, 2)
        
        return min(1, score)
    
    def _compute_health_alignment(
        self,
        action: FinancialAction,
        profile: UserProfile
    ) -> float:
        """
        Compute how appropriate the action is for the user's financial health.
        """
        health = profile.financial_health.value  # 1-5
        
        # Foundation actions are better for lower health
        is_foundation = "foundation" in action.tags
        
        # Growth actions better for higher health
        is_growth = action.category == "investment" or action.growth_impact > 0.5
        
        # Debt actions better for lower health
        is_debt = action.category == "debt"
        
        # Protection actions important at all levels but especially stable+
        is_protection = action.category == "protection"
        
        score = 0.5  # Base
        
        if health <= 2:  # Critical or Stressed
            if is_foundation or is_debt:
                score += 0.4
            if is_growth and action.risk_level.value >= 4:
                score -= 0.3  # Penalize risky growth
        
        elif health == 3:  # Stable
            if is_foundation:
                score += 0.2
            if is_debt:
                score += 0.2
            if is_protection:
                score += 0.1
        
        elif health >= 4:  # Healthy or Thriving
            if is_growth:
                score += 0.3
            if is_protection:
                score += 0.2
            if is_foundation:
                score -= 0.1  # Slightly less urgent
        
        return max(0, min(1, score))
    
    def _compute_age_alignment(
        self,
        action: FinancialAction,
        profile: UserProfile
    ) -> float:
        """
        Compute how appropriate the action is for the user's age/life stage.
        """
        age = profile.normalized_age
        stage = profile.life_stage
        
        score = 0.5  # Base
        
        # Time horizon alignment
        horizon_years = {
            Horizon.IMMEDIATE: 0.5,
            Horizon.SHORT: 1,
            Horizon.MEDIUM: 3,
            Horizon.LONG: 10,
            Horizon.EXTENDED: 20
        }
        
        years_to_retirement = max(0, 65 - age)
        action_years = horizon_years.get(action.horizon, 5)
        
        # Penalize long-term actions close to retirement
        if years_to_retirement < action_years:
            score -= 0.2
        
        # Life stage specific adjustments
        if stage == LifeStage.EARLY_CAREER:
            if action.growth_impact > 0.5:
                score += 0.2
            if "career" in action.tags or "income" in action.tags:
                score += 0.2
        
        elif stage == LifeStage.CAREER_GROWTH:
            if action.category == "protection" and profile.has_dependents:
                score += 0.3
            if action.subcategory == "retirement":
                score += 0.2
        
        elif stage == LifeStage.PEAK_EARNING:
            if "tax_advantaged" in action.tags:
                score += 0.2
            if action.subcategory in ["retirement", "estate"]:
                score += 0.2
        
        elif stage == LifeStage.PRE_RETIREMENT:
            if action.protection_impact > 0.5:
                score += 0.3
            if action.risk_level.value >= 4:
                score -= 0.3
        
        elif stage in [LifeStage.EARLY_RETIREMENT, LifeStage.LATE_RETIREMENT]:
            if action.liquidity > 0.7:
                score += 0.2
            if "retirement" in action.subcategory:
                score -= 0.1  # Already retired
            if action.risk_level.value >= 4:
                score -= 0.4
        
        return max(0, min(1, score))
    
    def _compute_risk_adjusted_return(self, action: FinancialAction) -> float:
        """
        Compute risk-adjusted return score.
        """
        if action.volatility == 0:
            # No volatility = guaranteed return
            if action.expected_return > 0:
                return min(1, action.expected_return / 0.2)  # Cap at 20%
            return 0.5  # Neutral for non-return actions
        
        sharpe = FinancialMath.calculate_sharpe_ratio(
            action.expected_return,
            self.RISK_FREE_RATE,
            action.volatility
        )
        
        # Normalize Sharpe ratio to 0-1
        # Good Sharpe: 1-2, Excellent: 2+
        return FinancialMath.sigmoid(sharpe, k=1, midpoint=1)
    
    def _compute_priority_alignment(
        self,
        action: FinancialAction,
        priorities: Dict[str, float]
    ) -> float:
        """
        Compute alignment with computed priority areas.
        """
        priority_area = self.CATEGORY_PRIORITY_MAP.get(action.category, "growth")
        base_priority = priorities.get(priority_area, 0.5)
        
        # Also consider impact factors
        impact_scores = [
            (action.debt_impact, priorities.get("debt_reduction", 0.5)),
            (action.savings_impact, priorities.get("emergency_savings", 0.5)),
            (action.growth_impact, priorities.get("growth", 0.5)),
            (action.protection_impact, priorities.get("protection", 0.5)),
            (action.income_impact, priorities.get("income", 0.5))
        ]
        
        weighted_impact = sum(impact * priority for impact, priority in impact_scores)
        total_impact = sum(impact for impact, _ in impact_scores)
        
        if total_impact > 0:
            avg_impact = weighted_impact / total_impact
            return (base_priority + avg_impact) / 2
        
        return base_priority
    
    def _compute_urgency_multiplier(
        self,
        action: FinancialAction,
        query: QueryInput
    ) -> float:
        """
        Compute urgency multiplier based on user's urgency and action horizon.
        """
        urgency = query.urgency_score  # 0-1
        
        # Immediate actions get boost when urgency is high
        if action.horizon == Horizon.IMMEDIATE:
            return 1.0 + (urgency * 0.3)  # Up to 30% boost
        elif action.horizon == Horizon.SHORT:
            return 1.0 + (urgency * 0.15)
        elif action.horizon == Horizon.LONG:
            return 1.0 - (urgency * 0.1)  # Slight penalty for long-term when urgent
        
        return 1.0
    
    def _compute_dependency_score(
        self,
        action: FinancialAction,
        context: Dict[str, Any]
    ) -> float:
        """
        Compute score adjustment based on dependencies.
        """
        if not action.dependencies:
            return 0.7  # Neutral-positive for independent actions
        
        # Check if dependencies are likely met
        # This is heuristic since we don't track action completion
        
        score = 0.5
        
        for dep in action.dependencies:
            if dep.dependency_type.value == "hard":
                # Hard dependencies reduce score if likely not met
                # Use heuristics based on financial health
                health = context.get("financial_health", FinancialHealth.STABLE)
                if health.value >= FinancialHealth.HEALTHY.value:
                    score += 0.1  # Likely met
                else:
                    score -= 0.1  # Likely not met
            else:
                # Soft dependencies have less impact
                score += 0.05
        
        return max(0, min(1, score))
    
    def _compute_effort_adjustment(self, action: FinancialAction) -> float:
        """
        Adjust score based on effort required.
        Lower effort = slight bonus.
        """
        # Effort hours: 1-100
        # Complexity: 0-1
        
        effort_factor = action.effort_hours * (1 + action.complexity)
        
        # Normalize: very easy (1-5 effort) = 1.1x, very hard (50+) = 0.95x
        if effort_factor <= 5:
            return 1.1
        elif effort_factor <= 10:
            return 1.05
        elif effort_factor <= 25:
            return 1.0
        elif effort_factor <= 50:
            return 0.98
        else:
            return 0.95


class AdaptiveScorer(MultiFactorScorer):
    """
    Extended scorer that adapts weights based on historical performance.
    Uses simple learning to adjust scoring over time.
    """
    
    def __init__(self, weights: ScoringWeights = None):
        super().__init__(weights)
        self.feedback_history: List[Dict[str, Any]] = []
    
    def record_feedback(
        self,
        action_id: str,
        was_helpful: bool,
        context: Dict[str, Any]
    ) -> None:
        """
        Record user feedback for future weight adjustment.
        """
        self.feedback_history.append({
            "action_id": action_id,
            "helpful": was_helpful,
            "context_summary": {
                "goal_category": context.get("goal_category"),
                "financial_health": context.get("financial_health"),
                "life_stage": context.get("life_stage"),
                "risk": context.get("normalized_risk")
            }
        })
    
    def adjust_weights(self) -> None:
        """
        Adjust weights based on accumulated feedback.
        Simple heuristic approach.
        """
        if len(self.feedback_history) < 10:
            return  # Need minimum feedback
        
        # Count helpful by category
        helpful_by_goal = {}
        for feedback in self.feedback_history:
            goal = feedback["context_summary"].get("goal_category", "general")
            if goal not in helpful_by_goal:
                helpful_by_goal[goal] = {"helpful": 0, "total": 0}
            
            helpful_by_goal[goal]["total"] += 1
            if feedback["helpful"]:
                helpful_by_goal[goal]["helpful"] += 1
        
        # Adjust goal alignment weight based on effectiveness
        overall_rate = sum(g["helpful"] for g in helpful_by_goal.values()) / \
                       max(1, sum(g["total"] for g in helpful_by_goal.values()))
        
        if overall_rate > 0.7:
            # Recommendations are working well
            pass
        elif overall_rate < 0.5:
            # Need to adjust - increase goal alignment weight
            self.weights.goal_alignment_weight = min(0.3, 
                self.weights.goal_alignment_weight * 1.1)
