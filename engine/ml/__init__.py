"""
Ascend Engine - Machine Learning Module
Provides clustering, similarity, and learning capabilities.
"""

from typing import Dict, List, Any, Tuple, Optional
import math
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import UserProfile, QueryInput, FinancialHealth, LifeStage, RiskLevel


class ProfileVectorizer:
    """
    Converts user profiles to numerical vectors for ML operations.
    """
    
    # Feature scaling ranges
    FEATURE_RANGES = {
        "age": (18, 85),
        "net_worth": (-100000, 5000000),
        "debt_to_income": (0, 2),
        "savings_rate": (0, 0.5),
        "salary": (0, 20000),
        "investments": (0, 2000000)
    }
    
    @classmethod
    def profile_to_vector(cls, profile: UserProfile) -> List[float]:
        """
        Convert a user profile to a feature vector.
        
        Features:
        - Normalized age
        - Net worth (scaled)
        - Debt-to-income ratio
        - Savings rate
        - Monthly salary (scaled)
        - Investment level (scaled)
        - Financial health (encoded)
        - Life stage (encoded)
        - Has dependents (binary)
        - Is homeowner (binary)
        - Employment stability
        """
        vector = []
        
        # Age (normalized 0-1)
        vector.append(cls._normalize(
            profile.normalized_age,
            *cls.FEATURE_RANGES["age"]
        ))
        
        # Net worth (scaled, can be negative)
        vector.append(cls._normalize(
            profile.net_worth,
            *cls.FEATURE_RANGES["net_worth"]
        ))
        
        # Debt-to-income
        dti = min(profile.debt_to_income_ratio, 2)  # Cap at 2
        vector.append(cls._normalize(dti, *cls.FEATURE_RANGES["debt_to_income"]))
        
        # Savings rate
        vector.append(cls._normalize(
            profile.savings_rate,
            *cls.FEATURE_RANGES["savings_rate"]
        ))
        
        # Monthly salary
        vector.append(cls._normalize(
            profile.normalized_salary,
            *cls.FEATURE_RANGES["salary"]
        ))
        
        # Investments
        vector.append(cls._normalize(
            profile.normalized_investments,
            *cls.FEATURE_RANGES["investments"]
        ))
        
        # Financial health (1-5 -> 0-1)
        vector.append((profile.financial_health.value - 1) / 4)
        
        # Life stage (one-hot encoding, 6 stages)
        life_stage_encoding = [0.0] * 6
        stage_index = list(LifeStage).index(profile.life_stage)
        life_stage_encoding[stage_index] = 1.0
        vector.extend(life_stage_encoding)
        
        # Binary features
        vector.append(1.0 if profile.has_dependents else 0.0)
        vector.append(1.0 if profile.is_homeowner else 0.0)
        vector.append(profile.employment_stability)
        
        return vector
    
    @classmethod
    def query_to_vector(cls, query: QueryInput) -> List[float]:
        """
        Convert a query to a feature vector.
        
        Features:
        - Risk level (encoded)
        - Urgency score
        - Goal category (one-hot)
        """
        vector = []
        
        # Risk level (1-5 -> 0-1)
        vector.append((query.normalized_risk.value - 1) / 4)
        
        # Urgency
        vector.append(query.urgency_score)
        
        # Goal category (one-hot, ~10 categories)
        goal_categories = [
            "debt_freedom", "emergency_savings", "retirement",
            "wealth_building", "home_ownership", "income_increase",
            "financial_protection", "education", "major_purchase", "general"
        ]
        goal_encoding = [0.0] * len(goal_categories)
        if query.goal_category in goal_categories:
            goal_encoding[goal_categories.index(query.goal_category)] = 1.0
        else:
            goal_encoding[-1] = 1.0  # "general"
        vector.extend(goal_encoding)
        
        return vector
    
    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range."""
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return max(0, min(1, normalized))


class KMeansCluster:
    """
    Simple K-Means clustering implementation for profile segmentation.
    No external dependencies.
    """
    
    def __init__(self, k: int = 5, max_iterations: int = 100):
        self.k = k
        self.max_iterations = max_iterations
        self.centroids: List[List[float]] = []
        self.labels: List[int] = []
    
    def fit(self, vectors: List[List[float]]) -> None:
        """Fit the clustering model to the data."""
        if len(vectors) < self.k:
            raise ValueError(f"Need at least {self.k} samples for {self.k} clusters")
        
        n_features = len(vectors[0])
        
        # Initialize centroids using k-means++ style
        self.centroids = self._initialize_centroids(vectors)
        
        for iteration in range(self.max_iterations):
            # Assign each point to nearest centroid
            new_labels = []
            for vec in vectors:
                distances = [self._euclidean_distance(vec, c) for c in self.centroids]
                new_labels.append(distances.index(min(distances)))
            
            # Check for convergence
            if new_labels == self.labels:
                break
            
            self.labels = new_labels
            
            # Update centroids
            for i in range(self.k):
                cluster_points = [
                    vectors[j] for j in range(len(vectors))
                    if self.labels[j] == i
                ]
                if cluster_points:
                    self.centroids[i] = self._compute_centroid(cluster_points)
    
    def predict(self, vector: List[float]) -> int:
        """Predict cluster for a new vector."""
        distances = [self._euclidean_distance(vector, c) for c in self.centroids]
        return distances.index(min(distances))
    
    def _initialize_centroids(self, vectors: List[List[float]]) -> List[List[float]]:
        """Initialize centroids using k-means++ style selection."""
        centroids = [vectors[0]]
        
        for _ in range(1, self.k):
            # Calculate distances to nearest existing centroid
            min_distances = []
            for vec in vectors:
                min_dist = min(self._euclidean_distance(vec, c) for c in centroids)
                min_distances.append(min_dist ** 2)  # Square for probability
            
            # Select next centroid (farthest point)
            total_dist = sum(min_distances)
            if total_dist == 0:
                # All points are at centroids, pick any
                next_idx = len(centroids)
            else:
                # Pick point with highest distance (simplified from probability)
                next_idx = min_distances.index(max(min_distances))
            
            centroids.append(vectors[next_idx])
        
        return centroids
    
    @staticmethod
    def _euclidean_distance(v1: List[float], v2: List[float]) -> float:
        """Calculate Euclidean distance between two vectors."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
    
    @staticmethod
    def _compute_centroid(points: List[List[float]]) -> List[float]:
        """Compute centroid of a set of points."""
        n = len(points)
        n_features = len(points[0])
        centroid = [0.0] * n_features
        
        for point in points:
            for i in range(n_features):
                centroid[i] += point[i]
        
        return [c / n for c in centroid]


class ProfileClusterEngine:
    """
    Clusters user profiles for finding similar users and
    generating segment-based recommendations.
    """
    
    # Pre-defined cluster labels based on common financial personas
    CLUSTER_LABELS = {
        0: "Early Saver",
        1: "Debt Fighter",
        2: "Wealth Builder",
        3: "Security Seeker",
        4: "Balanced Planner"
    }
    
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.clusterer = KMeansCluster(k=n_clusters)
        self.vectorizer = ProfileVectorizer()
        self.cluster_profiles: Dict[int, Dict[str, Any]] = {}
        self._fitted = False
    
    def fit(self, profiles: List[UserProfile]) -> None:
        """Fit the clustering model to a set of profiles."""
        if len(profiles) < self.n_clusters:
            raise ValueError(f"Need at least {self.n_clusters} profiles")
        
        vectors = [self.vectorizer.profile_to_vector(p) for p in profiles]
        self.clusterer.fit(vectors)
        
        # Compute cluster profiles
        self._compute_cluster_profiles(profiles)
        self._fitted = True
    
    def predict_cluster(self, profile: UserProfile) -> Tuple[int, str]:
        """
        Predict which cluster a profile belongs to.
        Returns (cluster_id, cluster_label).
        """
        if not self._fitted:
            # Use rule-based assignment if not fitted
            return self._rule_based_assignment(profile)
        
        vector = self.vectorizer.profile_to_vector(profile)
        cluster_id = self.clusterer.predict(vector)
        label = self.CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}")
        
        return cluster_id, label
    
    def _rule_based_assignment(self, profile: UserProfile) -> Tuple[int, str]:
        """
        Assign cluster using rules when ML model isn't fitted.
        """
        # Early Saver: Young, low debt, building savings
        if profile.life_stage == LifeStage.EARLY_CAREER and profile.debt_to_income_ratio < 0.2:
            return 0, "Early Saver"
        
        # Debt Fighter: High debt-to-income
        if profile.debt_to_income_ratio > 0.3:
            return 1, "Debt Fighter"
        
        # Wealth Builder: Good financial health, focus on growth
        if profile.financial_health.value >= FinancialHealth.HEALTHY.value:
            return 2, "Wealth Builder"
        
        # Security Seeker: Older, focused on protection
        if profile.life_stage in [LifeStage.PRE_RETIREMENT, LifeStage.EARLY_RETIREMENT, LifeStage.LATE_RETIREMENT]:
            return 3, "Security Seeker"
        
        # Balanced Planner: Everyone else
        return 4, "Balanced Planner"
    
    def _compute_cluster_profiles(self, profiles: List[UserProfile]) -> None:
        """Compute average profile characteristics for each cluster."""
        cluster_members = defaultdict(list)
        
        for i, profile in enumerate(profiles):
            cluster_id = self.clusterer.labels[i]
            cluster_members[cluster_id].append(profile)
        
        for cluster_id, members in cluster_members.items():
            self.cluster_profiles[cluster_id] = {
                "size": len(members),
                "avg_age": sum(p.normalized_age for p in members) / len(members),
                "avg_net_worth": sum(p.net_worth for p in members) / len(members),
                "avg_dti": sum(p.debt_to_income_ratio for p in members) / len(members),
                "common_life_stages": self._mode_counter([p.life_stage for p in members]),
                "common_health": self._mode_counter([p.financial_health for p in members])
            }
    
    @staticmethod
    def _mode_counter(items: List[Any]) -> Any:
        """Find the most common item."""
        counts = defaultdict(int)
        for item in items:
            counts[item] += 1
        return max(counts, key=counts.get)
    
    def get_cluster_recommendations_boost(
        self,
        cluster_id: int
    ) -> Dict[str, float]:
        """
        Get recommendation category boosts for a cluster.
        """
        boosts = {
            0: {"savings": 1.2, "investment": 1.1},  # Early Saver
            1: {"debt": 1.4, "optimization": 1.2},   # Debt Fighter
            2: {"investment": 1.3, "income": 1.2},   # Wealth Builder
            3: {"protection": 1.4, "income": 0.8},   # Security Seeker
            4: {"savings": 1.1, "investment": 1.1}   # Balanced
        }
        return boosts.get(cluster_id, {})


class SimilarityEngine:
    """
    Finds similar profiles and recommendations based on similarity.
    """
    
    def __init__(self):
        self.vectorizer = ProfileVectorizer()
        self.profile_cache: List[Tuple[UserProfile, List[float]]] = []
    
    def add_profile(self, profile: UserProfile) -> None:
        """Add a profile to the similarity cache."""
        vector = self.vectorizer.profile_to_vector(profile)
        self.profile_cache.append((profile, vector))
    
    def find_similar_profiles(
        self,
        profile: UserProfile,
        top_k: int = 5
    ) -> List[Tuple[UserProfile, float]]:
        """
        Find the most similar profiles.
        Returns list of (profile, similarity_score) tuples.
        """
        target_vector = self.vectorizer.profile_to_vector(profile)
        
        similarities = []
        for cached_profile, cached_vector in self.profile_cache:
            sim = self._cosine_similarity(target_vector, cached_vector)
            similarities.append((cached_profile, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def compute_profile_similarity(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Compute similarity between two profiles."""
        v1 = self.vectorizer.profile_to_vector(profile1)
        v2 = self.vectorizer.profile_to_vector(profile2)
        return self._cosine_similarity(v1, v2)
    
    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a ** 2 for a in v1))
        norm2 = math.sqrt(sum(b ** 2 for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class GoalSimilarityEngine:
    """
    Computes similarity between goals using keyword and category matching.
    """
    
    # Goal category embeddings (simplified semantic vectors)
    GOAL_EMBEDDINGS = {
        "debt_freedom": [1.0, 0.8, 0.2, 0.1, 0.3, 0.1, 0.4, 0.1, 0.2],
        "emergency_savings": [0.3, 1.0, 0.3, 0.2, 0.4, 0.1, 0.8, 0.1, 0.3],
        "retirement": [0.2, 0.4, 1.0, 0.7, 0.3, 0.2, 0.5, 0.1, 0.2],
        "wealth_building": [0.1, 0.3, 0.7, 1.0, 0.4, 0.5, 0.3, 0.2, 0.3],
        "home_ownership": [0.4, 0.5, 0.3, 0.4, 1.0, 0.2, 0.5, 0.3, 0.6],
        "income_increase": [0.3, 0.2, 0.4, 0.6, 0.3, 1.0, 0.2, 0.4, 0.3],
        "financial_protection": [0.2, 0.6, 0.4, 0.2, 0.4, 0.1, 1.0, 0.3, 0.2],
        "education": [0.2, 0.3, 0.3, 0.4, 0.2, 0.5, 0.2, 1.0, 0.3],
        "major_purchase": [0.3, 0.4, 0.2, 0.3, 0.5, 0.2, 0.3, 0.2, 1.0]
    }
    
    @classmethod
    def compute_goal_similarity(cls, goal1: str, goal2: str) -> float:
        """Compute similarity between two goal categories."""
        if goal1 not in cls.GOAL_EMBEDDINGS or goal2 not in cls.GOAL_EMBEDDINGS:
            return 0.5  # Default moderate similarity
        
        v1 = cls.GOAL_EMBEDDINGS[goal1]
        v2 = cls.GOAL_EMBEDDINGS[goal2]
        
        # Cosine similarity
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a ** 2 for a in v1))
        norm2 = math.sqrt(sum(b ** 2 for b in v2))
        
        return dot / (norm1 * norm2)
    
    @classmethod
    def get_related_goals(cls, goal: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Get most related goal categories."""
        if goal not in cls.GOAL_EMBEDDINGS:
            return []
        
        similarities = []
        for other_goal in cls.GOAL_EMBEDDINGS:
            if other_goal != goal:
                sim = cls.compute_goal_similarity(goal, other_goal)
                similarities.append((other_goal, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class RecommendationLearner:
    """
    Learns from user feedback to improve recommendations over time.
    Uses simple collaborative filtering concepts.
    """
    
    def __init__(self):
        # Maps (profile_cluster, action_id) -> (helpful_count, total_count)
        self.feedback_matrix: Dict[Tuple[int, str], Tuple[int, int]] = defaultdict(
            lambda: (0, 0)
        )
        self.cluster_engine = ProfileClusterEngine()
    
    def record_feedback(
        self,
        profile: UserProfile,
        action_id: str,
        was_helpful: bool
    ) -> None:
        """Record feedback for learning."""
        cluster_id, _ = self.cluster_engine.predict_cluster(profile)
        key = (cluster_id, action_id)
        
        helpful, total = self.feedback_matrix[key]
        if was_helpful:
            helpful += 1
        total += 1
        self.feedback_matrix[key] = (helpful, total)
    
    def get_action_score_adjustment(
        self,
        profile: UserProfile,
        action_id: str
    ) -> float:
        """
        Get score adjustment based on learned feedback.
        Returns multiplier (1.0 = no change).
        """
        cluster_id, _ = self.cluster_engine.predict_cluster(profile)
        key = (cluster_id, action_id)
        
        if key not in self.feedback_matrix:
            return 1.0
        
        helpful, total = self.feedback_matrix[key]
        if total < 5:  # Not enough data
            return 1.0
        
        success_rate = helpful / total
        
        # Convert to multiplier (0.5 success -> 1.0, 0.8 success -> 1.15)
        adjustment = 0.7 + (success_rate * 0.6)
        return max(0.8, min(1.2, adjustment))
    
    def export_learnings(self) -> Dict[str, Any]:
        """Export learned data for persistence."""
        return {
            "feedback": {
                f"{k[0]}_{k[1]}": {"helpful": v[0], "total": v[1]}
                for k, v in self.feedback_matrix.items()
            }
        }
    
    def import_learnings(self, data: Dict[str, Any]) -> None:
        """Import previously learned data."""
        for key_str, counts in data.get("feedback", {}).items():
            parts = key_str.split("_", 1)
            if len(parts) == 2:
                cluster_id = int(parts[0])
                action_id = parts[1]
                self.feedback_matrix[(cluster_id, action_id)] = (
                    counts["helpful"],
                    counts["total"]
                )
