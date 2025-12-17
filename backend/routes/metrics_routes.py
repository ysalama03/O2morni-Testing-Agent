"""
Metrics Routes
Handle metrics and observability endpoints for the 4-phase testing workflow
"""

from flask import Blueprint, jsonify
from datetime import datetime


# Global metrics storage (merged with agent metrics)
metrics_data = {
    'testsRun': 0,
    'testsPassed': 0,
    'testsFailed': 0,
    'executionTime': 0,
    'coverage': 0,
    'averageResponseTime': 0,
    'tokensConsumed': 0,
    # New real-time metrics
    'average_response_time': 0,
    'total_tokens_consumed': 0,
    'total_requests': 0,
    'response_times': [],
    'errors': []
}

# Reference to LLM agent (set from app.py)
llm_agent_ref = None


def set_llm_agent(agent):
    """Set reference to LLM agent for metrics collection"""
    global llm_agent_ref
    llm_agent_ref = agent


def create_metrics_routes():
    """Create metrics routes blueprint"""
    blueprint = Blueprint('metrics', __name__, url_prefix='/api/metrics')
    
    @blueprint.route('/', methods=['GET'])
    def get_metrics():
        """Get current metrics - combines test metrics with agent metrics"""
        try:
            # Start with base metrics
            combined_metrics = dict(metrics_data)
            
            # Merge with agent metrics if available
            if llm_agent_ref is not None:
                try:
                    agent_metrics = llm_agent_ref.get_metrics()
                    if agent_metrics:
                        combined_metrics.update(agent_metrics)
                except Exception as e:
                    print(f"Error getting agent metrics: {e}")
            
            return jsonify(combined_metrics)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/agent', methods=['GET'])
    def get_agent_metrics():
        """Get LLM agent specific metrics (response time, tokens)"""
        try:
            if llm_agent_ref is None:
                return jsonify({
                    'average_response_time': 0,
                    'total_tokens_consumed': 0,
                    'total_requests': 0,
                    'response_times': []
                })
            
            return jsonify(llm_agent_ref.get_metrics())
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
                'average_response_time': 0,
                'total_tokens_consumed': 0,
                'total_requests': 0,
                'response_times': [],
                'errors': []
            }
            return jsonify({'success': True, 'timestamp': datetime.utcnow().isoformat()})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/update', methods=['POST'])
    def update_metrics():
        """Update test execution metrics"""
        from flask import request
        try:
            data = request.get_json() or {}
            
            # Update test metrics
            for key in ['testsRun', 'testsPassed', 'testsFailed', 'executionTime', 'coverage']:
                if key in data:
                    metrics_data[key] = data[key]
            
            # Append errors if provided
            if 'error' in data:
                metrics_data['errors'].append({
                    'message': data['error'],
                    'timestamp': datetime.utcnow().isoformat()
                })
                # Keep only last 10 errors
                metrics_data['errors'] = metrics_data['errors'][-10:]
            
            return jsonify({'success': True, 'metrics': metrics_data})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint
