import React from 'react';

/**
 * BrowserView Component
 * Displays the live browser state or screenshots from Playwright
 */
const BrowserView = ({ screenshot, url, loading = false }) => {
  return (
    <div className="browser-view">
      <div className="browser-header">
        <h2>Browser View</h2>
      </div>
      <div className="browser-content">
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
      </div>
    </div>
  );
};

export default BrowserView;
