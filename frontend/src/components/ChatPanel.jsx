import React, { useState, useRef, useEffect } from 'react';

/**
 * ChatPanel Component
 * Provides an interactive chat interface for the 4-phase testing workflow
 * Displays workflow phase and supports markdown rendering
 */
const ChatPanel = ({ onSendMessage, messages = [], workflowPhase = 'idle', isLoading = false, onReset }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Phase info for display
  const phaseInfo = {
    'idle': { emoji: '⏸️', label: 'Ready to Start', hint: 'Send a URL to begin testing' },
    'exploration': { emoji: '🔍', label: 'Phase 1: Exploration', hint: 'Analyzing page structure...' },
    'collaborative_design': { emoji: '📝', label: 'Phase 2: Design', hint: 'Review test cases, approve/reject/revise' },
    'implementation': { emoji: '💻', label: 'Phase 3: Implementation', hint: 'Generating test code...' },
    'verification': { emoji: '✅', label: 'Phase 4: Verification', hint: 'Run tests or refactor' }
  };

  const currentPhase = phaseInfo[workflowPhase] || phaseInfo['idle'];

  // Quick action buttons based on current phase
  const quickActions = {
    'idle': ['Test https://example.com'],
    'exploration': ['Propose test cases'],
    'collaborative_design': ['Approve all', 'Generate code'],
    'implementation': ['Run tests', 'Export tests'],
    'verification': ['Run again', 'Export tests', 'Status']
  };

  const currentActions = quickActions[workflowPhase] || [];

  // Simple markdown-like rendering for code blocks
  const renderContent = (content) => {
    if (!content) return null;
    
    // Split by code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const code = part.replace(/```\w*\n?/g, '').replace(/```$/g, '');
        return (
          <pre key={index} className="code-block">
            <code>{code}</code>
          </pre>
        );
      }
      // Handle inline formatting
      return (
        <span key={index} dangerouslySetInnerHTML={{
          __html: part
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
            .replace(/^## (.*$)/gm, '<h3>$1</h3>')
            .replace(/^### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            .replace(/\n/g, '<br/>')
        }} />
      );
    });
  };

  return (
    <div className="chat-panel">
      {/* Header with phase indicator */}
      <div className="chat-header">
        <h2>🤖 O2morni Testing Agent</h2>
        {onReset && (
          <button 
            className="reset-btn"
            onClick={onReset}
            disabled={isLoading}
            title="Reset agent to start testing a new website"
          >
            🔄 Reset
          </button>
        )}
      </div>

      {/* Phase hint */}
      <div className="phase-hint">
        💡 {currentPhase.hint}
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>Welcome to the Web Testing Agent! 🚀</h3>
            <p>I follow a <strong>4-phase Human-in-the-Loop</strong> workflow:</p>
            <ol>
              <li><strong>Exploration:</strong> Analyze page structure</li>
              <li><strong>Design:</strong> Propose & refine test cases</li>
              <li><strong>Implementation:</strong> Generate Playwright code</li>
              <li><strong>Verification:</strong> Execute & validate tests</li>
            </ol>
            <p>Send me a URL to get started!</p>
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-header">
              <span className="message-role">
                {msg.role === 'user' ? '👤 You' : '🤖 Agent'}
              </span>
              {msg.phase && (
                <span className="message-phase">{msg.phase}</span>
              )}
            </div>
            <div className="message-content">
              {renderContent(msg.content)}
            </div>
            {msg.timestamp && (
              <div className="message-timestamp">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            )}
            {msg.code && (
              <div className="message-code">
                <div className="code-header">
                  <span>Generated Test Code</span>
                  <button 
                    className="copy-btn"
                    onClick={() => navigator.clipboard.writeText(msg.code)}
                  >
                    📋 Copy
                  </button>
                </div>
                <pre><code>{msg.code}</code></pre>
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message agent loading">
            <div className="loading-indicator">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
            <span>Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {currentActions.length > 0 && (
        <div className="quick-actions">
          {currentActions.map((action, index) => (
            <button 
              key={index}
              className="quick-action-btn"
              onClick={() => onSendMessage(action)}
              disabled={isLoading}
            >
              {action}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={isLoading ? 'Please wait...' : 'Type a message or URL to test...'}
          rows={3}
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          <img src="/right-arrow-svgrepo-com.svg" alt="Send" className="send-icon" />
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
