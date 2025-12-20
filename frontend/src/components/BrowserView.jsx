import React, { useState, useEffect } from 'react';

/**
 * BrowserView Component
 * Displays the live browser state or screenshots from Playwright
 */
const BrowserView = ({ screenshot, url, loading = false, executionProgress = null }) => {
  const [displayScreenshot, setDisplayScreenshot] = useState(screenshot);
  const [isImageLoading, setIsImageLoading] = useState(false);

  // Update displayed screenshot only when a new one is provided
  // This prevents flickering during polling
  useEffect(() => {
    if (screenshot) {
      // Only update if it's actually a different screenshot
      if (screenshot !== displayScreenshot) {
        setIsImageLoading(true);
        // Preload the new image before switching
        const img = new Image();
        img.onload = () => {
          setDisplayScreenshot(screenshot);
          setIsImageLoading(false);
        };
        img.onerror = () => {
          setIsImageLoading(false);
        };
        img.src = screenshot;
      }
    }
  }, [screenshot, displayScreenshot]);

  // Get status emoji and color
  const getStepStatusIcon = (status) => {
    switch (status) {
      case 'passed': return { emoji: '✅', color: '#10b981' };
      case 'failed': return { emoji: '❌', color: '#ef4444' };
      case 'error': return { emoji: '⚠️', color: '#f59e0b' };
      case 'running': return { emoji: '⏳', color: '#3b82f6' };
      case 'pending': return { emoji: '⏸️', color: '#6b7280' };
      default: return { emoji: '▶️', color: '#3b82f6' };
    }
  };

  return (
    <div className="browser-view">
      <div className="browser-header">
        <h2>Browser View</h2>
        {url && <span className="browser-url">{url}</span>}
      </div>
      
      {/* Execution Progress Panel */}
      {executionProgress && (executionProgress.status === 'running' || executionProgress.status === 'completed') && (
        <div className="execution-progress-panel">
          <div className="progress-header">
            <h3>🧪 Testing: {executionProgress.test_id}</h3>
            <span className="progress-status">{executionProgress.test_name}</span>
            {executionProgress.status === 'completed' && (
              <span className="completed-badge" style={{ 
                backgroundColor: '#10b981', 
                color: 'white', 
                padding: '4px 8px', 
                borderRadius: '4px',
                fontSize: '12px',
                marginLeft: '10px'
              }}>
                ✅ Completed
              </span>
            )}
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{
                width: `${Math.min((executionProgress.current_step / executionProgress.total_steps) * 100, 100)}%`,
                backgroundColor: executionProgress.status === 'completed' ? '#10b981' : '#3b82f6',
                transition: 'width 0.3s ease, background-color 0.3s ease'
              }}
            />
          </div>
          <div className="progress-info">
            Step {executionProgress.current_step} of {executionProgress.total_steps}
            {executionProgress.status === 'completed' && ' - All steps completed!'}
          </div>
          <div className="steps-list">
            {executionProgress.steps && executionProgress.steps.map((step, index) => {
              const statusInfo = getStepStatusIcon(step.status);
              return (
                <div key={index} className="step-item" style={{ borderLeftColor: statusInfo.color }}>
                  <span className="step-icon">{statusInfo.emoji}</span>
                  <div className="step-content">
                    <div className="step-number">Step {step.step_number}</div>
                    <div className="step-description">{step.description}</div>
                    {step.status !== 'pending' && (
                      <div className="step-status" style={{ color: statusInfo.color }}>
                        {step.status}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      <div className="browser-content">
        {loading && <div className="loading-spinner">Loading browser state...</div>}
        {displayScreenshot && !loading && (
          <img 
            src={displayScreenshot} 
            alt="Browser screenshot" 
            className="browser-screenshot"
            style={{
              opacity: isImageLoading ? 0.7 : 1,
              transition: 'opacity 0.2s ease-in-out'
            }}
          />
        )}
        {!displayScreenshot && !loading && (
          <div className="browser-placeholder">
            <p>No browser content available. Start a test to see the browser state.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BrowserView;
