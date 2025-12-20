"""
Chat Routes
Handle chat/messaging endpoints for smolagents-based LLM agent
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, UTC

def truncate_screenshot(data):
    """
    Returns a copy of the dictionary with the 'screenshot' field truncated 
    to prevent terminal log pollution.
    """
    if not isinstance(data, dict):
        return data
        
    # Create a shallow copy so we don't modify the original response
    clean_data = data.copy()
    
    if 'screenshot' in clean_data and isinstance(clean_data['screenshot'], str):
        s = clean_data['screenshot']
        # Show only first 30 and last 10 characters
        clean_data['screenshot'] = f"{s[:30]}...[truncated {len(s)} chars]...{s[-10:]}"
        
    # Also handle nested ground_truth if necessary
    if 'ground_truth' in clean_data and isinstance(clean_data['ground_truth'], dict):
        if 'screenshot' in clean_data['ground_truth']:
            clean_data['ground_truth']['screenshot'] = "[truncated]"
            
    return clean_data

def create_chat_routes(llm_agent):
    """Create chat routes blueprint"""
    blueprint = Blueprint('chat', __name__, url_prefix='/api/chat')
    
    @blueprint.route('/', methods=['POST'])
    def send_message():
        """Send a message to the LLM agent and receive a response"""
        try:
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({'error': 'Message is required'}), 400
            
            message = data.get('message')
            
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
                'timestamp': datetime.now(UTC).isoformat()
            })
        except Exception as e:
            print(f"Error in chat route: {e}")
            return jsonify({
                'error': str(e),
                'success': False,
                'timestamp': datetime.now(UTC).isoformat()
            }), 500
    
    @blueprint.route('/history', methods=['GET'])
    def get_history():
        """Get chat history"""
        try:
            history = llm_agent.get_chat_history()
            return jsonify({
                'history': history,
                'timestamp': datetime.now(UTC).isoformat()
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
                'timestamp': datetime.now(UTC).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/initialize', methods=['POST'])
    def initialize_agent():
        """Initialize or reinitialize the LLM agent"""
        try:
            # Note: browser_controller is already linked during app startup
            llm_agent.initialize()
            return jsonify({
                'message': 'Agent initialized successfully',
                'status': llm_agent.get_agent_status(),
                'timestamp': datetime.now(UTC).isoformat()
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
                'timestamp': datetime.now(UTC).isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint