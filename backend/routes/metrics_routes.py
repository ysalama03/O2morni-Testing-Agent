"""
Metrics Routes
Handle metrics and observability endpoints
"""

from flask import Blueprint, jsonify
from datetime import datetime


# Global metrics storage
metrics_data = {
    'testsRun': 0,
    'testsPassed': 0,
    'testsFailed': 0,
    'executionTime': 0,
    'coverage': 0,
    'averageResponseTime': 0,
    'tokensConsumed': 0,
    'errors': []
}


def create_metrics_routes():
    """Create metrics routes blueprint"""
    blueprint = Blueprint('metrics', __name__, url_prefix='/api/metrics')
    
    @blueprint.route('/', methods=['GET'])
    def get_metrics():
        """Get current metrics"""
        try:
            return jsonify(metrics_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/reset', methods=['POST'])
    def reset_metrics():
        """Reset metrics"""
        try:
            global metrics_data
            metrics_data = {
                'testsRun': 0,
                'testsPassed': 0,
                'testsFailed': 0,
                'executionTime': 0,
                'coverage': 0,
                'averageResponseTime': 0,
                'tokensConsumed': 0,
                'errors': []
            }
            return jsonify({'success': True, 'timestamp': datetime.utcnow().isoformat()})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint
