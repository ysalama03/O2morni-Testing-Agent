import React, { useState, useEffect } from 'react';
import ChatPanel from './ChatPanel';
import BrowserView from './BrowserView';
import MetricsPanel from './MetricsPanel';
import { sendMessage, getBrowserState, getMetrics } from '../api';

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
 * Dashboard Component
 * Main application dashboard that orchestrates the 4-phase testing workflow
 */
const Dashboard = () => {
  const [messages, setMessages] = useState([]);
  const [browserState, setBrowserState] = useState({
    screenshot: null,
    url: null,
    loading: false
  });
  const [metrics, setMetrics] = useState({});
  const [workflowPhase, setWorkflowPhase] = useState('idle');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Poll for updates periodically
    const interval = setInterval(async () => {
      try {
        const [browserData, metricsData] = await Promise.all([
          getBrowserState(),
          getMetrics(),
          fetch('/api/chat/status').then(res => res.json())
        ]);
        
        setBrowserState(prev => ({
          ...prev,
          ...browserData,
          // Keep existing screenshot if the polled data is empty
          screenshot: browserData.screenshot || prev.screenshot,
          url: browserData.url || prev.url
        }));
        if (metricsData) {
          setMetrics(prev => ({ ...prev, ...metricsData }));
        }
      } catch (error) {
        console.error('Error fetching updates:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async (content) => {
    const timestamp = new Date().toISOString();
    const userMessage = { role: 'user', content, timestamp };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendMessage(content);
      
      // Update workflow phase from response
      if (response.phase) {
        setWorkflowPhase(response.phase);
      }
      
      // Update metrics from response
      if (response.metrics) {
        setMetrics(prev => ({ ...prev, ...response.metrics }));
      }
      
      const agentMessage = {
        role: 'agent',
        content: response.text || response.message,
        timestamp: new Date().toISOString(),
        phase: response.phase,
        code: response.code,
        testCases: response.test_cases,
        groundTruth: response.ground_truth
      };
      
      setMessages(prev => [...prev, agentMessage]);
      
      // Update browser state if screenshot is included
      if (response.screenshot) {
        setBrowserState(prev => ({
          ...prev,
          screenshot: response.screenshot
        }));
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'system',
        content: `Error: ${error.message || 'Failed to communicate with the agent'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <img src="/logo.png" alt="O2morni Logo" className="dashboard-logo" />
        <div className="dashboard-header-text">
          <h1>O2morni Testing Agent</h1>
          <p>Human-in-the-Loop Web Testing Assistant</p>
        </div>
        {/* Real-time metrics in header */}
        <div className="header-metrics">
          <div className="header-metric">
            <span className="metric-icon">⏱️</span>
            <span className="metric-value">
              {formatDuration(metrics.average_response_time || 0)}
            </span>
          </div>
          <div className="header-metric">
            <span className="metric-icon">🎯</span>
            <span className="metric-value">
              {(metrics.total_tokens_consumed || 0).toLocaleString()}
            </span>
          </div>
        </div>
      </header>
      <div className="dashboard-layout">
        <div className="dashboard-left">
          <ChatPanel 
            messages={messages}
            onSendMessage={handleSendMessage}
            workflowPhase={workflowPhase}
            isLoading={isLoading}
          />
        </div>
        <div className="dashboard-center">
          <BrowserView 
            screenshot={browserState.screenshot}
            url={browserState.url}
            loading={browserState.loading}
            metrics={metrics}
          />
        </div>
        <div className="dashboard-right">
          <MetricsPanel 
            metrics={metrics}
            workflowPhase={workflowPhase}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
