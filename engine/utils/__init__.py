"""
Ascend Engine - Utility Functions
Helper functions for text analysis, math, and configuration.
"""

import re
import math
import json
from typing import Dict, List, Any, Tuple, Optional, Set
from pathlib import Path
from collections import defaultdict


# ============================================================================
# KEYWORD AND TEXT ANALYSIS
# ============================================================================

class KeywordExtractor:
    """
    Extract meaningful keywords and intents from user text input.
    Uses pattern matching and weighted keyword detection.
    """
    
    # Goal categories with associated keywords and weights
    GOAL_KEYWORDS = {
        "debt_freedom": {
            "keywords": ["debt", "loan", "credit card", "pay off", "owe", "owing", 
                        "interest", "balance", "mortgage", "student loan", "car loan"],
            "weight": 1.0
        },
        "emergency_savings": {
            "keywords": ["emergency", "rainy day", "safety net", "unexpected", 
                        "cushion", "backup", "3 months", "6 months", "job loss"],
            "weight": 1.0
        },
        "retirement": {
            "keywords": ["retire", "retirement", "401k", "ira", "pension", "rrsp",
                        "golden years", "stop working", "nest egg", "social security"],
            "weight": 1.0
        },
        "wealth_building": {
            "keywords": ["invest", "grow", "wealth", "rich", "portfolio", "stocks",
                        "bonds", "index", "etf", "compound", "passive income"],
            "weight": 1.0
        },
        "home_ownership": {
            "keywords": ["house", "home", "property", "mortgage", "down payment",
                        "real estate", "buy", "own", "rent", "condo", "apartment"],
            "weight": 1.0
        },
        "income_increase": {
            "keywords": ["earn", "income", "salary", "raise", "promotion", "side hustle",
                        "freelance", "business", "revenue", "money", "more income"],
            "weight": 1.0
        },
        "financial_protection": {
            "keywords": ["insurance", "protect", "coverage", "life insurance", 
                        "health insurance", "disability", "estate", "will", "trust"],
            "weight": 1.0
        },
        "education": {
            "keywords": ["education", "college", "university", "degree", "tuition",
                        "student", "school", "529", "resp", "learning"],
            "weight": 1.0
        },
        "major_purchase": {
            "keywords": ["car", "vehicle", "vacation", "wedding", "travel",
                        "renovation", "furniture", "big purchase", "save for"],
            "weight": 0.8
        }
    }
    
    # Urgency indicators
    URGENCY_KEYWORDS = {
        "high": ["urgent", "asap", "immediately", "now", "critical", "emergency",
                "desperate", "struggling", "drowning", "behind", "overdue"],
        "medium": ["soon", "this year", "planning", "want to", "hoping", "looking to"],
        "low": ["eventually", "someday", "future", "long term", "retirement", "later"]
    }
    
    # Situation keywords for context
    SITUATION_KEYWORDS = {
        "negative": ["lost job", "laid off", "unemployed", "divorced", "medical",
                    "illness", "accident", "debt collector", "bankruptcy", "foreclosure",
                    "struggling", "behind on", "can't afford", "maxed out"],
        "transitional": ["new job", "promotion", "married", "baby", "moving",
                        "relocating", "graduating", "starting", "changing careers"],
        "positive": ["raise", "bonus", "inheritance", "windfall", "paid off",
                    "debt free", "saving", "investing", "growing"]
    }
    
    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        """Extract all relevant keywords from text."""
        text_lower = text.lower()
        found_keywords = []
        
        for category, data in cls.GOAL_KEYWORDS.items():
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    @classmethod
    def detect_goal_category(cls, text: str) -> Tuple[str, float]:
        """
        Detect the primary goal category from text.
        Returns (category, confidence).
        """
        text_lower = text.lower()
        scores = {}
        
        for category, data in cls.GOAL_KEYWORDS.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    # Longer keywords are weighted more
                    score += len(keyword.split()) * data["weight"]
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return "general", 0.0
        
        best_category = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_category] / total_score if total_score > 0 else 0
        
        return best_category, confidence
    
    @classmethod
    def calculate_urgency(cls, text: str) -> float:
        """Calculate urgency score from text (0-1)."""
        text_lower = text.lower()
        
        high_count = sum(1 for kw in cls.URGENCY_KEYWORDS["high"] if kw in text_lower)
        med_count = sum(1 for kw in cls.URGENCY_KEYWORDS["medium"] if kw in text_lower)
        low_count = sum(1 for kw in cls.URGENCY_KEYWORDS["low"] if kw in text_lower)
        
        if high_count > 0:
            return min(0.7 + (high_count * 0.1), 1.0)
        elif med_count > 0:
            return 0.4 + (med_count * 0.1)
        elif low_count > 0:
            return max(0.2 - (low_count * 0.05), 0.1)
        
        return 0.5  # Default medium urgency
    
    @classmethod
    def analyze_situation(cls, text: str) -> Dict[str, Any]:
        """Analyze the current situation text."""
        text_lower = text.lower()
        
        sentiment_scores = {
            "negative": sum(1 for kw in cls.SITUATION_KEYWORDS["negative"] if kw in text_lower),
            "transitional": sum(1 for kw in cls.SITUATION_KEYWORDS["transitional"] if kw in text_lower),
            "positive": sum(1 for kw in cls.SITUATION_KEYWORDS["positive"] if kw in text_lower)
        }
        
        # Determine primary sentiment
        total = sum(sentiment_scores.values())
        if total == 0:
            sentiment = "neutral"
            stability = 0.5
        else:
            sentiment = max(sentiment_scores, key=sentiment_scores.get)
            stability = 1 - (sentiment_scores["negative"] / (total + 1))
        
        return {
            "sentiment": sentiment,
            "stability_score": stability,
            "scores": sentiment_scores,
            "keywords": [kw for cat in cls.SITUATION_KEYWORDS.values() 
                        for kw in cat if kw in text_lower]
        }


# ============================================================================
# MATHEMATICAL UTILITIES
# ============================================================================

class FinancialMath:
    """Financial calculation utilities."""
    
    @staticmethod
    def calculate_compound_growth(principal: float, rate: float, years: int, 
                                  contributions: float = 0, frequency: int = 12) -> float:
        """
        Calculate compound growth with regular contributions.
        
        Args:
            principal: Starting amount
            rate: Annual interest rate (decimal)
            years: Number of years
            contributions: Regular contribution amount
            frequency: Contributions per year (12 = monthly)
        """
        periodic_rate = rate / frequency
        periods = years * frequency
        
        # Future value of principal
        fv_principal = principal * ((1 + periodic_rate) ** periods)
        
        # Future value of contributions (annuity)
        if periodic_rate > 0:
            fv_contributions = contributions * (((1 + periodic_rate) ** periods - 1) / periodic_rate)
        else:
            fv_contributions = contributions * periods
        
        return fv_principal + fv_contributions
    
    @staticmethod
    def calculate_debt_payoff_months(balance: float, payment: float, rate: float) -> int:
        """Calculate months to pay off debt with fixed payment."""
        if payment <= balance * (rate / 12):
            return float('inf')  # Payment too low to ever pay off
        
        monthly_rate = rate / 12
        if monthly_rate == 0:
            return math.ceil(balance / payment)
        
        months = math.log(payment / (payment - balance * monthly_rate)) / math.log(1 + monthly_rate)
        return math.ceil(months)
    
    @staticmethod
    def calculate_sharpe_ratio(expected_return: float, risk_free_rate: float, 
                               volatility: float) -> float:
        """Calculate risk-adjusted return (Sharpe ratio)."""
        if volatility == 0:
            return 0 if expected_return <= risk_free_rate else float('inf')
        return (expected_return - risk_free_rate) / volatility
    
    @staticmethod
    def normalize_to_range(value: float, min_val: float, max_val: float,
                          target_min: float = 0, target_max: float = 1) -> float:
        """Normalize a value to a target range."""
        if max_val == min_val:
            return (target_min + target_max) / 2
        
        normalized = (value - min_val) / (max_val - min_val)
        return target_min + normalized * (target_max - target_min)
    
    @staticmethod
    def sigmoid(x: float, k: float = 1, midpoint: float = 0) -> float:
        """Sigmoid function for smooth transitions."""
        return 1 / (1 + math.exp(-k * (x - midpoint)))
    
    @staticmethod
    def weighted_average(values: List[float], weights: List[float]) -> float:
        """Calculate weighted average."""
        if not values or not weights:
            return 0
        total_weight = sum(weights)
        if total_weight == 0:
            return sum(values) / len(values)
        return sum(v * w for v, w in zip(values, weights)) / total_weight


# ============================================================================
# RANGE PARSING AND NORMALIZATION
# ============================================================================

class RangeParser:
    """Parse and normalize range strings to numeric values."""
    
    # Standard range mappings
    AGE_RANGES = {
        "18-24": (18, 24, 21),
        "25-29": (25, 29, 27),
        "30-34": (30, 34, 32),
        "35-44": (35, 44, 39.5),
        "45-54": (45, 54, 49.5),
        "55-64": (55, 64, 59.5),
        "65-74": (65, 74, 69.5),
        "75+": (75, 95, 82)
    }
    
    MONEY_RANGES = {
        "prefer_not_to_say": None,
        "none": (0, 0, 0),
        "no_property": (0, 0, 0),
        "no_car": (0, 0, 0),
        "$0": (0, 0, 0),
        "<$5k": (0, 5000, 2500),
        "<$100k": (0, 100000, 50000),
        "$5k-$10k": (5000, 10000, 7500),
        "$10k-$25k": (10000, 25000, 17500),
        "$25k-$50k": (25000, 50000, 37500),
        "$50k-$100k": (50000, 100000, 75000),
        "$100k-$250k": (100000, 250000, 175000),
        "$250k-$500k": (250000, 500000, 375000),
        "$500k-$1m": (500000, 1000000, 750000),
        "$1m-$2.5m": (1000000, 2500000, 1750000),
        "$2.5m+": (2500000, 10000000, 4000000),
        "$1m+": (1000000, 5000000, 2000000),
        "$150k+": (150000, 500000, 250000),
        "$75k+": (75000, 200000, 100000)
    }
    
    SALARY_RANGES = {
        "prefer_not_to_say": None,
        "<$1k": (0, 1000, 500),
        "$1k-$2k": (1000, 2000, 1500),
        "$2k-$3k": (2000, 3000, 2500),
        "$3k-$4k": (3000, 4000, 3500),
        "$4k-$5k": (4000, 5000, 4500),
        "$5k-$6k": (5000, 6000, 5500),
        "$6k-$7k": (6000, 7000, 6500),
        "$7k+": (7000, 15000, 9000)
    }
    
    @classmethod
    def parse_range(cls, value: str, range_type: str = "money") -> Optional[Tuple[float, float, float]]:
        """
        Parse a range string to (min, max, midpoint).
        Returns None for unknown or "prefer not to say".
        """
        value_normalized = value.lower().replace(" ", "_").replace(",", "")
        
        if range_type == "age":
            return cls.AGE_RANGES.get(value, cls.AGE_RANGES.get(value_normalized))
        elif range_type == "salary":
            return cls.SALARY_RANGES.get(value, cls.SALARY_RANGES.get(value_normalized))
        else:
            # Try direct lookup
            result = cls.MONEY_RANGES.get(value)
            if result is not None:
                return result
            result = cls.MONEY_RANGES.get(value_normalized)
            if result is not None:
                return result
            
            # Try pattern matching for numeric strings
            return cls._parse_numeric_string(value)
    
    @classmethod
    def _parse_numeric_string(cls, value: str) -> Optional[Tuple[float, float, float]]:
        """Parse numeric strings like "$50,000" or "50000"."""
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,]', '', value)
        
        # Try to parse as number
        try:
            num = float(cleaned)
            return (num, num, num)
        except ValueError:
            pass
        
        # Try range pattern like "50k-100k"
        match = re.match(r'(\d+)k?\s*[-–]\s*(\d+)k?', cleaned, re.IGNORECASE)
        if match:
            low = float(match.group(1))
            high = float(match.group(2))
            if 'k' in value.lower():
                low *= 1000
                high *= 1000
            return (low, high, (low + high) / 2)
        
        return None
    
    @classmethod
    def get_midpoint(cls, value: str, range_type: str = "money", 
                    default: Optional[float] = None) -> Optional[float]:
        """Get the midpoint value for a range string."""
        result = cls.parse_range(value, range_type)
        if result is None:
            return default
        return result[2]


# ============================================================================
# CONFIGURATION LOADER
# ============================================================================

class ConfigLoader:
    """Load and manage configuration files."""
    
    _cache: Dict[str, Any] = {}
    
    @classmethod
    def load_json(cls, filepath: str, use_cache: bool = True) -> Dict[str, Any]:
        """Load a JSON configuration file."""
        if use_cache and filepath in cls._cache:
            return cls._cache[filepath]
        
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        if use_cache:
            cls._cache[filepath] = data
        
        return data
    
    @classmethod
    def clear_cache(cls):
        """Clear the configuration cache."""
        cls._cache.clear()
    
    @classmethod
    def get_config_path(cls, filename: str) -> str:
        """Get the full path to a config file in the config directory."""
        base_dir = Path(__file__).parent.parent / "config"
        return str(base_dir / filename)


# ============================================================================
# GRAPH UTILITIES
# ============================================================================

class GraphUtils:
    """Utilities for working with directed graphs."""
    
    @staticmethod
    def topological_sort(nodes: List[str], edges: Dict[str, List[str]]) -> List[str]:
        """
        Perform topological sort on a DAG.
        
        Args:
            nodes: List of node IDs
            edges: Dict mapping node ID to list of dependency node IDs
        
        Returns:
            Topologically sorted list of node IDs
        """
        # Build in-degree map
        in_degree = {node: 0 for node in nodes}
        for node, deps in edges.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[node] = in_degree.get(node, 0) + 1
        
        # Find all nodes with no dependencies
        queue = [node for node in nodes if in_degree[node] == 0]
        result = []
        
        while queue:
            # Sort by some criteria for deterministic ordering
            queue.sort()
            node = queue.pop(0)
            result.append(node)
            
            # Reduce in-degree for dependent nodes
            for other_node, deps in edges.items():
                if node in deps:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        if len(result) != len(nodes):
            raise ValueError("Graph contains a cycle - not a valid DAG")
        
        return result
    
    @staticmethod
    def detect_cycles(nodes: List[str], edges: Dict[str, List[str]]) -> List[List[str]]:
        """Detect cycles in a graph. Returns list of cycles found."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in edges.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in nodes:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    @staticmethod
    def get_ancestors(node: str, edges: Dict[str, List[str]]) -> Set[str]:
        """Get all ancestor nodes (transitive dependencies)."""
        ancestors = set()
        stack = list(edges.get(node, []))
        
        while stack:
            current = stack.pop()
            if current not in ancestors:
                ancestors.add(current)
                stack.extend(edges.get(current, []))
        
        return ancestors
    
    @staticmethod
    def get_descendants(node: str, reverse_edges: Dict[str, List[str]]) -> Set[str]:
        """Get all descendant nodes (nodes that depend on this one)."""
        descendants = set()
        stack = list(reverse_edges.get(node, []))
        
        while stack:
            current = stack.pop()
            if current not in descendants:
                descendants.add(current)
                stack.extend(reverse_edges.get(current, []))
        
        return descendants


# ============================================================================
# SIMILARITY UTILITIES  
# ============================================================================

class SimilarityUtils:
    """Text and vector similarity utilities."""
    
    @staticmethod
    def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same length")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a ** 2 for a in vec1))
        norm2 = math.sqrt(sum(b ** 2 for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def keyword_overlap_score(text: str, keywords: List[str]) -> float:
        """Calculate how many keywords appear in text (0-1)."""
        if not keywords:
            return 0.0
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return matches / len(keywords)
