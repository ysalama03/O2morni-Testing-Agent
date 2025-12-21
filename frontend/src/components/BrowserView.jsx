import React, { useState, useEffect } from 'react';

/**
 * BrowserView Component
 * Displays the live browser state or screenshots from Playwright
 */
const BrowserView = ({ screenshot, url, loading = false, executionProgress = null }) => {
  const [displayScreenshot, setDisplayScreenshot] = useState(screenshot);
  const [isImageLoading, setIsImageLoading] = useState(false);

  // Get the best available screenshot (from prop or execution progress)
  const getBestScreenshot = () => {
    // First priority: screenshot from props (browser state)
    if (screenshot) {
      return screenshot;
    }
    
    // Second priority: latest screenshot from execution progress steps
    if (executionProgress && executionProgress.steps) {
      const stepsWithScreenshots = executionProgress.steps
        .filter(step => step.screenshot)
        .sort((a, b) => (b.step_number || 0) - (a.step_number || 0));
      if (stepsWithScreenshots.length > 0) {
        return stepsWithScreenshots[0].screenshot;
      }
    }
    
    return null;
  };

  const bestScreenshot = getBestScreenshot();

  // Update displayed screenshot only when a new one is provided
  // This prevents flickering during polling
  useEffect(() => {
    if (bestScreenshot) {
      // Only update if it's actually a different screenshot
      if (bestScreenshot !== displayScreenshot) {
        setIsImageLoading(true);
        // Preload the new image before switching
        const img = new Image();
        img.onload = () => {
          setDisplayScreenshot(bestScreenshot);
          setIsImageLoading(false);
        };
        img.onerror = () => {
          setIsImageLoading(false);
        };
        img.src = bestScreenshot;
      }
    } else if (displayScreenshot && !bestScreenshot) {
      // Clear screenshot if it's no longer available
      setDisplayScreenshot(null);
    }
  }, [bestScreenshot, displayScreenshot]);

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
      
      {/* Prominent Test Execution Banner */}
      {executionProgress && executionProgress.status === 'running' && (
        <div style={{
          backgroundColor: '#3b82f6',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontWeight: 'bold',
          fontSize: '16px',
          textAlign: 'center',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          ⏳ Testing {executionProgress.test_id || 'Test'} - Step {executionProgress.current_step || 0} of {executionProgress.total_steps || 0}
        </div>
      )}
      
      {/* Execution Progress Panel - Show prominently when running */}
      {executionProgress && (
        <div className="execution-progress-panel" style={{
          border: executionProgress.status === 'running' ? '2px solid #3b82f6' : '1px solid #e5e7eb',
          backgroundColor: executionProgress.status === 'running' ? '#eff6ff' : '#f9fafb'
        }}>
          <div className="progress-header">
            <h3 style={{ 
              color: executionProgress.status === 'running' ? '#1e40af' : '#374151',
              fontSize: '18px',
              fontWeight: 'bold',
              margin: 0
            }}>
              {executionProgress.status === 'running' ? '⏳' : executionProgress.status === 'completed' ? '✅' : '🧪'} 
              {' '}Testing: {executionProgress.test_id || 'Unknown'}
            </h3>
            <span className="progress-status" style={{ 
              fontSize: '14px',
              color: '#6b7280',
              marginTop: '4px',
              display: 'block'
            }}>
              {executionProgress.test_name || 'Test Execution'}
            </span>
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
          <div className="progress-info" style={{
            fontSize: '14px',
            fontWeight: executionProgress.status === 'running' ? '600' : '400',
            color: executionProgress.status === 'running' ? '#1e40af' : '#374151',
            marginTop: '8px'
          }}>
            {executionProgress.status === 'running' && '🔄 '}
            Step {executionProgress.current_step || 0} of {executionProgress.total_steps || 0}
            {executionProgress.status === 'completed' && ' - ✅ All steps completed!'}
            {executionProgress.status === 'running' && ' - In progress...'}
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
