import React, { useState, useEffect } from 'react';
import ChatPanel from './ChatPanel';
import BrowserView from './BrowserView';
import MetricsPanel from './MetricsPanel';
import { sendMessage, getBrowserState, getMetrics } from '../api';

/**
 * Dashboard Component
 * Main application dashboard that orchestrates all panels
 */
const Dashboard = () => {
  const [messages, setMessages] = useState([]);
  const [browserState, setBrowserState] = useState({
    screenshot: null,
    url: null,
    loading: false
  });
  const [metrics, setMetrics] = useState({});

  useEffect(() => {
    // Poll for updates periodically
    const interval = setInterval(async () => {
      try {
        const [browserData, metricsData] = await Promise.all([
          getBrowserState(),
          getMetrics()
        ]);
        setBrowserState(browserData);
        setMetrics(metricsData);
      } catch (error) {
        console.error('Error fetching updates:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async (content) => {
    const timestamp = new Date().toLocaleTimeString();
    const userMessage = { role: 'user', content, timestamp };
    
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await sendMessage(content);
      const agentMessage = {
        role: 'agent',
        content: response.message,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'system',
        content: 'Error communicating with the agent',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <img src="/logo.png" alt="O2morni Logo" className="dashboard-logo" />
        <div className="dashboard-header-text">
          <h1>O2morni Testing Agent</h1>
          <p>Bani Adam-in-the-Loop Testing Assistant</p>
        </div>
      </header>
      <div className="dashboard-layout">
        <div className="dashboard-left">
          <ChatPanel 
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        </div>
        <div className="dashboard-center">
          <BrowserView 
            screenshot={browserState.screenshot}
            url={browserState.url}
            loading={browserState.loading}
          />
        </div>
        <div className="dashboard-right">
          <MetricsPanel metrics={metrics} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
