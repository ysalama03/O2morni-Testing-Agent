import React, { useState } from 'react';
import MetricsPanel from './MetricsPanel';

/**
 * BrowserView Component
 * Displays the live browser state or screenshots from Playwright
 */
const BrowserView = ({ screenshot, url, loading = false, metrics = {} }) => {
  const [showMetrics, setShowMetrics] = useState(false);

  return (
    <div className="browser-view">
      <div className="browser-header">
        <h2>{showMetrics ? 'Metrics' : 'Browser View'}</h2>
        <button 
          className={`metrics-button ${showMetrics ? 'active' : ''}`}
          onClick={() => setShowMetrics(!showMetrics)}
        >
          <img src="/metrics-icon.svg" alt="Metrics" className="metrics-icon" />
        </button>
      </div>
      <div className="browser-content">
        {showMetrics ? (
          <div className="browser-metrics-view">
            <MetricsPanel metrics={metrics} />
          </div>
        ) : (
          <>
            {loading && <div className="loading-spinner">Loading browser state...</div>}
            {screenshot && !loading && (
              <img 
                src={screenshot} 
                alt="Browser screenshot" 
                className="browser-screenshot"
              />
            )}
            {!screenshot && !loading && (
              <div className="browser-placeholder">
                <p>No browser content available. Start a test to see the browser state.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default BrowserView;
