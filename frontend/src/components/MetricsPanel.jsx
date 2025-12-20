import React from 'react';

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return "0ms";
  // If the value is 1 or greater, it's likely seconds
  if (seconds >= 1) {
    return `${seconds.toFixed(2)}s`;
  }
  // Otherwise, convert to milliseconds for readability
  return `${(seconds * 1000).toFixed(0)}ms`;
};
/**
 * MetricsPanel Component
 * Displays real-time metrics: Average Response Time & Token Usage
 * Plus test execution metrics and workflow phase status
 */
const MetricsPanel = ({ metrics = {}, workflowPhase = 'idle' }) => {
  const {
    testsRun = 0,
    testsPassed = 0,
    testsFailed = 0,
    executionTime = 0,
    coverage = 0,
    // Real-time metrics from LLM agent
    average_response_time = 0,
    total_tokens_consumed = 0,
    total_requests = 0,
    response_times = [],
    // Legacy support
    averageResponseTime = 0,
    tokensConsumed = 0,
    errors = []
  } = metrics;

  // Use new metrics format if available, otherwise fall back to legacy
  const avgResponseTime = average_response_time || averageResponseTime;
  const totalTokens = total_tokens_consumed || tokensConsumed;

  const successRate = testsRun > 0 
    ? ((testsPassed / testsRun) * 100).toFixed(1) 
    : 0;

  // Phase display info
  const phaseInfo = {
    'idle': { emoji: '⏸️', label: 'Ready', color: '#6b7280' },
    'exploration': { emoji: '🔍', label: 'Exploring', color: '#3b82f6' },
    'collaborative_design': { emoji: '📝', label: 'Designing', color: '#8b5cf6' },
    'implementation': { emoji: '💻', label: 'Implementing', color: '#f59e0b' },
    'verification': { emoji: '✅', label: 'Verifying', color: '#10b981' }
  };

  const currentPhase = phaseInfo[workflowPhase] || phaseInfo['idle'];

  return (
    <div className="metrics-panel">
      {/* Workflow Phase Indicator */}
      <div className="phase-indicator" style={{ borderColor: currentPhase.color }}>
        <span className="phase-emoji">{currentPhase.emoji}</span>
        <span className="phase-label" style={{ color: currentPhase.color }}>
          {currentPhase.label}
        </span>
      </div>

      {/* Primary Real-Time Metrics */}
      <div className="realtime-metrics">
        <div className="realtime-metric primary">
          <div className="metric-icon">⏱️</div>
          <div className="metric-info">
            <div className="metric-label">Avg Response Time</div>
            <div className="metric-value highlight">
              {formatDuration(avgResponseTime)}
            </div>
          </div>
        </div>
        <div className="realtime-metric primary">
          <div className="metric-icon">🎯</div>
          <div className="metric-info">
            <div className="metric-label">Token Usage</div>
            <div className="metric-value highlight">
              {totalTokens.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Request Counter */}
      <div className="request-counter">
        <span className="request-label">API Requests:</span>
        <span className="request-value">{total_requests}</span>
      </div>

      {/* Test Execution Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Tests Run</div>
          <div className="metric-value">{testsRun}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Passed</div>
          <div className="metric-value success">{testsPassed}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Failed</div>
          <div className="metric-value error">{testsFailed}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Success Rate</div>
          <div className="metric-value">{successRate}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Execution Time</div>
          <div className="metric-value">{executionTime}ms</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Coverage</div>
          <div className="metric-value">{coverage}%</div>
        </div>
      </div>

      {/* Response Time History Chart (simple bar) */}
      {response_times && response_times.length > 0 && (
        <div className="response-time-chart">
          <h4>Response Time History</h4>
          <div className="chart-bars">
            {response_times.slice(-10).map((time, index) => (
              <div 
                key={index} 
                className="chart-bar"
                style={{ 
                  // If 'time' is in seconds (like 2.43), we multiply by 1000 to keep the logic consistent
                  height: `${Math.min((time >= 1 ? time * 1000 : time) / 50, 100)}%`,
                  backgroundColor: time > 3 ? '#ef4444' : time > 1 ? '#f59e0b' : '#10b981'
                }}
                title={formatDuration(time)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {errors.length > 0 && (
        <div className="metrics-errors">
          <h4>Recent Errors</h4>
          <ul>
            {errors.slice(-5).map((error, index) => (
              <li key={index} className="error-item">
                {error.message || error} - {error.timestamp || 'Just now'}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MetricsPanel;
