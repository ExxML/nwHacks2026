"""
Ascend Engine - Input Normalizer
Handles normalization of user profile and query inputs.
"""

from typing import Dict, Any, Tuple, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    UserProfile, QueryInput, RiskLevel, LifeStage, FinancialHealth
)
from utils import RangeParser, KeywordExtractor, FinancialMath


class InputNormalizer:
    """
    Normalizes and enriches user inputs with derived metrics.
    Handles missing data, range parsing, and feature extraction.
    """
    
    # Risk tolerance mapping
    RISK_MAPPING = {
        "risky": RiskLevel.AGGRESSIVE,
        "aggressive": RiskLevel.AGGRESSIVE,
        "high": RiskLevel.AGGRESSIVE,
        "medium": RiskLevel.MODERATE,
        "moderate": RiskLevel.MODERATE,
        "balanced": RiskLevel.MODERATE,
        "reliable": RiskLevel.CONSERVATIVE,
        "conservative": RiskLevel.CONSERVATIVE,
        "low": RiskLevel.CONSERVATIVE,
        "safe": RiskLevel.CONSERVATIVE
    }
    
    # Age to life stage mapping
    AGE_TO_LIFESTAGE = [
        (29, LifeStage.EARLY_CAREER),
        (44, LifeStage.CAREER_GROWTH),
        (54, LifeStage.PEAK_EARNING),
        (64, LifeStage.PRE_RETIREMENT),
        (74, LifeStage.EARLY_RETIREMENT),
        (float('inf'), LifeStage.LATE_RETIREMENT)
    ]
    
    # Default values for missing data (based on population medians)
    DEFAULTS = {
        "age": 35,
        "property": 0,
        "vehicle": 15000,
        "investments": 50000,
        "debt": 30000,
        "salary": 4500,  # Monthly
        "employment_stability": 0.7
    }
    
    def __init__(self):
        self.keyword_extractor = KeywordExtractor()
    
    def normalize_profile(self, profile: UserProfile) -> UserProfile:
        """
        Normalize a user profile, computing derived metrics.
        
        Args:
            profile: Raw user profile input
            
        Returns:
            Enriched user profile with all normalized values
        """
        # Normalize basic fields
        profile.normalized_age = self._normalize_age(profile.age_range)
        profile.normalized_property = self._normalize_money(
            profile.property_value, "property"
        )
        profile.normalized_vehicle = self._normalize_money(
            profile.vehicle_value, "vehicle"
        )
        profile.normalized_investments = self._normalize_money(
            profile.investments, "investments"
        )
        profile.normalized_debt = self._normalize_money(
            profile.debt, "debt"
        )
        profile.normalized_salary = self._normalize_salary(profile.monthly_salary)
        
        # Compute derived metrics
        profile.life_stage = self._determine_life_stage(profile.normalized_age)
        profile.is_homeowner = profile.normalized_property > 0
        
        # Debt-to-income ratio (annualized)
        annual_income = profile.normalized_salary * 12
        if annual_income > 0:
            profile.debt_to_income_ratio = profile.normalized_debt / annual_income
        else:
            profile.debt_to_income_ratio = float('inf') if profile.normalized_debt > 0 else 0
        
        # Net worth calculation
        total_assets = (
            profile.normalized_property + 
            profile.normalized_vehicle + 
            profile.normalized_investments
        )
        profile.net_worth = total_assets - profile.normalized_debt
        
        # Estimate savings rate (heuristic based on age and investments)
        profile.savings_rate = self._estimate_savings_rate(profile)
        
        # Determine financial health
        profile.financial_health = self._assess_financial_health(profile)
        
        # Estimate emergency fund status
        profile.has_emergency_fund = self._estimate_emergency_fund_status(profile)
        
        return profile
    
    def normalize_query(self, query: QueryInput) -> QueryInput:
        """
        Normalize a query input, extracting features from text.
        
        Args:
            query: Raw query input
            
        Returns:
            Enriched query with extracted features
        """
        # Normalize risk tolerance
        risk_key = query.risk_tolerance.lower().strip()
        query.normalized_risk = self.RISK_MAPPING.get(risk_key, RiskLevel.MODERATE)
        
        # Extract keywords from situation and goal
        query.situation_keywords = self.keyword_extractor.extract_keywords(
            query.current_situation
        )
        query.goal_keywords = self.keyword_extractor.extract_keywords(query.goal)
        
        # Detect goal category
        goal_category, confidence = self.keyword_extractor.detect_goal_category(
            query.goal
        )
        query.goal_category = goal_category
        
        # Calculate urgency
        combined_text = f"{query.current_situation} {query.goal}"
        query.urgency_score = self.keyword_extractor.calculate_urgency(combined_text)
        
        return query
    
    def _normalize_age(self, age_range: str) -> float:
        """Normalize age range to midpoint value."""
        result = RangeParser.parse_range(age_range, "age")
        if result is None:
            return self.DEFAULTS["age"]
        return result[2]  # Return midpoint
    
    def _normalize_money(self, value: str, field: str) -> float:
        """Normalize money range to midpoint value."""
        result = RangeParser.get_midpoint(value, "money")
        if result is None:
            return self.DEFAULTS.get(field, 0)
        return result
    
    def _normalize_salary(self, salary_range: str) -> float:
        """Normalize monthly salary to midpoint value."""
        result = RangeParser.get_midpoint(salary_range, "salary")
        if result is None:
            return self.DEFAULTS["salary"]
        return result
    
    def _determine_life_stage(self, age: float) -> LifeStage:
        """Determine life stage from age."""
        for threshold, stage in self.AGE_TO_LIFESTAGE:
            if age <= threshold:
                return stage
        return LifeStage.LATE_RETIREMENT
    
    def _estimate_savings_rate(self, profile: UserProfile) -> float:
        """
        Estimate savings rate based on profile characteristics.
        Uses heuristics since we don't have direct spending data.
        """
        # Base savings rate adjusted by income
        if profile.normalized_salary <= 0:
            return 0.0
        
        annual_income = profile.normalized_salary * 12
        
        # Higher income typically means higher savings potential
        income_factor = min(annual_income / 100000, 1.5)
        
        # Age-adjusted investment to income ratio as proxy
        if annual_income > 0:
            investment_ratio = profile.normalized_investments / (annual_income * profile.normalized_age / 25)
        else:
            investment_ratio = 0
        
        # Estimate based on these factors
        base_rate = 0.10  # 10% base
        
        # Adjust for income level
        if annual_income > 150000:
            base_rate += 0.10
        elif annual_income > 100000:
            base_rate += 0.05
        elif annual_income < 50000:
            base_rate -= 0.05
        
        # Adjust for debt load
        if profile.debt_to_income_ratio > 0.5:
            base_rate -= 0.10
        elif profile.debt_to_income_ratio > 0.3:
            base_rate -= 0.05
        
        # Adjust based on investment accumulation
        if investment_ratio > 1.0:
            base_rate += 0.05
        
        return max(0.0, min(0.50, base_rate))  # Cap between 0-50%
    
    def _assess_financial_health(self, profile: UserProfile) -> FinancialHealth:
        """
        Assess overall financial health based on multiple factors.
        Uses a scoring system across key indicators.
        """
        score = 0
        max_score = 100
        
        # Debt-to-income (25 points)
        if profile.debt_to_income_ratio == 0:
            score += 25
        elif profile.debt_to_income_ratio < 0.15:
            score += 20
        elif profile.debt_to_income_ratio < 0.30:
            score += 15
        elif profile.debt_to_income_ratio < 0.50:
            score += 8
        # else 0 points
        
        # Net worth relative to age (25 points)
        # Rule of thumb: net worth should be ~age/10 * annual income
        expected_net_worth = (profile.normalized_age / 10) * (profile.normalized_salary * 12)
        if expected_net_worth > 0:
            nw_ratio = profile.net_worth / expected_net_worth
            if nw_ratio >= 1.5:
                score += 25
            elif nw_ratio >= 1.0:
                score += 20
            elif nw_ratio >= 0.5:
                score += 12
            elif nw_ratio >= 0.25:
                score += 6
            elif nw_ratio >= 0:
                score += 3
        elif profile.net_worth > 0:
            score += 15
        
        # Savings rate (25 points)
        if profile.savings_rate >= 0.25:
            score += 25
        elif profile.savings_rate >= 0.15:
            score += 20
        elif profile.savings_rate >= 0.10:
            score += 15
        elif profile.savings_rate >= 0.05:
            score += 8
        # else 0
        
        # Asset diversification (25 points)
        has_property = profile.normalized_property > 0
        has_investments = profile.normalized_investments > 0
        has_vehicle = profile.normalized_vehicle > 0
        
        asset_count = sum([has_property, has_investments, has_vehicle])
        score += asset_count * 8  # Up to 24 points
        
        # Convert score to health level
        normalized_score = score / max_score
        
        if normalized_score >= 0.80:
            return FinancialHealth.THRIVING
        elif normalized_score >= 0.60:
            return FinancialHealth.HEALTHY
        elif normalized_score >= 0.40:
            return FinancialHealth.STABLE
        elif normalized_score >= 0.20:
            return FinancialHealth.STRESSED
        else:
            return FinancialHealth.CRITICAL
    
    def _estimate_emergency_fund_status(self, profile: UserProfile) -> bool:
        """
        Estimate whether user likely has an emergency fund.
        Based on overall financial picture since we don't have direct data.
        """
        # If no investments, unlikely to have emergency fund
        if profile.normalized_investments < 1000:
            return False
        
        # If good financial health, likely has emergency fund
        if profile.financial_health.value >= FinancialHealth.HEALTHY.value:
            return True
        
        # If stable and has some investments, maybe
        if profile.financial_health == FinancialHealth.STABLE:
            monthly_expenses = profile.normalized_salary * 0.7  # Estimate 70% of income
            three_months = monthly_expenses * 3
            return profile.normalized_investments >= three_months
        
        return False
    
    def create_evaluation_context(
        self, 
        profile: UserProfile, 
        query: QueryInput
    ) -> Dict[str, Any]:
        """
        Create a context dictionary for condition evaluation.
        This is used by the action registry to check conditions.
        """
        return {
            # Profile - normalized values
            "normalized_age": profile.normalized_age,
            "normalized_property": profile.normalized_property,
            "normalized_vehicle": profile.normalized_vehicle,
            "normalized_investments": profile.normalized_investments,
            "normalized_debt": profile.normalized_debt,
            "normalized_salary": profile.normalized_salary,
            
            # Profile - derived
            "life_stage": profile.life_stage,
            "financial_health": profile.financial_health,
            "debt_to_income_ratio": profile.debt_to_income_ratio,
            "net_worth": profile.net_worth,
            "savings_rate": profile.savings_rate,
            "has_dependents": profile.has_dependents,
            "is_homeowner": profile.is_homeowner,
            "has_emergency_fund": profile.has_emergency_fund,
            "employment_stability": profile.employment_stability,
            
            # Query - normalized
            "normalized_risk": query.normalized_risk,
            "goal_category": query.goal_category,
            "urgency_score": query.urgency_score,
            
            # Query - extracted
            "situation_keywords": query.situation_keywords,
            "goal_keywords": query.goal_keywords,
            
            # Helper values
            "age": profile.normalized_age,
            "salary": profile.normalized_salary,
            "debt": profile.normalized_debt,
            "investments": profile.normalized_investments
        }


class ProfileAnalyzer:
    """
    Advanced profile analysis for deeper insights.
    Computes additional metrics and patterns.
    """
    
    @staticmethod
    def compute_risk_capacity(profile: UserProfile) -> float:
        """
        Compute objective risk capacity (ability to take risk).
        Different from risk tolerance (willingness to take risk).
        """
        capacity = 0.5  # Base
        
        # Age factor (younger = more capacity)
        age_factor = max(0, (65 - profile.normalized_age) / 50)
        capacity += age_factor * 0.2
        
        # Financial health factor
        health_factor = (profile.financial_health.value - 1) / 4
        capacity += health_factor * 0.2
        
        # Debt factor (less debt = more capacity)
        if profile.debt_to_income_ratio < 0.1:
            capacity += 0.1
        elif profile.debt_to_income_ratio > 0.4:
            capacity -= 0.1
        
        return max(0, min(1, capacity))
    
    @staticmethod
    def compute_investment_horizon(profile: UserProfile) -> int:
        """Compute typical investment horizon in years."""
        # Base on retirement age of 65
        years_to_retirement = max(0, 65 - profile.normalized_age)
        
        # Adjust for life stage
        if profile.life_stage == LifeStage.EARLY_CAREER:
            return max(years_to_retirement, 30)
        elif profile.life_stage == LifeStage.CAREER_GROWTH:
            return max(years_to_retirement, 20)
        elif profile.life_stage == LifeStage.PEAK_EARNING:
            return max(years_to_retirement, 10)
        elif profile.life_stage == LifeStage.PRE_RETIREMENT:
            return max(years_to_retirement, 5)
        else:
            return 10  # Even in retirement, need some growth
    
    @staticmethod
    def identify_financial_gaps(profile: UserProfile) -> Dict[str, float]:
        """
        Identify gaps in financial plan.
        Returns dict of gap areas with severity (0-1).
        """
        gaps = {}
        
        # Emergency fund gap
        monthly_expenses = profile.normalized_salary * 0.7
        if not profile.has_emergency_fund:
            # More severe if less stable employment
            gaps["emergency_fund"] = 1.0 - profile.employment_stability * 0.3
        
        # Retirement savings gap
        # Rule: should have 1x salary saved by 30, 3x by 40, etc.
        age = profile.normalized_age
        salary = profile.normalized_salary * 12
        
        if age >= 30:
            multiplier = (age - 20) / 10
            expected_retirement = salary * multiplier
            actual = profile.normalized_investments
            
            if actual < expected_retirement * 0.5:
                gaps["retirement_savings"] = min(1.0, 1 - (actual / expected_retirement))
        
        # Debt gap
        if profile.debt_to_income_ratio > 0.3:
            gaps["high_debt"] = min(1.0, profile.debt_to_income_ratio)
        
        # Protection gap (insurance)
        if profile.has_dependents and profile.normalized_salary > 5000:
            gaps["life_insurance"] = 0.7  # Can't know for sure, assume gap
        
        # Diversification gap
        total_assets = profile.normalized_property + profile.normalized_investments
        if total_assets > 0:
            concentration = profile.normalized_property / total_assets
            if concentration > 0.8:
                gaps["diversification"] = concentration - 0.5
        
        return gaps
    
    @staticmethod
    def compute_financial_priorities(
        profile: UserProfile, 
        query: QueryInput
    ) -> Dict[str, float]:
        """
        Compute weighted priorities for different financial areas.
        Used to adjust action scoring.
        """
        priorities = {
            "debt_reduction": 0.5,
            "emergency_savings": 0.5,
            "retirement": 0.5,
            "growth": 0.5,
            "protection": 0.5,
            "income": 0.5
        }
        
        # Adjust based on financial health
        if profile.financial_health.value <= FinancialHealth.STRESSED.value:
            priorities["debt_reduction"] = 0.9
            priorities["emergency_savings"] = 0.85
            priorities["growth"] = 0.2
        elif profile.financial_health == FinancialHealth.STABLE:
            priorities["emergency_savings"] = 0.7
            priorities["retirement"] = 0.6
        elif profile.financial_health.value >= FinancialHealth.HEALTHY.value:
            priorities["growth"] = 0.8
            priorities["retirement"] = 0.75
        
        # Adjust based on life stage
        if profile.life_stage == LifeStage.EARLY_CAREER:
            priorities["income"] = 0.7
            priorities["growth"] = 0.65
        elif profile.life_stage == LifeStage.PRE_RETIREMENT:
            priorities["retirement"] = 0.9
            priorities["protection"] = 0.7
        elif profile.life_stage in [LifeStage.EARLY_RETIREMENT, LifeStage.LATE_RETIREMENT]:
            priorities["protection"] = 0.85
            priorities["income"] = 0.3
        
        # Adjust based on risk tolerance
        if query.normalized_risk == RiskLevel.AGGRESSIVE:
            priorities["growth"] *= 1.3
            priorities["protection"] *= 0.7
        elif query.normalized_risk == RiskLevel.CONSERVATIVE:
            priorities["protection"] *= 1.3
            priorities["growth"] *= 0.7
        
        # Adjust based on goal category
        goal_adjustments = {
            "debt_freedom": {"debt_reduction": 1.5},
            "emergency_savings": {"emergency_savings": 1.5},
            "retirement": {"retirement": 1.5},
            "wealth_building": {"growth": 1.4, "income": 1.2},
            "home_ownership": {"emergency_savings": 1.2},
            "income_increase": {"income": 1.5},
            "financial_protection": {"protection": 1.5}
        }
        
        if query.goal_category in goal_adjustments:
            for area, multiplier in goal_adjustments[query.goal_category].items():
                priorities[area] *= multiplier
        
        # Normalize to 0-1
        max_priority = max(priorities.values())
        if max_priority > 0:
            priorities = {k: v / max_priority for k, v in priorities.items()}
        
        return priorities
