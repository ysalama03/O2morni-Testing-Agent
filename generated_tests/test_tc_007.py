# pytest-playwright configuration
import pytest
from playwright.async_api import async_playwright

# Test case: Valid form_2 Submission (login)
@pytest.mark.asyncio
async def test_valid_form_2_submission(async_playwright):
    """
    Test successful form submission with valid data on https://automationexercise.com/login
    """
    # Create a new browser instance
    browser = await async_playwright().start()
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to the login page
    await page.goto("https://automationexercise.com/login")

    # Wait for the form to load
    await page.wait_for_selector('#email')

    # Fill csrfmiddlewaretoken with valid data
    await page.fill('[data-testid="csrfmiddlewaretoken"]', 'valid_token')
    await page.screenshot(path='step1_csrfmiddlewaretoken.png')

    # Fill email with valid data
    await page.fill('#email', 'valid_email@example.com')
    await page.screenshot(path='step2_email.png')

    # Fill password with valid data
    await page.fill('#password', 'valid_password')
    await page.screenshot(path='step3_password.png')

    # Click submit button
    await page.click('[role="button"][name="Submit"]')
    await page.screenshot(path='step4_submit.png')

    # Wait for response
    await page.wait_for_selector('#login-form')

    # Form submits successfully
    assert await page.query_selector('#login-form')

    # Success message displayed or redirect occurs
    success_message = await page.query_selector('#success')
    assert success_message is not None

    # Close the browser instance
    await browser.close()