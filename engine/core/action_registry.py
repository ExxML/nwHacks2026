"""
Ascend Engine - Action Registry
Dynamic loading and management of financial actions.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    FinancialAction, Condition, Dependency, DependencyType,
    Horizon, RiskLevel
)


class ActionRegistry:
    """
    Manages the registry of all financial actions.
    Supports dynamic loading, filtering, and conditional activation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the action registry.
        
        Args:
            config_path: Path to actions JSON config file
        """
        self.actions: Dict[str, FinancialAction] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}
        self._horizons: Dict[Horizon, Set[str]] = {}
        
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "actions.json"
        
        self.load_actions(config_path)
    
    def load_actions(self, config_path: str) -> None:
        """Load actions from JSON configuration file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Actions config not found: {config_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        for action_data in data.get("actions", []):
            action = self._parse_action(action_data)
            self._register_action(action)
    
    def _parse_action(self, data: Dict[str, Any]) -> FinancialAction:
        """Parse action data from JSON into FinancialAction object."""
        # Parse conditions
        conditions = []
        for cond_data in data.get("conditions", []):
            conditions.append(Condition(
                expression=cond_data["expression"],
                description=cond_data.get("description", "")
            ))
        
        # Parse dependencies
        dependencies = []
        for dep_data in data.get("dependencies", []):
            dependencies.append(Dependency(
                target_action_id=dep_data["target_action_id"],
                dependency_type=DependencyType(dep_data.get("dependency_type", "soft")),
                strength=dep_data.get("strength", 1.0),
                condition=dep_data.get("condition")
            ))
        
        # Parse horizon
        horizon_map = {
            "immediate": Horizon.IMMEDIATE,
            "short": Horizon.SHORT,
            "medium": Horizon.MEDIUM,
            "long": Horizon.LONG,
            "extended": Horizon.EXTENDED
        }
        horizon = horizon_map.get(data.get("horizon", "medium"), Horizon.MEDIUM)
        
        # Parse risk level
        risk_level = RiskLevel(data.get("risk_level", 3))
        
        return FinancialAction(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            horizon=horizon,
            category=data.get("category", "general"),
            subcategory=data.get("subcategory", "general"),
            tags=data.get("tags", []),
            dependencies=dependencies,
            conditions=conditions,
            base_priority=data.get("base_priority", 50.0),
            risk_level=risk_level,
            expected_return=data.get("expected_return", 0.0),
            volatility=data.get("volatility", 0.0),
            liquidity=data.get("liquidity", 1.0),
            effort_hours=data.get("effort_hours", 1.0),
            complexity=data.get("complexity", 0.5),
            recurring=data.get("recurring", False),
            debt_impact=data.get("debt_impact", 0.0),
            savings_impact=data.get("savings_impact", 0.0),
            income_impact=data.get("income_impact", 0.0),
            protection_impact=data.get("protection_impact", 0.0),
            growth_impact=data.get("growth_impact", 0.0),
            parameters=data.get("parameters", {})
        )
    
    def _register_action(self, action: FinancialAction) -> None:
        """Register an action and update indices."""
        self.actions[action.id] = action
        
        # Index by category
        if action.category not in self._categories:
            self._categories[action.category] = set()
        self._categories[action.category].add(action.id)
        
        # Index by tags
        for tag in action.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(action.id)
        
        # Index by horizon
        if action.horizon not in self._horizons:
            self._horizons[action.horizon] = set()
        self._horizons[action.horizon].add(action.id)
    
    def get_action(self, action_id: str) -> Optional[FinancialAction]:
        """Get an action by ID."""
        return self.actions.get(action_id)
    
    def get_all_actions(self) -> List[FinancialAction]:
        """Get all registered actions."""
        return list(self.actions.values())
    
    def get_actions_by_category(self, category: str) -> List[FinancialAction]:
        """Get all actions in a category."""
        action_ids = self._categories.get(category, set())
        return [self.actions[aid] for aid in action_ids]
    
    def get_actions_by_tag(self, tag: str) -> List[FinancialAction]:
        """Get all actions with a specific tag."""
        action_ids = self._tags.get(tag, set())
        return [self.actions[aid] for aid in action_ids]
    
    def get_actions_by_horizon(self, horizon: Horizon) -> List[FinancialAction]:
        """Get all actions for a specific time horizon."""
        action_ids = self._horizons.get(horizon, set())
        return [self.actions[aid] for aid in action_ids]
    
    def filter_applicable_actions(
        self, 
        context: Dict[str, Any]
    ) -> List[FinancialAction]:
        """
        Filter actions based on conditions and context.
        Returns only actions that are applicable to the user's situation.
        
        Args:
            context: Evaluation context with profile/query data
            
        Returns:
            List of applicable actions with applicability info set
        """
        applicable = []
        
        for action in self.actions.values():
            is_applicable, reasons = self._evaluate_conditions(action, context)
            
            # Create a copy to avoid modifying registry
            action_copy = self._copy_action(action)
            action_copy.is_applicable = is_applicable
            action_copy.applicability_reasons = reasons
            
            if is_applicable:
                applicable.append(action_copy)
        
        return applicable
    
    def _evaluate_conditions(
        self, 
        action: FinancialAction, 
        context: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Evaluate all conditions for an action.
        
        Returns:
            (is_applicable, list of reasons)
        """
        reasons = []
        
        # If no conditions, action is always applicable
        if not action.conditions:
            return True, ["No specific conditions required"]
        
        all_met = True
        for condition in action.conditions:
            try:
                met = condition.evaluate(context)
                if met:
                    reasons.append(f"✓ {condition.description}")
                else:
                    reasons.append(f"✗ {condition.description}")
                    all_met = False
            except Exception as e:
                # If condition can't be evaluated, assume it's not met
                reasons.append(f"? {condition.description} (could not evaluate)")
                all_met = False
        
        return all_met, reasons
    
    def _copy_action(self, action: FinancialAction) -> FinancialAction:
        """Create a copy of an action for modification."""
        return FinancialAction(
            id=action.id,
            name=action.name,
            description=action.description,
            horizon=action.horizon,
            category=action.category,
            subcategory=action.subcategory,
            tags=list(action.tags),
            dependencies=list(action.dependencies),
            conditions=list(action.conditions),
            base_priority=action.base_priority,
            risk_level=action.risk_level,
            expected_return=action.expected_return,
            volatility=action.volatility,
            liquidity=action.liquidity,
            effort_hours=action.effort_hours,
            complexity=action.complexity,
            recurring=action.recurring,
            debt_impact=action.debt_impact,
            savings_impact=action.savings_impact,
            income_impact=action.income_impact,
            protection_impact=action.protection_impact,
            growth_impact=action.growth_impact,
            parameters=dict(action.parameters)
        )
    
    def get_dependencies(self, action_id: str) -> List[FinancialAction]:
        """Get all actions that this action depends on."""
        action = self.get_action(action_id)
        if not action:
            return []
        
        deps = []
        for dep in action.dependencies:
            dep_action = self.get_action(dep.target_action_id)
            if dep_action:
                deps.append(dep_action)
        
        return deps
    
    def get_dependents(self, action_id: str) -> List[FinancialAction]:
        """Get all actions that depend on this action."""
        dependents = []
        for action in self.actions.values():
            for dep in action.dependencies:
                if dep.target_action_id == action_id:
                    dependents.append(action)
                    break
        return dependents
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return list(self._categories.keys())
    
    def get_tags(self) -> List[str]:
        """Get all unique tags."""
        return list(self._tags.keys())
    
    def add_custom_action(self, action: FinancialAction) -> None:
        """Add a custom action to the registry at runtime."""
        self._register_action(action)
    
    def remove_action(self, action_id: str) -> bool:
        """Remove an action from the registry."""
        if action_id not in self.actions:
            return False
        
        action = self.actions[action_id]
        
        # Remove from indices
        if action.category in self._categories:
            self._categories[action.category].discard(action_id)
        
        for tag in action.tags:
            if tag in self._tags:
                self._tags[tag].discard(action_id)
        
        if action.horizon in self._horizons:
            self._horizons[action.horizon].discard(action_id)
        
        del self.actions[action_id]
        return True


class ActionGenerator:
    """
    Generates dynamic actions based on user context.
    Creates personalized variations of base actions.
    """
    
    @staticmethod
    def generate_debt_payoff_actions(
        debt_amount: float,
        interest_rate: float,
        debt_type: str,
        monthly_payment: float
    ) -> List[FinancialAction]:
        """Generate specific debt payoff actions based on actual debt."""
        actions = []
        
        # Calculate payoff scenarios
        from utils import FinancialMath
        
        # Minimum payment scenario
        min_months = FinancialMath.calculate_debt_payoff_months(
            debt_amount, monthly_payment, interest_rate
        )
        
        # Accelerated payment scenario (1.5x payment)
        accel_payment = monthly_payment * 1.5
        accel_months = FinancialMath.calculate_debt_payoff_months(
            debt_amount, accel_payment, interest_rate
        )
        
        # Aggressive payment scenario (2x payment)
        aggressive_payment = monthly_payment * 2
        aggressive_months = FinancialMath.calculate_debt_payoff_months(
            debt_amount, aggressive_payment, interest_rate
        )
        
        # Create actions for each scenario
        base_priority = 90 if interest_rate > 0.15 else 70 if interest_rate > 0.07 else 50
        
        actions.append(FinancialAction(
            id=f"debt_payoff_{debt_type}_standard",
            name=f"Pay Off {debt_type.title()} (Standard)",
            description=f"Continue paying ${monthly_payment:.0f}/month. Payoff in {min_months} months.",
            horizon=Horizon.MEDIUM if min_months < 24 else Horizon.LONG,
            category="debt",
            subcategory=debt_type,
            tags=["debt", "standard"],
            base_priority=base_priority - 10,
            risk_level=RiskLevel.CONSERVATIVE,
            expected_return=interest_rate,
            debt_impact=0.6,
            parameters={
                "monthly_payment": monthly_payment,
                "months": min_months,
                "total_interest": debt_amount * interest_rate * (min_months / 12)
            }
        ))
        
        if accel_months < min_months:
            actions.append(FinancialAction(
                id=f"debt_payoff_{debt_type}_accelerated",
                name=f"Pay Off {debt_type.title()} (Accelerated)",
                description=f"Increase to ${accel_payment:.0f}/month. Payoff in {accel_months} months.",
                horizon=Horizon.SHORT if accel_months < 12 else Horizon.MEDIUM,
                category="debt",
                subcategory=debt_type,
                tags=["debt", "accelerated"],
                base_priority=base_priority,
                risk_level=RiskLevel.MODERATE,
                expected_return=interest_rate,
                debt_impact=0.8,
                parameters={
                    "monthly_payment": accel_payment,
                    "months": accel_months
                }
            ))
        
        return actions
    
    @staticmethod
    def generate_savings_goal_action(
        goal_name: str,
        target_amount: float,
        monthly_contribution: float,
        priority: float = 50
    ) -> FinancialAction:
        """Generate a custom savings goal action."""
        months = int(target_amount / monthly_contribution) if monthly_contribution > 0 else 999
        
        if months <= 6:
            horizon = Horizon.SHORT
        elif months <= 24:
            horizon = Horizon.MEDIUM
        else:
            horizon = Horizon.LONG
        
        return FinancialAction(
            id=f"savings_goal_{goal_name.lower().replace(' ', '_')}",
            name=f"Save for {goal_name}",
            description=f"Save ${target_amount:,.0f} by contributing ${monthly_contribution:,.0f}/month",
            horizon=horizon,
            category="savings",
            subcategory="goal",
            tags=["savings", "goal", "custom"],
            base_priority=priority,
            risk_level=RiskLevel.CONSERVATIVE,
            expected_return=0.04,  # Assume HYSA
            savings_impact=0.7,
            parameters={
                "target": target_amount,
                "monthly": monthly_contribution,
                "months": months
            }
        )
    
    @staticmethod
    def generate_investment_allocation_actions(
        age: float,
        risk_tolerance: RiskLevel,
        current_allocation: Dict[str, float]
    ) -> List[FinancialAction]:
        """Generate specific allocation adjustment actions."""
        actions = []
        
        # Target allocation based on age and risk
        target_stocks = max(20, min(90, 110 - age))  # Age-based rule
        
        # Adjust for risk tolerance
        if risk_tolerance == RiskLevel.AGGRESSIVE:
            target_stocks = min(95, target_stocks + 15)
        elif risk_tolerance == RiskLevel.CONSERVATIVE:
            target_stocks = max(20, target_stocks - 15)
        
        target_bonds = 100 - target_stocks
        
        current_stocks = current_allocation.get("stocks", 50)
        
        diff = target_stocks - current_stocks
        
        if abs(diff) > 10:
            if diff > 0:
                actions.append(FinancialAction(
                    id="rebalance_increase_stocks",
                    name="Increase Stock Allocation",
                    description=f"Shift {abs(diff):.0f}% from bonds to stocks to match target allocation",
                    horizon=Horizon.IMMEDIATE,
                    category="investment",
                    subcategory="rebalance",
                    tags=["rebalance", "stocks"],
                    base_priority=55,
                    risk_level=RiskLevel.MODERATE,
                    growth_impact=0.6
                ))
            else:
                actions.append(FinancialAction(
                    id="rebalance_decrease_stocks",
                    name="Decrease Stock Allocation",
                    description=f"Shift {abs(diff):.0f}% from stocks to bonds for more stability",
                    horizon=Horizon.IMMEDIATE,
                    category="investment",
                    subcategory="rebalance",
                    tags=["rebalance", "bonds"],
                    base_priority=55,
                    risk_level=RiskLevel.CONSERVATIVE,
                    protection_impact=0.5
                ))
        
        return actions
