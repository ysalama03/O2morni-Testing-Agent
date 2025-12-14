/**
 * Reporting Module
 * Manages test reports and results
 */

const fs = require('fs').promises;
const path = require('path');

const REPORTS_DIR = path.join(__dirname, '../../reports');

/**
 * Get list of all reports
 * @returns {Promise<Array>} List of reports
 */
async function getReportList() {
  try {
    await fs.mkdir(REPORTS_DIR, { recursive: true });
    const files = await fs.readdir(REPORTS_DIR);
    
    const reports = [];
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        const filePath = path.join(REPORTS_DIR, file);
        const content = await fs.readFile(filePath, 'utf8');
        const report = JSON.parse(content);
        
        reports.push({
          id: report.id,
          testPath: report.testPath,
          timestamp: report.timestamp,
          success: report.success,
          executionTime: report.executionTime
        });
      }
    }
    
    // Sort by timestamp descending
    reports.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    return reports;
  } catch (error) {
    console.error('Error getting report list:', error);
    return [];
  }
}

/**
 * Get a specific report by ID
 * @param {string} id - Report ID
 * @returns {Promise<Object|null>} Report data or null
 */
async function getReportById(id) {
  try {
    const filePath = path.join(REPORTS_DIR, `${id}.json`);
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error('Error getting report:', error);
    return null;
  }
}

/**
 * Save a screenshot to the reports directory
 * @param {string} name - Screenshot name
 * @param {Buffer} data - Screenshot data
 * @returns {Promise<string>} Screenshot path
 */
async function saveScreenshot(name, data) {
  await fs.mkdir(REPORTS_DIR, { recursive: true });
  const fileName = `screenshot-${name}-${Date.now()}.png`;
  const filePath = path.join(REPORTS_DIR, fileName);
  await fs.writeFile(filePath, data);
  return fileName;
}

/**
 * Clean old reports
 * @param {number} daysToKeep - Number of days to keep reports
 */
async function cleanOldReports(daysToKeep = 7) {
  try {
    const files = await fs.readdir(REPORTS_DIR);
    const cutoffDate = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000);
    
    for (const file of files) {
      const filePath = path.join(REPORTS_DIR, file);
      const stats = await fs.stat(filePath);
      
      if (stats.mtimeMs < cutoffDate) {
        await fs.unlink(filePath);
        console.log(`Deleted old report: ${file}`);
      }
    }
  } catch (error) {
    console.error('Error cleaning old reports:', error);
  }
}

module.exports = {
  getReportList,
  getReportById,
  saveScreenshot,
  cleanOldReports
};
