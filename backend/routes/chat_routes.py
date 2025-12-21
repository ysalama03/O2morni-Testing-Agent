"""
Chat Routes
Handle chat/messaging endpoints for smolagents-based LLM agent
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone


def create_chat_routes(llm_agent):
    """Create chat routes blueprint"""
    blueprint = Blueprint('chat', __name__, url_prefix='/api/chat')
    
    @blueprint.route('/', methods=['POST'])
    def send_message():
        """Send a message to the LLM agent and receive a response"""
        try:
            data = request.get_json()
            message = data.get('message')
            
            if not message:
                return jsonify({'error': 'Message is required'}), 400
            
            # Get full response from agent
            response = llm_agent.process_message(message)
            
            # Return complete response with all fields expected by frontend
            return jsonify({
                'text': response.get('text', ''),
                'message': response.get('text', ''),  # Backward compatibility
                'actions': response.get('actions', []),
                'code': response.get('code'),
                'phase': response.get('phase', 'idle'),
                'metrics': response.get('metrics', {}),
                'success': response.get('success', True),
                'test_cases': response.get('test_cases'),
                'ground_truth': response.get('ground_truth'),
                'screenshot': response.get('screenshot'),
                'execution_results': response.get('execution_results'),
                'generated_tests': response.get('generated_tests'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            print(f"Error in chat route: {e}")
            return jsonify({
                'error': str(e),
                'success': False,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
    
    @blueprint.route('/history', methods=['GET'])
    def get_history():
        """Get chat history"""
        try:
            history = llm_agent.get_chat_history()
            return jsonify({
                'history': history,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/status', methods=['GET'])
    def get_agent_status():
        """Get the current status of the LLM agent"""
        try:
            status = llm_agent.get_agent_status()
            return jsonify({
                'status': status,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/execution-progress', methods=['GET'])
    def get_execution_progress():
        """Get current test execution progress for real-time updates"""
        try:
            progress = llm_agent.get_execution_progress()
            return jsonify({
                'progress': progress,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/initialize', methods=['POST'])
    def initialize_agent():
        """Initialize or reinitialize the LLM agent"""
        try:
            llm_agent.initialize()
            return jsonify({
                'message': 'Agent initialized successfully',
                'status': llm_agent.get_agent_status(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/clear', methods=['POST'])
    def clear_history():
        """Clear chat history"""
        try:
            llm_agent.clear_chat_history()
            return jsonify({
                'message': 'Chat history cleared',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/reset', methods=['POST'])
    def reset_agent():
        """Reset the agent to initial state"""
        try:
            result = llm_agent.reset_agent()
            
            # Also reset global metrics data
            try:
                from routes.metrics_routes import metrics_data
                metrics_data.update({
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
                })
            except Exception as metrics_error:
                print(f"Warning: Could not reset metrics: {metrics_error}")
            
            return jsonify({
                'text': result.get('message', 'Agent reset successfully'),
                'message': result.get('message', 'Agent reset successfully'),
                'phase': result.get('phase', 'idle'),
                'success': result.get('success', True),
                'metrics': result.get('metrics', {}),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'success': False,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
    
    return blueprint
