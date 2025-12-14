# Generated Tests

This directory contains automatically generated test files created by the Web-based Testing Agent.

## Structure

Test files are generated in Playwright format with the naming convention:
- `<testName>.spec.js` - Generated test specifications

## Usage

Tests can be executed using:
```bash
npx playwright test <test-file>
```

Or through the API:
```bash
POST /api/tests/execute
{
  "testPath": "<test-file-name>"
}
```
