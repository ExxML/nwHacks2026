#!/usr/bin/env python3
"""
Simple Flask API for the Ascend Engine.
Run with: python api.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import (
    AscendEngine,
    create_profile,
    create_query
)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from React

engine = AscendEngine()


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """Generate recommendations from profile and query."""
    try:
        data = request.json
        
        # Create profile from request
        profile = create_profile(
            age_range=data.get('age_range', '30-34'),
            location=data.get('location', 'Unknown'),
            property_value=data.get('property_value', 'prefer_not_to_say'),
            vehicle_value=data.get('vehicle_value', 'prefer_not_to_say'),
            investments=data.get('investments', 'prefer_not_to_say'),
            debt=data.get('debt', 'prefer_not_to_say'),
            monthly_salary=data.get('monthly_salary', 'prefer_not_to_say'),
            has_dependents=data.get('has_dependents', False),
            employment_stability=float(data.get('employment_stability', 0.7))
        )
        
        # Create query from request
        query = create_query(
            risk_tolerance=data.get('risk_tolerance', 'medium'),
            current_situation=data.get('current_situation', ''),
            goal=data.get('goal', '')
        )
        
        # Process
        result = engine.process(profile, query)
        
        return jsonify(result.to_dict())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'engine': 'Ascend Engine v1.0'})


if __name__ == '__main__':
    print("🚀 Starting Ascend Engine API on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
