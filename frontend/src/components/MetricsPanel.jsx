import React from 'react';

/**
 * MetricsPanel Component
 * Displays test execution metrics and observability data
 */
const MetricsPanel = ({ metrics = {} }) => {
  const {
    testsRun = 0,
    testsPassed = 0,
    testsFailed = 0,
    executionTime = 0,
    coverage = 0,
    errors = []
  } = metrics;

  const successRate = testsRun > 0 
    ? ((testsPassed / testsRun) * 100).toFixed(1) 
    : 0;

  return (
    <div className="metrics-panel">
      <div className="metrics-header">
        <h2>Test Metrics</h2>
      </div>
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
      {errors.length > 0 && (
        <div className="metrics-errors">
          <h3>Recent Errors</h3>
          <ul>
            {errors.map((error, index) => (
              <li key={index} className="error-item">
                {error.message} - {error.timestamp}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MetricsPanel;
