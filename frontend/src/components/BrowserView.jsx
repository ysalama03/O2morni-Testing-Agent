import React, { useState, useEffect } from 'react';

/**
 * BrowserView Component
 * Displays the live browser state or screenshots from Playwright
 */
const BrowserView = ({ screenshot, url, loading = false }) => {
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

  return (
    <div className="browser-view">
      <div className="browser-header">
        <h2>Browser View</h2>
        {url && <span className="browser-url">{url}</span>}
      </div>
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
