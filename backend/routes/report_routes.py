"""
Report Routes
Handle report generation and retrieval endpoints
Integrates with LLM agent for report generation
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json


def create_report_routes(llm_agent):
    """Create report routes blueprint"""
    blueprint = Blueprint('reports', __name__, url_prefix='/api/reports')
    
    # Get base directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    
    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    def save_json_report(filename: str, data: dict) -> str:
        """Save report as JSON file"""
        file_path = os.path.join(REPORTS_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path
    
    def save_html_report(filename: str, html_content: str) -> str:
        """Save report as HTML file"""
        file_path = os.path.join(REPORTS_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return file_path
    
    def generate_html_report(execution_results: list, summary: dict, metrics: dict) -> str:
        """Generate HTML report from execution results"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Execution Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
        }}
        .summary-card.failed {{
            border-left-color: #f44336;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .test-result {{
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: #fafafa;
        }}
        .test-result.passed {{
            border-left: 4px solid #4CAF50;
        }}
        .test-result.failed {{
            border-left: 4px solid #f44336;
        }}
        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .test-name {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-badge.passed {{
            background: #4CAF50;
            color: white;
        }}
        .status-badge.failed {{
            background: #f44336;
            color: white;
        }}
        .steps {{
            margin-top: 15px;
        }}
        .step {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #2196F3;
        }}
        .error {{
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            border-left: 4px solid #f44336;
        }}
        .metrics {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .metrics h3 {{
            margin-top: 0;
            color: #666;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .metric-item {{
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Test Execution Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary.get('total', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="value" style="color: #4CAF50;">{summary.get('passed', 0)}</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="value" style="color: #f44336;">{summary.get('failed', 0)}</div>
            </div>
        </div>
"""
        
        # Add test results
        for result in execution_results:
            status = result.get('status', 'unknown')
            test_name = result.get('test_name', 'Unknown Test')
            steps = result.get('steps', [])
            errors = result.get('errors', [])
            
            html += f"""
        <div class="test-result {'passed' if status == 'passed' else 'failed'}">
            <div class="test-header">
                <div class="test-name">{test_name}</div>
                <span class="status-badge {status}">{status}</span>
            </div>
            <div class="steps">
"""
            for step in steps:
                step_desc = step.get('description', step.get('action', 'Unknown step'))
                html += f'                <div class="step">✓ {step_desc}</div>\n'
            
            if errors:
                html += '            </div>\n            <div class="error">\n'
                for error in errors:
                    error_msg = error.get('error', str(error))
                    html += f'                <strong>Error:</strong> {error_msg}<br>\n'
                html += '            </div>\n'
            else:
                html += '            </div>\n'
            
            html += '        </div>\n'
        
        # Add metrics
        if metrics:
            html += f"""
        <div class="metrics">
            <h3>📊 Execution Metrics</h3>
            <div class="metrics-grid">
"""
            if 'average_response_time' in metrics:
                html += f"""
                <div class="metric-item">
                    <div class="metric-value">{metrics.get('average_response_time', 0):.2f}ms</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
"""
            if 'total_tokens_consumed' in metrics:
                html += f"""
                <div class="metric-item">
                    <div class="metric-value">{metrics.get('total_tokens_consumed', 0)}</div>
                    <div class="metric-label">Total Tokens</div>
                </div>
"""
            if 'total_requests' in metrics:
                html += f"""
                <div class="metric-item">
                    <div class="metric-value">{metrics.get('total_requests', 0)}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
"""
            html += """
            </div>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html
    
    @blueprint.route('/list', methods=['GET'])
    def list_reports():
        """List all generated reports"""
        try:
            if not os.path.exists(REPORTS_DIR):
                return jsonify({'reports': []})
            
            reports = []
            for filename in sorted(os.listdir(REPORTS_DIR), reverse=True):
                if filename.endswith(('.html', '.json', '.xml')):
                    file_path = os.path.join(REPORTS_DIR, filename)
                    file_stat = os.stat(file_path)
                    reports.append({
                        'name': filename,
                        'path': file_path,
                        'size': file_stat.st_size,
                        'type': 'html' if filename.endswith('.html') else 'json' if filename.endswith('.json') else 'xml',
                        'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
            
            return jsonify({
                'reports': reports,
                'count': len(reports)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/generate', methods=['POST'])
    def generate_report():
        """Generate a test report from execution results"""
        try:
            data = request.get_json()
            execution_results = data.get('execution_results')
            summary = data.get('summary', {})
            metrics = data.get('metrics', {})
            format_type = data.get('format', 'html')  # 'html' or 'json'
            
            if not execution_results:
                # Try to get from LLM agent if available
                if llm_agent and hasattr(llm_agent, 'execution_results') and llm_agent.execution_results:
                    execution_results = [
                        {
                            'test_name': r.test_name,
                            'status': r.status,
                            'duration_ms': r.duration_ms,
                            'steps': r.steps_executed,
                            'errors': [{'error': r.error_message}] if r.error_message else []
                        }
                        for r in llm_agent.execution_results
                    ]
                    summary = {
                        'total': len(execution_results),
                        'passed': sum(1 for r in execution_results if r.get('status') == 'passed'),
                        'failed': sum(1 for r in execution_results if r.get('status') == 'failed')
                    }
                    metrics = llm_agent.metrics.to_dict() if hasattr(llm_agent, 'metrics') else {}
                else:
                    return jsonify({
                        'error': 'No execution results provided and none found in agent',
                        'timestamp': datetime.utcnow().isoformat()
                    }), 400
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            if format_type == 'html':
                html_content = generate_html_report(execution_results, summary, metrics)
                filename = f"test_report_{timestamp}.html"
                report_path = save_html_report(filename, html_content)
            else:
                report_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'summary': summary,
                    'execution_results': execution_results,
                    'metrics': metrics
                }
                filename = f"test_report_{timestamp}.json"
                report_path = save_json_report(filename, report_data)
            
            return jsonify({
                'success': True,
                'message': f'Report generated successfully',
                'filename': filename,
                'path': report_path,
                'format': format_type,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @blueprint.route('/<report_name>', methods=['GET'])
    def get_report(report_name):
        """Get a specific report file"""
        try:
            file_path = os.path.join(REPORTS_DIR, report_name)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'Report file not found'}), 404
            
            if report_name.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify(data)
            else:
                # For HTML/XML, return file info
                file_stat = os.stat(file_path)
                return jsonify({
                    'name': report_name,
                    'path': file_path,
                    'type': 'html' if report_name.endswith('.html') else 'xml',
                    'size': file_stat.st_size,
                    'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint
