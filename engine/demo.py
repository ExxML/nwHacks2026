#!/usr/bin/env python3
"""
Ascend Engine - Demo Script
Demonstrates the full capabilities of the financial decision engine.
"""

import json
import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import (
    AscendEngine,
    AscendEngineBuilder,
    create_profile,
    create_query,
    quick_recommend,
    ProfileClusterEngine,
    GoalSimilarityEngine,
    ScoringWeights
)


def demo_basic_usage():
    """Demonstrate basic engine usage."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Usage")
    print("="*60)
    
    # Create engine
    engine = AscendEngine()
    
    # Create user profile
    profile = create_profile(
        age_range="25-29",
        location="Seattle, WA",
        property_value="no_property",
        vehicle_value="$10k-$25k",
        investments="$5k-$10k",
        debt="$25k-$50k",
        monthly_salary="$4k-$5k",
        has_dependents=False,
        employment_stability=0.8
    )
    
    # Create query
    query = create_query(
        risk_tolerance="medium",
        current_situation="Just got my first real job after college, have student loans",
        goal="Pay off student loans and start investing for the future"
    )
    
    # Process
    result = engine.process(profile, query)
    
    # Display results
    print(f"\n📊 Profile Summary:")
    print(f"   Life Stage: {result.profile_summary['life_stage']}")
    print(f"   Financial Health: {result.profile_summary['financial_health']}")
    print(f"   Net Worth: ${result.profile_summary['net_worth']:,.0f}")
    print(f"   Debt-to-Income: {result.profile_summary['debt_to_income_ratio']:.1%}")
    print(f"   Goal Category: {result.profile_summary['goal_category']}")
    print(f"   Top Priorities: {', '.join(result.profile_summary['top_priorities'])}")
    
    print(f"\n🎯 Recommendations:")
    
    if result.immediate:
        print(f"\n   IMMEDIATE ({len(result.immediate)} actions):")
        for rec in result.immediate[:3]:
            print(f"   • [{rec.score:.0f}] {rec.action.name}")
            print(f"     └─ {rec.action.description[:60]}...")
    
    if result.short_term:
        print(f"\n   SHORT-TERM ({len(result.short_term)} actions):")
        for rec in result.short_term[:3]:
            print(f"   • [{rec.score:.0f}] {rec.action.name}")
    
    if result.medium_term:
        print(f"\n   MEDIUM-TERM ({len(result.medium_term)} actions):")
        for rec in result.medium_term[:3]:
            print(f"   • [{rec.score:.0f}] {rec.action.name}")
    
    if result.long_term:
        print(f"\n   LONG-TERM ({len(result.long_term)} actions):")
        for rec in result.long_term[:3]:
            print(f"   • [{rec.score:.0f}] {rec.action.name}")
    
    print(f"\n⏱️ Processing time: {result.processing_time_ms:.1f}ms")
    print(f"📈 Actions considered: {result.total_actions_considered}")
    
    return result


def demo_different_profiles():
    """Demonstrate how recommendations change for different profiles."""
    print("\n" + "="*60)
    print("DEMO 2: Different Profiles Comparison")
    print("="*60)
    
    engine = AscendEngine()
    
    profiles = [
        {
            "name": "Young Professional with Debt",
            "profile": create_profile(
                age_range="25-29",
                debt="$50k-$100k",
                investments="$0",
                monthly_salary="$4k-$5k"
            ),
            "query": create_query(
                risk_tolerance="medium",
                current_situation="Heavy student loan debt",
                goal="Become debt free"
            )
        },
        {
            "name": "Mid-Career Family Person",
            "profile": create_profile(
                age_range="35-44",
                property_value="$250k-$500k",
                debt="$100k-$250k",  # Mortgage
                investments="$50k-$100k",
                monthly_salary="$6k-$7k",
                has_dependents=True
            ),
            "query": create_query(
                risk_tolerance="reliable",
                current_situation="Married with kids, have mortgage",
                goal="Protect family and save for retirement"
            )
        },
        {
            "name": "Aggressive Wealth Builder",
            "profile": create_profile(
                age_range="30-34",
                property_value="no_property",
                debt="$0",
                investments="$100k-$250k",
                monthly_salary="$7k+"
            ),
            "query": create_query(
                risk_tolerance="risky",
                current_situation="High earner, no debt",
                goal="Maximize wealth growth and early retirement"
            )
        },
        {
            "name": "Pre-Retiree",
            "profile": create_profile(
                age_range="55-64",
                property_value="$500k-$1m",
                debt="$0",
                investments="$500k-$1m",
                monthly_salary="$5k-$6k"
            ),
            "query": create_query(
                risk_tolerance="reliable",
                current_situation="Planning to retire in 5-10 years",
                goal="Secure retirement and protect savings"
            )
        }
    ]
    
    for p in profiles:
        result = engine.process(p["profile"], p["query"])
        
        print(f"\n👤 {p['name']}")
        print(f"   Health: {result.profile_summary['financial_health']}")
        print(f"   Top 3 Actions:")
        
        all_recs = result.sequential_path[:3]
        for i, rec in enumerate(all_recs, 1):
            print(f"   {i}. [{rec.score:.0f}] {rec.action.name} ({rec.horizon.value})")


def demo_quick_recommend():
    """Demonstrate the quick one-liner API."""
    print("\n" + "="*60)
    print("DEMO 3: Quick Recommend API")
    print("="*60)
    
    result = quick_recommend(
        age_range="30-34",
        monthly_salary="$5k-$6k",
        debt="$10k-$25k",
        investments="$25k-$50k",
        risk_tolerance="medium",
        goal="Save for a house down payment"
    )
    
    print("\n📋 Quick Recommendation Result (JSON):")
    print(json.dumps(result["metadata"], indent=2))
    print(f"\nTop 5 Sequential Actions:")
    for i, action in enumerate(result["sequential_path"][:5], 1):
        print(f"   {i}. [{action['score']:.0f}] {action['name']}")


def demo_goal_similarity():
    """Demonstrate goal similarity engine."""
    print("\n" + "="*60)
    print("DEMO 4: Goal Similarity Analysis")
    print("="*60)
    
    goals = ["debt_freedom", "wealth_building", "retirement", "emergency_savings"]
    
    for goal in goals:
        related = GoalSimilarityEngine.get_related_goals(goal, top_k=3)
        print(f"\n🎯 {goal.replace('_', ' ').title()}")
        print(f"   Related goals:")
        for related_goal, similarity in related:
            print(f"   • {related_goal.replace('_', ' ').title()} ({similarity:.0%})")


def demo_profile_clustering():
    """Demonstrate profile clustering."""
    print("\n" + "="*60)
    print("DEMO 5: Profile Clustering")
    print("="*60)
    
    cluster_engine = ProfileClusterEngine()
    
    test_profiles = [
        create_profile(age_range="25-29", debt="$50k-$100k", investments="$0", monthly_salary="$3k-$4k"),
        create_profile(age_range="35-44", debt="$0", investments="$100k-$250k", monthly_salary="$7k+"),
        create_profile(age_range="55-64", debt="$0", investments="$250k-$500k", monthly_salary="$5k-$6k"),
    ]
    
    for i, profile in enumerate(test_profiles):
        cluster_id, label = cluster_engine.predict_cluster(profile)
        print(f"\n👤 Profile {i+1}")
        print(f"   Age: {profile.age_range}, Debt: {profile.debt}")
        print(f"   Cluster: {label}")
        boosts = cluster_engine.get_cluster_recommendations_boost(cluster_id)
        if boosts:
            print(f"   Category Boosts: {boosts}")


def demo_custom_weights():
    """Demonstrate custom scoring weights."""
    print("\n" + "="*60)
    print("DEMO 6: Custom Scoring Weights")
    print("="*60)
    
    # Default weights
    default_engine = AscendEngine()
    
    # Custom weights - heavily favor goal alignment
    custom_weights = ScoringWeights(
        goal_alignment_weight=0.40,  # Double the default
        risk_tolerance_weight=0.10,
        financial_health_weight=0.10,
        age_weight=0.10,
        base_priority_weight=0.10
    )
    
    custom_engine = AscendEngineBuilder() \
        .with_weights(custom_weights) \
        .build()
    
    profile = create_profile(
        age_range="30-34",
        debt="$25k-$50k",
        investments="$10k-$25k",
        monthly_salary="$5k-$6k"
    )
    
    # Goal-focused query
    query = create_query(
        risk_tolerance="medium",
        current_situation="Want to focus on retirement",
        goal="Maximize retirement contributions"
    )
    
    default_result = default_engine.process(profile, query)
    custom_result = custom_engine.process(profile, query)
    
    print("\n📊 Default Weights - Top 5 Actions:")
    for rec in default_result.sequential_path[:5]:
        print(f"   [{rec.score:.0f}] {rec.action.name}")
    
    print("\n🎯 Goal-Heavy Weights - Top 5 Actions:")
    for rec in custom_result.sequential_path[:5]:
        print(f"   [{rec.score:.0f}] {rec.action.name}")


def demo_detailed_reasoning():
    """Show detailed reasoning for recommendations."""
    print("\n" + "="*60)
    print("DEMO 7: Detailed Recommendation Reasoning")
    print("="*60)
    
    engine = AscendEngine()
    
    profile = create_profile(
        age_range="30-34",
        debt="$50k-$100k",
        investments="$5k-$10k",
        monthly_salary="$4k-$5k",
        has_dependents=True
    )
    
    query = create_query(
        risk_tolerance="reliable",
        current_situation="Have young children, worried about financial security",
        goal="Protect family and build emergency savings"
    )
    
    result = engine.process(profile, query)
    
    print("\n🔍 Detailed Analysis of Top 3 Recommendations:\n")
    
    for rec in result.sequential_path[:3]:
        print(f"━━━ {rec.action.name} ━━━")
        print(f"Score: {rec.score:.0f}/100")
        print(f"Category: {rec.action.category} > {rec.action.subcategory}")
        print(f"Horizon: {rec.horizon.value}")
        print(f"\nWhy recommended:")
        for reason in rec.reasoning[:4]:
            print(f"  • {reason}")
        
        print(f"\nScore Breakdown:")
        for factor, score in sorted(rec.score_breakdown.items(), key=lambda x: -x[1])[:4]:
            print(f"  • {factor}: {score:.3f}")
        
        if rec.prerequisites:
            print(f"\nPrerequisites: {', '.join(rec.prerequisites[:3])}")
        
        if rec.estimated_impact:
            print(f"\nEstimated Impact:")
            for impact, value in rec.estimated_impact.items():
                if isinstance(value, float) and value > 0:
                    print(f"  • {impact}: ${value:,.0f}" if value > 100 else f"  • {impact}: {value:.1f}")
        
        print()


def main():
    """Run all demos."""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " ASCEND ENGINE - Financial Decision Engine Demo ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    try:
        demo_basic_usage()
        demo_different_profiles()
        demo_quick_recommend()
        demo_goal_similarity()
        demo_profile_clustering()
        demo_custom_weights()
        demo_detailed_reasoning()
        
        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
