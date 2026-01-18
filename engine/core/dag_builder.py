"""
Ascend Engine - DAG Builder
Constructs and manages the directed acyclic graph of financial actions.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    FinancialAction, Dependency, DependencyType, Horizon
)
from utils import GraphUtils


class DAGBuilder:
    """
    Builds and manages the DAG of financial actions with dependencies.
    Handles dependency resolution, cycle detection, and path finding.
    """
    
    def __init__(self):
        self.nodes: Dict[str, FinancialAction] = {}
        self.edges: Dict[str, List[str]] = {}  # action_id -> [dependency_ids]
        self.reverse_edges: Dict[str, List[str]] = {}  # action_id -> [dependent_ids]
        self._scores: Dict[str, float] = {}
    
    def build_dag(
        self,
        actions: List[FinancialAction],
        scores: Dict[str, float] = None
    ) -> None:
        """
        Build the DAG from a list of actions.
        
        Args:
            actions: List of financial actions
            scores: Optional dict of action_id -> score
        """
        self.nodes.clear()
        self.edges.clear()
        self.reverse_edges.clear()
        self._scores = scores or {}
        
        # First pass: register all nodes
        for action in actions:
            self.nodes[action.id] = action
            self.edges[action.id] = []
            self.reverse_edges[action.id] = []
        
        # Second pass: build edges
        for action in actions:
            for dep in action.dependencies:
                # Only add edge if dependency exists in our action set
                if dep.target_action_id in self.nodes:
                    self.edges[action.id].append(dep.target_action_id)
                    self.reverse_edges[dep.target_action_id].append(action.id)
        
        # Validate DAG (check for cycles)
        self._validate_dag()
    
    def _validate_dag(self) -> None:
        """Validate that the graph is actually a DAG (no cycles)."""
        cycles = GraphUtils.detect_cycles(
            list(self.nodes.keys()),
            self.edges
        )
        
        if cycles:
            # Remove edges that cause cycles
            for cycle in cycles:
                if len(cycle) > 1:
                    # Remove last edge in cycle
                    from_node = cycle[-2]
                    to_node = cycle[-1]
                    if to_node in self.edges.get(from_node, []):
                        self.edges[from_node].remove(to_node)
                        if from_node in self.reverse_edges.get(to_node, []):
                            self.reverse_edges[to_node].remove(from_node)
    
    def topological_sort(self) -> List[str]:
        """
        Perform topological sort on the DAG.
        Returns action IDs in dependency order.
        """
        return GraphUtils.topological_sort(
            list(self.nodes.keys()),
            self.edges
        )
    
    def topological_sort_with_scores(self) -> List[str]:
        """
        Topological sort that also considers scores within same level.
        Higher scored items come first within each dependency level.
        """
        # Compute levels (distance from roots)
        levels = self._compute_levels()
        
        # Group by level, sort by score within level
        level_groups = defaultdict(list)
        for node_id, level in levels.items():
            level_groups[level].append(node_id)
        
        result = []
        for level in sorted(level_groups.keys()):
            nodes_at_level = level_groups[level]
            # Sort by score (descending) within level
            nodes_at_level.sort(
                key=lambda nid: self._scores.get(nid, 0),
                reverse=True
            )
            result.extend(nodes_at_level)
        
        return result
    
    def _compute_levels(self) -> Dict[str, int]:
        """Compute the level (distance from roots) for each node."""
        levels = {}
        
        # Find root nodes (no dependencies)
        roots = [nid for nid in self.nodes if not self.edges[nid]]
        
        # BFS from roots
        current_level = 0
        current_nodes = roots
        
        while current_nodes:
            for node in current_nodes:
                if node not in levels:
                    levels[node] = current_level
            
            next_nodes = []
            for node in current_nodes:
                for dependent in self.reverse_edges.get(node, []):
                    if dependent not in levels:
                        # Check if all dependencies are assigned
                        deps = self.edges.get(dependent, [])
                        if all(d in levels for d in deps):
                            next_nodes.append(dependent)
            
            current_nodes = list(set(next_nodes))
            current_level += 1
        
        # Handle any unassigned nodes (disconnected)
        for node_id in self.nodes:
            if node_id not in levels:
                levels[node_id] = 0
        
        return levels
    
    def get_execution_order(
        self,
        start_actions: List[str] = None,
        include_prerequisites: bool = True
    ) -> List[FinancialAction]:
        """
        Get actions in execution order.
        
        Args:
            start_actions: Optional specific actions to start from
            include_prerequisites: Whether to include prerequisite actions
            
        Returns:
            Ordered list of actions
        """
        if start_actions is None:
            sorted_ids = self.topological_sort_with_scores()
        else:
            # Get all actions needed including prerequisites
            needed_ids = set(start_actions)
            
            if include_prerequisites:
                for action_id in start_actions:
                    ancestors = GraphUtils.get_ancestors(action_id, self.edges)
                    needed_ids.update(ancestors)
            
            # Sort the needed actions
            all_sorted = self.topological_sort_with_scores()
            sorted_ids = [aid for aid in all_sorted if aid in needed_ids]
        
        return [self.nodes[aid] for aid in sorted_ids]
    
    def get_parallel_groups(self) -> List[List[FinancialAction]]:
        """
        Get groups of actions that can be executed in parallel.
        Actions in the same group have no dependencies on each other.
        """
        levels = self._compute_levels()
        
        # Group by level
        level_groups = defaultdict(list)
        for node_id, level in levels.items():
            level_groups[level].append(self.nodes[node_id])
        
        # Sort by level, then by score within each level
        result = []
        for level in sorted(level_groups.keys()):
            group = level_groups[level]
            group.sort(
                key=lambda a: self._scores.get(a.id, 0),
                reverse=True
            )
            result.append(group)
        
        return result
    
    def get_prerequisites(self, action_id: str) -> List[FinancialAction]:
        """Get all prerequisite actions (transitive dependencies)."""
        if action_id not in self.nodes:
            return []
        
        ancestors = GraphUtils.get_ancestors(action_id, self.edges)
        return [self.nodes[aid] for aid in ancestors if aid in self.nodes]
    
    def get_enabled_actions(self, action_id: str) -> List[FinancialAction]:
        """Get all actions that completing this action enables."""
        if action_id not in self.nodes:
            return []
        
        descendants = GraphUtils.get_descendants(action_id, self.reverse_edges)
        return [self.nodes[aid] for aid in descendants if aid in self.nodes]
    
    def get_critical_path(self, target_action_id: str) -> List[FinancialAction]:
        """
        Get the critical path to reach a target action.
        The longest path through dependencies to reach the target.
        """
        if target_action_id not in self.nodes:
            return []
        
        # Find all paths to target
        all_paths = self._find_all_paths_to(target_action_id)
        
        if not all_paths:
            return [self.nodes[target_action_id]]
        
        # Find longest path
        longest = max(all_paths, key=len)
        return [self.nodes[aid] for aid in longest]
    
    def _find_all_paths_to(self, target_id: str) -> List[List[str]]:
        """Find all paths from roots to target."""
        paths = []
        
        def dfs(current: str, path: List[str]):
            if current == target_id:
                paths.append(path + [current])
                return
            
            for next_node in self.reverse_edges.get(current, []):
                # This is reversed - we're going from target up
                pass
            
            # Actually go forward from dependencies
            for dep in self.edges.get(current, []):
                # This doesn't make sense for finding paths TO target
                pass
        
        # Better approach: work backwards from target
        def find_paths_backward(current: str, path: List[str]):
            deps = self.edges.get(current, [])
            if not deps:
                # Root node reached
                paths.append([current] + path)
                return
            
            for dep in deps:
                find_paths_backward(dep, [current] + path)
        
        find_paths_backward(target_id, [])
        return paths
    
    def get_quick_wins(self, max_effort_hours: float = 5) -> List[FinancialAction]:
        """
        Get actions that are quick wins - low effort with good scores.
        """
        quick = []
        for action in self.nodes.values():
            if action.effort_hours <= max_effort_hours:
                # Check if dependencies are already likely met (roots or few deps)
                num_deps = len(self.edges.get(action.id, []))
                if num_deps <= 1:
                    quick.append(action)
        
        # Sort by score
        quick.sort(
            key=lambda a: self._scores.get(a.id, 0),
            reverse=True
        )
        
        return quick
    
    def get_foundation_actions(self) -> List[FinancialAction]:
        """Get foundational actions (root nodes with no dependencies)."""
        foundations = []
        for action_id, deps in self.edges.items():
            if not deps:  # No dependencies
                foundations.append(self.nodes[action_id])
        
        foundations.sort(
            key=lambda a: self._scores.get(a.id, 0),
            reverse=True
        )
        
        return foundations
    
    def compute_action_impact(self, action_id: str) -> Dict[str, Any]:
        """
        Compute the total impact of completing an action.
        Considers direct impact plus enabled future actions.
        """
        if action_id not in self.nodes:
            return {}
        
        action = self.nodes[action_id]
        enabled = self.get_enabled_actions(action_id)
        
        direct_impact = {
            "debt": action.debt_impact,
            "savings": action.savings_impact,
            "income": action.income_impact,
            "protection": action.protection_impact,
            "growth": action.growth_impact
        }
        
        total_impact = dict(direct_impact)
        unlocked_value = 0
        
        for enabled_action in enabled:
            # Weight enabled actions by how close they are
            weight = 0.5  # Future actions count half
            total_impact["debt"] += enabled_action.debt_impact * weight
            total_impact["savings"] += enabled_action.savings_impact * weight
            total_impact["income"] += enabled_action.income_impact * weight
            total_impact["protection"] += enabled_action.protection_impact * weight
            total_impact["growth"] += enabled_action.growth_impact * weight
            unlocked_value += self._scores.get(enabled_action.id, 0) * weight
        
        return {
            "direct_impact": direct_impact,
            "total_impact": total_impact,
            "enabled_actions_count": len(enabled),
            "unlocked_value": unlocked_value
        }


class DAGOptimizer:
    """
    Optimizes action selection from the DAG based on constraints.
    """
    
    @staticmethod
    def select_optimal_actions(
        dag: DAGBuilder,
        max_actions: int = 10,
        max_effort_hours: float = 100,
        required_categories: List[str] = None
    ) -> List[FinancialAction]:
        """
        Select optimal subset of actions given constraints.
        Uses a greedy approach with score and dependency consideration.
        """
        selected = []
        remaining_effort = max_effort_hours
        selected_ids = set()
        
        # Get all actions sorted by score
        all_sorted = dag.topological_sort_with_scores()
        
        # Track which categories we've covered
        covered_categories = set()
        required = set(required_categories) if required_categories else set()
        
        for action_id in all_sorted:
            if len(selected) >= max_actions:
                break
            
            action = dag.nodes[action_id]
            
            # Check effort constraint
            if action.effort_hours > remaining_effort:
                continue
            
            # Check if dependencies are satisfied
            deps = dag.edges.get(action_id, [])
            deps_satisfied = all(d in selected_ids for d in deps)
            
            if not deps_satisfied:
                # Can we add the dependencies too?
                missing_deps = [d for d in deps if d not in selected_ids]
                total_effort = action.effort_hours + sum(
                    dag.nodes[d].effort_hours for d in missing_deps
                )
                
                if total_effort > remaining_effort:
                    continue
                
                # Add missing dependencies first
                for dep_id in missing_deps:
                    dep_action = dag.nodes[dep_id]
                    selected.append(dep_action)
                    selected_ids.add(dep_id)
                    remaining_effort -= dep_action.effort_hours
                    covered_categories.add(dep_action.category)
            
            # Add the action
            selected.append(action)
            selected_ids.add(action_id)
            remaining_effort -= action.effort_hours
            covered_categories.add(action.category)
        
        # Check if we covered required categories
        missing_categories = required - covered_categories
        if missing_categories:
            # Try to add one action from each missing category
            for category in missing_categories:
                for action_id in all_sorted:
                    if action_id in selected_ids:
                        continue
                    action = dag.nodes[action_id]
                    if action.category == category and action.effort_hours <= remaining_effort:
                        selected.append(action)
                        selected_ids.add(action_id)
                        remaining_effort -= action.effort_hours
                        break
        
        return selected
    
    @staticmethod
    def find_minimum_path(
        dag: DAGBuilder,
        target_action_id: str
    ) -> List[FinancialAction]:
        """
        Find the minimum effort path to reach a target action.
        """
        if target_action_id not in dag.nodes:
            return []
        
        # Get all prerequisites
        prereqs = dag.get_prerequisites(target_action_id)
        target = dag.nodes[target_action_id]
        
        # For each prerequisite, we need to include it
        # But we can choose which optional paths to take
        
        # Simplified: just return prerequisites + target in order
        sorted_prereqs = []
        sorted_ids = dag.topological_sort()
        prereq_ids = {p.id for p in prereqs}
        
        for aid in sorted_ids:
            if aid in prereq_ids:
                sorted_prereqs.append(dag.nodes[aid])
        
        sorted_prereqs.append(target)
        return sorted_prereqs
