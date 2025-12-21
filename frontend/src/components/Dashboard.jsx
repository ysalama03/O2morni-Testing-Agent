import React, { useState, useEffect } from 'react';
import ChatPanel from './ChatPanel';
import BrowserView from './BrowserView';
import MetricsPanel from './MetricsPanel';
import { sendMessage, getBrowserState, getMetrics, getExecutionProgress, resetAgent } from '../api';

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
  const [executionProgress, setExecutionProgress] = useState(null);

  useEffect(() => {
    let intervalId = null;
    let isPolling = true;
    
    const pollForUpdates = async () => {
      if (!isPolling) return;
      
      try {
        // Check execution progress first (lightweight check)
        const progressData = await getExecutionProgress().catch(() => ({ progress: null }));
        
        // If test is running, poll more frequently and get all updates
        const isTestRunning = progressData && progressData.progress && progressData.progress.status === 'running';
        
        if (isTestRunning) {
          // Test is running - get all updates including screenshots
          const [browserData, metricsData] = await Promise.all([
            getBrowserState(true),  // Request screenshot for real-time updates
            getMetrics()
          ]);
          
          setBrowserState(prev => ({
            ...prev,
            ...browserData,
            screenshot: browserData.screenshot || prev.screenshot,
            url: browserData.url || prev.url,
            loading: browserData.loading || false
          }));
          
          if (metricsData) {
            setMetrics(prev => ({ ...prev, ...metricsData }));
          }
          
          setExecutionProgress(progressData.progress);
          
          // Poll every 500ms when test is running
          intervalId = setTimeout(pollForUpdates, 500);
        } else {
          // No test running - poll less frequently (every 3 seconds)
          const [browserData, metricsData] = await Promise.all([
            getBrowserState(false),  // Don't request screenshot when idle (saves bandwidth)
            getMetrics()
          ]);
          
          setBrowserState(prev => ({
            ...prev,
            url: browserData.url || prev.url,
            loading: browserData.loading || false
            // Keep existing screenshot when idle
          }));
          
          if (metricsData) {
            setMetrics(prev => ({ ...prev, ...metricsData }));
          }
          
          // Update execution progress
          if (progressData && progressData.progress) {
            setExecutionProgress(progressData.progress);
            
            // If execution is completed, keep it visible for 5 seconds then clear
            if (progressData.progress.status === 'completed') {
              setTimeout(() => {
                setExecutionProgress(null);
              }, 5000);
            }
          } else {
            setExecutionProgress(null);
          }
          
          // Poll every 3 seconds when idle
          intervalId = setTimeout(pollForUpdates, 3000);
        }
      } catch (error) {
        console.error('Error fetching updates:', error);
        // Retry after 3 seconds on error
        intervalId = setTimeout(pollForUpdates, 3000);
      }
    };
    
    // Start polling
    pollForUpdates();

    return () => {
      isPolling = false;
      if (intervalId) {
        clearTimeout(intervalId);
      }
    };
  }, []); // Only run once on mount

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset the agent? This will clear all test data and allow you to start testing a new website.')) {
      try {
        const response = await resetAgent();
        setMessages([]);
        setWorkflowPhase('idle');
        setBrowserState({
          screenshot: null,
          url: null,
          loading: false
        });
        
        // Add reset confirmation message
        const resetMessage = {
          role: 'agent',
          content: response.text || response.message || 'Agent reset successfully. Send a URL to start testing a new website.',
          timestamp: new Date().toISOString(),
          phase: 'idle'
        };
        setMessages([resetMessage]);
      } catch (error) {
        console.error('Error resetting agent:', error);
        const errorMessage = {
          role: 'system',
          content: `Error: ${error.message || 'Failed to reset agent'}`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    }
  };

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
              {(metrics.average_response_time || 0).toFixed(0)}ms
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
            onReset={handleReset}
          />
        </div>
        <div className="dashboard-center">
          <BrowserView 
            screenshot={browserState.screenshot}
            url={browserState.url}
            loading={browserState.loading}
            metrics={metrics}
            executionProgress={executionProgress}
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
