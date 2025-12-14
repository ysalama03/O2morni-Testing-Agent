const express = require('express');
const cors = require('cors');
const path = require('path');
const chatRoutes = require('./routes/chat');
const browserRoutes = require('./routes/browser');
const testRoutes = require('./routes/tests');
const metricsRoutes = require('./routes/metrics');
const reportRoutes = require('./routes/reports');
const { initializeBrowser, closeBrowser } = require('./browser/browserControl');
const { initializeObservability } = require('./observability/monitoring');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize observability
initializeObservability(app);

// API Routes
app.use('/api/chat', chatRoutes);
app.use('/api/browser', browserRoutes);
app.use('/api/tests', testRoutes);
app.use('/api/metrics', metricsRoutes);
app.use('/api/reports', reportRoutes);

// Serve static files from generated tests and reports
app.use('/generated-tests', express.static(path.join(__dirname, '../generated_tests')));
app.use('/reports', express.static(path.join(__dirname, '../reports')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error',
    timestamp: new Date().toISOString()
  });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM signal received: closing HTTP server');
  await closeBrowser();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT signal received: closing HTTP server');
  await closeBrowser();
  process.exit(0);
});

// Start server
app.listen(PORT, async () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  
  // Initialize browser on startup
  try {
    await initializeBrowser();
    console.log('Browser initialized successfully');
  } catch (error) {
    console.error('Failed to initialize browser:', error);
  }
});

module.exports = app;
