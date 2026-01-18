"""
Ascend Engine - Recommendation Engine
Generates personalized financial recommendations from scored actions.
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    FinancialAction, UserProfile, QueryInput, Recommendation,
    EngineOutput, Horizon, ScoringWeights, LifeStage
)
from .normalizer import ProfileAnalyzer
from .dag_builder import DAGBuilder, DAGOptimizer


class RecommendationEngine:
    """
    Generates structured recommendations from scored actions.
    Handles prioritization, grouping, and personalization.
    """
    
    # Maximum recommendations per horizon
    MAX_PER_HORIZON = 5
    MAX_TOTAL = 20
    
    def __init__(self):
        self.dag = DAGBuilder()
    
    def generate_recommendations(
        self,
        actions: List[FinancialAction],
        scores: Dict[str, float],
        score_breakdowns: Dict[str, Dict[str, float]],
        profile: UserProfile,
        query: QueryInput,
        priorities: Dict[str, float]
    ) -> EngineOutput:
        """
        Generate complete recommendation output.
        
        Args:
            actions: List of applicable actions
            scores: Dict of action_id -> score
            score_breakdowns: Dict of action_id -> score component breakdown
            profile: User profile
            query: Current query
            priorities: Computed priority weights
            
        Returns:
            Complete EngineOutput with recommendations
        """
        # Build DAG with scores
        self.dag.build_dag(actions, scores)
        
        # Create recommendations from actions
        recommendations = self._create_recommendations(
            actions, scores, score_breakdowns, profile, query
        )
        
        # Group by horizon
        horizon_groups = self._group_by_horizon(recommendations)
        
        # Generate sequential path
        sequential = self._generate_sequential_path(recommendations)
        
        # Create profile summary
        profile_summary = self._create_profile_summary(profile, query, priorities)
        
        return EngineOutput(
            immediate=horizon_groups.get(Horizon.IMMEDIATE, [])[:self.MAX_PER_HORIZON],
            short_term=horizon_groups.get(Horizon.SHORT, [])[:self.MAX_PER_HORIZON],
            medium_term=horizon_groups.get(Horizon.MEDIUM, [])[:self.MAX_PER_HORIZON],
            long_term=horizon_groups.get(Horizon.LONG, [])[:self.MAX_PER_HORIZON],
            extended_term=horizon_groups.get(Horizon.EXTENDED, [])[:self.MAX_PER_HORIZON],
            sequential_path=sequential[:self.MAX_TOTAL],
            profile_summary=profile_summary,
            total_actions_considered=len(actions),
            total_actions_applicable=len([a for a in actions if a.is_applicable])
        )
    
    def _create_recommendations(
        self,
        actions: List[FinancialAction],
        scores: Dict[str, float],
        breakdowns: Dict[str, Dict[str, float]],
        profile: UserProfile,
        query: QueryInput
    ) -> List[Recommendation]:
        """Create Recommendation objects from actions."""
        recommendations = []
        
        # Sort by score
        sorted_actions = sorted(
            actions,
            key=lambda a: scores.get(a.id, 0),
            reverse=True
        )
        
        for rank, action in enumerate(sorted_actions, 1):
            score = scores.get(action.id, 0)
            breakdown = breakdowns.get(action.id, {})
            
            rec = Recommendation(
                action=action,
                score=score,
                rank=rank,
                horizon=action.horizon,
                reasoning=self._generate_reasoning(action, breakdown, profile, query),
                score_breakdown=breakdown,
                prerequisites=self._get_prerequisite_names(action),
                enables=self._get_enabled_names(action),
                personalized_description=self._personalize_description(action, profile),
                estimated_impact=self._estimate_impact(action, profile)
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_reasoning(
        self,
        action: FinancialAction,
        breakdown: Dict[str, float],
        profile: UserProfile,
        query: QueryInput
    ) -> List[str]:
        """Generate human-readable reasoning for a recommendation."""
        reasons = []
        
        # Find top scoring factors
        if breakdown:
            sorted_factors = sorted(
                breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for factor, value in sorted_factors[:3]:
                if value > 0.05:  # Only significant factors
                    reason = self._factor_to_reason(factor, value, profile, query)
                    if reason:
                        reasons.append(reason)
        
        # Add action-specific reasoning
        if action.category == "debt" and profile.debt_to_income_ratio > 0.2:
            reasons.append("Addresses your significant debt burden")
        
        if action.category == "savings" and not profile.has_emergency_fund:
            reasons.append("Builds essential financial safety net")
        
        if action.subcategory == "retirement" and profile.life_stage in [
            LifeStage.EARLY_CAREER, LifeStage.CAREER_GROWTH, LifeStage.PEAK_EARNING
        ]:
            reasons.append("Maximizes long-term compound growth potential")
        
        if action.category == "protection" and profile.has_dependents:
            reasons.append("Protects your family's financial security")
        
        # Add goal alignment reason
        if query.goal_category == "debt_freedom" and action.debt_impact > 0.5:
            reasons.append(f"Directly supports your goal of becoming debt-free")
        elif query.goal_category == "retirement" and action.subcategory == "retirement":
            reasons.append(f"Directly supports your retirement goals")
        elif query.goal_category == "wealth_building" and action.growth_impact > 0.5:
            reasons.append(f"Directly supports your wealth building goal")
        
        return reasons[:5]  # Max 5 reasons
    
    def _factor_to_reason(
        self,
        factor: str,
        value: float,
        profile: UserProfile,
        query: QueryInput
    ) -> Optional[str]:
        """Convert a scoring factor to a human-readable reason."""
        factor_reasons = {
            "base_priority": "High-priority financial action",
            "risk_alignment": f"Matches your {query.risk_tolerance} risk preference",
            "goal_alignment": f"Aligns with your goal: {query.goal[:50]}",
            "financial_health": f"Appropriate for your current financial situation",
            "age_alignment": f"Well-suited for your life stage ({profile.life_stage.value})",
            "risk_adjusted_return": "Offers favorable risk-adjusted returns",
            "priority_alignment": "Addresses a key priority area for you",
            "dependency": "Foundation for future financial growth"
        }
        
        return factor_reasons.get(factor)
    
    def _get_prerequisite_names(self, action: FinancialAction) -> List[str]:
        """Get names of prerequisite actions."""
        prereqs = self.dag.get_prerequisites(action.id)
        return [p.name for p in prereqs]
    
    def _get_enabled_names(self, action: FinancialAction) -> List[str]:
        """Get names of actions this enables."""
        enabled = self.dag.get_enabled_actions(action.id)
        return [e.name for e in enabled[:5]]  # Limit to top 5
    
    def _personalize_description(
        self,
        action: FinancialAction,
        profile: UserProfile
    ) -> str:
        """Create a personalized description of the action."""
        desc = action.description
        
        # Personalize based on profile
        params = action.parameters
        
        if "target_amount" in params:
            target = params["target_amount"]
            if profile.normalized_salary > 0:
                months = target / (profile.normalized_salary * 0.1)  # 10% savings
                desc += f" (approximately {months:.0f} months at 10% savings rate)"
        
        if "months_coverage" in params:
            months = params["months_coverage"]
            expenses = profile.normalized_salary * 0.7
            target = expenses * months
            desc = f"Build {months} months of expenses (${target:,.0f}) in accessible savings"
        
        if "annual_limit" in params and profile.normalized_age >= 50:
            if "catch_up_limit" in params:
                desc += f" (includes ${params['catch_up_limit'] - params['annual_limit']:,} catch-up contribution)"
        
        return desc
    
    def _estimate_impact(
        self,
        action: FinancialAction,
        profile: UserProfile
    ) -> Dict[str, float]:
        """Estimate the financial impact of the action."""
        impact = {}
        
        # Debt impact
        if action.debt_impact > 0 and profile.normalized_debt > 0:
            potential_reduction = profile.normalized_debt * action.debt_impact * 0.3
            impact["potential_debt_reduction"] = potential_reduction
        
        # Savings impact
        if action.savings_impact > 0:
            monthly_savings = profile.normalized_salary * 0.1 * action.savings_impact
            impact["monthly_savings_boost"] = monthly_savings
        
        # Income impact
        if action.income_impact > 0:
            annual_income = profile.normalized_salary * 12
            potential_increase = annual_income * action.income_impact * 0.1
            impact["potential_annual_income_increase"] = potential_increase
        
        # Growth impact (10-year projection)
        if action.growth_impact > 0 and action.expected_return > 0:
            from utils import FinancialMath
            monthly_contrib = profile.normalized_salary * 0.1
            fv = FinancialMath.calculate_compound_growth(
                0, action.expected_return, 10, monthly_contrib
            )
            impact["projected_10_year_growth"] = fv * action.growth_impact
        
        return impact
    
    def _group_by_horizon(
        self,
        recommendations: List[Recommendation]
    ) -> Dict[Horizon, List[Recommendation]]:
        """Group recommendations by time horizon."""
        groups = defaultdict(list)
        
        for rec in recommendations:
            groups[rec.horizon].append(rec)
        
        # Sort each group by score
        for horizon in groups:
            groups[horizon].sort(key=lambda r: r.score, reverse=True)
        
        return dict(groups)
    
    def _generate_sequential_path(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        Generate a sequential execution path respecting dependencies.
        """
        # Get topological order from DAG
        sorted_ids = self.dag.topological_sort_with_scores()
        
        # Create lookup
        rec_by_id = {rec.action.id: rec for rec in recommendations}
        
        # Build sequential list
        sequential = []
        for action_id in sorted_ids:
            if action_id in rec_by_id:
                sequential.append(rec_by_id[action_id])
        
        return sequential
    
    def _create_profile_summary(
        self,
        profile: UserProfile,
        query: QueryInput,
        priorities: Dict[str, float]
    ) -> Dict[str, Any]:
        """Create a summary of the user's financial profile."""
        # Identify gaps
        gaps = ProfileAnalyzer.identify_financial_gaps(profile)
        
        # Top priorities
        top_priorities = sorted(
            priorities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "life_stage": profile.life_stage.value,
            "financial_health": profile.financial_health.value,
            "risk_tolerance": query.normalized_risk.value,
            "goal_category": query.goal_category,
            "net_worth": profile.net_worth,
            "debt_to_income_ratio": round(profile.debt_to_income_ratio, 2),
            "savings_rate": round(profile.savings_rate, 2),
            "identified_gaps": list(gaps.keys()),
            "top_priorities": [p[0] for p in top_priorities],
            "has_emergency_fund": profile.has_emergency_fund,
            "is_homeowner": profile.is_homeowner,
            "has_dependents": profile.has_dependents
        }


class RecommendationPersonalizer:
    """
    Adds additional personalization to recommendations.
    """
    
    @staticmethod
    def add_estimated_timeline(
        recommendation: Recommendation,
        profile: UserProfile
    ) -> Recommendation:
        """Add estimated completion timeline."""
        action = recommendation.action
        
        # Base timeline from effort hours
        weeks = action.effort_hours / 5  # Assuming 5 hours/week available
        
        # Adjust for recurring actions
        if action.recurring:
            # Estimate time to meaningful impact
            if action.category == "savings":
                # Time to reach target
                target = action.parameters.get("target_amount", 1000)
                monthly_savings = profile.normalized_salary * 0.1
                if monthly_savings > 0:
                    months = target / monthly_savings
                    weeks = max(weeks, months * 4)
        
        recommendation.estimated_impact["estimated_weeks"] = weeks
        return recommendation
    
    @staticmethod
    def add_next_steps(
        recommendation: Recommendation
    ) -> Recommendation:
        """Add concrete next steps for the action."""
        action = recommendation.action
        
        next_steps = []
        
        if action.category == "savings":
            next_steps.extend([
                "Open a high-yield savings account if you don't have one",
                "Set up automatic transfers from checking",
                "Track progress monthly"
            ])
        elif action.category == "debt":
            next_steps.extend([
                "List all debts with balances and interest rates",
                "Calculate total monthly payments",
                "Contact lenders about payment options"
            ])
        elif action.category == "investment":
            next_steps.extend([
                "Review current investment accounts",
                "Check current contribution rates",
                "Evaluate fund options and fees"
            ])
        elif action.category == "protection":
            next_steps.extend([
                "Review current coverage",
                "Get quotes from multiple providers",
                "Compare coverage amounts and premiums"
            ])
        
        recommendation.reasoning.extend([f"Next step: {step}" for step in next_steps[:2]])
        return recommendation


class RecommendationFilter:
    """
    Filters recommendations based on various criteria.
    """
    
    @staticmethod
    def filter_by_effort(
        recommendations: List[Recommendation],
        max_effort_hours: float
    ) -> List[Recommendation]:
        """Filter to only include actions under effort threshold."""
        return [r for r in recommendations if r.action.effort_hours <= max_effort_hours]
    
    @staticmethod
    def filter_by_category(
        recommendations: List[Recommendation],
        categories: List[str]
    ) -> List[Recommendation]:
        """Filter to only include specific categories."""
        return [r for r in recommendations if r.action.category in categories]
    
    @staticmethod
    def filter_quick_wins(
        recommendations: List[Recommendation],
        min_score: float = 70,
        max_effort: float = 5
    ) -> List[Recommendation]:
        """Get quick wins - high score, low effort."""
        quick_wins = [
            r for r in recommendations
            if r.score >= min_score and r.action.effort_hours <= max_effort
        ]
        return sorted(quick_wins, key=lambda r: r.score, reverse=True)
    
    @staticmethod
    def filter_by_horizon(
        recommendations: List[Recommendation],
        horizons: List[Horizon]
    ) -> List[Recommendation]:
        """Filter by time horizon."""
        return [r for r in recommendations if r.horizon in horizons]
