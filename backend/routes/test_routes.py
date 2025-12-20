"""
Test Routes
Handle test generation and execution endpoints
Integrates with LLM agent for test generation and execution
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json


def create_test_routes(llm_agent):
    """Create test routes blueprint"""
    blueprint = Blueprint('tests', __name__, url_prefix='/api/tests')
    
    # Get base directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    TESTS_DIR = os.path.join(BASE_DIR, 'generated_tests')
    
    # Ensure tests directory exists
    os.makedirs(TESTS_DIR, exist_ok=True)
    
    def save_test_file(filename: str, code: str) -> str:
        """Save test code to file and return file path"""
        file_path = os.path.join(TESTS_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return file_path
    
    @blueprint.route('/generate', methods=['POST'])
    def generate_test():
        """Generate a test using LLM agent"""
        try:
            data = request.get_json()
            test_case_id = data.get('testCaseId')  # Optional: specific test case ID
            auto_save = data.get('autoSave', True)  # Auto-save to file by default
            
            if not llm_agent or not llm_agent.is_initialized:
                return jsonify({
                    'error': 'LLM agent not initialized. Please initialize the agent first.',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
            
            # Use LLM agent to generate test code
            result = llm_agent.generate_test_code(test_case_id)
            
            if not result.get('success'):
                return jsonify({
                    'error': result.get('error', 'Failed to generate test code'),
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
            
            # Save generated tests to files if auto_save is enabled
            saved_files = []
            if auto_save and result.get('generated_tests'):
                for test_data in result.get('generated_tests', []):
                    test_id = test_data.get('id') or test_data.get('test_id', 'unknown')
                    filename = f"test_{test_id.lower().replace('-', '_')}.py"
                    code = test_data.get('code', '')
                    
                    if code:
                        file_path = save_test_file(filename, code)
                        saved_files.append({
                            'filename': filename,
                            'path': file_path,
                            'test_id': test_id
                        })
            
            # Also save from generated_code dict if available
            if auto_save and hasattr(llm_agent, 'generated_code') and llm_agent.generated_code:
                for test_id, code in llm_agent.generated_code.items():
                    # Check if already saved
                    if not any(f['test_id'] == test_id for f in saved_files):
                        filename = f"test_{test_id.lower().replace('-', '_')}.py"
                        file_path = save_test_file(filename, code)
                        saved_files.append({
                            'filename': filename,
                            'path': file_path,
                            'test_id': test_id
                        })
            
            return jsonify({
                'success': True,
                'message': result.get('message', 'Test code generated successfully'),
                'generated_tests': result.get('generated_tests', []),
                'saved_files': saved_files,
                'phase': result.get('phase', 'implementation'),
                'metrics': result.get('metrics', {}),
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @blueprint.route('/execute', methods=['POST'])
    def execute_test():
        """Execute tests using LLM agent"""
        try:
            data = request.get_json()
            test_case_id = data.get('testCaseId')  # Optional: specific test case ID
            auto_save_report = data.get('autoSaveReport', True)  # Auto-save report by default
            
            if not llm_agent or not llm_agent.is_initialized:
                return jsonify({
                    'error': 'LLM agent not initialized. Please initialize the agent first.',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
            
            # Use LLM agent to execute tests
            result = llm_agent.execute_tests(test_case_id)
            
            if not result.get('success'):
                return jsonify({
                    'error': result.get('error', 'Failed to execute tests'),
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
            
            # Save execution report if auto_save_report is enabled
            report_path = None
            if auto_save_report and result.get('execution_results'):
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                report_filename = f"test_execution_report_{timestamp}.json"
                report_path = os.path.join(BASE_DIR, 'reports', report_filename)
                
                # Ensure reports directory exists
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                
                # Save report as JSON
                report_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'summary': result.get('summary', {}),
                    'execution_results': result.get('execution_results', []),
                    'screenshots': result.get('screenshots', []),
                    'metrics': result.get('metrics', {})
                }
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'message': result.get('message', 'Tests executed successfully'),
                'execution_results': result.get('execution_results', []),
                'summary': result.get('summary', {}),
                'screenshots': result.get('screenshots', []),
                'report_path': report_path,
                'phase': result.get('phase', 'verification'),
                'metrics': result.get('metrics', {}),
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @blueprint.route('/list', methods=['GET'])
    def list_tests():
        """List all generated test files"""
        try:
            if not os.path.exists(TESTS_DIR):
                return jsonify({'tests': []})
            
            tests = []
            for filename in sorted(os.listdir(TESTS_DIR)):
                if filename.endswith('.py'):
                    file_path = os.path.join(TESTS_DIR, filename)
                    file_stat = os.stat(file_path)
                    tests.append({
                        'name': filename,
                        'path': file_path,
                        'size': file_stat.st_size,
                        'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
            
            return jsonify({
                'tests': tests,
                'count': len(tests)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/export', methods=['POST'])
    def export_tests():
        """Export all generated tests to files"""
        try:
            if not llm_agent or not llm_agent.is_initialized:
                return jsonify({
                    'error': 'LLM agent not initialized. Please initialize the agent first.',
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
            
            # Use LLM agent's export method
            result = llm_agent._export_tests()
            
            if not result.get('success'):
                return jsonify({
                    'error': result.get('error', 'No tests to export'),
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
            
            # Save all exported tests to files
            saved_files = []
            for test_data in result.get('exported_tests', []):
                filename = test_data.get('filename')
                code = test_data.get('code', '')
                
                if filename and code:
                    file_path = save_test_file(filename, code)
                    saved_files.append({
                        'filename': filename,
                        'path': file_path
                    })
            
            return jsonify({
                'success': True,
                'message': f'Exported {len(saved_files)} test files',
                'saved_files': saved_files,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @blueprint.route('/<test_id>', methods=['GET'])
    def get_test(test_id):
        """Get a specific test file content"""
        try:
            # Try to find test file
            filename = f"test_{test_id.lower().replace('-', '_')}.py"
            file_path = os.path.join(TESTS_DIR, filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'Test file not found'}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return jsonify({
                'test_id': test_id,
                'filename': filename,
                'code': code,
                'path': file_path
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint
