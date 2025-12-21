# pytest-playwright test for Valid form_0 Submission (login)

import pytest
from playwright.async_api import async_playwright

# Test data
valid_credentials = {
    "csrfmiddlewaretoken": "your_csrf_token",
    "email": "test@example.com",
    "password": "password123"
}

# Test function
async def test_valid_login_form_submission(playwright, tmp_path):
    """
    Test successful form submission with valid data on https://automationexercise.com/login

    :param playwright: Playwright instance
    :param tmp_path: Temporary path for screenshot
    """
    # Create a new browser
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to the login page
    await page.goto("https://automationexercise.com/login")

    # Check if page loaded
    await page.wait_for_selector("data-testid=logoin-page")

    # Wait for page to load
    await page.wait_for_load_state("networkidle0")

    # Fill in the form
    await page.fill("data-testid=csrfmiddlewaretoken", valid_credentials["csrfmiddlewaretoken"])
    await page.fill("data-testid=email", valid_credentials["email"])
    await page.fill("data-testid=password", valid_credentials["password"])

    # Wait for submit button to be enabled
    await page.wait_for_selector("data-testid=submit-btn", state="visible")

    # Click submit button
    await page.click("data-testid=submit-btn")

    # Wait for response
    await page.wait_for_selector("data-testid=success-message", state="visible")

    # Check if form submitted successfully
    success_message = await page.query_selector("data-testid=success-message")
    assert success_message is not None, "Form submission failed"

    # Take screenshot at verification point
    await page.screenshot(path=tmp_path / "success_message.png")

    # Check if success message is displayed
    success_message_text = await success_message.text_content()
    assert success_message_text == "You are logged in successfully", "Success message not displayed"

    # Close browser
    await browser.close()


# Main function
async def main():
    # Create a new browser
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Run the test function
    await test_valid_login_form_submission(page)

    # Close the browser
    await browser.close()


# Run the test using pytest-playwright
pytest.main([__file__, "--headed", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "-v"])